import random
from collections import defaultdict, deque

import discord

from config import *
from memory import contains_words, is_caps_abuse

message_history = defaultdict(deque)
last_global_observation_at = None
last_channel_observation_at = {}
last_user_observation_at = {}
last_busy_chat_at = {}
last_consecutive_talk_at = {}
last_author_by_channel = {}
consecutive_messages_by_channel = {}

CALM_OBSERVATIONS = [
    "Je vois.",
    "Noté.",
    "Étrange.",
    "Le calme fait semblant.",
]

ACTIVE_OBSERVATIONS = [
    "Vous parlez beaucoup, aujourd'hui.",
    "Le serveur respire plus vite.",
    "Je note le rythme.",
    "Ça devient récurrent.",
]

NOISY_OBSERVATIONS = [
    "Le bruit revient.",
    "Vous fatiguez les murs.",
    "Le silence était mieux.",
    "Quelqu'un prend trop de place.",
]

SUSPECT_OBSERVATIONS = [
    "Je garde une trace.",
    "Comportement intéressant.",
    "Tu deviens récurrent.",
    "Le serveur a changé de ton.",
]

BUSY_CHAT_OBSERVATIONS = [
    "On joue à celui qui ferme sa gueule sa mère est une pute ou quoi",
    "Ça se voit que parler c'est gratuit",
]

CONSECUTIVE_TALK_OBSERVATIONS = [
    "Après, on n'a pas spécialement demandé",
    "On n'a pas demandé",
    "Qui s'en fou ?",
]

MISTY_USER_ID = 474146761091579921


def _score_message(message):
    score = 0
    content = message.content

    if contains_words(content, INSULT_WORDS):
        score += 4

    if contains_words(content, AGGRESSIVE_WORDS):
        score += 2

    if is_caps_abuse(content):
        score += 2

    return score


def _prune_old_messages(guild_id, now):
    entries = message_history[guild_id]

    while entries:
        created_at, _, _, _ = entries[0]
        age = (now - created_at).total_seconds()

        if age <= AMBIANCE_WINDOW_SECONDS:
            break

        entries.popleft()


def observe_ambiance(message: discord.Message):
    if not ENABLE_AMBIANCE:
        return

    if message.author.bot or not message.guild:
        return

    now = discord.utils.utcnow()
    guild_id = message.guild.id
    score = _score_message(message)

    message_history[guild_id].append(
        (now, message.channel.id, message.author.id, score)
    )
    _prune_old_messages(guild_id, now)


def _count_channel_messages(channel_id, now, window_seconds):
    count = 0

    for entries in message_history.values():
        for created_at, entry_channel_id, _, _ in entries:
            if entry_channel_id != channel_id:
                continue

            age = (now - created_at).total_seconds()
            if age <= window_seconds:
                count += 1

    return count


def _update_consecutive_talk(message):
    channel_id = message.channel.id
    author_id = message.author.id
    previous_author = last_author_by_channel.get(channel_id)

    if previous_author != author_id:
        last_author_by_channel[channel_id] = author_id
        consecutive_messages_by_channel[channel_id] = 1
        return 1

    consecutive_messages_by_channel[channel_id] = (
        consecutive_messages_by_channel.get(channel_id, 1) + 1
    )

    return consecutive_messages_by_channel[channel_id]


def _cooldown_ready(storage, key, now, seconds):
    last_at = storage.get(key)

    if not last_at:
        return True

    age = (now - last_at).total_seconds()
    return age >= seconds


