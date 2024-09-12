import asyncio
import logging
import sys

from aiogram.methods import DeleteWebhook

from config import dp, bot
from src.handlers.admin_handler import admin_router
from src.handlers.events import start_bot, stop_bot
from src.handlers.user_handler import user_router


async def start():
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    try:
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(start())
