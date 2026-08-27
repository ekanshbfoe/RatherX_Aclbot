import logging
from aiogram import Router, types, Bot
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, IS_NOT_MEMBER, MEMBER, ADMINISTRATOR
from config.settings import OWNER_ID, NOTIFICATION_LOG_GROUP, NOTIFICATION_LOG_TOPIC_ID

router = Router()
log = logging.getLogger(__name__)

@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=IS_NOT_MEMBER >> (MEMBER | ADMINISTRATOR)))
async def bot_added_to_group(event: types.ChatMemberUpdated, bot: Bot):
    chat = event.chat
    user = event.from_user
    
    try:
        member_count = await bot.get_chat_member_count(chat.id)
    except Exception:
        member_count = "Unknown"
        
    text = (
        f"🎉 <b>Bot Added to Group!</b>\n\n"
        f"📌 <b>Title:</b> {chat.title}\n"
        f"🆔 <b>Chat ID:</b> <code>{chat.id}</code>\n"
        f"👥 <b>Members:</b> {member_count}\n"
        f"👤 <b>Added By:</b> {user.first_name} (<code>{user.id}</code>)\n"
        f"@{user.username}" if user.username else ""
    )
    
    try:
        await bot.send_message(
            chat_id=NOTIFICATION_LOG_GROUP, 
            message_thread_id=NOTIFICATION_LOG_TOPIC_ID,
            text=text, 
            parse_mode="HTML"
        )
    except Exception as e:
        log.error(f"Failed to send bot_added notification to owner: {e}")
