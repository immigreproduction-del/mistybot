import os
import discord

from antispam import handle_antispam
from status import start_status_loop
from ai import handle_ai
from memory import observe_message
from logs import log_startup

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")
    start_status_loop(client)
    await log_startup(client)


@client.event
async def on_message(message):
    print(f"Message reçu : {message.author} -> {message.content}")

    await observe_message(message, client.user, client)
    await handle_antispam(message, client)
    await handle_ai(message, client.user, client)


client.run(TOKEN)
