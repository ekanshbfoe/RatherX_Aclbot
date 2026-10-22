import asyncio
import time
import logging
import itertools
from functools import wraps
from cachetools import TTLCache
from database.questions import get_question_by_id, ALL_QUESTIONS_MAP
from database.supabase_client import supabase, fetch_all_rows
from dataclasses import dataclass, field
from typing import Set, Dict, Optional, Any

log = logging.getLogger(__name__)

# Shared registry for all fire-and-forget background tasks across the bot
background_tasks = set()

def track_task(coro):
    """Schedules a coroutine and keeps a strong reference to prevent GC."""
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    return task

@dataclass
class GameSession:
    question_id: str
    is_nsfw: bool
    mode: str = "sfw" # "sfw" (random) or a category key; decides what 'Next Question' offers
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

def create_session(game_id: str, question_id: str, is_nsfw: bool, mode: str = "sfw") -> GameSession:
    session = GameSession(question_id=question_id, is_nsfw=is_nsfw, mode=mode)
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

# ----------------- GLOBAL & LOCAL HISTORY & MATCHING -----------------

# ----------------- GLOBAL & LOCAL HISTORY & MATCHING -----------------

def with_retry(max_retries=3, initial_delay=1, fallback_return=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        log.error(f"DB Error {func.__name__} (Final Attempt {attempt + 1}): {e}")
                        return fallback_return
                    log.warning(f"DB Error {func.__name__} (Attempt {attempt + 1}): {e}. Retrying in {delay}s...")
                    await asyncio.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

# LRU Cache for chat instances (reduces redundant /mylove DB lookups)
_chat_instance_cache = TTLCache(maxsize=2048, ttl=300)

@with_retry(fallback_return=None)
async def map_chat_instance(chat_id: int, chat_instance: str):
    """Maps a standard Telegram chat_id to a hidden chat_instance string."""
    if not supabase: return
    _chat_instance_cache[chat_id] = chat_instance
    await asyncio.to_thread(
        lambda: supabase.table("rather_chat_mappings").upsert(
            {"chat_id": chat_id, "chat_instance": chat_instance}
        ).execute()
    )

@with_retry(fallback_return=None)
async def get_chat_instance(chat_id: int) -> Optional[str]:
    """Retrieves the chat_instance for a given chat_id."""
    if chat_id in _chat_instance_cache:
        return _chat_instance_cache[chat_id]
        
    if not supabase: return None
    res = await asyncio.to_thread(
        lambda: supabase.table("rather_chat_mappings").select("chat_instance").eq("chat_id", chat_id).execute()
    )
    if res.data:
        val = res.data[0]["chat_instance"]
        _chat_instance_cache[chat_id] = val
        return val
    return None

@with_retry(fallback_return=None)
async def record_user_vote(user_id: int, user_name: str, question_id: str, vote_choice: str, chat_instance: Optional[str] = None, username: Optional[str] = None):
    """Records a vote into Supabase globally, and locally if chat_instance is provided."""
    if not supabase: return
    
    # Freeze all values into locals to break closure capture risk
    _uid, _uname, _qid, _vc, _ci, _uname2 = (
        user_id, user_name, question_id, vote_choice, chat_instance, username
    )

    # 1. Sequential Execution: Await User Upsert first to prevent Foreign Key constraint violation
    await asyncio.to_thread(
        lambda: supabase.table("rather_users").upsert(
            {"user_id": _uid, "first_name": _uname, "username": _uname2},
            on_conflict="user_id"
        ).execute()
    )
    
    # Step 2: Use default-arg binding to freeze values at definition time
    async def _upsert_global(uid=_uid, qid=_qid, vc=_vc):
        return await asyncio.to_thread(
            lambda: supabase.table("rather_votes_global").upsert(
                {"user_id": uid, "question_id": qid, "vote_choice": vc},
                on_conflict="user_id, question_id"
            ).execute()
        )

    tasks = [_upsert_global()]
    
    if _ci:
        async def _upsert_local(uid=_uid, qid=_qid, vc=_vc, ci=_ci):
            return await asyncio.to_thread(
                lambda: supabase.table("rather_votes_local").upsert(
                    {"chat_instance": ci, "user_id": uid, "question_id": qid, "vote_choice": vc},
                    on_conflict="chat_instance, user_id, question_id"
                ).execute()
            )
        tasks.append(_upsert_local())
        
    await asyncio.gather(*tasks)

@with_retry(fallback_return={})
async def get_global_history_dict() -> dict:
    if not supabase: return {}
    rows = await asyncio.to_thread(
        fetch_all_rows,
        lambda: supabase.table("rather_votes_global").select("user_id, question_id, vote_choice, rather_users(first_name, username)").order("user_id").order("question_id")
    )
    history = {}
    for row in rows:
        uid = row["user_id"]
        if uid not in history:
            u = row.get("rather_users") or {}
            history[uid] = {"name": u.get("first_name", "Unknown"), "username": u.get("username"), "votes": {}}
        history[uid]["votes"][row["question_id"]] = row["vote_choice"]
    return history

@with_retry(fallback_return={})
async def get_local_history_dict(chat_instance: str) -> dict:
    if not supabase: return {}
    rows = await asyncio.to_thread(
        fetch_all_rows,
        lambda: supabase.table("rather_votes_local").select("user_id, question_id, vote_choice, rather_users(first_name, username)").eq("chat_instance", chat_instance).order("user_id").order("question_id")
    )
    history = {}
    for row in rows:
        uid = row["user_id"]
        if uid not in history:
            u = row.get("rather_users") or {}
            history[uid] = {"name": u.get("first_name", "Unknown"), "username": u.get("username"), "votes": {}}
        history[uid]["votes"][row["question_id"]] = row["vote_choice"]
    return history

def _score_pair(u1_votes: dict, u2_votes: dict, q_map: dict):
    """Core matchmaking logic, extracted for reuse and speed."""
    # Use native dictionary keys intersection (O(min(N, M))) instead of converting both to sets first
    common_qids = u1_votes.keys() & u2_votes.keys()
    if len(common_qids) < 5:
        return None
        
    earned_points = 0
    possible_points = 0
    
    for qid in common_qids:
        v1 = u1_votes[qid]
        v2 = u2_votes[qid]
        
        question = q_map.get(qid)
        if not question:
            continue
            
        if v1 != v2:
            possible_points += 1
        else:
            majority_option = 'a' if question.global_votes_blue > question.global_votes_red else 'b'
            if v1 == majority_option:
                earned_points += 1
                possible_points += 1
            else:
                earned_points += 2
                possible_points += 2
                
    percentage = (earned_points / possible_points) * 100 if possible_points > 0 else 0
    return earned_points, round(percentage, 1), len(common_qids)

def _calculate_couples_sync(users_dict: dict, pairs: list) -> list:
    """CPU-bound computation — safe to run in threadpool."""
    couples = []
    
    for uid1, uid2 in pairs:
        u1_data = users_dict.get(uid1)
        u2_data = users_dict.get(uid2)
        if not u1_data or not u2_data:
            continue
            
        score = _score_pair(u1_data["votes"], u2_data["votes"], ALL_QUESTIONS_MAP)
        if not score:
            continue
            
        earned_points, percentage, common_count = score
        
        couples.append({
            "u1_id": uid1,
            "u2_id": uid2,
            "u1_name": u1_data["name"],
            "u2_name": u2_data["name"],
            "percentage": percentage,
            "points": earned_points,
            "common_count": common_count
        })
        
    # Sort by percentage desc, common count desc, points desc
    couples.sort(key=lambda x: (x["percentage"], x["common_count"], x["points"]), reverse=True)
    return couples

async def calculate_couples(scope: str, identifier = None) -> list:
    if scope == "local":
        users_dict = await get_local_history_dict(identifier)
        if not users_dict:
            return []
        user_ids = list(users_dict.keys())
        pairs_list = list(itertools.combinations(user_ids, 2))
    elif scope == "personal":
        users_dict = await get_global_history_dict()
        user_ids = list(users_dict.keys())
        if identifier not in user_ids:
            return []
        other_users = [u for u in user_ids if u != identifier]
        pairs_list = [(identifier, other) for other in other_users]
    else: # global
        users_dict = await get_global_history_dict()
        user_ids = list(users_dict.keys())
        pairs_list = list(itertools.combinations(user_ids, 2))
    
    # Offload heavy CPU work to thread pool — never block the event loop
    return await asyncio.to_thread(_calculate_couples_sync, users_dict, pairs_list)

def calculate_specific_compatibility(users_dict: dict, uid1: int, uid2: int) -> Optional[dict]:
    """Calculates the specific compatibility between two users in a given dictionary."""
    if uid1 not in users_dict or uid2 not in users_dict:
        return None
        
    u1_data = users_dict[uid1]
    u2_data = users_dict[uid2]
    
    score = _score_pair(u1_data["votes"], u2_data["votes"], ALL_QUESTIONS_MAP)
    if not score:
        return None
        
    earned_points, percentage, common_count = score
    
    return {
        "u1_name": u1_data["name"],
        "u2_name": u2_data["name"],
        "percentage": percentage,
        "points": earned_points,
        "common_count": common_count
    }
