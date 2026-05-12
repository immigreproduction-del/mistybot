import random
import discord

from config import *
from text_utils import contains_loose_any, contains_loose_word

MISTY_USER_ID = 474146761091579921


def chance(probability):
    return random.random() < probability


def contains_any(content, words):
    return contains_loose_any(content, words)


async def safe_react(message: discord.Message, emoji):
    try:
        await message.add_reaction(emoji)
    except Exception as e:
        print(f"Erreur réaction : {e}")


async def handle_reactions(message: discord.Message):
    if not ENABLE_REACTIONS:
        return

    if message.author.bot:
        return

    if not message.guild:
        return

    content = message.content

    # Réaction spéciale pour Misty
    if message.author.id == MISTY_USER_ID:
        if chance(REACTION_CHANCE_MISTY):
            await safe_react(message, random.choice(MISTY_REACTIONS))
        return

    # Réaction forte sur insultes
    if contains_any(content, INSULT_WORDS):
        if chance(REACTION_CHANCE_INSULT):
            await safe_react(message, random.choice(INSULT_REACTIONS))
        return

    # Réactions par mots-clés
    for keyword, emojis in REACTION_KEYWORDS.items():
        if contains_loose_word(content, keyword):
            if chance(REACTION_CHANCE_KEYWORD):
                await safe_react(message, random.choice(emojis))
            return

    # Réaction rare sur message normal
    if chance(REACTION_CHANCE_NORMAL):
        await safe_react(message, random.choice(NORMAL_REACTIONS))
