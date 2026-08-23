from __future__ import annotations

import os


class Config:
    # --------------------------------------------------------
    # Application
    # --------------------------------------------------------

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-only-change-this",
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "",
    )

    # --------------------------------------------------------
    # Bot authentication
    # --------------------------------------------------------

    BOT_API_KEY = os.getenv(
        "BOT_API_KEY",
        "",
    )

    # --------------------------------------------------------
    # Discord
    # --------------------------------------------------------

    DISCORD_GUILD_ID = os.getenv(
        "DISCORD_GUILD_ID",
        "",
    )

    DISCORD_ADMIN_ROLE_ID = os.getenv(
        "DISCORD_ADMIN_ROLE_ID",
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

    PAYPAL_MODE = os.getenv(
        "PAYPAL_MODE",
        "sandbox",
    ).lower()

    PAYPAL_WEBHOOK_ID = os.getenv(
        "PAYPAL_WEBHOOK_ID",
        "",
    )

    # --------------------------------------------------------
    # Website / downloads
    # --------------------------------------------------------

    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS",
        "",
    )

    DOWNLOAD_BASE_URL = os.getenv(
        "DOWNLOAD_BASE_URL",
        "",
    )

    # --------------------------------------------------------
    # Server
    # --------------------------------------------------------

    PORT = int(
        os.getenv(
            "PORT",
            "8000",
        )
    )

    @classmethod
    def validate_production(cls):
        """
        Check required production settings.

        This intentionally does not require PayPal or the
        download URL during the first deployment.
        """

        required = {
            "DATABASE_URL": cls.DATABASE_URL,
            "BOT_API_KEY": cls.BOT_API_KEY,
        }

        missing = [
            name
            for name, value in required.items()
            if not value
        ]

        if missing:
            raise RuntimeError(
                "Missing required environment variables: "
                + ", ".join(missing)
    )
