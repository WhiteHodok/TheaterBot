from aiogram.types import Message

from config import bot, secrets
from src.phrases import START_BOT, STOP_BOT


async def start_bot() -> None:
    await bot.send_message(secrets.admin_id, START_BOT)


async def stop_bot() -> None:
    await bot.send_message(secrets.admin_id, STOP_BOT)


async def error_bot(def_name: str, message: Message, error: str) -> None:
    await bot.send_message(
        chat_id=secrets.admin_id,
        text=f'Ошибка в функции <b>{def_name}</b>: \n<code>{error}</code>',
        parse_mode='HTML',
        message_thread_id=secrets.admin_thread
    )
    message_data = str(message)
    parts = [message_data[i:i + 4096] for i in range(0, len(message_data), 4096)]
    for part in parts:
        await bot.send_message(
            chat_id=secrets.admin_id,
            text=f'```{part}```',
            message_thread_id=secrets.admin_thread
        )
