"""
GW Esports Club Discord Bot
Entry point: starts the Discord bot and an aiohttp webserver 
(for the Google Apps Script tryout-form webhook) in the same event loop.
"""

import asyncio
import logging
import os

from aiohttp import web

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("gw-bot")

DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
WEBHOOK_PORT = int(os.environ.get("PORT", 8080))
WEBHOOK_SECRET = os.environ["WEBHOOK_SECRET"]

TEST_GUILD_ID = 560630881925201920

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

FAKE_TEAMS = {
    "valorant": {"status": "open", "form_link": "https://forms.gle/example"},
    "overwatch": {"status": "closed", "form_link": None},
}

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} ({bot.user.id})")
    guild = discord.Object(id=TEST_GUILD_ID)
    bot.tree.copy_global_to(guild=guild)
    synced = await bot.tree.sync(guild=guild)
    log.info(f"Synced {len(synced)} slash command (s)")


@bot.tree.command(name="health", description="Check if the bot is alive and responsive")
async def health(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Bot is up. Latency: {round(bot.latency * 1000)}ms"
    )


@bot.tree.command(name="team", description="Get info for a specific team")
@app_commands.describe(game="e.g. valorant, overwatch")
async def team(interaction: discord.Interaction, game: str):
    data = FAKE_TEAMS.get(game.lower())
    if data is None:
        await interaction.response.send_message(
            f"No team called `{game}` found.",
            ephemeral=True,
        )
        return

    embed = discord.Embed(
        title=f"{game.title()} - Team Hub",
        color=discord.Color.green() if data["status"] == "open" else discord.Color.greyple(),
    )
    embed.add_field(name="Tryout status", value=data["status"].capitalize(), inline=True)
    if data["status"] == "open":
        embed.add_field(name="Tryout signup", value=data["form_link"], inline=False)
    
    await interaction.response.send_message(embed=embed)

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("_"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            log.info(f"Loaded cog: {filename}")        


async def start_webhook_server():
    app = web.Application()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", WEBHOOK_PORT)
    await site.start()
    log.info(f"Webhook server listening on port {WEBHOOK_PORT}")


async def main():
    async with bot:
        await load_cogs()
        await start_webhook_server()
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())