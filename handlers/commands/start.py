import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import OWNER_ID, NOTIFICATION_LOG_GROUP, NOTIFICATION_LOG_TOPIC_ID
from database.supabase_client import supabase
from services.game_session import track_task
from cachetools import TTLCache

router = Router()

_known_users_cache = TTLCache(maxsize=8192, ttl=3600)

async def process_new_user(user: types.User, bot: Bot):
    if not supabase: return
    
    if user.id in _known_users_cache:
        return
        
    try:
        # Check if user exists
        res = await asyncio.to_thread(
            lambda: supabase.table("rather_users").select("user_id").eq("user_id", user.id).execute()
        )
        
        if not res.data:
            # User does not exist, send notification
            await bot.send_message(
                chat_id=NOTIFICATION_LOG_GROUP, 
                message_thread_id=NOTIFICATION_LOG_TOPIC_ID,
                text=f"👤 <b>New User Started Bot!</b>\nName: {user.first_name}\nID: <code>{user.id}</code>\nUsername: @{user.username}",
                parse_mode="HTML"
            )
            
            # Insert them into the DB so it doesn't trigger again
            await asyncio.to_thread(
                lambda: supabase.table("rather_users").upsert(
                    {"user_id": user.id, "first_name": user.first_name, "username": user.username},
                    on_conflict="user_id"
                ).execute()
            )
            
        _known_users_cache[user.id] = True
    except Exception:
        pass

@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    
    # 1. Immediate User Response
    if len(args) > 1 and args[1] == "love":
        await message.reply("💖 Successfully connected to your DMs! You can now use the /mylove command in group chats to receive your secret stats.")
    else:
        await message.reply(
            "<b>Welcome to Would You Rather Bot!</b>\n\n"
            "<b>🕹 How to play single player?</b>\n"
            "Use the following commands:\n"
            "<code>/next</code> - get a new Would You Rather question\n"
            "<code>/nsfw</code> - get a new NSFW (18+) question\n\n"
            "<b>👨‍👩‍👧‍👦 How to play in a group?</b>\n"
            "Add @RatherGameBot to your group and then use these commands:\n"
            "<code>/next@RatherGameBot</code> - get a new Would You Rather question\n"
            "<code>/nsfw@RatherGameBot</code> - get a new NSFW (18+) question\n\n"
            "<b>👫 How to play inline?</b>\n"
            "Type @RatherGameBot in a chat and select a question to play against a friend.\n\n"
            "<b>❓ Feedback or suggestions?</b>\n"
            "Please let us know with <code>/feedback</code>!\n\n"
            "To view this info again, use <code>/help</code>.",
            parse_mode="HTML"
        )

    # 2. Detached Background Task for Database Check
    if message.chat.type == "private":
        track_task(process_new_user(message.from_user, bot))
