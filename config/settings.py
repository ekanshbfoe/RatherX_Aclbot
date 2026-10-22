import os
import sys
import time
from dotenv import load_dotenv

load_dotenv()

BOOT_TIME = time.time()

BOT_TOKEN = os.getenv("BOT_TOKEN")
_owner_id_str = os.getenv("OWNER_ID")

if not BOT_TOKEN:
    sys.exit("FATAL: BOT_TOKEN must be set as an environment variable.")
if not _owner_id_str:
    sys.exit("FATAL: OWNER_ID must be set as an environment variable.")

def _optional_int(name: str) -> int | None:
    value = os.getenv(name)
    return int(value) if value else None

OWNER_ID = int(_owner_id_str)
# Optional: when unset, /feedback and the admin alerts are turned off
FEEDBACK_GROUP_ID = _optional_int("FEEDBACK_GROUP_ID")
FEEDBACK_TOPIC_ID = _optional_int("FEEDBACK_TOPIC_ID")
NOTIFICATION_LOG_GROUP = _optional_int("NOTIFICATION_LOG_GROUP")
NOTIFICATION_LOG_TOPIC_ID = _optional_int("NOTIFICATION_LOG_TOPIC_ID")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").rstrip("/")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET_TOKEN", "")
