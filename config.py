# =========================
# ANTI SPAM
# =========================

MESSAGE_LIMIT = 5
TIME_WINDOW_SECONDS = 60
TIMEOUT_MINUTES = 2

DM_SPAM_MESSAGE = "Doucement le spam 😭"


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

# Remplace par l'ID de ton salon #misty-logs
LOG_CHANNEL_ID = 123456789012345678


# =========================
# REACTIONS
# =========================

ENABLE_REACTIONS = True

# Chances de réaction
REACTION_CHANCE_NORMAL = 0.18
REACTION_CHANCE_KEYWORD = 0.55
REACTION_CHANCE_INSULT = 0.75
REACTION_CHANCE_MISTY = 0.70

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
