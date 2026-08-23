from __future__ import annotations

import secrets
from datetime import datetime

from database.models import Customer, Order, Payment, Product


def generate_public_order_id() -> str:
    return (
        "BOTLAB-"
        + secrets.token_hex(12).upper()
    )


def create_pending_order(
    db,
    customer: Customer,
    product: Product,
) -> Order:
    """
    Create a local pending order before contacting PayPal.
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
    paypal_payment_id: str | None = None,
) -> Payment:
    """
    Mark an order as paid and record the PayPal payment.
    """

    order.status = "paid"
    order.paypal_order_id = paypal_order_id
    order.paid_at = datetime.utcnow()

    payment = Payment(
        order_id=order.id,
        provider="paypal",
        provider_payment_id=paypal_payment_id,
        amount_cents=order.amount_cents,
        currency=order.currency,
        status="completed",
    )

    db.add(payment)
    db.flush()

    return payment
