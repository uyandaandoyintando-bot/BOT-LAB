from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.auth import require_admin_key
from backend.services.license_service import create_license
from database.database import SessionLocal
from database.models import Product


admin_bp = Blueprint("admin", __name__)


# ============================================================
# CREATE PRODUCT
# ============================================================

@admin_bp.post("/products")
@require_admin_key
def create_product():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    description = str(
        data.get("description", "")
    ).strip()

    subscription_tier = str(
        data.get("subscription_tier", "")
    ).strip().lower()

    price_cents = data.get("price_cents")
    duration_days = data.get("duration_days")

    if not name:
        return jsonify({
            "error": "name is required"
        }), 400

    if subscription_tier not in {
        "basic",
        "advanced",
        "premium",
    }:
        return jsonify({
            "error": (
                "subscription_tier must be "
                "basic, advanced, or premium"
            )
        }), 400

    try:
        price_cents = int(price_cents)
        duration_days = int(duration_days)
    except (TypeError, ValueError):
        return jsonify({
            "error": (
                "price_cents and duration_days "
                "must be integers"
            )
        }), 400

    if price_cents < 0:
        return jsonify({
            "error": "price_cents cannot be negative"
        }), 400

    if duration_days <= 0:
        return jsonify({
            "error": "duration_days must be positive"
        }), 400

    with SessionLocal() as db:
        product = Product(
            name=name,
            description=description or None,
            subscription_tier=subscription_tier,
            price_cents=price_cents,
            currency="USD",
            duration_days=duration_days,
            active=True,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return jsonify({
            "success": True,
            "product": {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "subscription_tier": (
                    product.subscription_tier
                ),
                "price_cents": product.price_cents,
                "currency": product.currency,
                "duration_days": product.duration_days,
                "active": product.active,
            },
        }), 201


# ============================================================
# LIST PRODUCTS
# ============================================================

@admin_bp.get("/products")
@require_admin_key
def list_products():
    with SessionLocal() as db:
        products = (
            db.query(Product)
            .order_by(Product.id)
            .all()
        )

        return jsonify({
            "products": [
                {
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "subscription_tier": (
                        product.subscription_tier
                    ),
                    "price_cents": product.price_cents,
                    "currency": product.currency,
                    "duration_days": (
                        product.duration_days
                    ),
                    "active": product.active,
                }
                for product in products
            ]
        }), 200


# ============================================================
# GENERATE LICENSE
# ============================================================

@admin_bp.post("/licenses")
@require_admin_key
def generate_license():
    data = request.get_json(silent=True) or {}

    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return jsonify({
            "error": "product_id is required"
        }), 400

    try:
        max_activations = int(
            data.get("max_activations", 1)
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": (
                "max_activations must be an integer"
            )
        }), 400

    if max_activations < 1:
        return jsonify({
            "error": (
                "max_activations must be at least 1"
            )
        }), 400

    with SessionLocal() as db:
        product = db.get(
            Product,
            product_id,
        )

        if product is None or not product.active:
            return jsonify({
                "error": "Product not found"
            }), 404

        license_key, license_record = create_license(
            product,
            max_activations=max_activations,
        )

        db.add(license_record)
        db.commit()
        db.refresh(license_record)

        return jsonify({
            "success": True,
            "license_key": license_key,
            "product": product.name,
            "subscription_tier": (
                product.subscription_tier
            ),
            "expires_at": (
                license_record.expires_at.isoformat()
                if license_record.expires_at
                else None
            ),
            "max_activations": (
                license_record.max_activations
            ),
        }), 201
