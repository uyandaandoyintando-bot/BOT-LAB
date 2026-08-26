from __future__ import annotations

from flask import Blueprint, jsonify

from database.database import SessionLocal
from database.models import Product


products_bp = Blueprint("products", __name__)


@products_bp.get("/")
def list_products():
    with SessionLocal() as db:
        products = (
            db.query(Product)
            .filter(Product.active.is_(True))
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
                }
                for product in products
            ]
        }), 200


@products_bp.get("/<int:product_id>")
def get_product(product_id: int):
    with SessionLocal() as db:
        product = db.get(Product, product_id)

        if product is None or not product.active:
            return jsonify({
                "error": "Product not found"
            }), 404

        return jsonify({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "subscription_tier": (
                product.subscription_tier
            ),
            "price_cents": product.price_cents,
            "currency": product.currency,
            "duration_days": product.duration_days,
        }), 200
