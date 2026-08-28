import asyncio
import time
from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.questions import get_question_by_id
from services.game_session import get_session, remove_session, create_session, record_user_vote, map_chat_instance, track_task
from utils.formatting import format_question_text, safe_edit_message_text

router = Router()

async def resolve_game(game_id: str, message: types.Message | None, inline_message_id: str | None, bot):
    """Resolves the game, shows final stats, and cleans up the session."""
    session = get_session(game_id)
    if not session:
        return
        
    async with session.lock:
        if session.is_finished:
            return
        session.is_finished = True
        
    question = get_question_by_id(session.question_id)
    if not question:
        remove_session(game_id)
        return

    # Calculate final stats
    real_votes_a = len(session.votes_a)
    real_votes_b = len(session.votes_b)
    
    # Merge with global stats
    total_a = question.global_votes_blue + real_votes_a
    total_b = question.global_votes_red + real_votes_b
    
    # Build player lists by choice
    players_a = [session.voters_names[uid] for uid in session.votes_a if uid in session.voters_names]
    players_b = [session.voters_names[uid] for uid in session.votes_b if uid in session.voters_names]
    
    text = format_question_text(
        question.option_blue,
        question.option_red,
        total_a,
        total_b,
        show_stats=True,
        players_a=players_a,
        players_b=players_b,
        is_nsfw=session.is_nsfw
    )

    # Add inline "Next Question" button for all games
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Next Question", switch_inline_query_current_chat="")
        
    reply_markup = builder.as_markup()
        
    if message:
        await safe_edit_message_text(message, text, reply_markup)
    elif inline_message_id:
        try:
            await bot.edit_message_text(inline_message_id=inline_message_id, text=text, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            pass
            
    # Cleanup memory
    remove_session(game_id)

async def game_timer(game_id: str, message: types.Message | None, inline_message_id: str | None, bot):
    """Waits 15 seconds then resolves the game."""
    await asyncio.sleep(15)
    await resolve_game(game_id, message, inline_message_id, bot)

@router.callback_query(lambda c: c.data and c.data.startswith('vote:'))
async def process_vote(callback_query: types.CallbackQuery):
    data_parts = callback_query.data.split(':')
    # vote:<category>:<question_id>:<color>
    category = data_parts[1]
    question_id = data_parts[2]
    vote_choice = data_parts[3]
    
    # Determine unified game_id
    is_inline = callback_query.inline_message_id is not None
    if is_inline:
        game_id = callback_query.inline_message_id
    else:
        game_id = f"{callback_query.message.chat.id}:{callback_query.message.message_id}"
        
    session = get_session(game_id)
    if not session:
        # Initialize session on the fly for inline queries or restarted bot cache misses
        is_nsfw = (category == "nsfw")
        session = create_session(game_id, question_id, is_nsfw=is_nsfw)
        
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name
    
    async with session.lock:
        if session.is_finished:
            await callback_query.answer("Game has ended!", show_alert=True)
            return
            
        if user_id in session.votes_a or user_id in session.votes_b:
            await callback_query.answer("You already voted!", show_alert=True)
            return
            
        # Register vote
        if vote_choice == 'a':
            session.votes_a.add(user_id)
        else:
            session.votes_b.add(user_id)
            
        session.voters_names[user_id] = first_name
        
        # Record vote for Global (and Local if applicable) Leaderboard
        username = callback_query.from_user.username
        track_task(record_user_vote(user_id, first_name, question_id, vote_choice, chat_instance=callback_query.chat_instance, username=username))
        
        # Map chat_id to chat_instance for local commands (/mylove, /compatibility)
        if not is_inline and callback_query.message.chat.type in ["group", "supergroup"]:
            track_task(map_chat_instance(callback_query.message.chat.id, callback_query.chat_instance))
        
        # Check chat type to determine execution flow
        is_private = not is_inline and callback_query.message.chat.type == "private"
        
        # ── SINGLE ATOMIC SECTION: Check + spawn timer + throttle UI ──
        num_voters = len(session.votes_a) + len(session.votes_b)
        is_first_vote = (num_voters == 1)
        spawned_timer = False

        if num_voters >= 2 and session.timer_task is None:
            session.timer_task = asyncio.create_task(
                game_timer(game_id, callback_query.message if not is_inline else None,
                           callback_query.inline_message_id, callback_query.bot)
            )
            spawned_timer = True

        now = time.time()
        should_update_ui = is_first_vote or spawned_timer or (now - session.last_ui_update_time > 1.5)
        if should_update_ui:
            session.last_ui_update_time = now

    # ── Outside lock: do the I/O work ──
    if is_private:
        await callback_query.answer("Vote registered!")
        await resolve_game(game_id, callback_query.message, None, callback_query.bot)
        return
        
    await callback_query.answer("Vote registered!")
    
    if should_update_ui:
        question = get_question_by_id(question_id)
        if not question:
            return
            
        players_list = ", ".join(session.voters_names.values())
        current_voters = len(session.votes_a) + len(session.votes_b)
        
        if current_voters == 1:
            waiting_text = f"Waiting for players to answer...\n\n{players_list} already answered!"
        else:
            waiting_text = f"Waiting 15 sec for players to answer...\n\n{players_list} already answered!"
        
        text = format_question_text(
            question.option_blue,
            question.option_red,
            waiting_text=waiting_text,
            is_nsfw=session.is_nsfw
        )
        
        builder = InlineKeyboardBuilder()
        builder.button(text="🔵", callback_data=f"vote:{category}:{question.id}:a")
        builder.button(text="🔴", callback_data=f"vote:{category}:{question.id}:b")
        builder.adjust(2)
        
        if not is_inline:
            await safe_edit_message_text(callback_query.message, text, builder.as_markup())
        else:
            try:
                await callback_query.bot.edit_message_text(
                    inline_message_id=callback_query.inline_message_id, 
                    text=text, 
                    reply_markup=builder.as_markup(), 
                    parse_mode="HTML"
                )
            except Exception:
                pass
