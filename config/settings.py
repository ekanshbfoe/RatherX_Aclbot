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

OWNER_ID = int(_owner_id_str)
FEEDBACK_GROUP_ID = int(os.getenv("FEEDBACK_GROUP_ID", "-1003049612396"))
FEEDBACK_TOPIC_ID = int(os.getenv("FEEDBACK_TOPIC_ID", "21"))
NOTIFICATION_LOG_GROUP = int(os.getenv("NOTIFICATION_LOG_GROUP", "-1003049612396"))
NOTIFICATION_LOG_TOPIC_ID = int(os.getenv("NOTIFICATION_LOG_TOPIC_ID", "18"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBAPP_HOST = os.getenv("WEBAPP_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("WEBAPP_PORT", "8080"))
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET_TOKEN", "")
