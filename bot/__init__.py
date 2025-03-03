from aiogram import Bot
from os import getenv

from project.src.bot.handlers import main_router, video_router, referal_router, admin_router, chat_router
from project.src.bot.handlers.chat import dp

TOKEN = getenv('TOKEN')
bot = Bot(TOKEN)


def bot_run():
    dp.include_routers(main_router, video_router, referal_router, admin_router, chat_router)
    dp.run_polling(bot)
