from aiogram import Router, types
from aiogram.filters import Command
import json
from config import ADMINS, SUPERADMINS

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    with open("database/users.json", "r+") as f:
        data = json.load(f)
        if str(user_id) not in data:
            role = "superadmin" if user_id in SUPERADMINS else "admin" if user_id in ADMINS else "user"
            data[str(user_id)] = {"role": role}
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    await message.answer("✅ Вы зарегистрированы в системе.")
