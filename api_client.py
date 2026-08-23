from __future__ import annotations
import os
import httpx

class BotAPI:
    def __init__(self):
        self.base = os.getenv("BOT_API_BASE_URL", "http://127.0.0.1:8000")
        self.headers = {"X-Bot-Api-Key": os.getenv("BOT_API_KEY", "")}
    async def get(self, path):
        async with httpx.AsyncClient() as client:
            response = await client.get(self.base + path, headers=self.headers)
            return response.json()

    async def post(self, path, payload):
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base + path, json=payload, headers=self.headers)
            return response.json()