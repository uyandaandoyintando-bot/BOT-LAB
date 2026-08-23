import os


class Config:
    PORT = int(os.getenv("PORT", "8000"))

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///botlab.db",
    )

    ADMIN_API_KEY = os.getenv(
        "ADMIN_API_KEY",
        "",
    )

    PAYPAL_MODE = os.getenv(
        "PAYPAL_MODE",
        "sandbox",
    )

    PAYPAL_CLIENT_ID = os.getenv(
        "PAYPAL_CLIENT_ID",
        "",
    )

    PAYPAL_CLIENT_SECRET = os.getenv(
        "PAYPAL_CLIENT_SECRET",
        "",
    )

    PAYPAL_WEBHOOK_ID = os.getenv(
        "PAYPAL_WEBHOOK_ID",
        "",
    )
