import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, ADMINS, SUPERADMINS
from handlers import admin, superadmin, user
from utils.scheduler import check_scheduled_signals
import json

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher()

# Роутинг
dp.include_router(superadmin.router)
dp.include_router(admin.router)
dp.include_router(user.router)

async def main():
    try:
        print("🛠 Инициализация users.json...")
        with open("database/users.json", "r+", encoding="utf-8") as f:
            users = json.load(f)
            for uid in SUPERADMINS:
                uid = str(uid)
                if uid not in users:
                    users[uid] = {"role": "superadmin"}
            for uid in ADMINS:
                uid = str(uid)
                if uid not in users:
                    users[uid] = {"role": "admin"}
            f.seek(0)
            json.dump(users, f, indent=2)
            f.truncate()
        print("✅ users.json готов")

        await bot.delete_webhook(drop_pending_updates=True)
        print("🔁 Webhook удалён")

        print("🔄 Запуск планировщика и восстановление отложенных сигналов...")
        asyncio.create_task(check_scheduled_signals(bot))
        print("🕒 Планировщик запущен")

        print("🚀 Бот запускается")
        await dp.start_polling(bot)

    except Exception as e:
        import traceback
        print("[FATAL] Бот упал с ошибкой:")
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"[FATAL] Запуск main() завершился с ошибкой: {e}")

