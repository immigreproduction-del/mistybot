import os
from datetime import timedelta

import discord

TOKEN = os.getenv("DISCORD_TOKEN")

MESSAGE_LIMIT = 5
TIME_WINDOW_SECONDS = 60
TIMEOUT_MINUTES = 2

last_author_by_channel = {}
streak_by_channel = {}
first_message_time_by_channel = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if not message.guild:
        return

    channel_id = message.channel.id
    author_id = message.author.id
    now = discord.utils.utcnow()

    previous_author = last_author_by_channel.get(channel_id)
    first_message_time = first_message_time_by_channel.get(channel_id)

    # Si quelqu’un d’autre parle, compteur reset
    if previous_author != author_id:
        last_author_by_channel[channel_id] = author_id
        streak_by_channel[channel_id] = 1
        first_message_time_by_channel[channel_id] = now
        return

    # Si plus de 60 secondes sont passées depuis le début de la série, compteur reset
    if first_message_time is None or (now - first_message_time).total_seconds() > TIME_WINDOW_SECONDS:
        streak_by_channel[channel_id] = 1
        first_message_time_by_channel[channel_id] = now
        return

    # Même personne, dans les 60 secondes : on augmente le compteur
    streak_by_channel[channel_id] = streak_by_channel.get(channel_id, 1) + 1

    if streak_by_channel[channel_id] >= MESSAGE_LIMIT:
        try:
            await message.delete()
        except discord.Forbidden:
            print("Impossible de supprimer le message : permission manquante.")
        except Exception as e:
            print(f"Erreur suppression message : {e}")

        try:
            await message.author.send("Doucement le spam 😭")
        except discord.Forbidden:
            print("Impossible d’envoyer un MP : messages privés fermés.")
        except Exception as e:
            print(f"Erreur MP : {e}")

        try:
            until = now + timedelta(minutes=TIMEOUT_MINUTES)
            await message.author.timeout(until, reason="Spam de messages consécutifs")
            print(f"Timeout appliqué à {message.author} pendant {TIMEOUT_MINUTES} minutes.")
        except discord.Forbidden:
            print("Impossible de timeout : rôle du bot trop bas ou permission manquante.")
        except Exception as e:
            print(f"Erreur timeout : {e}")

        # Reset après sanction
        last_author_by_channel[channel_id] = None
        streak_by_channel[channel_id] = 0
        first_message_time_by_channel[channel_id] = None


if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN manquant.")

client.run(TOKEN)
