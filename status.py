import random
import discord
from discord.ext import tasks

from config import *


async def set_random_status(client):

    status_text = random.choice(STATUSES)

    # Activités possibles
    activity_types = [

        discord.Game(name=status_text),

        discord.Activity(
            type=discord.ActivityType.watching,
            name=status_text
        ),

        discord.Activity(
            type=discord.ActivityType.listening,
            name=status_text
        ),
    ]

    # Statuts possibles
    discord_statuses = [
        discord.Status.online,
        discord.Status.idle,
        discord.Status.dnd
    ]

    activity = random.choice(activity_types)

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
