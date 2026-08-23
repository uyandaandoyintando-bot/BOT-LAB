from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


# ============================================================
# PRODUCT
# ============================================================

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    subscription_tier: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="basic",
    )

    price_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
    )

    duration_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# CUSTOMER
# ============================================================

class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    discord_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# ORDER
# ============================================================

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    public_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id"),
        nullable=False,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="USD",
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
    )

    paypal_order_id: Mapped[str | None] = mapped_column(
        String(100),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    customer: Mapped["Customer"] = relationship()

    product: Mapped["Product"] = relationship()


# ============================================================
# PAYMENT
# ============================================================

class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"),
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    provider_payment_id: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    amount_cents: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# LICENSE
# ============================================================

class License(Base):
    __tablename__ = "licenses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    license_key_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    license_key_last4: Mapped[str] = mapped_column(
        String(4),
        nullable=False,
    )

    order_id: Mapped[int | None] = mapped_column(
        ForeignKey("orders.id"),
        nullable=True,
    )

    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customers.id"),
        nullable=True,
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="unused",
    )

    hwid_hash: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )

    activation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_activations: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    product: Mapped["Product"] = relationship()


# ============================================================
# DOWNLOAD TOKEN
# ============================================================

class DownloadToken(Base):
    __tablename__ = "download_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
    )

    license_id: Mapped[int] = mapped_column(
        ForeignKey("licenses.id"),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    download_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    max_downloads: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


# ============================================================
# AUDIT LOG
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    actor_discord_id: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    target_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
