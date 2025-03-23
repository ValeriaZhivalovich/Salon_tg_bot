import os
from logs.logger_config import logger
from dotenv import load_dotenv

import asyncio
from aiogram import Bot, Dispatcher

from app.user import router
from app.database.models import async_main

load_dotenv()
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logger.error("Токен не найден! .env файл")
    raise ValueError("Токен бота не найден!")



async def main():
    await async_main()

    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка во время работы бота: {e}")
    finally:
        await bot.session.close()
        logger.info("Сессия бота закрыта.")



if __name__ == "__main__":
    try:
        logger.info("Бот запущен")
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
        logger.warning("Бот отключен")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")