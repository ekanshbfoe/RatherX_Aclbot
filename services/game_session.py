import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Set, Dict, Optional

log = logging.getLogger(__name__)

@dataclass
class GameSession:
    question_id: str
    is_nsfw: bool
    created_at: float = field(default_factory=time.time)
    votes_a: Set[int] = field(default_factory=set) # User IDs for option blue
    votes_b: Set[int] = field(default_factory=set) # User IDs for option red
    voters_names: Dict[int, str] = field(default_factory=dict) # User ID -> first name
    timer_task: Optional[asyncio.Task] = None
    is_finished: bool = False
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_ui_update_time: float = 0.0

# In-memory storage for active games
# Key: f"{chat_id}_{message_id}" for groups/private or f"inline_{inline_message_id}" for inline mode
active_games: Dict[str, GameSession] = {}

def get_session(game_id: str) -> Optional[GameSession]:
    return active_games.get(game_id)

def create_session(game_id: str, question_id: str, is_nsfw: bool) -> GameSession:
    session = GameSession(question_id=question_id, is_nsfw=is_nsfw)
    active_games[game_id] = session
    return session

def remove_session(game_id: str):
    session = active_games.pop(game_id, None)
    if session and session.timer_task and not session.timer_task.done():
        session.timer_task.cancel()
    log.debug(f"Removed session {game_id}")

async def cleanup_stale_sessions(max_age_seconds: int = 1800):
    """
    Periodic task to aggressively remove stale sessions older than 30 minutes.
    (Normal sessions resolve themselves in 15s and pop(), this is a fallback).
    """
    while True:
        await asyncio.sleep(60) # Check every minute
        now = time.time()
        stale_keys = [
            game_id for game_id, session in active_games.items()
            if now - session.created_at > max_age_seconds
        ]
        for game_id in stale_keys:
            remove_session(game_id)
