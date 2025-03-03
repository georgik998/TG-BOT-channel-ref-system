from project.src.bot.handlers.main import main_router
from project.src.bot.handlers.referal import referal_router
from project.src.bot.handlers.video import video_router
from project.src.bot.handlers.admin import admin_router
from project.src.bot.handlers.chat import chat_router
from project.src.bot.middleware import CheckUpMiddleware

referal_router.message.middleware(CheckUpMiddleware())
referal_router.callback_query.middleware(CheckUpMiddleware())

main_router.message.middleware(CheckUpMiddleware())
main_router.callback_query.middleware(CheckUpMiddleware())

video_router.message.middleware(CheckUpMiddleware())
video_router.callback_query.middleware(CheckUpMiddleware())

admin_router.message.middleware(CheckUpMiddleware())
admin_router.callback_query.middleware(CheckUpMiddleware())

chat_router.message.middleware(CheckUpMiddleware())
chat_router.callback_query.middleware(CheckUpMiddleware())