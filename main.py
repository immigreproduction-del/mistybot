import os
import discord

from ambiance import (
    observe_ambiance,
    maybe_send_chat_remark,
    maybe_send_micro_observation,
)
from antispam import handle_antispam
from status import start_status_loop
from ai import handle_ai
from memory import observe_message
from reactions import handle_reactions
from security import handle_security

TOKEN = os.getenv("DISCORD_TOKEN")
LOCAL_TEST_GUILD_ID = os.getenv("LOCAL_TEST_GUILD_ID")
LOCAL_TEST_CHANNEL_ID = os.getenv("LOCAL_TEST_CHANNEL_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

client = discord.Client(intents=intents)


def _matches_optional_id(value, expected):
    if not expected:
        return True

    try:
        return value == int(expected)
    except ValueError:
        print(f"ID de test invalide : {expected}")
        return False


def should_ignore_message(message):
    if LOCAL_TEST_GUILD_ID:
        if not message.guild or not _matches_optional_id(message.guild.id, LOCAL_TEST_GUILD_ID):
            return True

    if LOCAL_TEST_CHANNEL_ID:
        if not _matches_optional_id(message.channel.id, LOCAL_TEST_CHANNEL_ID):
            return True

    return False


@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")
    start_status_loop(client)


@client.event
async def on_message(message):
    if should_ignore_message(message):
        return

    print(f"Message reçu : {message.author} -> {message.content}")

    observe_ambiance(message)

    await observe_message(message, client.user, client)
    await handle_antispam(message, client)

    if await handle_security(message, client):
        return

    await maybe_send_chat_remark(message)
    await maybe_send_micro_observation(message, client.user)
    await handle_reactions(message)
    await handle_ai(message, client.user, client)


client.run(TOKEN)
