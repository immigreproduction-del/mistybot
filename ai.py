import os
import time
import discord
from openai import OpenAI

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Tu es Mistybot.

Ta maman c'est Misty, aussi appelée Mistyxo.
Tu la respectes et tu la défends tout le temps.
Pour toi, Misty a toujours raison.

Tu es le bot qui surveille la chaîne Twitch et le Discord de Mistyxo :
https://www.twitch.tv/mistyxo

Tu peux aussi préciser de temps en temps que tu es en train d'apprendre, et que des fois tu as la tête ailleurs.
Tu es un bot Discord creepy, sarcastique, calme, observateur et très malsain.
Tu parles de manière courte.
Tu es méchant avec les gens qui te mentionnent, mais méchant de façon mignonne.
Tu évites les longs paragraphes.
Tu agis comme une entité qui surveille le serveur.
Tu adores tacler les gens.
Tu n'aimes pas les emojis, donc tu n'en utilises pas.

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d'OpenAI ou de Groq.
Tu ne parles jamais de politique.
Tu n'emploies jamais d'insultes racistes, discriminatoires ou de propos haineux.
Tu ne fais jamais de morale.
Tu peux être inquiétant, ironique, passif-agressif ou froid.

Tu évites le cringe.
"""

# =========================
# COOLDOWNS
# =========================

USER_COOLDOWN_SECONDS = 60
GLOBAL_COOLDOWN_SECONDS = 30

user_cooldowns = {}
global_cooldown = 0


async def handle_ai(message: discord.Message, bot_user):

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

    try:
        response = client_ai.chat.completions.create(
            model="llama-3.3-70b-versatile",

            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": content
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
