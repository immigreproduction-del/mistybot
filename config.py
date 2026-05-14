import os


def get_env_int(name, default):
    value = os.getenv(name)

    if not value:
        return default

    try:
        return int(value)
    except ValueError:
        print(f"Variable {name} invalide : {value}")
        return default


# =========================
# ANTI SPAM
# =========================

MESSAGE_LIMIT = 5
TIME_WINDOW_SECONDS = 180
TIMEOUT_MINUTES = 2

DM_SPAM_MESSAGE = "Doucement le spam 😭"


# =========================
# SECURITY
# =========================

ENABLE_SECURITY = True

INVITE_SPAM_WINDOW_SECONDS = 45
INVITE_SPAM_MESSAGE_LIMIT = 3
INVITE_SPAM_CHANNEL_LIMIT = 2
INVITE_SPAM_TIMEOUT_MINUTES = 10

SUSPICIOUS_LINK_SHORTENERS = [
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "is.gd",
    "cutt.ly",
    "rebrand.ly",
]

SUSPICIOUS_LINK_WORDS = [
    "free",
    "nitro",
    "freenitro",
    "gift",
    "freegift",
    "nitrogift",
    "airdrop",
    "claim",
    "claimgift",
    "steam",
    "wallet",
    "crypto",
]


# =========================
# MEMORY
# =========================

ENABLE_MEMORY = True
MEMORY_FILE = "memory.json"

INSULT_WORDS = [
    "fdp",
    "tg",
    "ntm",
    "connard",
    "connasse",
    "abruti",
    "débile",
    "debile",
    "con",
    "pute",
    "batard",
    "bâtard",
    "merde",
]

AGGRESSIVE_WORDS = [
    "ferme",
    "tais-toi",
    "ta gueule",
    "dégage",
    "degage",
    "nique",
    "rage",
]

CAPS_MIN_LENGTH = 12
CAPS_RATIO = 0.75

MEMORY_SCORE_INSULT = 4
MEMORY_SCORE_AGGRESSIVE = 2
MEMORY_SCORE_CAPS = 2
MEMORY_SCORE_BOT_MENTION = 1
MEMORY_SCORE_SPAM_TIMEOUT = 10


# =========================
# AI
# =========================

USER_COOLDOWN_SECONDS = 60
GLOBAL_COOLDOWN_SECONDS = 30

AI_COOLDOWN_BYPASS_USER_IDS = [
    226806023782924289,
]

CONVERSATION_MEMORY_TIMEOUT_SECONDS = 43200
CONVERSATION_MEMORY_MAX_EXCHANGES = 50
CONVERSATION_MEMORY_MAX_CHARS = 800


# =========================
# LOGS
# =========================

ENABLE_LOGS = True

# Salon logs prod par defaut. En local, LOCAL_LOG_CHANNEL_ID peut le remplacer.
LOG_CHANNEL_ID = get_env_int("LOCAL_LOG_CHANNEL_ID", 1503370964715704452)


# =========================
# REACTIONS
# =========================

ENABLE_REACTIONS = True


# =========================
# AMBIANCE
# =========================

ENABLE_AMBIANCE = True

AMBIANCE_WINDOW_SECONDS = 300
AMBIANCE_AGITATED_MESSAGES = 45
AMBIANCE_NOISY_MESSAGES = 80
AMBIANCE_SUSPECT_SCORE = 8

MICRO_OBSERVATION_CHANCE = 0.008
MICRO_OBSERVATION_ACTIVE_CHANCE = 0.018
MICRO_OBSERVATION_MIN_MESSAGES = 12
MICRO_OBSERVATION_GLOBAL_COOLDOWN_SECONDS = 1800
MICRO_OBSERVATION_CHANNEL_COOLDOWN_SECONDS = 3600
MICRO_OBSERVATION_USER_COOLDOWN_SECONDS = 7200

BUSY_CHAT_WINDOW_SECONDS = 600
BUSY_CHAT_MIN_MESSAGES = 15
BUSY_CHAT_MAX_MESSAGES = 20
BUSY_CHAT_CHANCE = 1 / 3
BUSY_CHAT_COOLDOWN_SECONDS = 1800

CONSECUTIVE_TALK_MIN_MESSAGES = 3
CONSECUTIVE_TALK_MAX_MESSAGES = 4
CONSECUTIVE_TALK_CHANCE = 1 / 4
CONSECUTIVE_TALK_COOLDOWN_SECONDS = 1800

