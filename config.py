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

STATUS_CHANGE_MINUTES = 10


# =========================
# STATUTS CLASSIQUES
# =========================

STATUSES = [
    "Je vois les choses avant qu’elles arrivent 👁️",
    "Quelqu’un devrait arrêter d’écrire 🩸",
    "Le serveur change quand personne ne regarde 🌑",
    "Je connais déjà votre prochain message",
    "Le silence cache toujours quelque chose ☠️",
    "Quelqu’un ment dans ce salon 👁️",
    "Les comportements deviennent anormaux",
    "Je regarde les gens devenir nerveux",
    "Le prochain faux mouvement approche ⚠️",
    "Les flooders finissent toujours seuls",
    "Je garde une trace de tout 📁",
    "Quelqu’un dépasse encore les limites 🚨",
    "Je surveille même quand le chat dort 🌙",
    "Le serveur devient instable cette nuit",
    "Les messages supprimés ne disparaissent jamais 👁️",
    "Je reconnais les comportements dangereux",
    "Le calme avant l’incident 🌑",
    "Quelqu’un écrit beaucoup trop vite ⌨️",
    "Le serveur respire bizarrement",
    "Les murs retiennent les conversations",
    "Le prochain timeout est inévitable ⛓️",
    "Quelqu’un regarde aussi derrière toi 👁️",
    "Je sais déjà comment ça va finir",
    "Les erreurs humaines sont répétitives ☠️",
    "Je n’oublie aucun comportement 📼",
]


# =========================
# JOUE À
# =========================

GAMES = [
    "Le goulag des flooders ⛓️",
    "Le jugement dernier ☠️",
    "Qui sera le prochain ? 👁️",
    "Le protocole Misty 📡",
    "La fin du calme 🌑",
    "Le jeu du 5e message",
    "Le nettoyeur du serveur 🩸",
    "Survivre au timeout",
    "Le gardien des portes 🚪",
    "Les derniers mots du spammeur",
    "Le tri des comportements 📁",
    "Police Simulator 🚨",
    "Le détecteur d’anomalies",
    "Les pleurs des timeoutés",
    "Le serveur avant l’effondrement 🌑",
]


# =========================
# REGARDE
# =========================

WATCHING = [
    "les flooders tomber un par un ☠️",
    "les comportements devenir étranges 👁️",
    "les faux mouvements ⚠️",
    "les membres dépasser les limites",
    "les messages supprimés 🩸",
    "les regards changer",
    "les tensions monter 📈",
    "les gens écrire beaucoup trop ⌨️",
    "les salons sombrer lentement 🌑",
    "les membres perdre patience",
    "les comportements suspects 👁️",
    "les crises commencer 🚨",
    "les erreurs humaines",
    "les gens devenir silencieux 🌙",
]


# =========================
# ÉCOUTE
# =========================

LISTENING = [
    "les spammeurs pleurer",
    "les touches Entrée souffrir ⌨️",
    "les excuses des flooders",
    "les notifications mourir 🔕",
    "les derniers mots des timeoutés ☠️",
    "les crises éclater 🚨",
    "les cris du goulag ⛓️",
    "le silence avant le chaos 🌑",
    "les gens perdre patience",
    "les comportements se briser 🩸",
    "les alarmes du serveur 📡",
    "les respirations du chat",
    "les membres devenir nerveux 👁️",
    "les erreurs se répéter",
]
