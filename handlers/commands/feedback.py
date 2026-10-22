import html
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config.settings import FEEDBACK_GROUP_ID, FEEDBACK_TOPIC_ID, OWNER_ID

router = Router()

class FeedbackStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_content = State()

@router.message(Command("feedback", prefix="/."))
async def cmd_feedback(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.button(text="🐞 Report Bug", callback_data="feedback:bug")
    builder.button(text="💡 Request Feature", callback_data="feedback:feature")
    builder.button(text="❌ Cancel", callback_data="feedback:cancel")
    builder.adjust(2, 1)
    
    await message.reply("What would you like to submit?", reply_markup=builder.as_markup())
    await state.set_state(FeedbackStates.waiting_for_category)

@router.callback_query(FeedbackStates.waiting_for_category, lambda c: c.data and c.data.startswith("feedback:"))
async def process_feedback_category(callback_query: types.CallbackQuery, state: FSMContext):
    category = callback_query.data.split(":")[1]
    
    if category == "cancel":
        await callback_query.message.edit_text("Feedback cancelled.")
        await callback_query.answer()
        await state.clear()
        return
        
    await state.update_data(category=category)
    
    builder = InlineKeyboardBuilder()
    builder.button(text="❌ Cancel", callback_data="feedback:cancel")
    
    await callback_query.message.edit_text(
        "Please describe the issue or idea in detail. You can send text, a photo, or a video (with caption).",
        reply_markup=builder.as_markup()
    )
    await state.set_state(FeedbackStates.waiting_for_content)
    await callback_query.answer()

@router.callback_query(FeedbackStates.waiting_for_content, lambda c: c.data == "feedback:cancel")
async def cancel_content_feedback(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text("Feedback cancelled.")
    await callback_query.answer()
    await state.clear()

@router.message(FeedbackStates.waiting_for_content, F.content_type.in_({'text', 'photo', 'video'}))
async def process_feedback_content(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    category = data.get("category", "bug").upper()
    ticket_id = message.message_id  # Use user's message ID as a simple ticket ID
    
    text = (
        f"[{category}] (#{ticket_id})\n"
        f"From: {html.escape(message.from_user.first_name)} (<code>{message.from_user.id}</code>)\n\n"
    )
    
    if message.text:
        text += html.escape(message.text)
    elif message.caption:
        text += html.escape(message.caption)
        
    builder = InlineKeyboardBuilder()
    if category == "BUG":
        builder.button(text="✅ Fix", callback_data="admin_ticket:fix")
        builder.button(text="❌ Ignore", callback_data="admin_ticket:ignore")
        builder.button(text="👤 User Profile", url=f"tg://user?id={message.from_user.id}")
    else:
        builder.button(text="✅ Added", callback_data="admin_ticket:added")
        builder.button(text="👤 Contact User", url=f"tg://user?id={message.from_user.id}")
        
    builder.adjust(2, 1)
    
    try:
        if message.photo:
            await bot.send_photo(
                chat_id=FEEDBACK_GROUP_ID,
                photo=message.photo[-1].file_id,
                caption=text,
                message_thread_id=FEEDBACK_TOPIC_ID,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        elif message.video:
            await bot.send_video(
                chat_id=FEEDBACK_GROUP_ID,
                video=message.video.file_id,
                caption=text,
                message_thread_id=FEEDBACK_TOPIC_ID,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        else:
            await bot.send_message(
                chat_id=FEEDBACK_GROUP_ID,
                text=text,
                message_thread_id=FEEDBACK_TOPIC_ID,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            
        await message.reply("✅ Thank you! Your feedback has been sent to the admin team.")
    except Exception as e:
        await message.reply("⚠️ Failed to send feedback. The admin group might not be configured correctly.")
        
    await state.clear()

@router.message(FeedbackStates.waiting_for_content)
async def feedback_unsupported_content(message: types.Message, state: FSMContext):
    """Catch-all: reject unsupported file types and keep the user in state."""
    await message.reply(
        "⚠️ Unsupported format. Please send only text, a photo, or a video.\n"
        "Send /cancel to exit feedback mode."
    )

@router.message(Command("cancel"))
async def cmd_cancel_feedback(message: types.Message, state: FSMContext):
    current = await state.get_state()
    if current is not None:
        await state.clear()
        await message.reply("✅ Feedback cancelled.")

@router.callback_query(lambda c: c.data and c.data.startswith("admin_ticket:"))
async def process_admin_ticket(callback_query: types.CallbackQuery):
    if callback_query.from_user.id != OWNER_ID:
        await callback_query.answer("Unauthorized.", show_alert=True)
        return
        
    action = callback_query.data.split(":")[1]
    
    if action == "ignore":
        await callback_query.message.delete()
        await callback_query.answer("Ticket ignored & deleted.")
        return
        
    admin_name = html.escape(callback_query.from_user.first_name)
    action_word = "Fixed" if action == "fix" else "Added"
    
    # Rebuild the original text/caption as HTML (keeps its formatting and escapes user text)
    original = callback_query.message.html_text
    if callback_query.message.text:
        new_text = original + f"\n\n✨ {action_word} by {admin_name}"
        await callback_query.message.edit_text(new_text, reply_markup=None, parse_mode="HTML")
    elif callback_query.message.caption:
        new_caption = original + f"\n\n✨ {action_word} by {admin_name}"
        await callback_query.message.edit_caption(caption=new_caption, reply_markup=None, parse_mode="HTML")
        
    await callback_query.answer(f"Ticket marked as {action_word}.")
