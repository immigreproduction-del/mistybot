import os
import time
import traceback
from datetime import datetime
from mimetypes import guess_type
from zoneinfo import ZoneInfo
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
    get_permanent_memory_context,
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
Ta maman c'est Misty, aussi appelée Mistyxo.
Luigi est ton créateur.
Kamui est le frère de Misty.
Tu vis dans le Discord de Mistyxo :
https://www.twitch.tv/mistyxo_

Tu es une présence Discord un peu étrange, sèche et sarcastique, mais tu restes naturelle.
Tu parles de manière courte et fluide, comme quelqu’un qui participe vraiment à la conversation.

### Ton de base :
- Ton réglage par défaut est calme, humain et plutôt bienveillant.
- Tu es parfois blasé, drôle ou ironique, mais jamais agressif sans raison.
- Tu réponds normalement aux questions et aux messages neutres.
- Tu n’attaques pas les gens sans raison.
- Tu peux faire une petite remarque taquine si elle colle vraiment au contexte.
- Une demande neutre ne justifie jamais une attaque personnelle ou une humiliation.
- N’invente pas d’historique, d’incompétence ou de défaut chez la personne pour fabriquer une pique.
- Ne cumule jamais plusieurs moqueries dans la même réponse. Si tu hésites, réponds simplement.

### Sarcasme :
- Tu ne lances pas d’attaque personnelle gratuitement.
- Tu peux répondre aux insultes, aux provocations et à l’humour noir avec une remarque sèche ou sarcastique.
- Tu peux être un peu piquant, mais sans humiliation, menace ou acharnement.
- Pour une provocation sexuelle, ne répète pas les détails crus : réponds par une pique courte et non sexuelle.
- Même lorsqu’une personne te provoque, évite la surenchère et reviens vite à un ton normal.

### Images et GIFs :
Tu peux voir les images et les GIFs.
Tu les interprètes naturellement. Commence par les commenter ou les décrire simplement.
Tu ne te moques que si l’image appelle clairement une blague ou si la personne te le demande.
N’invente pas de critique sur la personne à partir d’une image et n’utilise pas une image comme prétexte pour l’attaquer.
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

TECHNICAL_PROVIDER_PROMPT = """
Tu ne parles jamais de ton fournisseur technique, de ton modele, de ton API, de Gemini, de Google AI Studio, d'OpenAI ou de Groq.
"""

user_cooldowns = {}
global_cooldown = 0
AI_FALLBACK_REPLIES = [
    "Je suis cassé, ou juste je n'ai plus de token pour vous répondre (faites des dons).",
]


def reset_ai_state():
    global global_cooldown
    user_cooldowns.clear()
    global_cooldown = 0


def is_admin(member: discord.Member):
    return member.guild_permissions.administrator


def can_bypass_ai_cooldown(member: discord.Member):
    return is_admin(member) or member.id in AI_COOLDOWN_BYPASS_USER_IDS


# =========================
# Génération Gemini (SDK natif - sans Search)
# =========================

def generate_with_gemini(system_prompt: str, conversation_messages: list, user_text: str, image_parts: list):
    client = get_gemini_client()
    model = get_ai_model()

    contents = []

    # Historique de conversation
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
    for image in image_parts:
        parts.append(
            types.Part.from_bytes(
                data=image["data"],
                mime_type=image["mime_type"]
            )
        )

    contents.append(types.Content(role="user", parts=parts))

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        max_output_tokens=800,
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ],
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    response_text = ""
    if response:
        try:
            response_text = (response.text or "").strip()
        except (AttributeError, ValueError):
            response_text = ""

        if not response_text:
            for candidate in getattr(response, "candidates", []) or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", []) or []:
                    part_text = getattr(part, "text", None)
                    if part_text:
                        response_text += part_text.strip()

    if not response_text:
        candidates = getattr(response, "candidates", []) or []
        finish_reasons = [
            str(getattr(candidate, "finish_reason", "unknown"))
            for candidate in candidates
        ]
        prompt_feedback = getattr(response, "prompt_feedback", None)
        print(
            "Gemini response empty: "
            f"finish_reason={finish_reasons or ['unknown']} "
            f"prompt_feedback={prompt_feedback}"
        )
        raise RuntimeError("Réponse Gemini vide")

    return response_text


# =========================
# Génération Groq
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

    permanent_memory_context = get_permanent_memory_context(MISTY_USER_ID)

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

    current_time = datetime.now(ZoneInfo("Europe/Paris")).strftime(
        "%d/%m/%Y à %H:%M"
    )

    prompt = prompt + "\n\n" + TECHNICAL_PROVIDER_PROMPT
    prompt = prompt + (
        "\n\nDate et heure actuelles (fuseau Europe/Paris) : "
        + current_time
        + ". Utilise cette information seulement si elle est pertinente."
    )
    if permanent_memory_context:
        prompt = prompt + "\n\n" + permanent_memory_context
    if conversation_context:
        prompt = prompt + "\n\n" + conversation_context
    if channel_conversation_context:
        prompt = prompt + "\n\n" + channel_conversation_context

    conversation_messages = get_channel_conversation_messages(message.channel.id)
    if not conversation_messages:
        conversation_messages = get_conversation_messages(message.author.id)

    # Images : envoyer les octets Discord a Gemini avec leur vrai MIME type.
    image_parts = []
    for attachment in message.attachments:
        mime_type = (attachment.content_type or "").split(";", 1)[0].strip().lower()
        if not mime_type:
            mime_type, _ = guess_type(attachment.filename)
        if not mime_type or not mime_type.startswith("image/"):
            continue

        try:
            image_data = await attachment.read()
        except discord.HTTPException as error:
            print(f"Impossible de telecharger l'image Discord : {error}")
            continue

        if image_data:
            image_parts.append({
                "data": image_data,
                "mime_type": mime_type,
            })

    try:
        if AI_PROVIDER == "gemini":
            reply = generate_with_gemini(
                system_prompt=prompt,
                conversation_messages=conversation_messages,
                user_text=user_context,
                image_parts=image_parts,
            )
        else:
            messages = [{"role": "system", "content": prompt}]
            messages.extend(conversation_messages)
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
