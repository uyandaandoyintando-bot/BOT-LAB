from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from database.models import License, Product


VALID_STATUSES = {
    "unused",
    "active",
    "expired",
    "revoked",
}


def hash_value(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def generate_license_key() -> str:
    """
    Generate a license key.

    The full key is only returned when the license is created.
    The database stores a hash instead of the raw key.
    """

    parts = [
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
        secrets.token_hex(4).upper(),
    ]

    return "BOTLAB-" + "-".join(parts)


def create_license(
    product: Product,
    *,
    order_id: int | None = None,
    max_activations: int = 1,
) -> tuple[str, License]:
    """
    Create a new license for a product.

    Returns:
        (plain_text_license_key, database_license)
    """

    plain_key = generate_license_key()

    license_record = License(
        license_key_hash=hash_value(plain_key),
        license_key_last4=plain_key[-4:],
        order_id=order_id,
        product_id=product.id,
        status="unused",
        activation_count=0,
        max_activations=max_activations,
    )

    if product.duration_days:
        license_record.expires_at = (
            datetime.utcnow()
            + timedelta(days=product.duration_days)
        )

    return plain_key, license_record


def find_license(
    db,
    plain_key: str,
) -> License | None:
    """
    Find a license using its plain-text key.
    """

    key_hash = hash_value(plain_key)

    license_record = (
        db.query(License)
        .filter(
            License.license_key_hash == key_hash
        )
        .first()
    )

    return license_record


def validate_license(
    license_record: License,
) -> tuple[bool, str]:
    """
    Validate a license before redemption/activation.
    """

    if license_record.status == "revoked":
        return False, "License has been revoked."

    if license_record.revoked_at is not None:
        return False, "License has been revoked."

    if (
        license_record.expires_at is not None
        and license_record.expires_at <= datetime.utcnow()
    ):
        license_record.status = "expired"
        return False, "License has expired."

    if (
        license_record.activation_count
        >= license_record.max_activations
        and license_record.status != "active"
    ):
        return False, "Activation limit reached."

    return True, "License is valid."


def redeem_license(
    db,
    license_record: License,
    customer_id: int,
    hwid: str | None = None,
) -> tuple[bool, str]:
    """
    Redeem/activate a license for a customer.
    """

    valid, message = validate_license(
        license_record
    )

    if not valid:
        return False, message

    if (
        license_record.customer_id is not None
        and license_record.customer_id != customer_id
    ):
        return False, "License belongs to another account."

    if license_record.status == "active":
        if (
            hwid
            and license_record.hwid_hash
            and hash_value(hwid)
            != license_record.hwid_hash
        ):
            return False, "License is already bound to another HWID."

        return True, "License is already active."

    license_record.customer_id = customer_id
    license_record.status = "active"
    license_record.activated_at = datetime.utcnow()

    if hwid:
        license_record.hwid_hash = hash_value(hwid)

    license_record.activation_count += 1

    return True, "License activated successfully."
