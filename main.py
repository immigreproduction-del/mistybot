import os
import discord

from antispam import handle_antispam
from status import start_status_loop

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")

    start_status_loop(client)


@client.event
async def on_message(message):
    await handle_antispam(message)


client.run(TOKEN)
