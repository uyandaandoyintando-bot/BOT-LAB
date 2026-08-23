from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from backend.services.licenses import create_license
from backend.services.order_service import (
    create_pending_order,
    mark_order_paid,
)
from backend.services.paypal_service import (
    capture_paypal_order,
    create_paypal_order,
    get_paypal_order,
)
from database.database import SessionLocal
from database.models import Customer, License, Order, Product


paypal_bp = Blueprint("paypal", __name__)


# ============================================================
# CREATE PAYPAL CHECKOUT
# ============================================================

@paypal_bp.post("/create-order")
def create_order():
    data = request.get_json(silent=True) or {}

    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "product_id is required"
        }), 400

    discord_id = str(
        data.get("discord_id", "")
    ).strip()

    if not discord_id:
        return jsonify({
            "error": "discord_id is required"
        }), 400

    with SessionLocal() as db:
        product = db.get(Product, product_id)

        if product is None or not product.active:
            return jsonify({
                "error": "Product not found"
            }), 404

        customer = (
            db.query(Customer)
            .filter(
                Customer.discord_id == discord_id
            )
            .first()
        )

        if customer is None:
            customer = Customer(
                discord_id=discord_id,
            )
            db.add(customer)
            db.flush()

        order = create_pending_order(
            db,
            customer,
            product,
        )

        try:
            paypal_data = await_create_paypal_order(
                order,
                product,
            )
        except Exception as exc:
            db.rollback()

            return jsonify({
                "error": "Unable to create PayPal order",
                "details": str(exc),
            }), 502

        paypal_order_id = paypal_data.get("id")

        if not paypal_order_id:
            db.rollback()

            return jsonify({
                "error": "PayPal did not return an order ID"
            }), 502

        order.paypal_order_id = paypal_order_id

        db.commit()

        approval_url = None

        for link in paypal_data.get("links", []):
            if link.get("rel") == "approve":
                approval_url = link.get("href")
                break

        return jsonify({
            "success": True,
            "order_id": order.public_id,
            "paypal_order_id": paypal_order_id,
            "subscription_tier": (
                product.subscription_tier
            ),
            "amount_cents": order.amount_cents,
            "currency": order.currency,
            "approval_url": approval_url,
        }), 201


async def await_create_paypal_order(
    order: Order,
    product: Product,
) -> dict:
    return await create_paypal_order(
        amount_cents=order.amount_cents,
        currency=order.currency,
        public_order_id=order.public_id,
        description=product.name,
    )


# ============================================================
# CAPTURE PAYPAL PAYMENT
# ============================================================

@paypal_bp.post("/capture")
async def capture():
    data = request.get_json(silent=True) or {}

    paypal_order_id = str(
        data.get("paypal_order_id", "")
    ).strip()

    if not paypal_order_id:
        return jsonify({
            "error": "paypal_order_id is required"
        }), 400

    with SessionLocal() as db:
        order = (
            db.query(Order)
            .filter(
                Order.paypal_order_id
                == paypal_order_id
            )
            .first()
        )

        if order is None:
            return jsonify({
                "error": "Local order not found"
            }), 404

        if order.status == "paid":
            license_record = (
                db.query(License)
                .filter(
                    License.order_id == order.id
                )
                .first()
            )

            return jsonify({
                "success": True,
                "message": "Order already processed",
                "order_id": order.public_id,
                "license_status": (
                    license_record.status
                    if license_record
                    else None
                ),
            }), 200

        try:
            paypal_data = await capture_paypal_order(
                paypal_order_id
            )
        except Exception as exc:
            return jsonify({
                "error": "PayPal capture failed",
                "details": str(exc),
            }), 502

        if paypal_data.get("status") != "COMPLETED":
            return jsonify({
                "error": "Payment was not completed",
                "paypal_status": paypal_data.get(
                    "status"
                ),
            }), 400

        # ----------------------------------------------------
        # Verify the captured amount/currency against our
        # trusted local order.
        # ----------------------------------------------------

        purchase_units = paypal_data.get(
            "purchase_units",
            [],
        )

        if not purchase_units:
            return jsonify({
                "error": "PayPal response has no purchase units"
            }), 502

        captured_amount = (
            purchase_units[0]
            .get("payments", {})
            .get("captures", [{}])[0]
            .get("amount", {})
        )

        expected_value = (
            f"{order.amount_cents / 100:.2f}"
        )

        actual_value = captured_amount.get(
            "value"
        )

        actual_currency = captured_amount.get(
            "currency_code"
        )

        if actual_value != expected_value:
            return jsonify({
                "error": "Payment amount mismatch"
            }), 400

        if actual_currency != order.currency:
            return jsonify({
                "error": "Payment currency mismatch"
            }), 400

        capture_id = (
            purchase_units[0]
            .get("payments", {})
            .get("captures", [{}])[0]
            .get("id")
        )

        product = db.get(
            Product,
            order.product_id,
        )

        if product is None:
            return jsonify({
                "error": "Product no longer exists"
            }), 500

        payment = mark_order_paid(
            db,
            order,
            paypal_order_id,
            capture_id,
        )

        # ----------------------------------------------------
        # Generate the license only after successful payment.
        # ----------------------------------------------------

        license_key, license_record = create_license(
            product,
            order_id=order.id,
            max_activations=1,
        )

        license_record.customer_id = (
            order.customer_id
        )

        db.add(license_record)

        db.commit()

        return jsonify({
            "success": True,
            "order_id": order.public_id,
            "payment_id": payment.id,
            "license_key": license_key,
            "subscription_tier": (
                product.subscription_tier
            ),
            "product": product.name,
            "expires_at": (
                license_record.expires_at.isoformat()
                if license_record.expires_at
                else None
            ),
        }), 200


# ============================================================
# CHECK PAYPAL ORDER
# ============================================================

@paypal_bp.get("/order/<paypal_order_id>")
async def get_order(paypal_order_id: str):
    try:
        data = await get_paypal_order(
            paypal_order_id
        )
    except Exception as exc:
        return jsonify({
            "error": "Unable to retrieve PayPal order",
            "details": str(exc),
        }), 502

    return jsonify(data), 200
