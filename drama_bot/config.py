"""Sozlamalar (.env faylidan o'qiladi)."""
import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
OWNER_ID: int = int(os.getenv("OWNER_ID", "0"))
MAIN_CHANNEL_URL: str = os.getenv("MAIN_CHANNEL_URL", "https://t.me/your_main_channel")
DB_PATH: str = os.getenv("DB_PATH", "drama.db")

if not BOT_TOKEN or not OWNER_ID:
    raise SystemExit("❌ .env faylida BOT_TOKEN va OWNER_ID ko'rsatilishi shart!")
