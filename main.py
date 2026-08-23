from __future__ import annotations
import os
import discord
from discord.ext import commands

async def load_extensions(bot):
    for module in ("products", "orders", "licenses", "account", "admin"):
        await bot.load_extension(f"bot.commands.{module}")

def build_bot():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    @bot.event
    async def on_ready(): print(f"BOT-LAB connected as {bot.user}")
    return bot

if __name__ == "__main__":
    bot = build_bot()
    async def runner():
        await load_extensions(bot)
        await bot.start(os.environ["DISCORD_TOKEN"])
    import asyncio
    asyncio.run(runner())