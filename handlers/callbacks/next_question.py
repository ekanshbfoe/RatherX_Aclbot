from aiogram import Router, F
from aiogram.types import CallbackQuery
from database.questions import get_random_question
from services.game_session import create_session
from utils.formatting import format_question_text, get_voting_keyboard

router = Router()

@router.callback_query(F.data.startswith("next_q_"))
async def handle_next_question(callback_query: CallbackQuery):
    is_nsfw = bool(int(callback_query.data.split("_")[2]))
    question = get_random_question(nsfw=is_nsfw)
    
    if callback_query.inline_message_id:
        # For inline mode, we edit the same message with a new question
        game_id = f"inline_{callback_query.inline_message_id}"
        create_session(game_id, question.id, is_nsfw=is_nsfw)
        text = format_question_text(question)
        keyboard = get_voting_keyboard(game_id)
        
        await callback_query.bot.edit_message_text(
            text=text,
            inline_message_id=callback_query.inline_message_id,
            reply_markup=keyboard
        )
    else:
        # For regular chat, we remove the keyboard from the old message
        await callback_query.message.edit_reply_markup(reply_markup=None)
        
        # And send a new message
        temp_msg = await callback_query.message.answer("Loading...")
        
        chat_id = temp_msg.chat.id
        msg_id = temp_msg.message_id
        game_id = f"{chat_id}_{msg_id}"
        
        create_session(game_id, question.id, is_nsfw=is_nsfw)
        
        text = format_question_text(question)
        keyboard = get_voting_keyboard(game_id)
        
        await temp_msg.edit_text(text, reply_markup=keyboard)
        
    await callback_query.answer()
