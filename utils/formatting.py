import html
from aiogram.exceptions import TelegramBadRequest
import logging

log = logging.getLogger(__name__)

def create_progress_bar(percentage: float, length: int = 10) -> str:
    """Creates a simple block progress bar."""
    filled_blocks = int(round((percentage / 100) * length))
    empty_blocks = length - filled_blocks
    return "█" * filled_blocks + "░" * empty_blocks

def format_question_text(option_a: str, option_b: str, 
                         votes_a: int = 0, votes_b: int = 0, 
                         show_stats: bool = False, 
                         players_a: list = None, players_b: list = None, 
                         waiting_text: str = "",
                         is_nsfw: bool = False) -> str:
    """Formats the question message text."""
    # Ensure lists are instantiated
    if players_a is None: players_a = []
    if players_b is None: players_b = []
    
    option_a = html.escape(option_a)
    option_b = html.escape(option_b)
    
    text = "<b>[18+] Would you rather...</b>\n\n" if is_nsfw else "<b>Would you rather...</b>\n\n"
    
    if show_stats:
        total_votes = votes_a + votes_b
        pct_a = (votes_a / total_votes * 100) if total_votes > 0 else 0
        pct_b = (votes_b / total_votes * 100) if total_votes > 0 else 0
        
        text += f"<b>({int(round(pct_a))}%)</b> 🔵 {option_a}\n"
        text += f"<b>({int(round(pct_b))}%)</b> 🔴 {option_b}\n\n"
        
        if players_a:
            text += f"🔵 {', '.join([html.escape(p) for p in players_a])}\n"
        if players_b:
            text += f"🔴 {', '.join([html.escape(p) for p in players_b])}\n"
    else:
        text += f"🔵 {option_a}\n"
        text += f"🔴 {option_b}\n\n"
        
    if waiting_text:
        text += f"<i>{waiting_text}</i>"
    elif not show_stats:
        text += "Select your answer:"
        
    return text

async def safe_edit_message_text(message, text: str, reply_markup=None):
    """Edits message text and gracefully ignores MessageNotModified errors."""
    try:
        if reply_markup is not None:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
        else:
            await message.edit_text(text, parse_mode="HTML")
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass # Ignore benign error
        else:
            log.error(f"Error editing message: {e}")
            raise e
