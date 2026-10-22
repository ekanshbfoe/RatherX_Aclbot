# Ordered list of question categories: (key, emoji, label)
# The key matches the data file name: data/questions_<key>.json
CATEGORIES = [
    ("daily", "🤔", "Daily"),
    ("money", "💰", "Money"),
    ("celebrity", "🎬", "Celebrity"),
    ("gross", "🤢", "Gross"),
    ("survival", "🏕", "Survival"),
    ("school", "🎓", "School"),
    ("social", "💬", "Social"),
    ("deal_with_the_devil", "😈", "Deal with the Devil"),
    ("food", "🍕", "Food"),
    ("sports", "🏆", "Sports"),
    ("normal", "📅", "Normal"),
    ("extreme", "🔥", "Extreme"),
    ("fantasy", "🔮", "Fantasy"),
    ("hard", "🌀", "Hard"),
    ("love_life", "💖", "Love Life"),
    ("time_travel", "⏳", "Time Travel"),
    ("nsfw", "🌶", "NSFW"),
]

NSFW_CATEGORY = "nsfw"

_LABELS = {key: f"{emoji} {label}" for key, emoji, label in CATEGORIES}

# Twemoji PNGs on jsDelivr, used as inline result icons (Telegram needs an image URL, not an emoji)
_TWEMOJI_BASE = "https://cdn.jsdelivr.net/gh/jdecked/twemoji@15.1.0/assets/72x72"

def emoji_icon_url(emoji: str) -> str:
    """Returns the Twemoji image URL for an emoji, e.g. 💰 -> .../1f4b0.png"""
    codepoints = "-".join(f"{ord(char):x}" for char in emoji if char != "\ufe0f")
    return f"{_TWEMOJI_BASE}/{codepoints}.png"

def category_label(key: str) -> str:
    """Returns the display label (emoji + name) for a category key."""
    return _LABELS.get(key, key.replace("_", " ").title())
