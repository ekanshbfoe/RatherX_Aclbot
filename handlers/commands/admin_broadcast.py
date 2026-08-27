import asyncio
import logging
from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import OWNER_ID
from database.supabase_client import supabase

router = Router()
log = logging.getLogger(__name__)

# Keep strong references to background tasks to prevent garbage collection
background_tasks = set()

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != OWNER_ID:
        return
        
    if not message.reply_to_message:
        await message.reply("⚠️ You must reply to the message you want to broadcast!")
        return
        
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Users", callback_data=f"broadcast:users:{message.reply_to_message.message_id}")
    builder.button(text="🌍 Groups", callback_data=f"broadcast:groups:{message.reply_to_message.message_id}")
    builder.button(text="🌐 All", callback_data=f"broadcast:all:{message.reply_to_message.message_id}")
    builder.button(text="❌ Cancel", callback_data="broadcast:cancel:0")
    builder.adjust(2, 1, 1)
    
    await message.reply("Select the broadcast target:", reply_markup=builder.as_markup())

@router.callback_query(lambda c: c.data and c.data.startswith('broadcast:'))
async def process_broadcast(callback_query: types.CallbackQuery, bot: Bot):
    if callback_query.from_user.id != OWNER_ID:
        await callback_query.answer("Unauthorized.", show_alert=True)
        return
        
    _, target, msg_id_str = callback_query.data.split(':')
    
    if target == "cancel":
        await callback_query.message.edit_text("Broadcast cancelled.")
        await callback_query.answer()
        return
        
    msg_id = int(msg_id_str)
    
    await callback_query.message.edit_text(f"<i>⏳ Broadcast started for <b>{target}</b>...</i>", parse_mode="HTML")
    await callback_query.answer()
    
    # Detach to background task
    task = asyncio.create_task(
        execute_broadcast(bot, callback_query.message.chat.id, msg_id, target, callback_query.message)
    )
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

async def execute_broadcast(bot: Bot, from_chat_id: int, message_id: int, target: str, status_message: types.Message):
    if not supabase:
        await status_message.edit_text("⚠️ Database offline. Broadcast failed.")
        return
        
    targets = set()
    
    try:
        if target in ["users", "all"]:
            res = await asyncio.to_thread(lambda: supabase.table("rather_users").select("user_id").execute())
            for row in res.data:
                targets.add(row["user_id"])
                
        if target in ["groups", "all"]:
            res = await asyncio.to_thread(lambda: supabase.table("rather_chat_mappings").select("chat_id").execute())
            for row in res.data:
                targets.add(row["chat_id"])
    except Exception as e:
        log.error(f"Broadcast DB fetch error: {e}")
        await status_message.edit_text(f"⚠️ Failed to fetch targets from DB: {e}")
        return
        
    if not targets:
        await status_message.edit_text("⚠️ No targets found in database.")
        return
        
    sent_count = 0
    fail_count = 0
    
    for i, target_id in enumerate(targets):
        try:
            await bot.forward_message(chat_id=target_id, from_chat_id=from_chat_id, message_id=message_id)
            sent_count += 1
        except Exception as e:
            fail_count += 1
            
        await asyncio.sleep(0.05)
        
        if (i + 1) % 25 == 0:
            await asyncio.sleep(1.5)
            
    await status_message.edit_text(
        f"✅ <b>Broadcast Complete</b>\n\n"
        f"🎯 <b>Target:</b> {target.capitalize()}\n"
        f"📨 <b>Sent:</b> {sent_count}\n"
        f"❌ <b>Failed:</b> {fail_count}",
        parse_mode="HTML"
    )
