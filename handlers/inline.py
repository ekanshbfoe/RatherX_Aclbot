import uuid
from aiogram import Router
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton
from database.questions import SFW_QUESTIONS, NSFW_QUESTIONS

router = Router()

@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    results = []
    
    questions_to_show = SFW_QUESTIONS[:3] + NSFW_QUESTIONS[:3]
    
    for q in questions_to_show:
        prefix = "[18+] " if q.is_nsfw else ""
        title = f"{prefix}Would you rather..."
        description = f"{q.option_a} OR {q.option_b}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔵", callback_data=f"vote_a_temp_{q.id}"),
                InlineKeyboardButton(text="🔴", callback_data=f"vote_b_temp_{q.id}")
            ]
        ])
        
        result_id = str(uuid.uuid4())
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=title,
                description=description,
                input_message_content=InputTextMessageContent(
                    message_text=f"{prefix}Would you rather...\n\n🔵 {q.option_a}\n🔴 {q.option_b}\n\nSelect your answer:"
                ),
                reply_markup=keyboard
            )
        )
        
    await query.answer(results, cache_time=1)
