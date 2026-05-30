import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
    API_ID     = int(os.getenv("API_ID") or "0")
    API_HASH   = os.getenv("API_HASH", "")
    PHONE      = os.getenv("PHONE", "")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "")
    DB_PATH        = "yukonuz.db"
    SESSION        = "logibot_session"
    SESSION_STRING = os.getenv("SESSION_STRING", "")
    # Admin user IDs (comma-separated in .env: ADMIN_IDS=123456789,987654321)
    ADMIN_IDS      = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
