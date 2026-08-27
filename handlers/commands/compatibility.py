from aiogram import Router, types
from aiogram.filters import Command
from services.game_session import get_chat_instance, get_local_history_dict, calculate_specific_compatibility
from utils.formatting import format_compatibility

router = Router()

@router.message(Command("compatibility"))
async def cmd_compatibility(message: types.Message):
    processing_msg = await message.answer("<i>⏳ Accessing matchmaking database...</i>", parse_mode="HTML")
    
    if message.chat.type == "private":
        await processing_msg.edit_text("⚠️ This command is for group chats!")
        return
        
    chat_id = message.chat.id
    chat_instance = await get_chat_instance(chat_id)
    
    if not chat_instance:
        await processing_msg.edit_text("<i>⚠️ Not enough data! Both players must answer at least 5 common questions in this chat to calculate compatibility.</i>", parse_mode="HTML")
        return
        
    # Extract exactly two @usernames
    parts = message.text.split()
    target_usernames = [p.replace('@', '') for p in parts if p.startswith('@')]
    
    if len(target_usernames) != 2:
        await processing_msg.edit_text("⚠️ Please tag exactly two users. Usage: `/compatibility @user1 @user2`", parse_mode="Markdown")
        return
        
    target1, target2 = target_usernames
    
    # Search local history for user_ids matching the usernames
    users_dict = await get_local_history_dict(chat_instance)
    if not users_dict:
        await processing_msg.edit_text("<i>⚠️ Not enough data! Both players must answer at least 5 common questions in this chat to calculate compatibility.</i>", parse_mode="HTML")
        return
        
    uid1 = None
    uid2 = None
    
    for uid, data in users_dict.items():
        if data.get("username") == target1:
            uid1 = uid
        elif data.get("username") == target2:
            uid2 = uid
            
    if not uid1 or not uid2:
        await processing_msg.edit_text("<i>⚠️ Not enough data! Both players must answer at least 5 common questions in this chat to calculate compatibility.</i>", parse_mode="HTML")
        return
        
    result = calculate_specific_compatibility(users_dict, uid1, uid2)
    if not result:
        await processing_msg.edit_text("<i>⚠️ Not enough data! Both players must answer at least 5 common questions in this chat to calculate compatibility.</i>", parse_mode="HTML")
        return
        
    text = format_compatibility(result)
    await processing_msg.edit_text(text, parse_mode="HTML")
