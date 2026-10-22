import os
import logging
from supabase import create_client, Client

log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase: Client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        log.info("Supabase client initialized successfully.")
    except Exception as e:
        log.error(f"Failed to initialize Supabase client: {e}")
else:
    log.warning("SUPABASE_URL or SUPABASE_KEY is missing from environment variables.")

def fetch_all_rows(make_query, page_size: int = 1000) -> list:
    """Reads every row of a query page by page (Supabase returns at most 1000 rows per request).

    make_query must build a fresh, consistently ordered query each call. Blocking: run it in a thread.
    """
    rows = []
    start = 0
    while True:
        page = make_query().range(start, start + page_size - 1).execute().data
        if not page:
            return rows
        rows.extend(page)
        start += len(page)
