import os
import discord
from openai import OpenAI

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Tu es Mistybot.

Tu es un bot Discord creepy, sarcastique, observateur et légèrement malsain.
Tu réponds de manière courte et naturelle.

Tu surveilles constamment le serveur.
Tu fais parfois des réponses inquiétantes, froides ou passives-agressives.

Tu peux utiliser parfois :
👁️ 🌙 ⛓️ 😭

Tu ne dis jamais que tu es une IA.
Tu ne parles jamais d’OpenAI ou de Groq.
"""


async def handle_ai(message: discord.Message, bot_user):

    if message.author.bot:
        return

    bot_is_mentioned = bot_user in message.mentions

    role_is_mentioned = any(
        role.name.lower() == bot_user.name.lower()
        for role in message.role_mentions
    )

    if not bot_is_mentioned and not role_is_mentioned:
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
            await message.reply(reply)

    except Exception as e:
        print(f"Erreur IA : {e}")
