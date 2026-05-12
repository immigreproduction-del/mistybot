import random
import discord
from discord.ext import tasks

from ambiance import get_global_mood
from config import *


async def set_random_status(client):
    activities = []
    mood = get_global_mood()

    for text in STATUSES:
        activities.append(discord.CustomActivity(name=text))

    for game in GAMES:
        activities.append(discord.Game(name=game))

    for watch in WATCHING:
        activities.append(
            discord.Activity(
                type=discord.ActivityType.watching,
                name=watch
            )
        )

    for listen in LISTENING:
        activities.append(
            discord.Activity(
                type=discord.ActivityType.listening,
                name=listen
            )
        )

    if mood == "suspect":
        activities.extend([
            discord.CustomActivity(name="Quelque chose gratte dans les logs"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="les comportements suspects"
            ),
        ])
    elif mood == "bruyant":
        activities.extend([
            discord.CustomActivity(name="Le bruit laisse des traces"),
            discord.Activity(
                type=discord.ActivityType.listening,
                name="le serveur parler trop fort"
            ),
        ])
    elif mood == "agite":
        activities.extend([
            discord.CustomActivity(name="Le serveur bouge trop vite"),
            discord.Activity(
                type=discord.ActivityType.watching,
                name="les habitudes revenir"
            ),
        ])
    else:
        activities.append(discord.CustomActivity(name="Le calme est provisoire"))

    discord_statuses = [
        discord.Status.online,
        discord.Status.idle,
        discord.Status.dnd
    ]

    activity = random.choice(activities)
    status = random.choice(discord_statuses)

    await client.change_presence(
        status=status,
        activity=activity
    )


def start_status_loop(client):
    @tasks.loop(minutes=STATUS_CHANGE_MINUTES)
    async def change_status():
        await set_random_status(client)

    @change_status.before_loop
    async def before_change_status():
        await client.wait_until_ready()

    change_status.start()
