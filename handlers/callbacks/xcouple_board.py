from aiogram import Router, types
from services.game_session import calculate_couples
from utils.formatting import format_interactive_couple_board

router = Router()

@router.callback_query(lambda c: c.data and c.data.startswith('xboard:'))
async def process_xboard(callback_query: types.CallbackQuery):
    scope = callback_query.data.split(':')[1]
    user_id = callback_query.from_user.id
    
    if scope == "local":
        if callback_query.message.chat.type == "private":
            await callback_query.answer("Local scan requires a group chat!", show_alert=True)
            return
        identifier = callback_query.chat_instance
    elif scope == "personal":
        identifier = user_id
    else:
        identifier = None
        
    couples = calculate_couples(scope, identifier)
    text = format_interactive_couple_board(couples, scope.capitalize())
    
    try:
        await callback_query.message.edit_text(text, parse_mode="HTML")
        await callback_query.answer(f"{scope.capitalize()} scan complete!")
    except Exception:
        await callback_query.answer("Data is up to date!")
