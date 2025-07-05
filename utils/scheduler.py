import asyncio
import json
from datetime import datetime
import pytz
from aiogram import Bot
from config import TIMEZONE

async def schedule_signal(bot: Bot, signal: dict, send_time: datetime):
    delay = (send_time - datetime.now(pytz.timezone(TIMEZONE))).total_seconds()
    await asyncio.sleep(delay)

    try:
        with open("templates/styles.json", "r", encoding="utf-8") as f:
            styles = json.load(f)
        with open("database/users.json", "r", encoding="utf-8") as f:
            users = json.load(f)

        template = styles[signal["style"]]
        message_text = f"{template['title']}\n\n" + "\n".join([
            line.format(
                ticker=signal["ticker"],
                position=signal["position"],
                take=signal["take"],
                risk=signal["risk"]
            ) for line in template["body"]
        ]) + "\n\n" + template["footer"]

        for uid, info in users.items():
            if info["role"] == "user":
                try:
                    await bot.send_message(uid, message_text)
                except Exception as e:
                    print(f"Ошибка при отправке {uid}: {e}")
    except Exception as e:
        print(f"[Schedule Execution Error] {e}")


async def check_scheduled_signals(bot: Bot):
    while True:
        try:
            with open("database/signals.json", "r+", encoding="utf-8") as f:
                signals = json.load(f)

            now = datetime.now(pytz.timezone(TIMEZONE))
            to_send = []
            remaining = []

            future_signals = []

            for signal in signals:
                try:
                    send_time = datetime.strptime(signal["send_at"], "%Y-%m-%d %H:%M")
                    send_time = pytz.timezone(TIMEZONE).localize(send_time)

                    if send_time <= now:
                        to_send.append(signal)
                    else:
                        future_signals.append(signal)
                        # Добавим в будущий планировщик заново
                        asyncio.create_task(schedule_signal(bot, signal, send_time))
                except Exception as e:
                    print(f"[Scheduler Parsing Error] Сигнал пропущен: {e}")

            if to_send:
                with open("templates/styles.json", "r", encoding="utf-8") as f:
                    styles = json.load(f)

                with open("database/users.json", "r", encoding="utf-8") as f:
                    users = json.load(f)

                for signal in to_send:
                    template = styles[signal["style"]]
                    message_text = f"{template['title']}\n\n" + "\n".join([
                        line.format(
                            ticker=signal["ticker"],
                            position=signal["position"],
                            take=signal["take"],
                            risk=signal["risk"]
                        ) for line in template["body"]
                    ]) + "\n\n" + template["footer"]

                    for uid, info in users.items():
                        if info["role"] == "user":
                            try:
                                await bot.send_message(uid, message_text)
                            except Exception as e:
                                print(f"Ошибка при отправке {uid}: {e}")

                # Обновляем signals.json (оставляем только неотправленные)
                with open("database/signals.json", "w", encoding="utf-8") as f:
                    json.dump(remaining, f, indent=2)
                    print(f"✅ Восстановлено {len(future_signals)} отложенных сигналов")

        except Exception as e:
            print(f"[Scheduler Error] {e}")

        await asyncio.sleep(30)  # интервал проверки
