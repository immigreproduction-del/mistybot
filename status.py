import discord


async def clear_status(client):
    await client.wait_until_ready()
    await client.change_presence(
        status=discord.Status.online,
        activity=None
    )


def start_status_loop(client):
    if getattr(client, "_status_clear_task_started", False):
        return

    client._status_clear_task_started = True
    client.loop.create_task(clear_status(client))
