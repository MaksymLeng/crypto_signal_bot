from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.send_signal import save_signal_for_later, send_signal_to_users
from config import SUPERADMINS, ADMINS
import os
import json

router = Router()

class SignalForm(StatesGroup):
    full_text = State()
    wait_time = State()

@router.message(Command("signal"))
async def start_signal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMINS and user_id not in SUPERADMINS:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")

    await state.set_state(SignalForm.full_text)
    await message.answer("📝 Введи полный текст сигнала:")

@router.message(SignalForm.full_text)
async def preview_signal(message: types.Message, state: FSMContext):
    signal_text = message.text
    await state.update_data(full_text=signal_text)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить сейчас", callback_data="send_now_full")],
        [InlineKeyboardButton(text="🕒 Отправить позже", callback_data="send_later_full")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_signal")]
    ])

    await message.answer("✅ Проверь текст сигнала:")
    await message.answer(signal_text, reply_markup=buttons)

@router.callback_query(F.data == "send_now_full")
async def send_now_full(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get("full_text")

    if not text:
        return await callback.message.answer("⚠️ Нет текста сигнала.")

    try:
        # Удаляем сообщение с кнопками (где был превью сигнала)
        await callback.message.delete()
    except Exception as e:
        print(f"[⚠] Не удалось удалить сообщение: {e}")

    await callback.message.answer("📤 Отправляю...")
    await send_signal_to_users(callback.bot, {"custom_text": text})
    await callback.message.answer("✅ Сигнал отправлен.")
    await state.clear()


@router.callback_query(F.data == "send_later_full")
async def ask_time_full(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SignalForm.wait_time)
    await callback.message.answer("⏰ Введи время отправки (формат HH:MM по Москве):")

@router.message(SignalForm.wait_time)
async def save_delayed_signal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = data.get("full_text")

    if not text:
        return await message.answer("⚠️ Нет текста сигнала.")

    result = await save_signal_for_later({"custom_text": text}, message.text.strip())

    if result:
        await message.answer(result)
        await state.clear()
    else:
        await message.answer("⚠️ Неверный формат времени. Введи в формате HH:MM")

@router.callback_query(F.data == "cancel_signal")
async def cancel_signal(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Сигнал отменён.")

@router.message(Command("scheduled"))
async def view_scheduled(message: types.Message):
    user_id = str(message.from_user.id)

    with open("database/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    if user_id not in users or users[user_id]["role"] not in ["admin", "superadmin"]:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")

    if not os.path.exists("database/signals.json"):
        return await message.answer("📭 Нет отложенных сигналов.")

    with open("database/signals.json", "r", encoding="utf-8") as f:
        signals = json.load(f)

    if not signals:
        return await message.answer("📭 Нет отложенных сигналов.")

    text = "📝 <b>Список отложенных сигналов:</b>\n\n"
    for s in signals:
        try:
            text += (
                f"🆔 <code>{s.get('id', '[нет id]')}</code>\n"
                f"🕒 {s.get('send_at', '[нет времени]')}\n"
                f"📋 {s.get('custom_text', '[текст не указан]')[:100]}...\n\n"
            )
        except Exception as e:
            print(f"[❗] Ошибка сигнала: {s} → {e}")

    await message.answer(text, parse_mode="HTML")

@router.message(Command("deletesignal"))
async def delete_scheduled(message: types.Message):
    user_id = str(message.from_user.id)

    with open("database/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    if user_id not in users or users[user_id]["role"] not in ["admin", "superadmin"]:
        return await message.answer("❌ You are not an admin. Please wait for signals from the bot.")

    parts = message.text.strip().split()
    if len(parts) != 2:
        return await message.answer(
            "⚠ Чтобы удалить сигнал, укажи его ID.\n\n"
            "Пример: <code>/deletesignal 2391fc9a</code>\n"
            "👉 Посмотри список ID с помощью команды <b>/scheduled</b>.",
            parse_mode="HTML"
        )

    signal_id = parts[1]

    try:
        with open("database/signals.json", "r+", encoding="utf-8") as f:
            signals = json.load(f)
            updated = [s for s in signals if s["id"] != signal_id]

            if len(signals) == len(updated):
                return await message.answer("⚠ Сигнал с таким ID не найден.")

            f.seek(0)
            json.dump(updated, f, indent=2)
            f.truncate()

        await message.answer(f"🗑 Сигнал с ID <code>{signal_id}</code> удалён.", parse_mode="HTML")

    except Exception as e:
        await message.answer(f"❌ Ошибка при удалении: {e}")
