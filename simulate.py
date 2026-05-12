import asyncio
import os
import sys
from types import SimpleNamespace

from ambiance import (
    _count_channel_messages,
    get_global_mood,
    observe_ambiance,
)
from antispam import handle_antispam
from memory import contains_words
from reactions import contains_any
from security import get_link_reason, handle_security
from text_utils import contains_loose_word

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MEMORY_FILE = "memory.json"


class FakeGuildPermissions:
    def __init__(self, administrator=False):
        self.administrator = administrator


class FakeAuthor:
    def __init__(self, user_id, name="TestUser", bot=False, admin=False):
        self.id = user_id
        self.name = name
        self.display_name = name
        self.bot = bot
        self.guild_permissions = FakeGuildPermissions(admin)
        self.timed_out_until = None
        self.dm_messages = []

    async def send(self, content):
        self.dm_messages.append(content)
        print(f"DM -> {self.name}: {content}")

    async def timeout(self, until, reason=None):
        self.timed_out_until = until
        print(f"TIMEOUT -> {self.name}: {reason}")


class FakeChannel:
    def __init__(self, channel_id, name="test"):
        self.id = channel_id
        self.name = name
        self.mention = f"#{name}"
        self.sent_messages = []

    async def send(self, content=None, embed=None):
        if embed:
            title = getattr(embed, "title", "embed")
            description = getattr(embed, "description", "")
            print(f"LOG -> {title}: {description.strip()[:160]}")
            return

        self.sent_messages.append(content)
        print(f"BOT -> {self.name}: {content}")


class FakeClient:
    def __init__(self, log_channel):
        self.log_channel = log_channel

    def get_channel(self, channel_id):
        return self.log_channel


class FakeMessage:
    def __init__(self, content, author, channel, guild_id=999):
        self.content = content
        self.clean_content = content
        self.author = author
        self.channel = channel
        self.guild = SimpleNamespace(id=guild_id)
        self.mentions = []
        self.role_mentions = []
        self.deleted = False

    async def delete(self):
        self.deleted = True
        print(f"DELETE -> {self.channel.name}: {self.content}")

    async def add_reaction(self, emoji):
        print(f"REACTION -> {emoji}")

    async def reply(self, content):
        print(f"REPLY -> {content}")


def print_title(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


async def test_security():
    print_title("SECURITE")

    logs = FakeChannel(9999, "logs")
    client = FakeClient(logs)
    author = FakeAuthor(123, "NonAdmin")
    admin = FakeAuthor(456, "Admin", admin=True)
    channel = FakeChannel(111, "general")

    for content in [
        "discord.gg/test",
        "www.bit.ly/freenitro",
        "bit.ly/freenitro",
        "https://example.com",
    ]:
        print(f"\nMessage: {content}")
        print(f"Detection: {get_link_reason(content)}")
        message = FakeMessage(content, author, channel)
        handled = await handle_security(message, client)
        print(f"Traite: {handled} | Supprime: {message.deleted}")

    print("\nAdmin avec invitation:")
    message = FakeMessage("discord.gg/test", admin, channel)
    handled = await handle_security(message, client)
    print(f"Traite: {handled} | Supprime: {message.deleted}")


async def test_antispam():
    print_title("ANTI-SPAM")

    logs = FakeChannel(9999, "logs")
    client = FakeClient(logs)
    author = FakeAuthor(123, "Flooder")
    channel = FakeChannel(222, "spam-test")

    for index in range(1, 6):
        message = FakeMessage(f"spam {index}", author, channel)
        await handle_antispam(message, client)
        print(f"Message {index} | Supprime: {message.deleted}")


def test_text_matching():
    print_title("MOTS-CLES SOUPLES")

    checks = [
        ("BONNES NUITS", "bonne nuit"),
        ("Bonne nuit !!!", "bonne nuit"),
        ("connards", "connard"),
        ("ta gueules", "ta gueule"),
    ]

    for content, keyword in checks:
        print(f"{content!r} / {keyword!r} -> {contains_loose_word(content, keyword)}")

    print("Reaction insultes:", contains_any("CONNARDS", ["connard"]))
    print("Memoire agressive:", contains_words("ta gueules", ["ta gueule"]))


def test_ambiance():
    print_title("AMBIANCE")

    author = FakeAuthor(123, "Bavard")
    channel = FakeChannel(333, "ambiance")

    for index in range(50):
        observe_ambiance(FakeMessage(f"message {index}", author, channel, guild_id=1234))

    print("Messages salon sur 10 min:", _count_channel_messages(channel.id, __import__("discord").utils.utcnow(), 600))
    print("Humeur globale:", get_global_mood())

    suspect = FakeAuthor(321, "Bruyant")
    for _ in range(2):
        observe_ambiance(FakeMessage("TA GUEULE CONNARD", suspect, channel, guild_id=4321))

    print("Humeur apres agressivite:", get_global_mood())


async def main():
    memory_backup = None

    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            memory_backup = file.read()

    test_text_matching()
    test_ambiance()
    await test_security()
    await test_antispam()

    if memory_backup is not None:
        with open(MEMORY_FILE, "w", encoding="utf-8") as file:
            file.write(memory_backup)


if __name__ == "__main__":
    asyncio.run(main())
