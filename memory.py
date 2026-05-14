import json
import os
import re
from datetime import datetime, timezone

import discord

from config import *
from logs import log_memory_observation
from text_utils import contains_loose_any


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


def get_default_user_memory():
    return {
        "messages": 0,
        "bot_mentions": 0,
        "insults": 0,
        "aggressive_messages": 0,
        "caps_messages": 0,
        "spam_timeouts": 0,
        "behavior_score": 0,
        "last_seen": None,
        "conversation": [],
        "conversation_updated_at": None,
    }


def get_user_memory(user_id):
    memory = load_memory()
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = get_default_user_memory()
        save_memory(memory)

    return memory[user_id]


def update_user_memory(user_id, updates):
    memory = load_memory()
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = get_default_user_memory()

    for key, value in updates.items():
        memory[user_id][key] = memory[user_id].get(key, 0) + value

    memory[user_id]["last_seen"] = datetime.now(timezone.utc).isoformat()

    save_memory(memory)


def contains_words(content, words):
    return contains_loose_any(content, words)


def _trim_conversation_text(content):
    content = " ".join(content.split())

    if len(content) <= CONVERSATION_MEMORY_MAX_CHARS:
        return content

    return content[:CONVERSATION_MEMORY_MAX_CHARS].rstrip() + "..."


def _conversation_is_expired(updated_at):
    if not updated_at:
        return False

    try:
        last_update = datetime.fromisoformat(updated_at)
    except ValueError:
        return True

    now = datetime.now(timezone.utc)
    return (now - last_update).total_seconds() > CONVERSATION_MEMORY_TIMEOUT_SECONDS


def _get_active_conversation(user_data):
    conversation = user_data.get("conversation", [])
    updated_at = user_data.get("conversation_updated_at")

    if _conversation_is_expired(updated_at):
        return []

    return conversation


def remember_conversation_exchange(user_id, user_message, bot_reply):
    if not ENABLE_MEMORY:
        return

    memory = load_memory()
    user_id = str(user_id)

    if user_id not in memory:
        memory[user_id] = get_default_user_memory()

    conversation = _get_active_conversation(memory[user_id])
    conversation.append({
        "user": _trim_conversation_text(user_message),
        "bot": _trim_conversation_text(bot_reply),
    })

    memory[user_id]["conversation"] = conversation[-CONVERSATION_MEMORY_MAX_EXCHANGES:]
    memory[user_id]["conversation_updated_at"] = datetime.now(timezone.utc).isoformat()

    save_memory(memory)


def get_conversation_context(user_id):
    data = get_user_memory(user_id)
    conversation = _get_active_conversation(data)

    if not conversation:
        return ""

    lines = [
        "Conversation récente avec cette personne :"
    ]

    for exchange in conversation:
        lines.append(f"- Elle a dit : {exchange.get('user', '')}")
        lines.append(f"- Tu as répondu : {exchange.get('bot', '')}")

    lines.append(
        "Utilise ce contexte pour garder le fil si la personne continue la discussion."
    )

    return "\n".join(lines)


def is_caps_abuse(content):
    letters = [char for char in content if char.isalpha()]

    if len(letters) < CAPS_MIN_LENGTH:
        return False

    uppercase = [char for char in letters if char.isupper()]
    ratio = len(uppercase) / len(letters)

    return ratio >= CAPS_RATIO


async def observe_message(message: discord.Message, bot_user, client):
    if not ENABLE_MEMORY:
        return

    if message.author.bot or not message.guild:
        return

    content = message.content

    updates = {"messages": 1}
    behavior_points = 0

    bot_is_mentioned = bot_user in message.mentions

    role_is_mentioned = any(
        role.name.lower() == bot_user.name.lower()
        for role in message.role_mentions
    )

    if bot_is_mentioned or role_is_mentioned:
        updates["bot_mentions"] = 1
        behavior_points += MEMORY_SCORE_BOT_MENTION

    if contains_words(content, INSULT_WORDS):
        updates["insults"] = 1
        behavior_points += MEMORY_SCORE_INSULT

        await log_memory_observation(
            client,
            message,
            "Insulte détectée",
            MEMORY_SCORE_INSULT
        )

    if contains_words(content, AGGRESSIVE_WORDS):
        updates["aggressive_messages"] = 1
        behavior_points += MEMORY_SCORE_AGGRESSIVE

        await log_memory_observation(
            client,
            message,
            "Message agressif détecté",
            MEMORY_SCORE_AGGRESSIVE
        )

    if is_caps_abuse(content):
        updates["caps_messages"] = 1
        behavior_points += MEMORY_SCORE_CAPS

        await log_memory_observation(
            client,
            message,
            "Abus de majuscules détecté",
            MEMORY_SCORE_CAPS
        )

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
