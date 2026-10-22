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

def category_label(key: str) -> str:
    """Returns the display label (emoji + name) for a category key."""
    return _LABELS.get(key, key.replace("_", " ").title())
