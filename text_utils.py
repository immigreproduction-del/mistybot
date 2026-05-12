import re
import unicodedata


def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def normalize_token(token):
    token = normalize_text(token)

    if len(token) > 3 and token.endswith("s"):
        token = token[:-1]

    return token


def normalized_tokens(text):
    return [
        normalize_token(token)
        for token in normalize_text(text).split()
        if token
    ]


def contains_loose_word(content, word):
    content_tokens = normalized_tokens(content)
    word_tokens = normalized_tokens(word)

    if not word_tokens:
        return False

    if len(word_tokens) == 1:
        return word_tokens[0] in content_tokens

    for index in range(len(content_tokens) - len(word_tokens) + 1):
        if content_tokens[index:index + len(word_tokens)] == word_tokens:
            return True

    return False


def contains_loose_any(content, words):
    return any(contains_loose_word(content, word) for word in words)
