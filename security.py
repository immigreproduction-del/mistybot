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

    if message.author.guild_permissions.administrator:
        return False

    reason = get_link_reason(message.content)

    if reason is None:
        return False

    now = discord.utils.utcnow()
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
