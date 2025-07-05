from aiogram import Router, types
from aiogram.filters import Command
import json
from config import ADMINS, SUPERADMINS
from aiogram.types import FSInputFile

router = Router()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    user_id_str = str(user_id)

    with open("database/users.json", "r+", encoding="utf-8") as f:
        data = json.load(f)
        # Присваиваем роль, если пользователь новый
        if user_id_str not in data:
            if user_id in SUPERADMINS:
                role = "superadmin"
            elif user_id in ADMINS:
                role = "admin"
            else:
                role = "user"
            data[user_id_str] = {"role": role}
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
        else:
            role = data[user_id_str]["role"]

    # Приветствие по роли
    if role == "user":
        await message.answer_photo(
            photo=FSInputFile("assets/tradePower.jpg"),
            caption="👋 Selamat datang di bot sinyal dari kanal TradePower!"
        )
    elif role == "admin":
        await message.answer(
            "🛠 Вы вошли как админ.\n\n"
            "Доступные команды:\n"
            "/signal — создать сигнал\n"
            "/start — перезапуск панели"
        )
    elif role == "superadmin":
        await message.answer(
            "👑 Вы вошли как супер-админ.\n\n"
            "Доступные команды:\n"
            "/signal — создать сигнал\n"
            "/addadmin user_id — добавить админа\n"
            "/removeadmin user_id — убрать админа\n"
            "/listadmins — список админов\n"
            "/scheduled — список отложенных сигналов\n"
            "/deletesignal id — удалить отложенный сигнал\n"
            "/start — перезапуск панели"
        )


