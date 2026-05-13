import asyncio
import random
import discord

from config import *


async def set_random_status(client):
    activities = []

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
    async def change_status():
        await client.wait_until_ready()

        while not client.is_closed():
            await set_random_status(client)

            delay_minutes = random.randint(
                STATUS_CHANGE_MINUTES_MIN,
                STATUS_CHANGE_MINUTES_MAX
            )
            await asyncio.sleep(delay_minutes * 60)

    client.loop.create_task(change_status())
