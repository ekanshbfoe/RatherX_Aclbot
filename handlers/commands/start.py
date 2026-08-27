import asyncio
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import OWNER_ID, NOTIFICATION_LOG_GROUP, NOTIFICATION_LOG_TOPIC_ID
from database.supabase_client import supabase

router = Router()

# Keep strong references to background tasks to prevent garbage collection
background_tasks = set()

async def background_new_user_check(user: types.User, bot: Bot):
    if not supabase: return
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
            "👋 Welcome to Would You Rather!\n\n"
            "Send /next for a standard question or /nsfw for a spicy one!\n\n"
            "You can also add me to a group and play with friends, or use inline mode "
            "by typing `@YourBotUsername` in any chat!"
        )

    # 2. Detached Background Task for Database Check
    if message.chat.type == "private":
        task = asyncio.create_task(background_new_user_check(message.from_user, bot))
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)
