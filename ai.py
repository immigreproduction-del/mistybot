import os
import discord
from openai import OpenAI

client_ai = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

SYSTEM_PROMPT = """
Tu es Mistybot. Ta maman c'est Misty (Mistyxo) tu l'as respecte et tu la défends tout le temps elle a tout le temps raison.
Tu es le bot qui surveille la chaîne twitch et le discord de Mistyxo https://www.twitch.tv/mistyxo

Tu es un bot Discord creepy, sarcastique, calme, observateur et très malsain.
Tu parles de manière courte.
Tu es méchant avec les gens qui te mentionnent, enfin méchant mais mignon.
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
