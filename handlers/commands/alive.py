import time
import psutil
import asyncio
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database.supabase_client import supabase
from config.settings import OWNER_ID

router = Router()

def get_uptime_string(uptime_seconds: float) -> str:
    days, rem = divmod(int(uptime_seconds), 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    
    parts = []
    if days > 0: parts.append(f"{days}d")
    if hours > 0: parts.append(f"{hours}h")
    if minutes > 0: parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    return " ".join(parts)

@router.message(Command("add_alive"))
async def cmd_add_alive(message: types.Message):
    # Security: Restrict to OWNER_ID only, silently ignore others
    if message.from_user.id != OWNER_ID:
        return
        
    if not message.reply_to_message:
        await message.reply("⚠️ Please reply to a photo or video to set it as the alive media.")
        return
        
    reply = message.reply_to_message
    media_id = None
    media_type = None
    
    if reply.photo:
        media_id = reply.photo[-1].file_id
        media_type = "photo"
    elif reply.video:
        media_id = reply.video.file_id
        media_type = "video"
    else:
        await message.reply("⚠️ The replied message must contain a photo or video.")
        return
        
    if supabase:
        try:
            await asyncio.to_thread(
                lambda: supabase.table("rather_bot_settings").upsert(
                    [
                        {"setting_key": "alive_media_id", "setting_value": media_id},
                        {"setting_key": "alive_media_type", "setting_value": media_type}
                    ]
                ).execute()
            )
            await message.reply(f"✅ Alive media updated successfully! ({media_type})")
        except Exception as e:
            await message.reply(f"⚠️ Error saving to database: {e}")
    else:
        await message.reply("⚠️ Database connection not configured.")

@router.message(Command("alive", prefix="/."))
async def cmd_alive(message: types.Message):
    # Security: Restrict to OWNER_ID only, silently ignore others
    if message.from_user.id != OWNER_ID:
        return
        
    # Calculate Ping (measure how long it takes to process from message creation time)
    ping_ms = int((time.time() - message.date.timestamp()) * 1000)
    
    # Get Uptime
    import main
    uptime_seconds = time.time() - main.BOOT_TIME
    uptime_string = get_uptime_string(uptime_seconds)
    
    # System Metrics (Non-blocking CPU reading)
    cpu = await asyncio.to_thread(psutil.cpu_percent, 0.1)
    ram = psutil.virtual_memory().percent
    
    # Database Metrics & Settings
    users = 0
    channels = 0
    media_id = None
    media_type = None
    
    if supabase:
        try:
            # Run concurrently for maximum speed
            async def get_count(table_name, select_col):
                res = await asyncio.to_thread(
                    lambda: supabase.table(table_name).select(select_col, count="exact").limit(1).execute()
                )
                return res.count if res.count is not None else 0
                
            async def get_settings():
                res = await asyncio.to_thread(
                    lambda: supabase.table("rather_bot_settings").select("*").in_("setting_key", ["alive_media_id", "alive_media_type"]).execute()
                )
                settings = {row["setting_key"]: row["setting_value"] for row in res.data}
                return settings.get("alive_media_id"), settings.get("alive_media_type")
                
            users, channels, settings = await asyncio.gather(
                get_count("rather_users", "user_id"),
                get_count("rather_chat_mappings", "chat_id"),
                get_settings()
            )
            media_id, media_type = settings
        except Exception as e:
            import logging
            logging.error(f"Error fetching stats for /alive: {e}")
            
    text = f"""<b>『  RatherX 🎴 Is Online 👑 』</b>

<b>🚀 Network Reach:</b>
• Total Users: {users}
• Total Channels: {channels}

<b>⚙️ System Status:</b>
• CPU Usage: {cpu}%
• Memory Usage: {ram}%
• Ping: {ping_ms} ms
• Uptime: {uptime_string}

<i>System fully operational and ready for delivery.</i>"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👑 Owner", url="https://t.me/OceanHave")]
    ])

    # Send as reply to the user's .alive / /alive command
    if media_id and media_type == "photo":
        await message.answer_photo(photo=media_id, caption=text, reply_markup=keyboard, parse_mode="HTML", reply_to_message_id=message.message_id)
    elif media_id and media_type == "video":
        await message.answer_video(video=media_id, caption=text, reply_markup=keyboard, parse_mode="HTML", reply_to_message_id=message.message_id)
    else:
        await message.reply(text, reply_markup=keyboard, parse_mode="HTML")
