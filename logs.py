import discord

from config import *


async def send_log(client, title, description, color=discord.Color.dark_grey()):
    if not ENABLE_LOGS:
        return

    channel = client.get_channel(LOG_CHANNEL_ID)

    if channel is None:
        print("Salon logs introuvable. Vérifie LOG_CHANNEL_ID dans config.py.")
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    try:
        await channel.send(embed=embed)
    except Exception as e:
        print(f"Erreur log : {e}")


async def log_startup(client):
    await send_log(
        client,
        "🌙 Mistybot réveillé",
        "Surveillance active. Le serveur est observé.",
        discord.Color.dark_purple()
    )


async def log_spam_timeout(client, message):
    description = f"""
**Utilisateur :** {message.author.display_name}
**Username :** `{message.author.name}`
**ID :** `{message.author.id}`
**Salon :** {message.channel.mention}

**Raison :** spam détecté
**Limite :** {MESSAGE_LIMIT} messages en {TIME_WINDOW_SECONDS} secondes
**Sanction :** timeout {TIMEOUT_MINUTES} minutes
"""

    await send_log(
        client,
        "⛓️ Timeout anti-spam",
        description,
        discord.Color.red()
    )


async def log_ai_response(client, message, is_misty=False):
    user_type = "Misty" if is_misty else "Utilisateur normal"

    description = f"""
**Utilisateur :** {message.author.display_name}
**Username :** `{message.author.name}`
**ID :** `{message.author.id}`
**Type :** {user_type}
**Salon :** {message.channel.mention}

**Message :**
{message.clean_content}
"""

    await send_log(
        client,
        "👁️ Mention IA",
        description,
        discord.Color.purple()
    )


async def log_memory_observation(client, message, reason, score_added):
    description = f"""
**Utilisateur :** {message.author.display_name}
**Username :** `{message.author.name}`
**ID :** `{message.author.id}`
**Salon :** {message.channel.mention}

**Observation :** {reason}
**Score ajouté :** +{score_added}

**Message :**
{message.clean_content}
"""

    await send_log(
        client,
        "📼 Observation comportementale",
        description,
        discord.Color.orange()
    )
