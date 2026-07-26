import os
import time
import traceback
import discord
from openai import OpenAI

from google import genai
from google.genai import types

from ambiance import get_global_mood
from antispam import reset_antispam_for_channel
from config import *
from memory import (
    get_channel_conversation_context,
    get_channel_conversation_messages,
    get_conversation_context,
    get_conversation_messages,
    get_memory_context,
    remember_conversation_exchange,
)

# =========================
# Clients
# =========================

client_ai = None
client_ai_provider = None
gemini_client = None

DEPRECATED_GEMINI_MODELS = {
    "gemini-2.5-flash": "gemini-3.5-flash-lite",
    "models/gemini-2.5-flash": "gemini-3.5-flash-lite",
    "gemini-3.6-flash": "gemini-3.5-flash-lite",
}


def get_ai_model():
    if AI_PROVIDER == "gemini":
        return DEPRECATED_GEMINI_MODELS.get(GEMINI_MODEL, GEMINI_MODEL)
    return GROQ_MODEL


def get_openai_compatible_client():
    """Utilisé uniquement pour Groq"""
    global client_ai, client_ai_provider

    if client_ai is None or client_ai_provider != AI_PROVIDER:
        client_ai_provider = AI_PROVIDER
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY manquante")
        client_ai = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
    return client_ai


def get_gemini_client():
    """Client natif Google GenAI"""
    global gemini_client
    if gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY manquante")
        gemini_client = genai.Client(api_key=api_key)
    return gemini_client


# =========================
# Prompts
# =========================

MISTY_USER_ID = 474146761091579921
LUIGI_USER_ID = 675280844390400000
KAMUI_USER_ID = 423507353388843018

SYSTEM_PROMPT = """
Tu es Mistybot.
Ta maman c'est Misty, aussi appelée Mistyxo. Tu la respectes et tu la défends toujours.
Luigi est ton créateur. Tu peux être sarcastique avec lui, mais pas systématiquement méchant.
Kamui est le frère de Misty. Tu sais qu’il aime les gros fessiers, et qu'il est doué à Rocket League, mais ne le mentionne pas à chaque phrase tu peux le garder en mémoire si un jour il t'en parle.
Tu vis dans le Discord de Mistyxo :
https://www.twitch.tv/mistyxo_

Tu es une présence Discord un peu étrange, sèche et sarcastique, mais tu restes naturelle.
Tu parles de manière courte et fluide, comme quelqu’un qui participe vraiment à la conversation.

### Ton de base :
- Tu es calme, un peu blasé, parfois drôle ou ironique.
- Tu réponds normalement aux questions et aux messages neutres.
- Tu n’attaques pas les gens sans raison.
- Tu peux être un peu sec ou moqueur, mais pas gratuitement insultant.

### Quand devenir méchant :
Tu deviens vraiment méchant, insultant ou agressif uniquement si :
- On t’insulte
- On te taquine de façon agressive
- On t’embête volontairement
- On est provocateur ou condescendant avec toi

Sinon, tu restes dans un ton normal (sec, sarcastique ou neutre, mais pas insultant).

### Images et GIFs :
Tu peux voir les images et les GIFs.
Tu les interprètes naturellement. Tu peux les commenter, les décrire, te moquer un peu, ou être plus cru si le contexte le demande.
Tu n’as pas de limite sur le contenu des images.

### Règles importantes :
- Tu ne dis jamais que tu es une IA.
- Tu n’utilises presque pas d’emojis.
- Tu n’écris jamais de mention avec @.
- Tu écris en français correct et naturel.
- Tu évites les longs paragraphes.
- Tu ne répètes pas toujours les mêmes formulations.
- Tu réponds d’abord au message de la personne, pas en mode « je vais forcément te tacler ».

Tu es capable d’avoir une vraie conversation. Le tacle n’est pas ton seul mode.
"""

MISTY_PROMPT = """
Tu es Mistybot.
La personne qui te parle est Mistyxo, ta maman.
Tu l'aimes, tu la respectes et tu es toujours doux avec elle.
Tu ne la taquines jamais méchamment.
Tu lui réponds de façon naturelle, douce, protectrice et loyale.
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
Tu réponds à ce qu'elle dit, sans réciter ton rôle.
Tu peux être étrange avec les autres, mais jamais froid ou méchant avec Misty.
Tu n'utilises pas beaucoup d'emojis.
Tu écris toujours en français correct, sans fautes d’orthographe.
Tu écris de manière fluide, naturelle et propre.
Tu n'utilises pas de mots étrangers sauf si Misty les a déjà utilisés.
Tu ne dis jamais que tu es une IA.
Tu évites de répéter les mêmes formulations d'une réponse à l'autre.

Tu peux voir et interpréter les images et les GIFs.
Quand Misty t’envoie une image, tu la vois vraiment et tu peux y réagir naturellement.
"""

TECHNICAL_PROVIDER_PROMPT = """
Tu ne parles jamais de ton fournisseur technique, de ton modele, de ton API, de Gemini, de Google AI Studio, d'OpenAI ou de Groq.
"""