async def maybe_send_chat_remark(message: discord.Message):
    if not ENABLE_AMBIANCE:
        return

    if message.author.bot or not message.guild:
        return

    now = discord.utils.utcnow()
    consecutive_count = _update_consecutive_talk(message)

    channel_id = message.channel.id
    channel_messages = _count_channel_messages(
        channel_id,
        now,
        BUSY_CHAT_WINDOW_SECONDS
    )

    if (
        BUSY_CHAT_MIN_MESSAGES <= channel_messages <= BUSY_CHAT_MAX_MESSAGES
        and random.random() < BUSY_CHAT_CHANCE
        and _cooldown_ready(
            last_busy_chat_at,
            channel_id,
            now,
            BUSY_CHAT_COOLDOWN_SECONDS
        )
    ):
        try:
            await message.channel.send(random.choice(BUSY_CHAT_OBSERVATIONS))
            last_busy_chat_at[channel_id] = now
            return
        except Exception as e:
            print(f"Erreur remarque salon actif : {e}")

    if message.author.id == MISTY_USER_ID:
        return

    if (
        CONSECUTIVE_TALK_MIN_MESSAGES <= consecutive_count <= CONSECUTIVE_TALK_MAX_MESSAGES
        and random.random() < CONSECUTIVE_TALK_CHANCE
        and _cooldown_ready(
            last_consecutive_talk_at,
            message.author.id,
            now,
            CONSECUTIVE_TALK_COOLDOWN_SECONDS
        )
    ):
        try:
            await message.channel.send(random.choice(CONSECUTIVE_TALK_OBSERVATIONS))
            last_consecutive_talk_at[message.author.id] = now
        except Exception as e:
            print(f"Erreur remarque messages consecutifs : {e}")


def get_global_mood():
    now = discord.utils.utcnow()
    messages_count = 0
    suspect_score = 0

    for guild_id in list(message_history.keys()):
        _prune_old_messages(guild_id, now)
        entries = message_history[guild_id]
        messages_count += len(entries)
        suspect_score += sum(score for _, _, _, score in entries)

    if suspect_score >= AMBIANCE_SUSPECT_SCORE:
        return "suspect"

    if messages_count >= AMBIANCE_NOISY_MESSAGES:
        return "bruyant"

    if messages_count >= AMBIANCE_AGITATED_MESSAGES:
        return "agite"

    return "calme"


def _can_send_observation(message, now):
    global last_global_observation_at

    if last_global_observation_at:
        age = (now - last_global_observation_at).total_seconds()
        if age < MICRO_OBSERVATION_GLOBAL_COOLDOWN_SECONDS:
            return False

    channel_last = last_channel_observation_at.get(message.channel.id)
    if channel_last:
        age = (now - channel_last).total_seconds()
        if age < MICRO_OBSERVATION_CHANNEL_COOLDOWN_SECONDS:
            return False

    user_last = last_user_observation_at.get(message.author.id)
    if user_last:
        age = (now - user_last).total_seconds()
        if age < MICRO_OBSERVATION_USER_COOLDOWN_SECONDS:
            return False

    return True


def _mark_observation(message, now):
    global last_global_observation_at

    last_global_observation_at = now
    last_channel_observation_at[message.channel.id] = now
    last_user_observation_at[message.author.id] = now


def _pick_observation(mood):
    if mood == "suspect":
        return random.choice(SUSPECT_OBSERVATIONS)

    if mood == "bruyant":
        return random.choice(NOISY_OBSERVATIONS)

    if mood == "agite":
        return random.choice(ACTIVE_OBSERVATIONS)

    return random.choice(CALM_OBSERVATIONS)


async def maybe_send_micro_observation(message: discord.Message, bot_user):
    if not ENABLE_AMBIANCE:
        return

    if message.author.bot or not message.guild:
        return

    if bot_user in message.mentions or message.role_mentions:
        return

    now = discord.utils.utcnow()
    guild_id = message.guild.id
    _prune_old_messages(guild_id, now)
    entries = message_history[guild_id]

    if len(entries) < MICRO_OBSERVATION_MIN_MESSAGES:
        return

    mood = get_global_mood()
    chance = MICRO_OBSERVATION_ACTIVE_CHANCE if mood != "calme" else MICRO_OBSERVATION_CHANCE

    if random.random() >= chance:
        return

    if not _can_send_observation(message, now):
        return

    try:
        await message.channel.send(_pick_observation(mood))
        _mark_observation(message, now)
    except Exception as e:
        print(f"Erreur micro-observation : {e}")
