import uuid
import random
from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import SFW_QUESTIONS
from services.game_session import create_session
from utils.formatting import format_question_text

router = Router()

@router.inline_query()
async def inline_query_handler(inline_query: types.InlineQuery):
    if not SFW_QUESTIONS:
        return
        
    # Get 5 random SFW questions for the inline menu
    sampled = random.sample(SFW_QUESTIONS, min(5, len(SFW_QUESTIONS)))
    results = []
    
    for q in sampled:
        builder = InlineKeyboardBuilder()
        builder.button(text="🔵 Option 1", callback_data=f"vote_a_{q.id}")
        builder.button(text="🔴 Option 2", callback_data=f"vote_b_{q.id}")
        builder.adjust(2)
        
        text = format_question_text(
            q.option_blue, 
            q.option_red
        )
        
        results.append(
            InlineQueryResultArticle(
                id=q.id,
                title=f"Would You Rather: {q.option_blue} OR {q.option_red}",
                description="Challenge a friend!",
                input_message_content=InputTextMessageContent(
                    message_text=text,
                    parse_mode="HTML"
                ),
                reply_markup=builder.as_markup()
            )
        )
        
    # Cache time is short so they get new random questions often
    await inline_query.answer(results, cache_time=5, is_personal=True)

@router.chosen_inline_result()
async def chosen_inline_result_handler(chosen_result: types.ChosenInlineResult):
    # The result_id is the question ID, which we set in InlineQueryResultArticle
    question_id = chosen_result.result_id
    inline_message_id = chosen_result.inline_message_id
    
    if inline_message_id:
        game_id = f"inline_{inline_message_id}"
        is_nsfw = question_id.startswith("nsfw")
        create_session(game_id, question_id, is_nsfw=is_nsfw)
