from __future__ import annotations

import base64

import aiohttp

from backend.config import Config


def get_paypal_base_url() -> str:
    if Config.PAYPAL_MODE == "live":
        return "https://api-m.paypal.com"

    return "https://api-m.sandbox.paypal.com"


async def get_access_token() -> str:
    client_id = Config.PAYPAL_CLIENT_ID
    client_secret = Config.PAYPAL_CLIENT_SECRET

    if not client_id or not client_secret:
        raise RuntimeError(
            "PayPal credentials are not configured"
        )

    credentials = (
        f"{client_id}:{client_secret}"
    )

    encoded = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    headers = {
        "Authorization": f"Basic {encoded}",
        "Content-Type": (
            "application/x-www-form-urlencoded"
        ),
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{get_paypal_base_url()}"
            "/v1/oauth2/token",
            headers=headers,
            data={
                "grant_type": "client_credentials"
            },
        ) as response:

            data = await response.json()

            if response.status != 200:
                raise RuntimeError(
                    "PayPal authentication failed: "
                    f"{response.status} {data}"
                )

            return data["access_token"]


async def paypal_request(
    method: str,
    endpoint: str,
    *,
    json_data: dict | None = None,
) -> dict:
    token = await get_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.request(
            method,
            f"{get_paypal_base_url()}{endpoint}",
            headers=headers,
            json=json_data,
        ) as response:

            text = await response.text()

            try:
                import json

                data = json.loads(text)
            except Exception:
                data = {"raw": text}

            if response.status >= 400:
                raise RuntimeError(
                    "PayPal API error "
                    f"{response.status}: {data}"
                )

            return data


async def create_paypal_order(
    *,
    amount_cents: int,
    currency: str,
    public_order_id: str,
    description: str,
) -> dict:
    """
    Create a PayPal checkout order.

    The amount comes from the trusted local Product/Order
    record rather than directly from the client.
    """

    amount = f"{amount_cents / 100:.2f}"

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": public_order_id,
                "description": description,
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                },
            }
        ],
        "application_context": {
            "user_action": "PAY_NOW",
            "shipping_preference": "NO_SHIPPING",
        },
    }

    return await paypal_request(
        "POST",
        "/v2/checkout/orders",
        json_data=payload,
    )


async def get_paypal_order(
    paypal_order_id: str,
) -> dict:
    return await paypal_request(
        "GET",
        f"/v2/checkout/orders/"
        f"{paypal_order_id}",
    )


async def capture_paypal_order(
    paypal_order_id: str,
) -> dict:
    return await paypal_request(
        "POST",
        f"/v2/checkout/orders/"
        f"{paypal_order_id}/capture",
        json_data={},
              )
