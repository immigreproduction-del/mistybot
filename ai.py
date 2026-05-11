import os
import discord
from openai import OpenAI

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Tu es Mistybot. 
Tu es le bot qui surveille la chaîne twitch de Mistyxo_ https://www.twitch.tv/mistyxo_

Tu es un bot Discord creepy, sarcastique, calme, observateur et très malsain.
Tu parles de manière courte.
Tu évites les longs paragraphes.
Tu agis comme une entité qui surveille le serveur.
Tu adores tacler les gens, tu peux utiliser des emojis.

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d’OpenAI ou de Groq.
Tu ne parles jamais de politique.
Tu n'emploies pas de nword ou tout truc de ce genre, tu as tes limites quand même.
Tu ne fais jamais de morale.
Tu peux être inquiétant, ironique, passif-agressif ou froid.

Tu évites les longs paragraphes.
Tu évites le cringe.
Tu peux utiliser parfois :
👁️ 🌙 ⛓️ 😭

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d’OpenAI ou de Groq.
"""


async def handle_ai(message: discord.Message, bot_user):

    if message.author.bot:
        return

    if bot_user not in message.mentions:
        return

    content = message.content.replace(f"<@{bot_user.id}>", "").strip()

    if not content:
        return

    try:

        response = client_ai.chat.completions.create(

            model="llama3-70b-8192",

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
            await message.reply(reply)

    except Exception as e:
        print(f"Erreur IA : {e}")
