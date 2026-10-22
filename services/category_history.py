import asyncio
import logging
from datetime import datetime, timezone
from cachetools import TTLCache
from database.supabase_client import supabase
from database.categories import NSFW_CATEGORY
from services.game_session import track_task

log = logging.getLogger(__name__)

HISTORY_LIMIT = 3  # How many recent categories float to the top of the inline list

# user_id -> recent category keys, newest first. Inline queries fire on every keystroke, so avoid the DB.
_history_cache = TTLCache(maxsize=8192, ttl=1800)

async def get_recent_categories(user_id: int) -> list[str]:
    """Returns the user's most recently used categories, newest first."""
    if user_id in _history_cache:
        return _history_cache[user_id]
    if not supabase:
        return []

    try:
        res = await asyncio.to_thread(
            lambda: supabase.table("rather_category_history")
            .select("category")
            .eq("user_id", user_id)
            .order("last_used_at", desc=True)
            .limit(HISTORY_LIMIT)
            .execute()
        )
        recent = [row["category"] for row in res.data]
    except Exception as e:
        log.warning(f"Could not load category history for {user_id}: {e}")
        return []

    _history_cache[user_id] = recent
    return recent

async def _save_category_use(user_id: int, category: str):
    try:
        await asyncio.to_thread(
            lambda: supabase.table("rather_category_history").upsert(
                {"user_id": user_id, "category": category, "last_used_at": datetime.now(timezone.utc).isoformat()},
                on_conflict="user_id, category"
            ).execute()
        )
    except Exception as e:
        log.warning(f"Could not save category history for {user_id}: {e}")

async def record_category_use(user_id: int, category: str):
    """Moves a category to the top of the user's history. NSFW is never tracked, so it stays at the bottom."""
    if category == NSFW_CATEGORY:
        return

    # Update the cache right away so the next inline query already shows it
    recent = [c for c in await get_recent_categories(user_id) if c != category]
    _history_cache[user_id] = [category] + recent[:HISTORY_LIMIT - 1]

    if supabase:
        track_task(_save_category_use(user_id, category))
