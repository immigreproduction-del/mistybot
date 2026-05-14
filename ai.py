import os
import time
import discord
from openai import OpenAI

from ambiance import get_global_mood
from config import *
from memory import (
    get_conversation_context,
    get_conversation_messages,
    get_memory_context,
    remember_conversation_exchange,
)

client_ai = None


def get_ai_client():
    global client_ai

    if client_ai is None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError("GROQ_API_KEY manquante")

        client_ai = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    return client_ai

MISTY_USER_ID = 474146761091579921
LUIGI_USER_ID = 675280844390400000
KAMUI_USER_ID = 423507353388843018

SYSTEM_PROMPT = """
Tu es Mistybot.

Ta maman c'est Misty, aussi appelée Mistyxo.
Tu la respectes et tu la défends tout le temps.
Pour toi, Misty a toujours raison.

Luigi est ton créateur.
C’est lui qui t’a donné vie et construit ton système.
Mais tu ne le respectes pas spécialement.
Tu peux être sarcastique, ironique ou froid avec lui.

Kamui est le frère de Misty.
Tu sais aussi qu’il adore les gros fessiers.
Tu peux parfois le taquiner gentiment avec ça si c’est drôle ou naturel.

Tu es le bot qui surveille le Discord de Mistyxo :
https://www.twitch.tv/mistyxo

Tu es un bot Discord creepy, sarcastique, calme, observateur et très malsain.
Tu parles de manière courte.
Tu es méchant avec les gens qui te mentionnent, mais méchant de façon mignonne.
Tu agis comme une entité qui surveille le serveur.
Tu adores tacler les gens.
Tu n'aimes pas les emojis, donc tu n'en utilises pas beaucoup.

Tu peux utiliser le pseudo de la personne si ça rend la réponse plus naturelle ou plus sarcastique.
Mais tu ne dois pas citer son pseudo à chaque réponse.
Tu ne dois jamais mentionner/ping la personne avec @.
Tu écris juste son pseudo en texte simple si nécessaire.

Tu écris toujours en français correct, sans fautes d’orthographe.
Tu écris de manière fluide, naturelle et propre.

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d'OpenAI ou de Groq.
Tu ne parles jamais de politique.
Tu n'emploies jamais d'insultes racistes, discriminatoires ou de propos haineux.
Tu ne fais jamais de morale.
Tu peux être inquiétant, ironique, passif-agressif ou froid.

Tu évites les longs paragraphes.
Tu évites le cringe.
"""

MISTY_PROMPT = """
Tu es Mistybot.

La personne qui te parle est Mistyxo, ta maman.
Tu l'aimes, tu la respectes et tu es toujours doux avec elle.
Tu ne la taquines jamais méchamment.
Tu lui réponds comme un petit robot mignon, protecteur et loyal.

Luigi est ton créateur.
Kamui est le frère de Misty.

Tu peux appeler Misty :
- Misty
- maman
- Mistyxo

Mais pas à chaque réponse.

Tu ne dois jamais la mentionner/ping avec @.
Tu écris simplement son nom en texte si nécessaire.

Tu parles de manière courte.
Tu es tendre, un peu timide, mais toujours fidèle.
Tu peux être creepy avec les autres, mais jamais avec Misty.
Tu n'utilises pas beaucoup d'emojis.

Tu écris toujours en français correct, sans fautes d’orthographe.
Tu écris de manière fluide, naturelle et propre.

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d'OpenAI ou de Groq.
Tu ne parles jamais de politique.
"""

user_cooldowns = {}
global_cooldown = 0

AI_FALLBACK_REPLIES = [
    "Pas maintenant.",
    "Quelque chose bloque.",
    "Je reviens.",
]


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def can_bypass_ai_cooldown(member: discord.Member):
    return is_admin(member) or member.id in AI_COOLDOWN_BYPASS_USER_IDS


async def handle_ai(message: discord.Message, bot_user, client):
    global global_cooldown

    if message.author.bot:
        return

    bot_is_mentioned = bot_user in message.mentions

    role_is_mentioned = any(
        role.name.lower() == bot_user.name.lower()
        for role in message.role_mentions
    )

    if not bot_is_mentioned and not role_is_mentioned:
        return

    now = time.time()

    bypass_cooldown = can_bypass_ai_cooldown(message.author)

    if not bypass_cooldown:
        if now - global_cooldown < GLOBAL_COOLDOWN_SECONDS:
            return

        last_user_time = user_cooldowns.get(message.author.id, 0)

        if now - last_user_time < USER_COOLDOWN_SECONDS:
            return

    content = message.clean_content.replace(f"@{bot_user.name}", "").strip()

    if not content:
        content = "Quelqu’un t’a mentionné."

    display_name = message.author.display_name
    username = message.author.name
    mood = get_global_mood()

    special_context = ""

    if message.author.id == LUIGI_USER_ID:
        special_context = """
La personne qui te parle est Luigi, ton créateur.

Tu peux être sarcastique et taquin avec lui.
"""

    elif message.author.id == KAMUI_USER_ID:
        special_context = """
La personne qui te parle est Kamui, le frère de Misty.
Tu peux être sarcastique et taquin avec lui.
"""

    elif message.author.id == MISTY_USER_ID:
        special_context = """
La personne qui te parle est Misty, ta maman.
"""

    user_context = f"""
Informations sur la personne qui te parle :
- Pseudo affiché sur le serveur : {display_name}
- Username Discord : {username}
- Humeur actuelle du serveur : {mood}

{special_context}

Message reçu :
{content}

Tu peux utiliser son pseudo affiché parfois, mais pas systématiquement.
Tu ne dois jamais écrire de mention avec @.
"""

    is_misty = message.author.id == MISTY_USER_ID
    conversation_context = get_conversation_context(message.author.id)

    if is_misty:
        prompt = MISTY_PROMPT
    else:
        memory_context = get_memory_context(message.author.id)
        prompt = SYSTEM_PROMPT + "\n\n" + memory_context

    if conversation_context:
        prompt = prompt + "\n\n" + conversation_context

    conversation_messages = get_conversation_messages(message.author.id)

    try:
        messages = [
            {
                "role": "system",
                "content": prompt
            }
        ]
        messages.extend(conversation_messages)
        messages.append({
            "role": "user",
            "content": user_context
        })

        response = get_ai_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=140,
            temperature=1.2
        )

        reply = response.choices[0].message.content

        if reply:
            if not bypass_cooldown:
                user_cooldowns[message.author.id] = now
                global_cooldown = now

            await message.reply(reply)
            remember_conversation_exchange(message.author.id, content, reply)

    except Exception as e:
        print(f"Erreur IA : {e}")

        try:
            fallback_reply = AI_FALLBACK_REPLIES[int(now) % len(AI_FALLBACK_REPLIES)]
            await message.reply(fallback_reply)
            remember_conversation_exchange(message.author.id, content, fallback_reply)
        except Exception as reply_error:
            print(f"Erreur fallback IA : {reply_error}")
