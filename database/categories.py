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

# Microsoft Fluent 3D emoji PNGs on jsDelivr, used as inline result icons
# (Telegram needs an image URL, not an emoji). Pinned to a commit so the images never change.
_FLUENT_BASE = "https://cdn.jsdelivr.net/gh/microsoft/fluentui-emoji@1ffb34c752ecf5d402f04cfb4b392c77f57c54bc/assets"
_FLUENT_NAMES = {
    "🎲": "Game die", "🤔": "Thinking face", "💰": "Money bag", "🎬": "Clapper board",
    "🤢": "Nauseated face", "🏕": "Camping", "🎓": "Graduation cap", "💬": "Speech balloon",
    "😈": "Smiling face with horns", "🍕": "Pizza", "🏆": "Trophy", "📅": "Calendar",
    "🔥": "Fire", "🔮": "Crystal ball", "🌀": "Cyclone", "💖": "Sparkling heart",
    "⏳": "Hourglass not done", "🌶": "Hot pepper",
}

def emoji_icon_url(emoji: str) -> str:
    """Returns the Fluent 3D image URL for an emoji, e.g. 💰 -> .../Money%20bag/3D/money_bag_3d.png"""
    name = _FLUENT_NAMES[emoji]
    file_name = name.lower().replace(" ", "_")
    return f"{_FLUENT_BASE}/{name.replace(' ', '%20')}/3D/{file_name}_3d.png"

def category_label(key: str) -> str:
    """Returns the display label (emoji + name) for a category key."""
    return _LABELS.get(key, key.replace("_", " ").title())
