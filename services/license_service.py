from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from database.models import License, Product


def generate_license_key() -> str:
    """
    Generate a license key that is safe to show to a customer.
    The raw key is returned only at creation time.
    """

    parts = [
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
    ]

    return "BL-" + "-".join(parts)


def hash_license_key(license_key: str) -> str:
    return hashlib.sha512(
        license_key.strip().encode("utf-8")
    ).hexdigest()


def create_license(
    product: Product,
    *,
    order_id: int | None = None,
    customer_id: int | None = None,
    max_activations: int = 1,
) -> tuple[str, License]:
    """
    Create a license.

    Returns:
        (raw_license_key, License_record)

    The raw key should only be shown to the customer once.
    """

    raw_key = generate_license_key()

    key_hash = hash_license_key(
        raw_key
    )

    duration_days = product.duration_days

    expires_at = None

    if duration_days is not None:
        expires_at = (
            datetime.utcnow()
            + timedelta(days=duration_days)
        )

    license_record = License(
        license_key_hash=key_hash,
        license_key_last4=raw_key[-4:],
        order_id=order_id,
        customer_id=customer_id,
        product_id=product.id,
        status="unused",
        activation_count=0,
        max_activations=max_activations,
        expires_at=expires_at,
    )

    return raw_key, license_record


def verify_license_key(
    license_key: str,
    license_record: License,
) -> bool:
    """
    Compare a supplied license key against
    the stored SHA-512 hash.
    """

    if not license_key.strip():
        return False

    supplied_hash = hash_license_key(
        license_key
    )

    return secrets.compare_digest(
        supplied_hash,
        license_record.license_key_hash,
    )


def can_activate_license(
    license_record: License,
) -> tuple[bool, str]:
    """
    Check whether the license can currently
    be activated.
    """

    if license_record.status == "revoked":
        return False, "License has been revoked"

    if license_record.revoked_at is not None:
        return False, "License has been revoked"

    if (
        license_record.expires_at is not None
        and datetime.utcnow()
        >= license_record.expires_at
    ):
        license_record.status = "expired"
        return False, "License has expired"

    if (
        license_record.activation_count
        >= license_record.max_activations
    ):
        return False, "Activation limit reached"

    return True, ""


def activate_license(
    license_record: License,
) -> License:
    """
    Activate a valid license.
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

    return license_record


def revoke_license(
    license_record: License,
) -> License:
    """
    Revoke a license.
    """

    license_record.status = "revoked"
    license_record.revoked_at = (
        datetime.utcnow()
    )

    return license_record
