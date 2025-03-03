from aiogram import Bot, Router, F, Dispatcher
from aiogram.filters import StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ContentType
from aiogram.exceptions import TelegramForbiddenError

from datetime import datetime

from project.src.bot.db.database import DB_ROOT, DataBase, ChatHistory, CHAT_ROOT, create_connection, close_connection
import project.src.bot.keyboards as kb
from project.src.bot.fsm import *

dp = Dispatcher()

chat_router = Router()
database = DataBase()
chat_database = ChatHistory()

TEXT_CASH = {}
messages_chat_cash = {}
chat_nickname = {}


class Admin(Filter):

    async def __call__(self, message: Message) -> bool:
        create_connection(DB_ROOT, database)
        admins = database.get_admins()
        close_connection(database)

        return (message.from_user.id,) in admins


@chat_router.message(Admin(), StateFilter(default_state), F.text == '/chat')
async def chat(message: Message):
    global chat_nickname
    chats = 'Все никнеймы:\n'
    for nick in chat_nickname.items():
        chats += f'{nick}\n'

    keyboard = [
        [['Начать чат', 'chat:start']]
    ]
    await message.answer(chats, reply_markup=kb.create_keyboard_inline(keyboard))


@chat_router.callback_query(Admin(), StateFilter(default_state), F.data == 'chat:start')
async def chat_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Chat.wait_for_user_id_to_start_chat)
    await callback.message.edit_text('Напише id юзера с кем хотите открыть чат', reply_markup=kb.close)


@chat_router.message(Admin(), StateFilter(Chat.wait_for_user_id_to_start_chat))
async def chat_start_begin(message: Message, state: FSMContext, bot: Bot):
    try:

        user_to_chat = int(message.text)

        await dp.fsm.get_context(
            bot, user_id=user_to_chat, chat_id=user_to_chat
        ).set_state(Chat.chat)
        await dp.fsm.get_context(
            bot, user_id=user_to_chat, chat_id=user_to_chat
        ).update_data({'partner_id': message.from_user.id})
        TEXT_CASH.update({
            user_to_chat: ''
        })

        await bot.send_message(chat_id=user_to_chat, text='⚠️ВНИМАНИЕ⚠️\n'
                                                          'Администратор открыл с вами чат.\n'
                                                          'Функция бота недоступны пока чат не будет закрыт.\n'
                                                          'Закрыть его может только администратор.\n'
                                                          'История переписки будет сохранена.\n'
                                                          'Можете уточнить некоторые данные ?')

        await state.set_state(default_state)
        await message.answer('Чат открыт.')
    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова', reply_markup=kb.close)
    except Exception:
        await message.answer('Пользователя с таким id нет. Попробуйте снова', reply_markup=kb.close)


@chat_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('chat_close')] == 'chat_close')
async def close_chat(callback: CallbackQuery):
    global TEXT_CASH, messages_chat_cash
    partner_id = int(callback.data.split(':')[1])
    try:
        TEXT_CASH[partner_id]
        await callback.message.answer('Вы уверены что хотите закрыть чат?', reply_markup=kb.create_keyboard_inline([
            [['Да', f'chat_finish:1:{partner_id}'], ['Нет', f'chat_finish:0:{partner_id}']]
        ]))
        # try:
        #     await callback.message.answer('Закрываем чат...')
        #
        #     await dp.fsm.get_context(
        #         bot, user_id=partner_id, chat_id=partner_id
        #     ).set_state(default_state)
        #     await dp.fsm.get_context(
        #         bot, user_id=partner_id, chat_id=partner_id
        #     ).update_data()
        #     await bot.send_message(chat_id=partner_id,
        #                            text='Админ закрыл диалог с вами, помните что диалог был записан.\n'
        #                                 'Спасибо что сотрудничаете с нами!')
        #
        #     create_connection(CHAT_ROOT, chat_database)
        #     chat_database.write_new_chat(partner_id=partner_id,
        #                                  date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
        #                                  text=TEXT_CASH[partner_id])
        #     close_connection(chat_database)
        # except TelegramForbiddenError:
        #
        #     create_connection(CHAT_ROOT, chat_database)
        #     chat_database.write_new_chat(partner_id=partner_id,
        #                                  date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
        #                                  text=TEXT_CASH[partner_id])
        #     close_connection(chat_database)
        # del TEXT_CASH[partner_id]
        # key_to_delete = []
        # for key, value in messages_chat_cash.items():
        #     if value == partner_id:
        #         key_to_delete.append(key)
        # for key in key_to_delete: del messages_chat_cash[key]
        # del chat_nickname[partner_id]
        # await state.clear()
        # await callback.message.answer('Чат успешно закрыт!')
    except KeyError:
        await callback.message.answer('Чат уже закрыт.')


