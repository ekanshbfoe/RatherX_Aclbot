import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from services.game_session import get_chat_instance, get_local_history_dict, calculate_specific_compatibility
from utils.formatting import format_compatibility
from database.supabase_client import supabase

router = Router()

async def resolve_user_id(target: str) -> int | None:
    if target.isdigit():
        return int(target)
    elif target.startswith('@'):
        username = target[1:]
        if not supabase:
            return None
        res = await asyncio.to_thread(
            lambda: supabase.table("rather_users").select("user_id").eq("username", username).execute()
        )
        if res.data:
            return res.data[0]["user_id"]
    return None

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
        
    # Extract arguments (ignoring the command itself)
    parts = message.text.split()
    target_args = [p for p in parts[1:] if p.startswith('@') or p.isdigit()]
    
    if len(target_args) != 2:
        await processing_msg.edit_text("⚠️ Please provide exactly two users (usernames or IDs). Usage: `/compatibility @user1 784548961`", parse_mode="Markdown")
        return
        
    target1, target2 = target_args
    
    # Update Supabase GET request logic to query rather_users
    uid1 = await resolve_user_id(target1)
    uid2 = await resolve_user_id(target2)
    
    if not uid1 or not uid2:
        await processing_msg.edit_text("⚠️ Could not find one or both users in the database. Make sure they have played the game before.")
        return

    # Fetch local history and calculate
    users_dict = await get_local_history_dict(chat_instance)
        
    result = calculate_specific_compatibility(users_dict, uid1, uid2)
    if not result:
        await processing_msg.edit_text("<i>⚠️ Not enough data! Both players must answer at least 5 common questions in this chat to calculate compatibility.</i>", parse_mode="HTML")
        return
        
    text = format_compatibility(result)
    await processing_msg.edit_text(text, parse_mode="HTML")
