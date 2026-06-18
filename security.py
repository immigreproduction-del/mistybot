import re
from collections import defaultdict, deque
from datetime import timedelta
from urllib.parse import urlparse

import discord

from config import *
from logs import log_security_action, log_security_raid

INVITE_PATTERN = re.compile(
    r"(discord\.gg/|discord(?:app)?\.com/invite/)",
    re.IGNORECASE
)

URL_PATTERN = re.compile(
    r"(?:https?://|www\.)[^\s<>()]+",
    re.IGNORECASE
)

SHORTENER_PATTERN = re.compile(
    r"(?:^|\s)("
    + "|".join(re.escape(domain) for domain in SUSPICIOUS_LINK_SHORTENERS)
    + r")/[^\s<>()]+",
    re.IGNORECASE
)

recent_link_messages = defaultdict(deque)
recent_attachment_messages = defaultdict(deque)


def contains_forbidden_timeout_word(content):
    lowered_content = content.lower()

    return any(
        re.search(rf"\b{re.escape(word.lower())}\b", lowered_content)
        for word in FORBIDDEN_TIMEOUT_WORDS
    )


def has_attachment(message):
    return bool(message.attachments)


def contains_discord_invite(content):
    return bool(INVITE_PATTERN.search(content))


def extract_urls(content):
    urls = URL_PATTERN.findall(content)
    urls.extend(match.group(0).strip() for match in SHORTENER_PATTERN.finditer(content))
    return urls


def is_suspicious_url(url):
    lowered_url = url.lower()

    if lowered_url.startswith("www.") or any(
        lowered_url.startswith(f"{domain}/")
        for domain in SUSPICIOUS_LINK_SHORTENERS
    ):
        url = "https://" + url

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    full_url = url.lower()

    if "@" in parsed.netloc:
        return True

    if host.startswith("www."):
        host = host[4:]

    if host.startswith("xn--"):
        return True

    if host in SUSPICIOUS_LINK_SHORTENERS:
        return True

    return any(word in full_url for word in SUSPICIOUS_LINK_WORDS)


def get_link_reason(content):
    urls = extract_urls(content)

    if contains_discord_invite(content):
        return "invitation Discord"

    if any(is_suspicious_url(url) for url in urls):
        return "lien suspect"

    if urls:
        return "lien"

    return None


def remember_link_message(message, now):
    user_id = message.author.id
    entries = recent_link_messages[user_id]
    entries.append((now, message.channel.id))

    while entries:
        created_at, _ = entries[0]
        age = (now - created_at).total_seconds()

        if age <= INVITE_SPAM_WINDOW_SECONDS:
            break

        entries.popleft()

    channel_ids = {channel_id for _, channel_id in entries}
    return len(entries), len(channel_ids)


def remember_attachment_message(message, now):
    user_id = message.author.id
    entries = recent_attachment_messages[user_id]
    entries.append((now, message.channel.id, message.id))

    while entries:
        created_at, _, _ = entries[0]
        age = (now - created_at).total_seconds()

        if age <= ATTACHMENT_SPAM_WINDOW_SECONDS:
            break

        entries.popleft()

    channel_ids = {channel_id for _, channel_id, _ in entries}
    return len(entries), len(channel_ids), list(entries)


async def delete_recent_attachment_messages(client, entries, current_message):
    for _, channel_id, message_id in entries:
        if message_id == current_message.id:
            await safe_delete(current_message)
            continue

        channel = client.get_channel(channel_id)

        if channel is None or not hasattr(channel, "fetch_message"):
            continue

        try:
            old_message = await channel.fetch_message(message_id)
        except Exception:
            continue

        await safe_delete(old_message)


async def safe_delete(message):
    try:
        await message.delete()
        return True
    except Exception as e:
        print(f"Erreur suppression securite : {e}")
        return False


async def safe_timeout(member, until, reason):
    try:
        await member.timeout(until, reason=reason)
        return True
    except Exception as e:
        print(f"Erreur timeout securite : {e}")
        return False


async def handle_security(message: discord.Message, client):
    if not ENABLE_SECURITY:
        return False

    if message.author.bot or not message.guild:
        return False

    if contains_forbidden_timeout_word(message.content):
        await safe_delete(message)

        now = discord.utils.utcnow()
        timed_out = await safe_timeout(
            message.author,
            now + timedelta(days=FORBIDDEN_WORD_TIMEOUT_DAYS),
            reason="Mot interdit"
        )

        action = "message supprime"
        if timed_out:
            action += f" + timeout {FORBIDDEN_WORD_TIMEOUT_DAYS} jours"

        await log_security_action(
            client,
            message,
            "mot interdit",
            action
        )
        return True

    if message.author.guild_permissions.administrator:
        return False

    now = discord.utils.utcnow()

    if has_attachment(message):
        messages_count, channels_count, attachment_entries = remember_attachment_message(message, now)

        is_attachment_raid = (
            messages_count >= ATTACHMENT_SPAM_MESSAGE_LIMIT
            and channels_count >= ATTACHMENT_SPAM_CHANNEL_LIMIT
        )

        if is_attachment_raid:
            await delete_recent_attachment_messages(client, attachment_entries, message)

            timed_out = await safe_timeout(
                message.author,
                now + timedelta(days=ATTACHMENT_SPAM_TIMEOUT_DAYS),
                reason="Spam de fichiers/images dans plusieurs salons"
            )

            await log_security_raid(
                client,
                message,
                "spam de fichiers/images",
                channels_count,
                messages_count,
                f"timeout {ATTACHMENT_SPAM_TIMEOUT_DAYS} jours"
            )

            recent_attachment_messages[message.author.id].clear()
            return True

    reason = get_link_reason(message.content)

    if reason is None:
        return False

    messages_count, channels_count = remember_link_message(message, now)

    is_raid_pattern = (
        messages_count >= INVITE_SPAM_MESSAGE_LIMIT
        and channels_count >= INVITE_SPAM_CHANNEL_LIMIT
    )

    if reason == "invitation Discord" or reason == "lien suspect" or is_raid_pattern:
        await safe_delete(message)

    if is_raid_pattern:
        until = now + timedelta(minutes=INVITE_SPAM_TIMEOUT_MINUTES)
        timed_out = await safe_timeout(
            message.author,
            until,
            reason="Spam de liens/invitations dans plusieurs salons"
        )

        action = "message supprime"
        if timed_out:
            action += " + timeout"

        await log_security_raid(
            client,
            message,
            reason,
            channels_count,
            messages_count
        )

        recent_link_messages[message.author.id].clear()
        return True

    if reason == "invitation Discord" or reason == "lien suspect":
        await log_security_action(
            client,
            message,
            reason,
            "message supprime"
        )
        return True

    return False
