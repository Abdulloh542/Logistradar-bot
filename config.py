import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN  = os.getenv("BOT_TOKEN", "")
    API_ID     = int(os.getenv("API_ID") or "0")
    API_HASH   = os.getenv("API_HASH", "")
    PHONE      = os.getenv("PHONE", "")
    WEBAPP_URL = os.getenv("WEBAPP_URL", "")
    DB_PATH    = "yukonuz.db"
    SESSION    = "userbot_session"
