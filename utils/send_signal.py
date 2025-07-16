import json
from datetime import datetime
import pytz
import uuid

async def send_signal_to_users(bot, signal_data):
    from config import SUPERADMINS, ADMINS

    # Если кастомный текст — просто отправляем его
    if "custom_text" in signal_data:
        message_text = signal_data["custom_text"]
    else:
        with open("templates/styles.json", "r", encoding="utf-8") as f:
            styles = json.load(f)

        style = styles[signal_data["style"]]

        message_text = f"{style['title']}\n\n" + "\n".join([
            line.format(
                ticker=signal_data["ticker"],
                position=signal_data["position"],
                take=signal_data["take"],
                risk=signal_data["risk"]
            ) for line in style["body"]
        ]) + "\n\n" + style["footer"]

    # Читаем юзеров и отправляем
    with open("database/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    for uid, info in users.items():
        if info["role"] == "user":
            try:
                await bot.send_message(uid, message_text)
            except Exception as e:
                print(f"❗️ Ошибка при отправке {uid}: {e}")

async def save_signal_for_later(data, time_str):
    try:
        input_time = datetime.strptime(time_str.strip(), "%H:%M")
        now = datetime.now(pytz.timezone("Europe/Moscow"))
        target_time = now.replace(hour=input_time.hour, minute=input_time.minute, second=0,
                                  microsecond=0)
        if target_time < now:
            target_time = target_time.replace(day=now.day + 1)

        data["send_at"] = target_time.strftime("%Y-%m-%d %H:%M")
        data["id"] = str(uuid.uuid4())

        with open("database/signals.json", "r+", encoding="utf-8") as f:
            signals = json.load(f)
            signals.append(data)
            f.seek(0)
            json.dump(signals, f, indent=2)
            f.truncate()

        return f"🕓 Сигнал запланирован на {data['send_at']} (МСК)"
    except ValueError:
        return None
