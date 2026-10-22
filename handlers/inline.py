from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from database.categories import CATEGORIES, NSFW_CATEGORY, emoji_icon_url
from services.category_history import get_recent_categories, record_category_use
from utils.formatting import format_question_text

router = Router()

def build_article(article_id: str, mode: str, title: str, icon_emoji: str):
    """Builds one inline result holding a random question for the given mode ("sfw" = random SFW)."""
    if mode == "sfw":
        question = get_random_question(nsfw=False)
    else:
        question = get_random_question(category=mode)
    if not question:
        return None

    builder = InlineKeyboardBuilder()
    builder.button(text="🔵", callback_data=f"vote:{mode}:{question.id}:a")
    builder.button(text="🔴", callback_data=f"vote:{mode}:{question.id}:b")
    builder.adjust(2)

    text = format_question_text(
        question.option_blue,
        question.option_red,
        is_nsfw=(mode == NSFW_CATEGORY),
        category=question.category
    )

    return InlineQueryResultArticle(
        id=article_id,
        title=title,
        description=question.question, # Preview of the exact question that will be sent
        thumbnail_url=emoji_icon_url(icon_emoji),
        thumbnail_width=72,
        thumbnail_height=72,
        input_message_content=InputTextMessageContent(
            message_text=text,
            parse_mode="HTML"
        ),
        reply_markup=builder.as_markup()
    )

def match_categories(query: str) -> list:
    """Returns categories whose key or name contains the typed text (e.g. "love" -> Love Life)."""
    query = query.strip().lower()
    if not query:
        return []
    query_key = query.replace(" ", "_")
    return [
        (key, emoji, label) for key, emoji, label in CATEGORIES
        if query_key in key or query in label.lower()
    ]

@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    matches = match_categories(inline_query.query)

    candidates = []
    recent = []
    if not matches:
        # Empty or unmatched query: the user's recent categories, a random pick, then every other category
        recent_keys = await get_recent_categories(inline_query.from_user.id)
        by_key = {key: (key, emoji, label) for key, emoji, label in CATEGORIES}
        recent = [by_key[key] for key in recent_keys if key in by_key]
        for key, emoji, label in recent:
            candidates.append(build_article(f"cat_{key}", key, f"🕘 {emoji} {label}", emoji))
        candidates.append(build_article("article_sfw", "sfw", "🎲 Random Question", "🎲"))
        matches = [category for category in CATEGORIES if category not in recent]

    # One article per category, e.g. "@RatherX_Aclbot money" shows only Money
    for key, emoji, label in matches:
        title = f"{emoji} {label} (18+)" if key == NSFW_CATEGORY else f"{emoji} {label}"
        candidates.append(build_article(f"cat_{key}", key, title, emoji))
    results = [article for article in candidates if article]

    # cache_time=0 and is_personal=True ensures they get fresh random questions every time they query
    await inline_query.answer(
        results,
        cache_time=0,
        is_personal=True,
        button=InlineQueryResultsButton(text="Would You Rather え", start_parameter="inline_promo")
    )

@router.chosen_inline_result()
async def chosen_inline_result_handler(chosen: types.ChosenInlineResult):
    # Needs inline feedback turned on in @BotFather (/setinlinefeedback)
    if chosen.result_id.startswith("cat_"):
        await record_category_use(chosen.from_user.id, chosen.result_id[len("cat_"):])