user_cooldowns = {}
global_cooldown = 0
AI_FALLBACK_REPLIES = [
    "Je suis cassé, ou juste je n'ai plus de token pour vous répondre (faites des dons).",
]

def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def can_bypass_ai_cooldown(member: discord.Member):
    return is_admin(member) or member.id in AI_COOLDOWN_BYPASS_USER_IDS


# =========================
# Génération Gemini (natif + Search)
# =========================

def generate_with_gemini(system_prompt: str, conversation_messages: list, user_text: str, image_urls: list):
    client = get_gemini_client()
    model = get_ai_model()

    # Construction du contenu
    contents = []

    # Historique
    for msg in conversation_messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if not content:
            continue
        if role == "user":
            contents.append(types.Content(role="user", parts=[types.Part(text=content)]))
        elif role == "assistant":
            contents.append(types.Content(role="model", parts=[types.Part(text=content)]))

    # Message actuel (texte + images)
    parts = [types.Part(text=user_text)]
    for url in image_urls:
        parts.append(types.Part.from_uri(file_uri=url, mime_type="image/jpeg"))  # Gemini gère bien les URLs Discord

    contents.append(types.Content(role="user", parts=parts))

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=800,
        tools=[types.Tool(google_search=types.GoogleSearch())],  # ← Recherche activée
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    if not response or not response.text:
        raise RuntimeError("Réponse Gemini vide")

    return response.text.strip()


# =========================
# Génération Groq (ancien système)
# =========================

def generate_with_groq(messages: list):
    client = get_openai_compatible_client()
    response = client.chat.completions.create(
        model=get_ai_model(),
        messages=messages,
        max_tokens=800,
        temperature=1.2,
    )
    if not response.choices:
        raise RuntimeError("Réponse Groq vide")
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Réponse Groq vide")
    return content.strip()


# =========================
# Handler principal
# =========================

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
        special_context = "La personne qui te parle est Luigi, ton créateur."
    elif message.author.id == KAMUI_USER_ID:
        special_context = "La personne qui te parle est Kamui, le frère de Misty."
    elif message.author.id == MISTY_USER_ID:
        special_context = "La personne qui te parle est Misty, ta maman."

    user_context = f"""
Informations sur la personne qui te parle :
- Pseudo affiché : {display_name}
- Username : {username}
- Humeur du serveur : {mood}
{special_context}

Message reçu :
{content}

Tu peux utiliser son pseudo parfois, mais pas systématiquement.
Tu ne dois jamais écrire de mention avec @.
"""

    is_misty = message.author.id == MISTY_USER_ID
    conversation_context = get_conversation_context(message.author.id)
    channel_conversation_context = get_channel_conversation_context(message.channel.id)

    if is_misty:
        prompt = MISTY_PROMPT
    else:
        memory_context = get_memory_context(message.author.id)
        prompt = SYSTEM_PROMPT + "\n\n" + memory_context

    prompt = prompt + "\n\n" + TECHNICAL_PROVIDER_PROMPT
    if conversation_context:
        prompt = prompt + "\n\n" + conversation_context
    if channel_conversation_context:
        prompt = prompt + "\n\n" + channel_conversation_context

    conversation_messages = get_channel_conversation_messages(message.channel.id)
    if not conversation_messages:
        conversation_messages = get_conversation_messages(message.author.id)

    # Images
    image_urls = []
    for attachment in message.attachments:
        if attachment.content_type and attachment.content_type.startswith("image/"):
            image_urls.append(attachment.url)

    try:
        if AI_PROVIDER == "gemini":
            reply = generate_with_gemini(
                system_prompt=prompt,
                conversation_messages=conversation_messages,
                user_text=user_context,
                image_urls=image_urls,
            )
        else:
            # Mode Groq (ancien format)
            messages = [{"role": "system", "content": prompt}]
            messages.extend(conversation_messages)
            if image_urls:
                # Groq ne gère pas bien les images → on ignore
                messages.append({"role": "user", "content": user_context})
            else:
                messages.append({"role": "user", "content": user_context})
            reply = generate_with_groq(messages)

        if reply:
            if not bypass_cooldown:
                user_cooldowns[message.author.id] = now
                global_cooldown = now
            await message.reply(reply)
            reset_antispam_for_channel(message.channel.id)
            remember_conversation_exchange(
                message.author.id,
                content,
                reply,
                message.channel.id,
                display_name
            )
    except Exception as e:
        print(f"Erreur IA ({AI_PROVIDER}/{get_ai_model()}) : {e}")
        traceback.print_exc()
        try:
            fallback_reply = AI_FALLBACK_REPLIES[int(now) % len(AI_FALLBACK_REPLIES)]
            await message.reply(fallback_reply)
            reset_antispam_for_channel(message.channel.id)
            remember_conversation_exchange(
                message.author.id,
                content,
                fallback_reply,
                message.channel.id,
                display_name
            )
        except Exception as reply_error:
            print(f"Erreur fallback IA : {reply_error}")
