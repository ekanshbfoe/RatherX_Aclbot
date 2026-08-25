import asyncio
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
from database.questions import get_question_by_id
from services.game_session import get_session, remove_session, create_session
from utils.formatting import format_waiting_text, format_results_text, get_voting_keyboard, get_next_question_keyboard

router = Router()

async def finish_game(game_id: str, bot, inline_message_id=None, chat_id=None, message_id=None):
    session = get_session(game_id)
    if not session or session.is_finished:
        return
        
    session.is_finished = True
    question = get_question_by_id(session.question_id)
    text = format_results_text(question, session)
    keyboard = get_next_question_keyboard(session.is_nsfw)
    
    try:
        if inline_message_id:
            await bot.edit_message_text(
                text=text,
                inline_message_id=inline_message_id,
                reply_markup=keyboard
            )
        elif chat_id and message_id:
            await bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=message_id,
                reply_markup=keyboard
            )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            print(f"Error editing message in finish_game: {e}")
    except Exception as e:
        print(f"Error editing message in finish_game: {e}")
    finally:
        remove_session(game_id)

@router.callback_query(F.data.startswith("vote_a_") | F.data.startswith("vote_b_"))
async def handle_vote(callback_query: CallbackQuery):
    data_parts = callback_query.data.split("_")
    vote_type = data_parts[1] # 'a' or 'b'
    
    if data_parts[2] == "temp":
        # This is the first vote from an inline mode message!
        # callback data: vote_a_temp_questionId
        question_id = "_".join(data_parts[3:]) # sfw_1, nsfw_2 etc.
        inline_msg_id = callback_query.inline_message_id
        game_id = f"inline_{inline_msg_id}"
        
        # Check if already created (race condition)
        session = get_session(game_id)
        if not session:
            question = get_question_by_id(question_id)
            session = create_session(game_id, question_id, question.is_nsfw)
    else:
        # Normal vote
        game_id = "_".join(data_parts[2:]) # might contain underscores if it's inline_msgid or chat_msgid
        session = get_session(game_id)
        
    if not session:
        await callback_query.answer("This game session has expired or not found.", show_alert=True)
        return
        
    if session.is_finished:
        await callback_query.answer("This game is already finished!", show_alert=True)
        return
        
    user_id = callback_query.from_user.id
    name = callback_query.from_user.first_name
    
    if user_id in session.votes_a or user_id in session.votes_b:
        await callback_query.answer("You have already voted!", show_alert=True)
        return
        
    # Record vote
    if vote_type == 'a':
        session.votes_a.add(user_id)
    else:
        session.votes_b.add(user_id)
        
    session.voters_names[user_id] = name
    
    question = get_question_by_id(session.question_id)
    
    # Determine chat type (private, group, or inline)
    chat_type = "group"
    if callback_query.message and callback_query.message.chat.type == "private":
        chat_type = "private"
    elif callback_query.inline_message_id:
        chat_type = "inline" # inline behaves like group (15 sec wait)
        
    # Start timer if it's the first vote
    if not session.timer_task:
        bot_instance = callback_query.bot
        inline_id = callback_query.inline_message_id
        c_id = callback_query.message.chat.id if callback_query.message else None
        m_id = callback_query.message.message_id if callback_query.message else None
        
        if chat_type == "private":
            # Immediate resolution
            await finish_game(game_id, bot_instance, inline_message_id=inline_id, chat_id=c_id, message_id=m_id)
            await callback_query.answer("Voted!")
            return
        else:
            # Group or inline, start 15-second timer
            async def timer_func(b=bot_instance, i_id=inline_id, chat=c_id, msg=m_id):
                await asyncio.sleep(15)
                await finish_game(game_id, b, inline_message_id=i_id, chat_id=chat, message_id=msg)
                
            session.timer_task = asyncio.create_task(timer_func())

    # Edit message to show waiting state
    text = format_waiting_text(question, session, chat_type)
    keyboard = get_voting_keyboard(game_id)
    
    try:
        if callback_query.inline_message_id:
            await callback_query.bot.edit_message_text(
                text=text,
                inline_message_id=callback_query.inline_message_id,
                reply_markup=keyboard
            )
        else:
            await callback_query.message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            print(f"Update edit failed: {e}")
    except TelegramRetryAfter as e:
        print(f"Rate limited: {e}")
    except Exception as e:
        print(f"Update edit failed: {e}")
        
    await callback_query.answer("Voted!")
