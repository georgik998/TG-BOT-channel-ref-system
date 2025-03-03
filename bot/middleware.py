from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from project.src.bot.db.database import DB_ROOT, DataBase, create_connection, close_connection

from datetime import datetime

database = DataBase()

DATE = datetime.now().strftime("%d.%m.%Y").split(':')[0]


class CheckUpMiddleware(BaseMiddleware):

    async def __call__(self,
                       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        global DATE

        create_connection(DB_ROOT, database)
        block_user = database.get_block_user(user_id=data['event_context'].chat.id)
        if not block_user:

            if datetime.now().strftime("%d.%m.%Y").split(':')[0] == DATE:
                database.update_user_action(user_id=data['event_context'].chat.id)
            else:
                database.activity_change(date=DATE, pepople=len(database.get_statistic()))
                DATE = datetime.now().strftime("%d.%m.%Y").split(':')[0]
                database.update_statistic()
            close_connection(database)
            return await handler(event, data)
        close_connection(database)


    # self.cursor.execute(f"""UPDATE users_info_referal SET balance = balance + 15 WHERE user_id = {father}""")
    #     self.cursor.execute(f"UPDATE users_info_referal SET invites = invites + 1 WHERE user_id = {father}")