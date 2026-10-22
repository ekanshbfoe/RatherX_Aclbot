from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from database.categories import CATEGORIES, NSFW_CATEGORY
from utils.formatting import format_question_text

router = Router()

def build_article(article_id: str, mode: str, title: str, description: str):
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
        description=description,
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

    if matches:
        # One article per matching category, e.g. "@RatherGameBot money"
        candidates = [
            build_article(f"cat_{key}", key, f"{emoji} {label}", f"Play a {label} question")
            for key, emoji, label in matches
        ]
    else:
        # Default: random SFW question and 18+ question
        candidates = [
            build_article("article_sfw", "sfw", "Get Question", "Play a standard Would You Rather question"),
            build_article("article_nsfw", NSFW_CATEGORY, "Get Question (18+)", "Play an NSFW 18+ question"),
        ]
    results = [article for article in candidates if article]

    # cache_time=0 and is_personal=True ensures they get fresh random questions every time they query
    await inline_query.answer(
        results,
        cache_time=0,
        is_personal=True,
        button=InlineQueryResultsButton(text="Would You Rather え", start_parameter="inline_promo")
    )
