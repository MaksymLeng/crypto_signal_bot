import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

ADMINS = list(map(int, os.getenv("ADMINS", "").split(",")))
SUPERADMINS = list(map(int, os.getenv("SUPERADMINS", "").split(",")))
