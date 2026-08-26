from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.services.license_service import (
    activate_license,
    can_activate_license,
    verify_license_key,
)
from database.database import SessionLocal
from database.models import License


licenses_bp = Blueprint("licenses", __name__)


# ============================================================
# REDEEM / ACTIVATE LICENSE
# ============================================================

@licenses_bp.post("/redeem")
def redeem_license():
    data = request.get_json(silent=True) or {}

    license_key = str(
        data.get("license_key", "")
    ).strip()

    if not license_key:
        return jsonify({
            "error": "license_key is required"
        }), 400

    with SessionLocal() as db:
        licenses = (
            db.query(License)
            .all()
        )

        license_record = None

        for record in licenses:
            if verify_license_key(
                license_key,
                record,
            ):
                license_record = record
                break

        if license_record is None:
            return jsonify({
                "error": "Invalid license key"
            }), 404

        allowed, reason = can_activate_license(
            license_record
        )

        if not allowed:
            return jsonify({
                "error": reason
            }), 400

        activate_license(
            license_record
        )

        db.commit()
        db.refresh(license_record)

        product = license_record.product

        return jsonify({
            "success": True,
            "message": "License redeemed successfully",
            "subscription_tier": (
                product.subscription_tier
            ),
            "product": product.name,
            "status": license_record.status,
            "activation_count": (
                license_record.activation_count
            ),
            "max_activations": (
                license_record.max_activations
            ),
            "expires_at": (
                license_record.expires_at.isoformat()
                if license_record.expires_at
                else None
            ),
        }), 200


# ============================================================
# CHECK LICENSE
# ============================================================

@licenses_bp.post("/check")
def check_license():
    data = request.get_json(silent=True) or {}

    license_key = str(
        data.get("license_key", "")
    ).strip()

    if not license_key:
        return jsonify({
            "error": "license_key is required"
        }), 400

    with SessionLocal() as db:
        licenses = (
            db.query(License)
            .all()
        )

        license_record = None

        for record in licenses:
            if verify_license_key(
                license_key,
                record,
            ):
                license_record = record
                break

        if license_record is None:
            return jsonify({
                "error": "Invalid license key"
            }), 404

        product = license_record.product

        return jsonify({
            "valid": (
                license_record.status
                != "revoked"
            ),
            "subscription_tier": (
                product.subscription_tier
            ),
            "product": product.name,
            "status": license_record.status,
            "activation_count": (
                license_record.activation_count
            ),
            "max_activations": (
                license_record.max_activations
            ),
            "expires_at": (
                license_record.expires_at.isoformat()
                if license_record.expires_at
                else None
            ),
        }), 200
