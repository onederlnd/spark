import re


def sanitize_plain(value, max_length=None):
    """Strip all HTML and return plain text. For titles, usernames, bio, etc"""
    if not value:
        return ""
    value = value.strip()
    value = re.sub(r"<[^>]+>", "", value)
    if max_length:
        value = value[:max_length]
    return value


def sanitize_bbcode(value, max_length=None):
    """Strip all HTML from BBCode input. Store raw BBCode in DB."""
    if not value:
        return ""
    value = value.strip()
    value = re.sub(r"<[^>]+>", "", value)
    if max_length:
        value = value[:max_length]
    return value


def sanitize_username(value):
    """Only allow letters, numbers, and underscores. Max 32 characters"""
    if not value:
        return ""
    value = value.strip()
    value = re.sub(r"[^\w]", "", value)
    return value[:32]