@chat_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('chat_finish')] == 'chat_finish')
async def close_chat(callback: CallbackQuery, bot: Bot, state: FSMContext):
    global TEXT_CASH, messages_chat_cash
    answer = int(callback.data.split(':')[1])
    if answer:
        partner_id = int(callback.data.split(':')[2])
        try:
            TEXT_CASH[partner_id]
            try:
                await callback.message.edit_text('Закрываем чат...')

                await dp.fsm.get_context(
                    bot, user_id=partner_id, chat_id=partner_id
                ).set_state(default_state)
                await dp.fsm.get_context(
                    bot, user_id=partner_id, chat_id=partner_id
                ).update_data()
                await bot.send_message(chat_id=partner_id,
                                       text='Админ закрыл диалог с вами, помните что диалог был записан.\n'
                                            'Спасибо что сотрудничаете с нами!')

                create_connection(CHAT_ROOT, chat_database)
                chat_database.write_new_chat(partner_id=partner_id,
                                             date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
                                             text=TEXT_CASH[partner_id])
                close_connection(chat_database)
            except TelegramForbiddenError:

                create_connection(CHAT_ROOT, chat_database)
                chat_database.write_new_chat(partner_id=partner_id,
                                             date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
                                             text=TEXT_CASH[partner_id])
                close_connection(chat_database)
            del TEXT_CASH[partner_id]
            key_to_delete = []
            for key, value in messages_chat_cash.items():
                if value == partner_id:
                    key_to_delete.append(key)
            for key in key_to_delete: del messages_chat_cash[key]
            del chat_nickname[partner_id]
            await callback.message.edit_text('Чат успешно закрыт!')
        except KeyError:
            await callback.message.edit_text('Чат уже закрыт.')
    else:
        await callback.message.edit_text('Дейстиве отменено.')
    await state.clear()


@chat_router.message(StateFilter(Chat.chat))
async def chatting(message: Message, bot: Bot, state: FSMContext):
    keyboard = kb.create_keyboard_inline([
        [[f'{message.from_user.first_name}', '-']],
        [['💢 Закрыть чат', f'chat_close:{message.from_user.id}']]
    ])

    global TEXT_CASH, chat_nickname
    cash = await state.get_data()
    id = cash['partner_id']
    partner_id = id

    if message.from_user.id not in chat_nickname.keys():
        chat_nickname.update({
            message.from_user.id: message.from_user.first_name
        })

    try:
        if message.content_type == ContentType.VIDEO:
            TEXT_CASH[message.from_user.id] += f"""user:[Видео файл]\n"""
            if message.caption:
                sms = await bot.send_video(chat_id=id, video=message.video.file_id, caption=message.caption,
                                           reply_markup=keyboard)
                TEXT_CASH[message.from_user.id] += f"""Подпись к видео:{message.caption}\n\n"""

            else:
                sms = await bot.send_video(chat_id=id, video=message.video.file_id, reply_markup=keyboard)
        elif message.content_type == ContentType.PHOTO:
            TEXT_CASH[message.from_user.id] += f"""user:[Фото файл]\n"""
            if message.caption:
                sms = await bot.send_photo(chat_id=id, photo=message.photo[-1].file_id, caption=message.caption,
                                           reply_markup=keyboard)
                TEXT_CASH[message.from_user.id] += f"""Подпись к фото:{message.caption}\n\n"""

            else:
                sms = await bot.send_photo(chat_id=id, photo=message.photo[-1].file_id, reply_markup=keyboard)

        else:
            TEXT_CASH[message.from_user.id] += f"""user:{message.text}\n\n"""
            sms = await bot.send_message(chat_id=id, text=message.text, reply_markup=keyboard)

        messages_chat_cash.update({
            sms.message_id: message.from_user.id
        })
    except TelegramForbiddenError:
        # закроем чат
        create_connection(CHAT_ROOT, chat_database)
        chat_database.write_new_chat(partner_id=partner_id,
                                     date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
                                     text=TEXT_CASH[partner_id])
        close_connection(chat_database)
        del TEXT_CASH[partner_id]
        key_to_delete = []
        for key, value in messages_chat_cash.items():
            if value == partner_id:
                key_to_delete.append(key)
        for key in key_to_delete: del messages_chat_cash[key]
        del chat_nickname[partner_id]
        await message.answer('Юзер заблокировал бота, чат закрыт.')

    await state.update_data(cash)


# Ответ для админа
@chat_router.message(Admin(), StateFilter(default_state))
async def chatting_admin(message: Message, bot: Bot):
    if message.reply_to_message:

        text = message.text

        try:
            partner_id = messages_chat_cash[message.reply_to_message.message_id]

            if message.content_type == ContentType.VIDEO:
                TEXT_CASH[partner_id] += f"""admin:[Видео файл]\n"""
                if message.caption:
                    await bot.send_video(chat_id=partner_id, video=message.video.file_id, caption=message.caption)
                    TEXT_CASH[partner_id] += f"""Подпись к видео:{message.caption}\n\n"""
                else:
                    await bot.send_video(chat_id=partner_id, video=message.video.file_id)
            elif message.content_type == ContentType.PHOTO:
                TEXT_CASH[partner_id] += f"""admin:[Фото файл]\n"""
                if message.caption:
                    await bot.send_photo(chat_id=partner_id, photo=message.photo[-1].file_id, caption=message.caption)
                    TEXT_CASH[partner_id] += f"""Подпись к фото:{message.caption}\n\n"""
                else:
                    await bot.send_photo(chat_id=partner_id, photo=message.photo[-1].file_id)
            else:
                TEXT_CASH[partner_id] += f"""admin:{message.text}\n\n"""
                await bot.send_message(chat_id=partner_id, text=text)


        except KeyError:
            pass
