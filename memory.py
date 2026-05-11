import json
import os
from datetime import datetime, timezone

import discord

from config import *


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except:
        return {}


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as file:
        json.dump(memory, file, indent=4, ensure_ascii=False)


def get_user_memory(user_id):
    memory = load_memory()
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = {
            "messages": 0,
            "bot_mentions": 0,
            "insults": 0,
            "aggressive_messages": 0,
            "caps_messages": 0,
            "spam_timeouts": 0,
            "behavior_score": 0,
            "last_seen": None
        }
        save_memory(memory)

    return memory[user_id]


def update_user_memory(user_id, updates):
    memory = load_memory()
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = {
            "messages": 0,
            "bot_mentions": 0,
            "insults": 0,
            "aggressive_messages": 0,
            "caps_messages": 0,
            "spam_timeouts": 0,
            "behavior_score": 0,
            "last_seen": None
        }

    for key, value in updates.items():
        memory[user_id][key] = memory[user_id].get(key, 0) + value

    memory[user_id]["last_seen"] = datetime.now(timezone.utc).isoformat()

    save_memory(memory)


def contains_words(content, words):
    content = content.lower()
    return any(word in content for word in words)


def is_caps_abuse(content):
    letters = [char for char in content if char.isalpha()]

    if len(letters) < CAPS_MIN_LENGTH:
        return False

    uppercase = [char for char in letters if char.isupper()]
    ratio = len(uppercase) / len(letters)

    return ratio >= CAPS_RATIO


async def observe_message(message: discord.Message, bot_user):
    if not ENABLE_MEMORY:
        return

    if message.author.bot or not message.guild:
        return

    content = message.content

    updates = {"messages": 1}
    behavior_points = 0

    if bot_user in message.mentions:
        updates["bot_mentions"] = 1
        behavior_points += MEMORY_SCORE_BOT_MENTION

    role_is_mentioned = any(
        role.name.lower() == bot_user.name.lower()
        for role in message.role_mentions
    )

    if role_is_mentioned:
        updates["bot_mentions"] = 1
        behavior_points += MEMORY_SCORE_BOT_MENTION

    if contains_words(content, INSULT_WORDS):
        updates["insults"] = 1
        behavior_points += MEMORY_SCORE_INSULT

    if contains_words(content, AGGRESSIVE_WORDS):
        updates["aggressive_messages"] = 1
        behavior_points += MEMORY_SCORE_AGGRESSIVE

    if is_caps_abuse(content):
        updates["caps_messages"] = 1
        behavior_points += MEMORY_SCORE_CAPS

    if behavior_points > 0:
        updates["behavior_score"] = behavior_points

    update_user_memory(message.author.id, updates)


def record_spam_timeout(user_id):
    if not ENABLE_MEMORY:
        return

    update_user_memory(
        user_id,
        {
            "spam_timeouts": 1,
            "behavior_score": MEMORY_SCORE_SPAM_TIMEOUT
        }
    )


def get_memory_context(user_id):
    data = get_user_memory(user_id)

    score = data.get("behavior_score", 0)

    if score >= 80:
        level = "très problématique"
    elif score >= 40:
        level = "suspect et instable"
    elif score >= 15:
        level = "à surveiller"
    else:
        level = "plutôt calme"

    return f"""
Mémoire utilisateur :
- Messages observés : {data.get("messages", 0)}
- Mentions du bot : {data.get("bot_mentions", 0)}
- Insultes détectées : {data.get("insults", 0)}
- Messages agressifs : {data.get("aggressive_messages", 0)}
- Abus de majuscules : {data.get("caps_messages", 0)}
- Timeouts pour spam : {data.get("spam_timeouts", 0)}
- Score comportemental : {score}
- Profil actuel : {level}

Adapte légèrement ta réponse à ce profil.
Ne cite pas les chiffres directement sauf si c’est drôle ou pertinent.
"""
