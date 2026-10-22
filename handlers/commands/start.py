import asyncio
import html
from aiogram import Router, types, Bot
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import OWNER_ID, NOTIFICATION_LOG_GROUP, NOTIFICATION_LOG_TOPIC_ID
from database.supabase_client import supabase
from database.questions import ALL_QUESTIONS_MAP, QUESTIONS_BY_CATEGORY
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

def build_welcome_text(first_name: str) -> str:
    question_count = len(ALL_QUESTIONS_MAP)
    category_count = len(QUESTIONS_BY_CATEGORY)
    return (
        "<b>『 RatherX 🎴 Would You Rather 』</b>\n\n"
        f"Hey <b>{html.escape(first_name or 'there')}</b> 👋\n"
        "<blockquote>Two choices. No escape. 🔵 or 🔴\n"
        f"<b>{question_count:,}</b> questions • <b>{category_count}</b> categories • real human votes</blockquote>\n\n"
        "<b>🎮 Play</b>\n"
        "<blockquote>/next — a random question\n"
        "/categories — pick from Money, Gross, Love Life &amp; more\n"
        "/nsfw — spicy 18+ questions 🌶</blockquote>\n\n"
        "<b>👥 Groups &amp; Friends</b>\n"
        "<blockquote>Add me to a group: after 2 votes a 15s timer starts, then everyone's picks are revealed.\n"
        "Or type <code>@RatherX_Aclbot</code> in any chat to send a question.</blockquote>\n\n"
        "<b>💞 Matchmaking</b>\n"
        "<blockquote>/xcouple • /mylove • /compatibility\n"
        "Find out who thinks just like you.</blockquote>\n\n"
        "<i>Need help? /help  •  Got ideas? /feedback</i>"
    )

def build_welcome_keyboard() -> types.InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Add to Group", url="https://t.me/RatherX_Aclbot?startgroup=true")
    builder.button(text="🗂 Categories", callback_data="menu:categories")
    builder.button(text="🎲 Play Here", switch_inline_query_current_chat="")
    builder.button(text="👥 Challenge a Friend", switch_inline_query="")
    builder.adjust(1, 2, 1)
    return builder.as_markup()

@router.message(Command("start"))
async def cmd_start(message: types.Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    
    # 1. Immediate User Response
    if len(args) > 1 and args[1] == "love":
        await message.reply("💖 Successfully connected to your DMs! You can now use the /mylove command in group chats to receive your secret stats.")
    else:
        await message.reply(
            build_welcome_text(message.from_user.first_name),
            reply_markup=build_welcome_keyboard(),
            parse_mode="HTML"
        )

    # 2. Detached Background Task for Database Check
    if message.chat.type == "private":
        track_task(process_new_user(message.from_user, bot))
