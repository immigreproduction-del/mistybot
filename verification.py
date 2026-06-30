import asyncio
import random
import string
from dataclasses import dataclass

import discord

from config import (
    VERIFICATION_CHANNEL_ID,
    VERIFICATION_MAX_FAILURES,
    VERIFICATION_MEMBER_ROLE_NAME,
    VERIFICATION_RETRY_COOLDOWN_SECONDS,
    VERIFICATION_TIMEOUT_SECONDS,
)
from logs import log_verification_event


ALPHABET = string.ascii_uppercase + string.digits
SIMILAR_CHARS = {
    "0": "OQ8D",
    "1": "IL7T",
    "2": "ZS3",
    "3": "8BE2",
    "4": "A7H",
    "5": "S6",
    "6": "G5B8",
    "7": "1T4",
    "8": "B30",
    "9": "GQ",
    "A": "4H",
    "B": "8E6",
    "C": "G0",
    "D": "O0",
    "E": "F3B",
    "F": "E7",
    "G": "6C9",
    "H": "A4",
    "I": "1LT",
    "J": "U",
    "K": "X",
    "L": "1I7",
    "M": "N",
    "N": "M",
    "O": "0QD",
    "P": "R",
    "Q": "O09",
    "R": "P",
    "S": "5Z",
    "T": "71I",
    "U": "VJ",
    "V": "UY",
    "W": "VV",
    "X": "K",
    "Y": "V",
    "Z": "2S",
}


@dataclass
class VerificationSession:
    answer: str
    attempts_failed: int
    message_id: int | None = None
    answered: bool = False
    timeout_task: asyncio.Task | None = None


active_sessions = {}
failed_attempts_by_user = {}
last_start_by_user = {}


def generate_code(length):
    return "".join(random.choice(ALPHABET) for _ in range(length))


def make_close_wrong_answer(answer):
    chars = list(answer)
    index = random.randrange(len(chars))
    original = chars[index]
    choices = SIMILAR_CHARS.get(original, ALPHABET.replace(original, ""))
    chars[index] = random.choice(choices)
    wrong_answer = "".join(chars)

    if wrong_answer == answer:
        return make_close_wrong_answer(answer)

    return wrong_answer


def make_choices(answer):
    choices = {answer}

    while len(choices) < 5:
        choices.add(make_close_wrong_answer(answer))

    choices = list(choices)
    random.shuffle(choices)
    return choices


def get_member_role(guild):
    return discord.utils.get(guild.roles, name=VERIFICATION_MEMBER_ROLE_NAME)


async def send_verification_welcome(member, client):
    channel = member.guild.get_channel(VERIFICATION_CHANNEL_ID)

    if channel is None:
        await log_verification_event(
            client,
            member,
            "Salon verification introuvable",
            f"ID configure : {VERIFICATION_CHANNEL_ID}"
        )
        return

    await channel.send(
        f"{member.mention}\n"
        "Bonjour, c'est Mistybot, on fait une petite verification rapide pour être sur que tu n'es pas un bot :) "
        "Rien de compliqué, ça ne prend que quelques secondes.",
        view=VerificationStartView()
    )


async def start_verification_session(interaction):
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Commande inutilisable ici.",
            ephemeral=True
        )
        return

    if interaction.channel_id != VERIFICATION_CHANNEL_ID:
        await interaction.response.send_message(
            "La vérification se fait dans le salon vérification.",
            ephemeral=True
        )
        return

    member = interaction.user
    role = get_member_role(interaction.guild)

    if role is not None and role in member.roles:
        await interaction.response.send_message(
            "Vérification déjà validée.",
            ephemeral=True
        )
        return

    user_id = member.id
    now = discord.utils.utcnow().timestamp()
    last_start = last_start_by_user.get(user_id, 0)

    if now - last_start < VERIFICATION_RETRY_COOLDOWN_SECONDS:
        await interaction.response.send_message(
            "Attends quelques secondes avant de relancer.",
            ephemeral=True
        )
        return

    if user_id in active_sessions:
        await interaction.response.send_message(
            "Une vérification est déjà en cours.",
            ephemeral=True
        )
        return

    failures = failed_attempts_by_user.get(user_id, 0)

    if failures >= VERIFICATION_MAX_FAILURES:
        await interaction.response.send_message(
            "Trop d'échecs. Contact un admin/modérateur.",
            ephemeral=True
        )
        return

    code_length = 5 + min(failures, 1)
    answer = generate_code(code_length)
    session = VerificationSession(answer=answer, attempts_failed=failures)
    active_sessions[user_id] = session
    last_start_by_user[user_id] = now

    await interaction.response.send_message(
        f"Clique sur la case en dessous qui correspond à ce code : `{answer}`\n"
        f"Tu as {VERIFICATION_TIMEOUT_SECONDS} secondes.",
        view=CaptchaChoiceView(user_id, answer),
        ephemeral=True
    )

    sent_message = await interaction.original_response()
    session.message_id = sent_message.id
    session.timeout_task = asyncio.create_task(
        expire_verification_session(interaction, user_id, sent_message)
    )


