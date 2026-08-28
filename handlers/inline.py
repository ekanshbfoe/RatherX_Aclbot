from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQueryResultsButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_random_question
from utils.formatting import format_question_text

router = Router()

@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    results = []
    
    # 1. SFW Question Article
    sfw_q = get_random_question(nsfw=False)
    if sfw_q:
        builder_sfw = InlineKeyboardBuilder()
        builder_sfw.button(text="🔵", callback_data=f"vote:sfw:{sfw_q.id}:a")
        builder_sfw.button(text="🔴", callback_data=f"vote:sfw:{sfw_q.id}:b")
        builder_sfw.adjust(2)
        
        text_sfw = format_question_text(sfw_q.option_blue, sfw_q.option_red)
        
        results.append(
            InlineQueryResultArticle(
                id="article_sfw",
                title="Get Question",
                description="Play a standard Would You Rather question",
                input_message_content=InputTextMessageContent(
                    message_text=text_sfw,
                    parse_mode="HTML"
                ),
                reply_markup=builder_sfw.as_markup()
            )
        )
        
    # 2. NSFW Question Article
    nsfw_q = get_random_question(nsfw=True)
    if nsfw_q:
        builder_nsfw = InlineKeyboardBuilder()
        builder_nsfw.button(text="🔵", callback_data=f"vote:nsfw:{nsfw_q.id}:a")
        builder_nsfw.button(text="🔴", callback_data=f"vote:nsfw:{nsfw_q.id}:b")
        builder_nsfw.adjust(2)
        
        text_nsfw = format_question_text(nsfw_q.option_blue, nsfw_q.option_red, is_nsfw=True)
        
        results.append(
            InlineQueryResultArticle(
                id="article_nsfw",
                title="Get Question (18+)",
                description="Play an NSFW 18+ question",
                input_message_content=InputTextMessageContent(
                    message_text=text_nsfw,
                    parse_mode="HTML"
                ),
                reply_markup=builder_nsfw.as_markup()
            )
        )
        
    # cache_time=0 and is_personal=True ensures they get fresh random questions every time they query
    await inline_query.answer(
        results, 
        cache_time=0, 
        is_personal=True,
        button=InlineQueryResultsButton(text="Would You Rather え", start_parameter="inline_promo")
    )
