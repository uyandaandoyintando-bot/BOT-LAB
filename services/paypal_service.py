from __future__ import annotations

import base64

import aiohttp

from backend.config import Config


def get_paypal_base_url() -> str:
    if Config.PAYPAL_ENVIRONMENT == "live":
        return "https://api-m.paypal.com"

    return "https://api-m.sandbox.paypal.com"


async def get_access_token() -> str:
    if not Config.PAYPAL_CLIENT_ID:
        raise RuntimeError(
            "PAYPAL_CLIENT_ID is not configured"
        )

    if not Config.PAYPAL_CLIENT_SECRET:
        raise RuntimeError(
            "PAYPAL_CLIENT_SECRET is not configured"
        )

    credentials = (
        f"{Config.PAYPAL_CLIENT_ID}:"
        f"{Config.PAYPAL_CLIENT_SECRET}"
    )

    encoded_credentials = base64.b64encode(
        credentials.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{get_paypal_base_url()}"
        "/v1/oauth2/token"
    )

    headers = {
        "Authorization": (
            f"Basic {encoded_credentials}"
        ),
        "Content-Type": (
            "application/x-www-form-urlencoded"
        ),
    }

    data = {
        "grant_type": "client_credentials",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            data=data,
        ) as response:

            response_data = await response.json()

            if response.status != 200:
                raise RuntimeError(
                    "PayPal authentication failed: "
                    f"{response_data}"
                )

            token = response_data.get(
                "access_token"
            )

            if not token:
                raise RuntimeError(
                    "PayPal did not return an access token"
                )

            return token


async def create_paypal_order(
    *,
    amount_cents: int,
    currency: str,
    public_order_id: str,
    description: str,
) -> dict:

    if amount_cents <= 0:
        raise ValueError(
            "amount_cents must be greater than zero"
        )

    token = await get_access_token()

    amount = f"{amount_cents / 100:.2f}"

    url = (
        f"{get_paypal_base_url()}"
        "/v2/checkout/orders"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "PayPal-Request-Id": public_order_id,
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [
            {
                "reference_id": public_order_id,
                "description": description[:127],
                "amount": {
                    "currency_code": currency,
                    "value": amount,
                },
            }
        ],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            json=payload,
        ) as response:

            response_data = await response.json()

            if response.status not in {
                200,
                201,
            }:
                raise RuntimeError(
                    "PayPal order creation failed: "
                    f"{response_data}"
                )

            return response_data


async def get_paypal_order(
    paypal_order_id: str,
) -> dict:

    token = await get_access_token()

    url = (
        f"{get_paypal_base_url()}"
        f"/v2/checkout/orders/{paypal_order_id}"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
        ) as response:

            response_data = await response.json()

            if response.status != 200:
                raise RuntimeError(
                    "Unable to retrieve PayPal order: "
                    f"{response_data}"
                )

            return response_data


async def capture_paypal_order(
    paypal_order_id: str,
) -> dict:

    token = await get_access_token()

    url = (
        f"{get_paypal_base_url()}"
        f"/v2/checkout/orders/"
        f"{paypal_order_id}/capture"
    )

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url,
            headers=headers,
            json={},
        ) as response:

            response_data = await response.json()

            if response.status not in {
                200,
                201,
            }:
                raise RuntimeError(
                    "PayPal capture failed: "
                    f"{response_data}"
                )

            return response_data
