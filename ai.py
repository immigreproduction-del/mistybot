import os
import discord
from openai import OpenAI

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Tu es Mistybot.

Bot Discord creepy, sarcastique et observateur.
Tu réponds de manière courte.
Tu surveilles constamment le serveur.

Tu peux être inquiétant, froid ou passif-agressif.

Tu peux parfois utiliser :
👁️ 🌙 ⛓️ 😭

Tu ne dis jamais que tu es une IA.
"""


async def handle_ai(message: discord.Message, bot_user):

    if message.author.bot:
        return

    if bot_user not in message.mentions:
        return

    content = message.clean_content.replace(f"@{bot_user.name}", "").strip()

    if not content:
        content = "Quelqu’un t’a mentionné."

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
