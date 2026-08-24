from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.services.license_service import create_license
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
# CREATE PAYPAL ORDER
# ============================================================

@paypal_bp.post("/create-order")
async def create_order():
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
                discord_id=discord_id
            )
            db.add(customer)
            db.flush()

        order = create_pending_order(
            db,
            customer,
            product,
        )

        try:
            paypal_data = await create_paypal_order(
                amount_cents=order.amount_cents,
                currency=order.currency,
                public_order_id=order.public_id,
                description=product.name,
            )
        except Exception:
            db.rollback()

            return jsonify({
                "error": "Unable to create PayPal order"
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
            "product": product.name,
            "subscription_tier": (
                product.subscription_tier
            ),
            "amount_cents": order.amount_cents,
            "currency": order.currency,
            "approval_url": approval_url,
        }), 201


# ============================================================
# CAPTURE PAYMENT
# ============================================================

@paypal_bp.post("/capture")
async def capture_payment():
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
                "error": "Order not found"
            }), 404

        # Prevent duplicate license generation.
        if order.status == "paid":
            existing_license = (
                db.query(License)
                .filter(
                    License.order_id == order.id
                )
                .first()
            )

            return jsonify({
                "success": True,
                "already_processed": True,
                "order_id": order.public_id,
                "subscription_tier": (
                    order.product.subscription_tier
                    if order.product
                    else None
                ),
                "license_last4": (
                    existing_license.license_key_last4
                    if existing_license
                    else None
                ),
            }), 200

        try:
            paypal_data = await capture_paypal_order(
                paypal_order_id
            )
        except Exception:
            return jsonify({
                "error": "PayPal capture failed"
            }), 502

        if paypal_data.get("status") != "COMPLETED":
            return jsonify({
                "error": "Payment was not completed",
                "paypal_status": paypal_data.get(
                    "status"
                ),
            }), 400

        purchase_units = paypal_data.get(
            "purchase_units",
            [],
        )

        if not purchase_units:
            return jsonify({
                "error": "Invalid PayPal response"
            }), 502

        captures = (
            purchase_units[0]
            .get("payments", {})
            .get("captures", [])
        )

        if not captures:
            return jsonify({
                "error": "No PayPal capture found"
            }), 502

        capture = captures[0]

        captured_amount = capture.get(
            "amount",
            {},
        )

        expected_amount = (
            f"{order.amount_cents / 100:.2f}"
        )

        actual_amount = captured_amount.get(
            "value"
        )

        actual_currency = captured_amount.get(
            "currency_code"
        )

        # Never trust PayPal success alone.
        # Verify amount and currency against our DB.
        if actual_amount != expected_amount:
            return jsonify({
                "error": "Payment amount mismatch"
            }), 400

        if actual_currency != order.currency:
            return jsonify({
                "error": "Payment currency mismatch"
            }), 400

        product = db.get(
            Product,
            order.product_id,
        )

        if product is None:
            return jsonify({
                "error": "Product not found"
            }), 500

        capture_id = capture.get("id")

        mark_order_paid(
            db,
            order,
            paypal_order_id,
            capture_id,
        )

        license_key, license_record = create_license(
            product,
            order_id=order.id,
            customer_id=order.customer_id,
            max_activations=1,
        )

        db.add(license_record)

        db.commit()

        return jsonify({
            "success": True,
            "order_id": order.public_id,
            "paypal_order_id": paypal_order_id,
            "product": product.name,
            "subscription_tier": (
                product.subscription_tier
            ),
            "license_key": license_key,
            "expires_at": (
                license_record.expires_at.isoformat()
                if license_record.expires_at
                else None
            ),
        }), 200


# ============================================================
# GET PAYPAL ORDER
# ============================================================

@paypal_bp.get("/order/<paypal_order_id>")
async def get_order(paypal_order_id: str):
    if not paypal_order_id.strip():
        return jsonify({
            "error": "Invalid PayPal order ID"
        }), 400

    try:
        paypal_data = await get_paypal_order(
            paypal_order_id
        )
    except Exception:
        return jsonify({
            "error": "Unable to retrieve PayPal order"
        }), 502

    return jsonify({
        "id": paypal_data.get("id"),
        "status": paypal_data.get("status"),
    }), 200
