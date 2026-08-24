from __future__ import annotations

import os


class Config:
    # --------------------------------------------------------
    # Server
    # --------------------------------------------------------

    PORT = int(
        os.getenv("PORT", "8000")
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///botlab.db",
    )

    # --------------------------------------------------------
    # Admin
    # --------------------------------------------------------

    ADMIN_API_KEY = os.getenv(
        "ADMIN_API_KEY",
        "",
    )

    # --------------------------------------------------------
    # PayPal
    # --------------------------------------------------------

    PAYPAL_CLIENT_ID = os.getenv(
        "PAYPAL_CLIENT_ID",
        "",
    )

    PAYPAL_CLIENT_SECRET = os.getenv(
        "PAYPAL_CLIENT_SECRET",
        "",
    )

    PAYPAL_ENVIRONMENT = os.getenv(
        "PAYPAL_ENVIRONMENT",
        "sandbox",
    ).lower()

    # --------------------------------------------------------
    # Downloads
    # --------------------------------------------------------

    DOWNLOAD_BASE_URL = os.getenv(
        "DOWNLOAD_BASE_URL",
        "",
    )

    # --------------------------------------------------------
    # CORS
    # --------------------------------------------------------

    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS",
        "",
    )
