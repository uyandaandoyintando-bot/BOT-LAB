from __future__ import annotations

import secrets
from datetime import datetime

from database.models import Customer, Order, Payment, Product


def generate_public_order_id() -> str:
    return (
        "BL-"
        + secrets.token_hex(8).upper()
    )


def create_pending_order(
    db,
    customer: Customer,
    product: Product,
) -> Order:
    """
    Create a local pending order using the
    product price stored in the database.
    """

    order = Order(
        public_id=generate_public_order_id(),
        customer_id=customer.id,
        product_id=product.id,
        amount_cents=product.price_cents,
        currency=product.currency,
        status="pending",
    )

    db.add(order)
    db.flush()

    return order


def mark_order_paid(
    db,
    order: Order,
    paypal_order_id: str,
    capture_id: str | None = None,
) -> Payment:
    """
    Mark an order as paid and create its payment record.
    """

    if order.status == "paid":
        existing_payment = (
            db.query(Payment)
            .filter(
                Payment.order_id == order.id
            )
            .first()
        )

        if existing_payment is not None:
            return existing_payment

    order.status = "paid"
    order.paid_at = datetime.utcnow()
    order.paypal_order_id = paypal_order_id

    payment = Payment(
        order_id=order.id,
        provider="paypal",
        provider_payment_id=capture_id,
        amount_cents=order.amount_cents,
        currency=order.currency,
        status="completed",
    )

    db.add(payment)
    db.flush()

    return payment


def cancel_order(
    db,
    order: Order,
) -> None:
    """
    Cancel an unpaid order.
    """

    if order.status == "paid":
        raise ValueError(
            "A paid order cannot be cancelled"
        )

    order.status = "cancelled"
    order.cancelled_at = datetime.utcnow()

    db.flush()
