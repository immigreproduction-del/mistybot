import os
import discord
from discord import app_commands

from ambiance import (
    observe_ambiance,
    maybe_send_chat_remark,
    maybe_send_micro_observation,
)
from antispam import handle_antispam
from config import AI_COOLDOWN_BYPASS_USER_IDS
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
tree = app_commands.CommandTree(client)


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


def can_use_sendmsg(member):
    if member.guild_permissions.administrator:
        return True

    return member.id in AI_COOLDOWN_BYPASS_USER_IDS


@tree.command(
    name="sendmsg",
    description="Envoie un message dans ce salon avec Mistybot."
)
@app_commands.describe(message="Message à envoyer avec Mistybot")
async def sendmsg(interaction: discord.Interaction, message: str):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Commande inutilisable ici.",
            ephemeral=True
        )
        return

    if not can_use_sendmsg(interaction.user):
        await interaction.response.send_message(
            "Non.",
            ephemeral=True
        )
        return

    await interaction.channel.send(message)
    await interaction.response.send_message(
        "Message envoyé.",
        ephemeral=True
    )


@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")
    await tree.sync()

    for guild in client.guilds:
        tree.copy_global_to(guild=guild)
        await tree.sync(guild=guild)

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
