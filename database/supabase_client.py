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
