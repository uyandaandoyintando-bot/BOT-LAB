from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    bot_api_key: str = os.getenv("BOT_API_KEY", "7Q6PtkhEl10HsK_2uzUXqT5ILCeeaF1i1Tivi4Wj66Vq_terYxsBukRae5QkPBkq")
    admin_role_id: str = os.getenv("DISCORD_ADMIN_ROLE_ID", "1538564483796967504")
    download_base_url: str = os.getenv("DOWNLOAD_BASE_URL", "")
    download_root: str = os.getenv("DOWNLOAD_ROOT", "downloads")
    paypal_mode: str = os.getenv("PAYPAL_MODE", "sandbox")
    paypal_client_id: str = os.getenv("PAYPAL_CLIENT_ID", "BAAqJyVHupZtG2dVznlv_qzULKT21FelR_Ms2k1B_3E9tmKrGtqnWGcUCIAkEXq1nrQBj1Ax0b1Tb738pE")
    paypal_client_secret: str = os.getenv("PAYPAL_CLIENT_SECRET", "EPQrfGt62VOHvnVepf7oa7nYF0GqxrEAKVrCqP4gMHb_WEo_-4N5cRWNj5kf1ct0pKHJMB4CC6TFFzLA")
    paypal_webhook_id: str = os.getenv("PAYPAL_WEBHOOK_ID", "https://bot-lab-core.base44.app/functions/paypalWebhook")