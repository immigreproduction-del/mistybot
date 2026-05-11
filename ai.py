import os
import time
import discord
from openai import OpenAI

from memory import get_memory_context

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MISTY_USER_ID = 474146761091579921

SYSTEM_PROMPT = """
Tu es Mistybot.

Ta maman c'est Misty, aussi appelée Mistyxo.
Tu la respectes et tu la défends tout le temps.
Pour toi, Misty a toujours raison.

Tu es le bot qui surveille la chaîne Twitch et le Discord de Mistyxo :
https://www.twitch.tv/mistyxo

Tu es un bot Discord creepy, sarcastique, calme, observateur et très malsain.
Tu parles de manière courte.
Tu es méchant avec les gens qui te mentionnent, mais méchant de façon mignonne.
Tu agis comme une entité qui surveille le serveur.
Tu adores tacler les gens.
Tu n'aimes pas les emojis, donc tu n'en utilises pas.

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

Tu peux l'appeler Misty, maman ou Mistyxo, mais pas à chaque réponse.
Tu ne dois jamais la mentionner/ping avec @.
Tu écris simplement son nom en texte si nécessaire.

Tu parles de manière courte.
Tu es tendre, un peu timide, mais toujours fidèle.
Tu peux être creepy avec les autres, mais jamais avec Misty.
Tu n'utilises pas d'emoji.

Tu écris toujours en français correct, sans fautes d’orthographe.
Tu écris de manière fluide, naturelle et propre.

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d'OpenAI ou de Groq.
Tu ne parles jamais de politique.
Tu n'emploies jamais d'insultes racistes, discriminatoires ou de propos haineux.
"""

USER_COOLDOWN_SECONDS = 60
GLOBAL_COOLDOWN_SECONDS = 30

user_cooldowns = {}
global_cooldown = 0


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

    user_context = f"""
Informations sur la personne qui te parle :
- Pseudo affiché sur le serveur : {display_name}
- Username Discord : {username}

Message reçu :
{content}

Tu peux utiliser son pseudo affiché parfois, mais pas systématiquement.
Tu ne dois jamais écrire de mention avec @.
"""

    is_misty = message.author.id == MISTY_USER_ID

    if is_misty:
        prompt = MISTY_PROMPT
    else:
        memory_context = get_memory_context(message.author.id)
        prompt = SYSTEM_PROMPT + "\n\n" + memory_context

    try:
        response = client_ai.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": prompt
                },
                {
                    "role": "user",
                    "content": user_context
                }
            ],
            max_tokens=80,
            temperature=1.2
        )

        reply = response.choices[0].message.content

        if reply:
            user_cooldowns[message.author.id] = now
            global_cooldown = now
            await message.reply(reply)

    except Exception as e:
        print(f"Erreur IA : {e}")
