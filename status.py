import random
import discord
from discord.ext import tasks

from config import *


async def set_random_status(client):

    activities = []

    # Statuts classiques
    for text in STATUSES:
        activities.append(
            discord.CustomActivity(name=text)
        )

    # Joue à
    for game in GAMES:
        activities.append(
            discord.Game(name=game)
        )

    # Regarde
    for watch in WATCHING:
        activities.append(
            discord.Activity(
                type=discord.ActivityType.watching,
                name=watch
            )
        )

    # Écoute
    for listen in LISTENING:
        activities.append(
            discord.Activity(
                type=discord.ActivityType.listening,
                name=listen
            )
        )

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