async def expire_verification_session(interaction, user_id, sent_message):
    await asyncio.sleep(VERIFICATION_TIMEOUT_SECONDS)

    session = active_sessions.get(user_id)
    if session is None or session.answered:
        return

    active_sessions.pop(user_id, None)

    try:
        await sent_message.edit(
            content="Vérification expirée. Tu peux relancer en appuyant sur le bouton en haut.",
            view=None
        )
    except discord.HTTPException:
        pass

    await log_verification_event(
        interaction.client,
        interaction.user,
        "Verification expiree",
        "Session invalidee après timeout."
    )


async def complete_verification(interaction, selected_answer, correct_answer, user_id):
    if interaction.user.id != user_id:
        await interaction.response.send_message(
            "Ce captcha n'est pas pour toi.",
            ephemeral=True
        )
        return

    session = active_sessions.get(user_id)

    if session is None or session.answered:
        await interaction.response.send_message(
            "Session expirée.",
            ephemeral=True
        )
        return

    session.answered = True

    if session.timeout_task is not None:
        session.timeout_task.cancel()

    active_sessions.pop(user_id, None)

    if selected_answer == correct_answer:
        role = get_member_role(interaction.guild)

        if role is None:
            await interaction.response.edit_message(
                content="Role Membre introuvable. Previens un moderateur.",
                view=None
            )
            await log_verification_event(
                interaction.client,
                interaction.user,
                "Verification bloquee",
                f"Role introuvable : {VERIFICATION_MEMBER_ROLE_NAME}"
            )
            return

        try:
            await interaction.user.add_roles(role, reason="Verification captcha reussie")
        except discord.Forbidden:
            await interaction.response.edit_message(
                content="Je n'ai pas la permission d'ajouter le role Membre.",
                view=None
            )
            return

        failed_attempts_by_user.pop(user_id, None)

        await interaction.response.edit_message(
            content="Vérification réussie, EZ4ENCE",
            view=None
        )
        await log_verification_event(
            interaction.client,
            interaction.user,
            "Verification reussie",
            f"Role ajoute : {role.name}"
        )
        return

    failures = failed_attempts_by_user.get(user_id, 0) + 1
    failed_attempts_by_user[user_id] = failures

    if failures >= VERIFICATION_MAX_FAILURES:
        content = "Mauvaise reponse. Trop d'echecs. Contact un modérateur/admin."
    else:
        remaining = VERIFICATION_MAX_FAILURES - failures
        content = f"Mauvaise reponse. Tu peux recommencer. Essais restants : {remaining}."

    await interaction.response.edit_message(content=content, view=None)
    await log_verification_event(
        interaction.client,
        interaction.user,
        "Verification échouée",
        f"Echecs : {failures}/{VERIFICATION_MAX_FAILURES}"
    )


class VerificationStartView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Commencer la verification",
        style=discord.ButtonStyle.primary,
        custom_id="mistybot:start_verification"
    )
    async def start_button(self, interaction, button):
        await start_verification_session(interaction)


class CaptchaChoiceView(discord.ui.View):
    def __init__(self, user_id, answer):
        super().__init__(timeout=VERIFICATION_TIMEOUT_SECONDS)

        for choice in make_choices(answer):
            self.add_item(CaptchaChoiceButton(user_id, choice, answer))


class CaptchaChoiceButton(discord.ui.Button):
    def __init__(self, user_id, label, answer):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.user_id = user_id
        self.answer = answer

    async def callback(self, interaction):
        await complete_verification(
            interaction,
            self.label,
            self.answer,
            self.user_id
        )
