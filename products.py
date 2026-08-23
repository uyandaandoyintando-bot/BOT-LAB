from __future__ import annotations

from flask import Blueprint, jsonify, request
from sqlalchemy import select

from database.database import SessionLocal
from database.models import Product


products_bp = Blueprint(
    "products",
    __name__,
)


VALID_TIERS = {
    "basic",
    "advanced",
    "premium",
}


@products_bp.get("/")
def list_products():
    """
    Return all active products.
    """

    with SessionLocal() as db:
        products = db.scalars(
            select(Product)
            .where(Product.active.is_(True))
            .order_by(Product.price_cents)
        ).all()

        return jsonify(
            {
                "products": [
                    {
                        "id": product.id,
                        "name": product.name,
                        "description": product.description,
                        "subscription_tier": product.subscription_tier,
                        "price_cents": product.price_cents,
                        "currency": product.currency,
                        "duration_days": product.duration_days,
                    }
                    for product in products
                ]
            }
        )


@products_bp.get("/<int:product_id>")
def get_product(product_id: int):
    """
    Return one active product.
    """

    with SessionLocal() as db:
        product = db.get(Product, product_id)

        if product is None or not product.active:
            return jsonify(
                {
                    "error": "Product not found"
                }
            ), 404

        return jsonify(
            {
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "subscription_tier": product.subscription_tier,
                "price_cents": product.price_cents,
                "currency": product.currency,
                "duration_days": product.duration_days,
            }
        )


@products_bp.post("/")
def create_product():
    """
    Create a product.

    This endpoint will later be protected by the
    admin authentication system.
    """

    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    description = data.get("description")
    tier = str(
        data.get("subscription_tier", "")
    ).strip().lower()

    price_cents = data.get("price_cents")
    currency = str(
        data.get("currency", "USD")
    ).strip().upper()

    duration_days = data.get("duration_days")

    if not name:
        return jsonify(
            {
                "error": "Product name is required"
            }
        ), 400

    if tier not in VALID_TIERS:
        return jsonify(
            {
                "error": "subscription_tier must be "
                         "basic, advanced, or premium"
            }
        ), 400

    try:
        price_cents = int(price_cents)
    except (TypeError, ValueError):
        return jsonify(
            {
                "error": "price_cents must be an integer"
            }
        ), 400

    if price_cents < 0:
        return jsonify(
            {
                "error": "price_cents cannot be negative"
            }
        ), 400

    if duration_days is not None:
        try:
            duration_days = int(duration_days)
        except (TypeError, ValueError):
            return jsonify(
                {
                    "error": "duration_days must be an integer"
                }
            ), 400

        if duration_days <= 0:
            return jsonify(
                {
                    "error": "duration_days must be positive"
                }
            ), 400

    product = Product(
        name=name,
        description=description,
        subscription_tier=tier,
        price_cents=price_cents,
        currency=currency,
        duration_days=duration_days,
        active=True,
    )

    with SessionLocal() as db:
        db.add(product)
        db.commit()
        db.refresh(product)

        return jsonify(
            {
                "id": product.id,
                "name": product.name,
                "subscription_tier": product.subscription_tier,
                "price_cents": product.price_cents,
                "currency": product.currency,
                "duration_days": product.duration_days,
            }
        ), 201
