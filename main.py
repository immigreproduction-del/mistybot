import os
from datetime import timedelta
import discord

TOKEN = os.getenv("DISCORD_TOKEN")

MESSAGE_LIMIT = 4
TIMEOUT_MINUTES = 2

last_author_by_channel = {}
streak_by_channel = {}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Bot connecté : {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.guild:
        return

    channel_id = message.channel.id
    author_id = message.author.id

    previous_author = last_author_by_channel.get(channel_id)

    if previous_author == author_id:
        streak_by_channel[channel_id] = streak_by_channel.get(channel_id, 1) + 1
    else:
        last_author_by_channel[channel_id] = author_id
        streak_by_channel[channel_id] = 1

    if streak_by_channel[channel_id] > MESSAGE_LIMIT:
        try:
            await message.delete()
        except:
            pass

        try:
            until = discord.utils.utcnow() + timedelta(minutes=TIMEOUT_MINUTES)
            await message.author.timeout(until, reason="Spam de messages consécutifs")
        except Exception as e:
            print(f"Erreur timeout : {e}")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN manquant.")

client.run(TOKEN)