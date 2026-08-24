from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from database.models import License, Product


def generate_license_key() -> str:
    """
    Generate a license key that is safe to give to the customer.

    Example:
        BOTLAB-BASIC-A1B2-C3D4-E5F6-G7H8
    """

    groups = [
        secrets.token_hex(2).upper()
        for _ in range(4)
    ]

    return "BOTLAB-" + "-".join(groups)


def hash_license_key(license_key: str) -> str:
    return hashlib.sha256(
        license_key.strip().upper().encode("utf-8")
    ).hexdigest()


def create_license(
    product: Product,
    *,
    order_id: int | None = None,
    customer_id: int | None = None,
    max_activations: int = 1,
) -> tuple[str, License]:
    """
    Create a license for a product.

    The plaintext license key is returned once to the caller.
    Only its SHA-256 hash is stored in the database.
    """

    if max_activations < 1:
        raise ValueError(
            "max_activations must be at least 1"
        )

    license_key = generate_license_key()

    license_record = License(
        license_key_hash=hash_license_key(
            license_key
        ),
        license_key_last4=license_key[-4:],
        order_id=order_id,
        customer_id=customer_id,
        product_id=product.id,
        status="unused",
        activation_count=0,
        max_activations=max_activations,
    )

    if product.duration_days:
        license_record.expires_at = (
            datetime.utcnow()
            + timedelta(
                days=product.duration_days
            )
        )

    return license_key, license_record


def verify_license_key(
    license_key: str,
    license_record: License,
) -> bool:
    """
    Check a supplied license key against the
    stored hash.
    """

    if not license_key:
        return False

    supplied_hash = hash_license_key(
        license_key
    )

    return supplied_hash == (
        license_record.license_key_hash
    )


def is_license_expired(
    license_record: License,
) -> bool:
    if license_record.expires_at is None:
        return False

    return datetime.utcnow() >= (
        license_record.expires_at
    )


def can_activate_license(
    license_record: License,
) -> tuple[bool, str]:
    """
    Check whether a license is currently
    eligible for activation.
    """

    if license_record.status == "revoked":
        return False, "License has been revoked"

    if is_license_expired(license_record):
        return False, "License has expired"

    if (
        license_record.activation_count
        >= license_record.max_activations
    ):
        return False, "Activation limit reached"

    return True, "License can be activated"


def activate_license(
    license_record: License,
) -> None:
    """
    Mark a license as activated.
    """

    allowed, reason = can_activate_license(
        license_record
    )

    if not allowed:
        raise ValueError(reason)

    license_record.activation_count += 1

    if license_record.status == "unused":
        license_record.status = "active"
        license_record.activated_at = (
            datetime.utcnow()
        )


def revoke_license(
    license_record: License,
) -> None:
    """
    Revoke a license.
    """

    license_record.status = "revoked"
    license_record.revoked_at = (
        datetime.utcnow()
  )
