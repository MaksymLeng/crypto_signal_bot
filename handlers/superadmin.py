from aiogram import Router, types
from aiogram.filters import Command
from config import SUPERADMINS
import json

router = Router()

def sync_superadmin_to_users(user_id: int):
    """Добавляет SUPERADMIN в users.json, если его там нет"""
    with open("database/users.json", "r+", encoding="utf-8") as f:
        users = json.load(f)
        uid = str(user_id)
        if user_id in SUPERADMINS and uid not in users:
            users[uid] = {"role": "superadmin"}
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()

@router.message(Command("addadmin"))
async def add_admin(message: types.Message):
    sync_superadmin_to_users(message.from_user.id)

    if message.from_user.id not in SUPERADMINS:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")


    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("⚠️ Используй: /addadmin user_id")

    new_id = parts[1]

    with open("database/users.json", "r+", encoding="utf-8") as f:
        users = json.load(f)
        if new_id not in users:
            users[new_id] = {"role": "admin"}
        else:
            users[new_id]["role"] = "admin"
        f.seek(0)
        json.dump(users, f, indent=2)
        f.truncate()

    await message.answer(f"✅ <code>{new_id}</code> теперь админ.", parse_mode="HTML")

@router.message(Command("removeadmin"))
async def remove_admin(message: types.Message):
    sync_superadmin_to_users(message.from_user.id)

    if message.from_user.id not in SUPERADMINS:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")

    parts = message.text.strip().split()
    if len(parts) != 2 or not parts[1].isdigit():
        return await message.answer("⚠️ Используй: /removeadmin user_id")

    rm_id = parts[1]

    with open("database/users.json", "r+", encoding="utf-8") as f:
        users = json.load(f)
        if rm_id in users:
            users[rm_id]["role"] = "user"
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()
            await message.answer(f"🚫 <code>{rm_id}</code> больше не админ.", parse_mode="HTML")
        else:
            await message.answer("⛔️ Пользователь не найден.")

@router.message(Command("listadmins"))
async def list_admins(message: types.Message):
    sync_superadmin_to_users(message.from_user.id)

    if message.from_user.id not in SUPERADMINS:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")

    with open("database/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    admins = [uid for uid, info in users.items() if info["role"] == "admin"]
    superadmins = [uid for uid, info in users.items() if info["role"] == "superadmin"]

    if not admins and not superadmins:
        return await message.answer("😶 Админов пока нет.")

    text = "<b>👑 Супер-админы:</b>\n" + \
        "\n".join([f"<code>{uid}</code>" for uid in superadmins]) + \
        "\n\n<b>🛡 Админы:</b>\n" + \
        "\n".join([f"<code>{uid}</code>" for uid in admins])

    await message.answer(text, parse_mode="HTML")

