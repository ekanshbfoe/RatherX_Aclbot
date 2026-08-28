import time
from aiogram import Router, types
from services.game_session import calculate_couples
from utils.formatting import format_interactive_couple_board

router = Router()

_xboard_cooldowns: dict[int, float] = {}
XBOARD_COOLDOWN_SECONDS = 30

@router.callback_query(lambda c: c.data and c.data.startswith('xboard:'))
async def process_xboard(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    now = time.time()
    last = _xboard_cooldowns.get(user_id, 0)
    if now - last < XBOARD_COOLDOWN_SECONDS:
        remaining = int(XBOARD_COOLDOWN_SECONDS - (now - last))
        await callback_query.answer(f"Please wait {remaining}s before refreshing.", show_alert=True)
        return
    _xboard_cooldowns[user_id] = now
    
    await callback_query.message.edit_text("<i>⏳ Crunching compatibility algorithms...</i>", parse_mode="HTML")
    
    scope = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id
    
    if scope == "local":
        if callback_query.message.chat.type == "private":
            await callback_query.message.edit_text("Local scan requires a group chat!")
            await callback_query.answer("Local scan requires a group chat!", show_alert=True)
            return
        identifier = callback_query.chat_instance
    elif scope == "personal":
        identifier = user_id
    else:
        identifier = None
        
    try:
        couples = await calculate_couples(scope, identifier)
        text = format_interactive_couple_board(couples, scope.capitalize())
        await callback_query.message.edit_text(text, parse_mode="HTML")
        await callback_query.answer(f"{scope.capitalize()} scan complete!")
    except Exception:
        await callback_query.message.edit_text("⚠️ Database timeout. Please try again in a moment.", parse_mode="HTML")
        await callback_query.answer("Error accessing database.", show_alert=True)
