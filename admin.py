from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.services.licenses import create_license
from database.database import SessionLocal
from database.models import Product


admin_bp = Blueprint("admin", __name__)


@admin_bp.post("/products")
def create_product():
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    tier = str(
        data.get("subscription_tier", "")
    ).strip().lower()
    description = str(
        data.get("description", "")
    ).strip()

    price_cents = data.get("price_cents")
    duration_days = data.get("duration_days")

    if not name:
        return jsonify({"error": "name is required"}), 400

    if tier not in {"basic", "advanced", "premium"}:
        return jsonify(
            {
                "error": (
                    "subscription_tier must be "
                    "basic, advanced, or premium"
                )
            }
        ), 400

    try:
        price_cents = int(price_cents)
        duration_days = int(duration_days)
    except (TypeError, ValueError):
        return jsonify(
            {
                "error": (
                    "price_cents and duration_days "
                    "must be integers"
                )
            }
        ), 400

    if price_cents < 0 or duration_days <= 0:
        return jsonify(
            {
                "error": (
                    "price_cents must be >= 0 and "
                    "duration_days must be > 0"
                )
            }
        ), 400

    with SessionLocal() as db:
        product = Product(
            name=name,
            description=description or None,
            subscription_tier=tier,
            price_cents=price_cents,
            currency="USD",
            duration_days=duration_days,
            active=True,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

        return jsonify(
            {
                "success": True,
                "product": {
                    "id": product.id,
                    "name": product.name,
                    "subscription_tier": (
                        product.subscription_tier
                    ),
                    "price_cents": product.price_cents,
                    "currency": product.currency,
                    "duration_days": (
                        product.duration_days
                    ),
                },
            }
        ), 201


@admin_bp.post("/licenses")
def generate_license():
    data = request.get_json(silent=True) or {}

    try:
        product_id = int(data.get("product_id"))
    except (TypeError, ValueError):
        return jsonify(
            {"error": "product_id is required"}
        ), 400

    try:
        max_activations = int(
            data.get("max_activations", 1)
        )
    except (TypeError, ValueError):
        return jsonify(
            {
                "error": (
                    "max_activations must be an integer"
                )
            }
        ), 400

    if max_activations < 1:
        return jsonify(
            {
                "error": (
                    "max_activations must be at least 1"
                )
            }
        ), 400

    with SessionLocal() as db:
        product = db.get(Product, product_id)

        if product is None or not product.active:
            return jsonify(
                {"error": "Product not found"}
            ), 404

        plain_key, license_record = create_license(
            product,
            max_activations=max_activations,
        )

        db.add(license_record)
        db.commit()
        db.refresh(license_record)

        return jsonify(
            {
                "success": True,
                "license_key": plain_key,
                "subscription_tier": (
                    product.subscription_tier
                ),
                "product": product.name,
                "expires_at": (
                    license_record.expires_at.isoformat()
                    if license_record.expires_at
                    else None
                ),
                "max_activations": (
                    license_record.max_activations
                ),
            }
        ), 201