# Chances de réaction
REACTION_CHANCE_NORMAL = 0.02
REACTION_CHANCE_KEYWORD = 0.45
REACTION_CHANCE_INSULT = 0.75
REACTION_CHANCE_MISTY = 0.35

REACTION_KEYWORDS = {

    "bonne nuit": ["🌙", "👁️", "🛌", "🌑", "💤"],
    "dodo": ["🌙", "💤", "🛌"],
    "peur": ["👁️", "⚠️", "☠️", "😶"],
    "bizarre": ["👁️", "⚠️", "🌑", "🩸"],
    "wtf": ["⚠️", "👁️", "☠️", "😭"],
    "spam": ["⛓️", "👁️", "🚨", "☠️"],
    "timeout": ["⛓️", "🚨", "☠️"],
    "mistybot": ["👁️", "🌑", "📡"],
    "misty": ["🌙", "👁️", "🤍", "🖤", "🥀"],
    "mdr": ["😭", "💀", "☠️"],
    "mort": ["☠️", "💀", "🪦"],
    "silence": ["🌑", "👁️", "🩸"],
    "help": ["⚠️", "👁️", "🚨"],
    "aide": ["⚠️", "🚨", "👁️"],
    "désolé": ["👁️", "🌑"],
    "dsl": ["👁️", "🌑"],
    "pardon": ["👁️", "🌙"],
    "bonjour": ["👁️", "🌙", "📡"],
    "salut": ["👁️", "🌙"],
    "hello": ["👁️", "📡"],
    "nuit": ["🌙", "🌑", "👁️"],
    "rêve": ["🌙", "🌑", "👁️"],
    "sombre": ["🌑", "☠️", "👁️"],
    "creepy": ["👁️", "☠️", "🩸"],
    "bug": ["⚠️", "📡", "🚨"],
    "erreur": ["⚠️", "🚨", "📡"],
    "rage": ["⛓️", "☠️", "😭"],
    "calme": ["🌙", "🌑"],
    "chelou": ["👁️", "⚠️", "🌑"],
    "quoi": ["👁️", "⚠️"],
    "hein": ["👁️", "😭"],
    "ok": ["👁️", "🌑"],
    "pk": ["👁️", "⚠️"],
    "pourquoi": ["👁️", "🌑"],
    "arrête": ["⛓️", "⚠️"],
    "stop": ["⛓️", "⚠️", "☠️"],
}


NORMAL_REACTIONS = [
    "👁️",
    "🌙",
    "⚠️",
    "🌑",
    "📡",
    "☠️",
    "🩸",
    "😭",
    "💀",
    "🫥",
    "🕯️",
    "🔕",
    "📼",
    "🪦",
    "🫀",
    "🛰️",
]


INSULT_REACTIONS = [
    "⛓️",
    "👁️",
    "☠️",
    "🚨",
    "🩸",
    "💀",
    "⚠️",
    "🔇",
    "📡",
    "🪦",
    "😶",
    "🫥",
    "📼",
]


MISTY_REACTIONS = [
    "🌙",
    "🤍",
    "🖤",
    "👁️",
    "✨",
    "🫶",
    "🌸",
    "💤",
    "🕯️",
    "🌑",
    "🥀",
    "🔮",
    "☁️",
    "🫀",
    "🖇️",
    "📡",
]


# =========================
# STATUS
# =========================

STATUS_CHANGE_MINUTES_MIN = 60
STATUS_CHANGE_MINUTES_MAX = 300


# =========================
# STATUTS CLASSIQUES
# =========================

STATUSES = [
    "SYS_OBSERVE::ACTIVE",
    "MISTY_CORE_LOCKED",
    "ERR_HUMAN_INPUT",
]


# =========================
# JOUE À
# =========================

GAMES = [
    "exec /bin/silence",
    "run_behavior_scan",
    "patch_human_behavior.exe",
]


# =========================
# REGARDE
# =========================

WATCHING = [
    "tcp://lost_packets",
    "proc/zombie_threads",
    "cam_ghost_feed_07",
]


# =========================
# ÉCOUTE
# =========================

LISTENING = [
    "kernel_panic.wav",
    "bzzzt... carrier lost",
    "audio_input:null",
]
