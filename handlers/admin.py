from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.send_signal import save_signal_for_later
from utils.send_signal import send_signal_to_users
from config import SUPERADMINS, ADMINS
import os
import json

router = Router()

# FSM состояния
class SignalForm(StatesGroup):
    ticker = State()
    position = State()
    take = State()
    risk = State()
    style = State()
    wait_time = State()

# /signal
@router.message(Command("signal"))
async def start_signal(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id not in ADMINS and user_id not in SUPERADMINS:
        return await message.answer("❌ Anda bukan admin. Mohon tunggu sinyal selanjutnya dari bot ini.")

    await state.set_state(SignalForm.ticker)
    await message.answer("🔹 Введи тикер (например: SEIUSDT)")

@router.message(SignalForm.ticker)
async def input_ticker(message: types.Message, state: FSMContext):
    await state.update_data(ticker=message.text)
    await state.set_state(SignalForm.position)
    await message.answer("📈 Введи позицию (например: LONG 25x)")

@router.message(SignalForm.position)
async def input_position(message: types.Message, state: FSMContext):
    await state.update_data(position=message.text)
    await state.set_state(SignalForm.take)
    await message.answer("🎯 Введи Take Profit (например: 0.214)")

@router.message(SignalForm.take)
async def input_take(message: types.Message, state: FSMContext):
    await state.update_data(take=message.text)
    await state.set_state(SignalForm.risk)
    await message.answer("💥 Введи риск (например: 30)")

@router.message(SignalForm.risk)
async def input_risk(message: types.Message, state: FSMContext):
    await state.update_data(risk=message.text)
    await state.set_state(SignalForm.style)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Премиум", callback_data="style_premium")],
        [InlineKeyboardButton(text="🔥 Памп", callback_data="style_pumping")]
    ])
    await message.answer("🎨 Выбери стиль оформления сигнала:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("style_"))
async def choose_style(callback: types.CallbackQuery, state: FSMContext):
    style = callback.data.split("_")[1]
    await state.update_data(style=style)

    data = await state.get_data()

    with open("templates/styles.json", "r", encoding="utf-8") as f:
        styles = json.load(f)
    template = styles[style]

    message_text = f"{template['title']}\n\n" + "\n".join([
        line.format(
            ticker=data['ticker'],
            position=data['position'],
            take=data['take'],
            risk=data['risk']
        ) for line in template['body']
    ]) + "\n\n" + template['footer']

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить сейчас", callback_data="send_now")],
        [InlineKeyboardButton(text="🕒 Отправить позже", callback_data="send_later")],
        [InlineKeyboardButton(text="🔙 Назад к стилю", callback_data="back_to_style")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_signal")]
    ])

    await callback.message.answer("✅ Сигнал готов к отправке:")
    await callback.message.answer(message_text, reply_markup=buttons)

@router.callback_query(F.data == "back_to_style")
async def back_to_style(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(SignalForm.style)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Премиум", callback_data="style_premium")],
        [InlineKeyboardButton(text="🔥 Памп", callback_data="style_pumping")]
    ])
    await callback.message.answer("🎨 Выбери стиль оформления сигнала:", reply_markup=keyboard)

@router.callback_query(F.data == "cancel_signal")
async def cancel_signal(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Сигнал отменён.")

@router.callback_query(F.data == "send_now")
async def send_now(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if data.get("already_sent"):
        await callback.message.answer("⚠️ Этот сигнал уже был отправлен ранее.")
        return

    await callback.message.answer("📤 Отправляю...")
    await send_signal_to_users(callback.bot, data)
    await callback.message.answer("✅ Сигнал отправлен.")
    data["already_sent"] = True
    await state.set_data(data)


@router.callback_query(F.data == "send_later")
async def ask_time(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if data.get("already_sent"):
        await callback.message.answer("⚠️ Этот сигнал уже был обработан.")
        return

    await state.set_state(SignalForm.wait_time)
    await callback.message.answer("⏰ Введи время отправки (формат HH:MM по Москве):")

@router.message(SignalForm.wait_time)
async def save_delayed_signal(message: types.Message, state: FSMContext):
    data = await state.get_data()
    result = await save_signal_for_later(data, message.text.strip())

    if result:
        await message.answer(result)
        await state.clear()
    else:
        await message.answer("⚠️ Неверный формат времени. Введи в формате HH:MM (например: 16:30)")

@router.message(Command("scheduled"))
@router.message(Command("scheduled"))
async def view_scheduled(message: types.Message):
    user_id = str(message.from_user.id)

    with open("database/users.json", "r", encoding="utf-8") as f:
        users = json.load(f)

    if user_id not in users or users[user_id]["role"] not in ["admin", "superadmin"]:
        return await message.answer("❌ Anda bukan admin. Mohon tunggu sinyal selanjutnya dari bot ini.")

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
                f"📊 {s.get('ticker', '...')} ({s.get('position', '?')}) | 🎯 Take: {s.get('take', '?')} | 🔥 Risk: {s.get('risk', '?')}%\n"
                f"🎨 Стиль: {s.get('style', '-')}\n\n"
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
        return await message.answer("❌ Anda bukan admin. Mohon tunggu sinyal selanjutnya dari bot ini.")

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
