from aiogram import Bot, Router, F
from aiogram.filters import StateFilter, ChatMemberUpdatedFilter, JOIN_TRANSITION, CommandStart, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated
from aiogram.utils.deep_linking import create_start_link

import project.src.bot.keyboards as kb
from project.src.bot.db.database import DB_ROOT, DataBase, create_connection, close_connection

main_router = Router()

database = DataBase()


async def create_links(bot: Bot):
    create_connection(DB_ROOT, database)
    chats = database.get_channels()
    close_connection(database)

    links = []
    for chat_id in chats:
        link = await bot.create_chat_invite_link(chat_id=chat_id[0], expire_date=None)
        links.append(
            link.invite_link
        )
    return links


@main_router.message(CommandStart(deep_link=True), StateFilter(default_state))
async def start(message: Message, bot: Bot, command: CommandObject):
    # Добавление юзера в бд
    links = await create_links(bot=bot)
    bot_invite_link = await create_start_link(bot, message.from_user.id)

    father = command.args

    create_connection(DB_ROOT, database)
    channels = database.get_channels_id()
    database.add_new_user(user_id=message.from_user.id,
                          links=links,
                          channels=channels,
                          bot_invite_link=bot_invite_link,
                          father=father)
    text = database.get_text(text='start')
    close_connection(database)

    text += f"""\n\n<b>Реферальная ссылка для приглашения в бот:</b> {bot_invite_link}"""
    await message.answer(text, reply_markup=kb.start, parse_mode="HTML")


@main_router.message(CommandStart(deep_link=False), StateFilter(default_state))
async def start(message: Message, bot: Bot):
    # Добавление юзера в бд
    links = await create_links(bot=bot)
    bot_invite_link = await create_start_link(bot, message.from_user.id)

    create_connection(DB_ROOT, database)
    channels = database.get_channels_id()
    database.add_new_user(user_id=message.from_user.id,
                          links=links,
                          channels=channels,
                          bot_invite_link=bot_invite_link)
    text = database.get_text(text='start')
    close_connection(database)
    text += f"""\n\n<b>Реферальная ссылка для приглашения в бот:</b> {bot_invite_link}"""
    await message.answer(text, reply_markup=kb.start, parse_mode="HTML")


@main_router.message(F.text == '/info', StateFilter(default_state))
async def info(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    create_connection(DB_ROOT, database)
    text = database.get_text(text='start')
    bot_invite_link = database.query_execute(
        f"""SELECT invite_link FROM users_info_referal WHERE user_id = {message.from_user.id}""")
    close_connection(database)
    text += f"""\n\n<b>Реферальная ссылка для приглашения в бот:</b> {bot_invite_link[0][0]}"""

    await message.answer(text, reply_markup=kb.info, parse_mode="HTML")


@main_router.message(F.text == '/help', StateFilter(default_state))
async def start(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    sticker_id = await message.answer_sticker(
        sticker='CAACAgEAAxkBAAEMCqhmM8s6yTsW9CJKA2wgVFQaHGZ0KwACMQIAAsOjKEdLBVdiYsQQXzQE')
    sticker_id = sticker_id.message_id

    keyboard = kb.create_keyboard_inline([
        [['Написать', 'https://t.me/CashEazyHelp_bot']],
        [['💢 Закрыть', f'close:{sticker_id}']]
    ])
    await message.answer(
        text='<b>Если вы столкнулись с какой-то проблемой или у вас есть какое-то уникальное предложение, то напишите нам в бот помощи</b>',
        reply_markup=keyboard, parse_mode="HTML")


# close
@main_router.callback_query(F.data[:len('close')] == 'close')
async def close(callback: CallbackQuery, state: FSMContext, bot: Bot):
    user_state = await state.get_state()

    if str(user_state) != 'Chat:chat' and str(user_state) != 'AdminState:wait_channel_confirm':
        try:
            sticker = int(callback.data.split(':')[1])
            if sticker != 0:
                await bot.delete_message(chat_id=callback.from_user.id, message_id=sticker)
        except IndexError:
            pass
        await state.clear()
        await callback.message.delete()


@main_router.chat_member(ChatMemberUpdatedFilter(JOIN_TRANSITION))
async def subscribe_check(event: ChatMemberUpdated):
    if event.invite_link:
        link = event.invite_link.invite_link
        channel = event.chat.id
        user_id = event.from_user.id

        create_connection(DB_ROOT, database)
        subscribers = database.get_subscribers(channel_id=channel)
        if user_id not in subscribers:
            subscribers.append(user_id)
            referal_id = database.add_referal(link=link,
                                              channel=channel)[0]
            database.change_profile_balance_referal(user_id=referal_id,
                                                    balance=10,
                                                    balance_outputted=0,
                                                    balance_on_output=0)
            database.add_subscribers(channel_id=channel, subscribers=subscribers)
        close_connection(database)
