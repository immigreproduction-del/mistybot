from datetime import timedelta
import discord

MESSAGE_LIMIT = 5
TIME_WINDOW_SECONDS = 60
TIMEOUT_MINUTES = 2

last_author_by_channel = {}
streak_by_channel = {}
first_message_time_by_channel = {}


async def handle_antispam(message: discord.Message):
    if message.author.bot:
        return

    if not message.guild:
        return

    channel_id = message.channel.id
    author_id = message.author.id
    now = discord.utils.utcnow()

    previous_author = last_author_by_channel.get(channel_id)
    first_message_time = first_message_time_by_channel.get(channel_id)

    # Quelqu’un d’autre parle = reset
    if previous_author != author_id:
        last_author_by_channel[channel_id] = author_id
        streak_by_channel[channel_id] = 1
        first_message_time_by_channel[channel_id] = now
        return

    # Temps dépassé = reset
    if first_message_time is None or (now - first_message_time).total_seconds() > TIME_WINDOW_SECONDS:
        streak_by_channel[channel_id] = 1
        first_message_time_by_channel[channel_id] = now
        return

    # Même personne dans le délai = compteur +1
    streak_by_channel[channel_id] = streak_by_channel.get(channel_id, 1) + 1

    if streak_by_channel[channel_id] >= MESSAGE_LIMIT:
        try:
            await message.delete()
        except:
            pass

        try:
            await message.author.send("Doucement le spam 😭")
        except:
            pass

        try:
            until = now + timedelta(minutes=TIMEOUT_MINUTES)
            await message.author.timeout(until, reason="Spam de messages consécutifs")
        except Exception as e:
            print(f"Erreur timeout : {e}")

        # Reset après sanction
        last_author_by_channel[channel_id] = None
        streak_by_channel[channel_id] = 0
        first_message_time_by_channel[channel_id] = None
