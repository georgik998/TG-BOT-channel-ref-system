from aiogram import Bot, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

import project.src.bot.keyboards as kb
from project.src.bot.db.database import DB_ROOT, DataBase, create_connection, close_connection
from project.src.bot.fsm import ReferalState

from datetime import datetime
from math import ceil

referal_router = Router()
database = DataBase()


@referal_router.message(F.text == '👨‍👧‍👦 Реферальная программа', StateFilter(default_state))
async def referal(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)

    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=message.from_user.id, type='referal')
    bank = database.get_bank_balance()[0]
    channels = database.get_channels()
    close_connection(database)

    channel_text = ''
    for i in range(len(channels)):
        channel_text += f"{i + 1}. {channels[i][1]}\n"

    text = f"""
<b>👨‍💻 Личный кабинет</b>

💵 Общая сумма : balance ₽
💸 Стоит на выплате: balance_output ₽
💰 Всего выплачено: all_time_balance ₽
🏦 Общий банк на выплаты: bank ₽

<b>Каналы:</b> <a href="https://telegra.ph/Kanaly-07-29-2">👀 Посмотреть 👀</a>

За каждого приглашенного 🧑 человека в один из каналов вы получаете <b>10</b> рублей.

<b>📤 Реферальная ссылка для приглашения в этот бот:</b> 
{user_info[5]}

За каждого приглашенного 👱 человека в бот вы получите <b>15</b> рублей.

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b>
"""
    text = text.replace('balance', str(user_info[1]), 1).replace('balance_output', str(user_info[2])).replace(
        'all_time_balance', str(user_info[3])).replace('bank', str(bank))

    sms = await message.answer_sticker(
        sticker='CAACAgEAAxkBAAEMBu5mMPayC3c0VPhEsHI0nhTXaq7pyQACDAMAAjXQ4EQn8zNZl8R3bjQE')

    keyboard = kb.create_keyboard_inline([
        [['👨‍👧‍👦 Реферальные ссылки', f'referal_channels:{sms.message_id}']],
        [['💵 Поставить на выплату', f'referal_withdrawal:{sms.message_id}']],
        [['🗂️ Истории выплат', f'referal_history_withdrawal:{sms.message_id}']],
        [['💢 Закрыть ', f'close:{sms.message_id}']]
    ])
    await message.answer(
        text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


# Список каналов
@referal_router.callback_query(F.data[:len('referal_channels')] == 'referal_channels', StateFilter(default_state))
async def referal_channels(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    channels = database.get_channels()
    close_connection(database)
    keyboard = []
    pages = ceil(len(channels) / 5)
    if pages == 0: pages = 1

    for channel in channels[:5]:
        keyboard.append(
            [[channel[1], f'channels:{channel[0]}:{sticker_id}']]
        )
    if pages == 1:
        keyboard.extend([
            [[f'1/{pages}', '_']],
            [['⬅️ Назад', f'back_channels:{sticker_id}']]

        ])
    else:
        keyboard.extend([
            [[f'1/{pages}', '_'], ['➡️', f'move_channels:1:1:{sticker_id}']],
            [['⬅️ Назад', f'back_channels:{sticker_id}']]

        ])
    keyboard = kb.create_keyboard_inline(keyboard)
    await callback.message.edit_text(
        text='👇Выберите канал👇',
        reply_markup=keyboard)


@referal_router.callback_query(F.data[:len('move_channels')] == 'move_channels', StateFilter(default_state))
async def move_channels(callback: CallbackQuery):
    data = callback.data.split(':')
    sticker_id = data[3]
    page = int(data[1]) + int(data[2])

    if page > 0:

        create_connection(DB_ROOT, database)
        channels = database.get_channels()
        close_connection(database)

        pages = ceil(len(channels) / 5)
        channels = channels[5 * (page - 1):5 * pages]

        if channels:
            keyboard = []
            for channel in channels[:5]:
                keyboard.append(
                    [[channel[1], f'channels:{channel[0]}:{sticker_id}']]
                )
            if page == pages:
                keyboard.extend([
                    [['⬅️', f'move_channels:{page}:-1:{sticker_id}'], [f'{page}/{pages}', '_']],
                    [['⬅️ Назад', f'back_channels:{sticker_id}']]

                ])
            elif page == 1 and pages == 1:
                keyboard.extend([
                    [[f'{page}/{pages}', '_']],
                    [['⬅️ Назад', f'back_channels:{sticker_id}']]

                ])
            elif page == 1:
                keyboard.extend([
                    [[f'{page}/{pages}', '_'], ['➡️', f'move_channels:{page}:1:{sticker_id}']],
                    [['⬅️ Назад', f'back_channels:{sticker_id}']]

                ])
            else:

                keyboard.extend([
                    [['⬅️', f'move_channels:{page}:-1:{sticker_id}'], [f'{page}/{pages}', '_'],
                     ['➡️', f'move_channels:{page}:1:{sticker_id}']],
                    [['⬅️ Назад', f'back_channels:{sticker_id}']]

                ])
            keyboard = kb.create_keyboard_inline(keyboard)
            await callback.message.edit_text(
                text='👇Выберите канал👇',
                reply_markup=keyboard)


@referal_router.callback_query(F.data[:len('back_channels_info')] == 'back_channels_info', StateFilter(default_state))
async def back_channels_info(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    channels = database.get_channels()
    close_connection(database)
    keyboard = []
    pages = ceil(len(channels) / 5)

    for channel in channels[:5]:
        keyboard.append(
            [[channel[1], f'channels:{channel[0]}:{sticker_id}']]
        )
    if pages == 1:
        keyboard.extend([
            [[f'1/{pages}', '_']],
            [['⬅️ Назад', f'back_channels:{sticker_id}']]

        ])
    else:
        keyboard.extend([
            [[f'1/{pages}', '_'], ['➡️', f'move_channels:1:1:{sticker_id}']],
            [['⬅️ Назад', f'back_channels:{sticker_id}']]

        ])
    keyboard = kb.create_keyboard_inline(keyboard)
    await callback.message.edit_text(
        text='👇Выберите канал👇',
        reply_markup=keyboard)


@referal_router.callback_query(F.data[:len('back_channels')] == 'back_channels', StateFilter(default_state))
async def back_channels(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    bank = database.get_bank_balance()[0]
    channels = database.get_channels()
    close_connection(database)

    channel_text = ''
    for i in range(len(channels)):
        channel_text += f"{i + 1}. {channels[i][1]}\n"

    text = f"""
<b>👨‍💻 Личный кабинет</b>

💵 Общая сумма : {user_info[1]}₽
💸 Стоит на выплате: {user_info[2]}₽
💰 Всего выплачено: {user_info[3]}₽
🏦 Общий банк на выплаты: {bank}₽

<b>Каналы:</b> <a href="https://telegra.ph/Kanaly-07-29-2">👀 Посмотреть 👀</a>

За каждого приглашенного 🧑 человека в один из каналов вы получаете <b>10</b> рублей.

<b>📤 Реферальная ссылка для приглашения в этот бот:</b> 
{user_info[5]}

За каждого приглашенного 👱 человека в бот вы получите <b>15</b> рублей.

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b>
"""

    keyboard = kb.create_keyboard_inline([
        [['👨‍👧‍👦 Реферальные ссылки', f'referal_channels:{sticker_id}']],
        [['💵 Поставить на выплату', f'referal_withdrawal:{sticker_id}']],
        [['🗂️ Истории выплат', f'referal_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть ', f'close:{sticker_id}']]
    ])
    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


# Канал
@referal_router.callback_query(F.data[:len('channels')] == 'channels', StateFilter(default_state))
async def channel_info(callback: CallbackQuery):

    data = callback.data.split(':')
    channel_id = int(data[1])
    sticker_id = data[2]

    create_connection(DB_ROOT, database)
    channel_info = database.get_channel(channel_id=channel_id)
    channel_user_info = database.get_user_channel_info(user_id=callback.from_user.id, channel=channel_id)
    close_connection(database)

    text = f"""
<b>Канал</b>    

🖼️ <a href="{channel_info[3]}">{channel_info[1]}</a>
📝 <b>Тематика канала:</b>
{channel_info[2]}
📤 <b>Реферальная ссылка:</b>
{channel_user_info[0]}

👨‍👧‍👦 <b>Пригласили в этот канал:</b> {channel_user_info[2]}

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b>  
"""

    keyboard = kb.create_keyboard_inline([
        [['🏠 На главную', f'referal_main:{sticker_id}']],
        [['⬅️ Назад ', f'back_channels_info:{sticker_id}']],
        [['💢 Закрыть ', f'close:{sticker_id}']]
    ])
    await callback.message.edit_text(text=text,
                                     reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


# Канал назад


@referal_router.callback_query(F.data[:len('referal_main_withdrawal')] == 'referal_main_withdrawal',
                               StateFilter(default_state))
async def referal_home(callback: CallbackQuery, bot: Bot):
    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    bank = database.get_bank_balance()[0]
    channels = database.get_channels()
    close_connection(database)

    channel_text = ''
    for i in range(len(channels)):
        channel_text += f"{i + 1}. {channels[i][1]}\n"
    text = f"""
<b>👨‍💻 Личный кабинет</b>

💵 Общая сумма : {user_info[1]}₽
💸 Стоит на выплате: {user_info[2]}₽
💰 Всего выплачено: {user_info[3]}₽
🏦 Общий банк на выплаты: {bank}₽

<b>Каналы:</b> <a href="https://telegra.ph/Kanaly-07-29-2">👀 Посмотреть 👀</a>

За каждого приглашенного 🧑 человека в один из каналов вы получаете <b>10</b> рублей.

<b>📤 Реферальная ссылка для приглашения в этот бот:</b> 
{user_info[5]}

За каждого приглашенного 👱 человека в бот вы получите <b>15</b> рублей.

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b> 
"""

    sticker_id = callback.data.split(':')[1]
    await bot.delete_message(chat_id=callback.from_user.id, message_id=int(sticker_id))

    keyboard = kb.create_keyboard_inline([
        [['👨‍👧‍👦 Реферальные ссылки', f'referal_channels:0']],
        [['💵 Поставить на выплату', f'referal_withdrawal:0']],
        [['🗂️ Истории выплат', f'referal_history_withdrawal:0']],
        [['💢 Закрыть ', f'close:0']]
    ])
    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


# История выплат
def create_history_text(orders, page) -> str:
    TEXT = ''
    number = (page - 1) * 10 + 1
    for item in orders:
        TEXT += f"""
<b>{number}.</b>\t{item[3]} - {item[4]}₽\t{item[2]}
"""
        number += 1
    return TEXT


@referal_router.callback_query(F.data[:len('referal_history_withdrawal')] == 'referal_history_withdrawal',
                               StateFilter(default_state))
async def referal_history_withdrawal(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    orders = database.get_user_orders(user_id=callback.from_user.id, type='referal')
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    close_connection(database)
    orders = orders[::-1]
    text = create_history_text(orders[:10], page=1)
    text = ('🗓 <b>Ваша история по выплатам:</b>\n\n'
            f'<b>Общая сумма выплачена: {user_info[3]}₽</b>\n'
            '') + text
    pages = ceil(len(orders) / 10)
    if pages == 0 or pages == 1:
        keyboard = kb.create_keyboard_inline([
            [[f'1/1', '-']],
            [['💢 Закрыть ', f'close:{sticker_id}']],
            [[' ⬅️ Назад', f'referal_main:{sticker_id}']]
        ])
    else:
        keyboard = kb.create_keyboard_inline([
            [[f'1/{ceil(len(orders) / 10)}', '-'], ['➡️ ', f'referal_pagination:1:1:{sticker_id}']],
            [['💢 Закрыть ', f'close:{sticker_id}']],
            [[' ⬅️ Назад', f'referal_main:{sticker_id}']]
        ])
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard, parse_mode='HTML')


@referal_router.callback_query(F.data[:len('referal_pagination')] == 'referal_pagination', StateFilter(default_state))
async def referal_pagination(callback: CallbackQuery, state: FSMContext):
    data = callback.data.split(':')
    page = int(data[2]) + int(data[1])
    sticker_id = data[3]

    create_connection(DB_ROOT, database)
    orders = database.get_user_orders(user_id=callback.from_user.id, type='referal')
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    close_connection(database)
    orders = orders[::-1]
    text = create_history_text(orders[(page - 1) * 10:page * 10], page=page)

    if text:
        text = ('🗓 <b>Ваша история по выплатам:</b>\n\n'
                f'<b>Общая сумма выплачена: {user_info[3]}₽</b>\n'
                '') + text

        if page == ceil(len(orders) / 10):
            keyboard = kb.create_keyboard_inline([
                [[' ⬅️', f'referal_pagination:-1:{page}:{sticker_id}'], [f'{page}/{ceil(len(orders) / 10)}', '-']],
                [['💢 Закрыть ', f'close:{sticker_id}']],
                [[' ⬅️ Назад', f'referal_main:{sticker_id}']]
            ])
        elif page == 1:
            keyboard = kb.create_keyboard_inline([
                [[f'{page}/{ceil(len(orders) / 10)}', '-'], ['➡️ ', f'referal_pagination:1:{page}:{sticker_id}']],
                [['💢 Закрыть ', f'close:{sticker_id}']],
                [[' ⬅️ Назад', f'referal_main:{sticker_id}']]
            ])
        else:
            keyboard = kb.create_keyboard_inline([
                [[' ⬅️', f'referal_pagination:-1:{page}:{sticker_id}'], [f'{page}/{ceil(len(orders) / 10)}', '-'],
                 ['➡️ ', f'referal_pagination:1:{page}:{sticker_id}']],
                [['💢 Закрыть ', f'close:{sticker_id}']],
                [[' ⬅️ Назад', f'referal_main:{sticker_id}']]
            ])
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard, parse_mode='HTML')


# Поставить на выплату
@referal_router.callback_query(F.data[:len('referal_withdrawal')] == 'referal_withdrawal', StateFilter(default_state))
async def referal_withdrawal(callback: CallbackQuery, state: FSMContext):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    close_connection(database)

    text = f"""
<b>📤 Вывод</b>

Доступно для вывода: {user_info[1]}₽

<b>Напишите сумму которую хотите, поставить на выплату:</b>
"""

    keyboard = kb.create_keyboard_inline([
        [[' ⬅️ Назад', f'referal_main:{sticker_id}']],
        [['💢 Закрыть ', f'close:{sticker_id}']]
    ])

    await state.set_state(ReferalState.sum_to_output)
    await callback.message.edit_text(text=text,
                                     reply_markup=keyboard, parse_mode='HTML')


@referal_router.message(StateFilter(ReferalState.sum_to_output))
async def sum_to_output(message: Message, state: FSMContext):
    sum = message.text
    try:
        sum = int(sum)

        create_connection(DB_ROOT, database)
        user_info = database.get_user_info(user_id=message.from_user.id, type='referal')
        close_connection(database)
        if sum < 500:
            await message.answer('❌ Минимальная сумма для вывода - 500₽',
                                 reply_markup=kb.close)
        elif sum <= user_info[1]:
            text = f"""
<b>🎉 Все прошло удачно!</b>

<b>Вы поставили на вывод:</b> {sum}₽ 

Сумма, которую вы поставили на вывод, изменяется в личном кабинете в разделе 'Стоит на выплате'. 
Счетчик приглашений обновляется, и сумма, заработанная из общей суммы и каналов, пересчитывается и отображается как 'Стоит на выплате'.
"""
            create_connection(DB_ROOT, database)
            database.add_order_referal(user_id=message.from_user.id, sum=sum,
                                       date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
                                       user_name=message.from_user.username)
            database.change_profile_balance_referal(user_id=message.from_user.id,
                                                    balance=-sum,
                                                    balance_on_output=sum,
                                                    balance_outputted=0)
            close_connection(database)
            sms = await message.answer_sticker(
                sticker='CAACAgEAAxkBAAEMCZtmMnTLnf5P31aUdWK8tSRWeXisKQAC-gEAAoyxIER4c3iI53gcxDQE')
            keyboard = kb.create_keyboard_inline([
                [[' ⬅️ Назад', f'referal_main_withdrawal:{sms.message_id}']]
            ])
            await message.answer(text=text, reply_markup=keyboard, parse_mode='HTML')
            await state.set_state(default_state)
        else:
            await message.answer('❌ Недостаточно средств, попробуйте еще раз.',
                                 reply_markup=kb.close)

    except ValueError:
        await message.answer('🤔Неверное значение, попробуйте еще раз.', reply_markup=kb.close)


@referal_router.callback_query(F.data[:len('referal_main')] == 'referal_main', StateFilter(ReferalState.sum_to_output))
async def referal_withdrawal_proccess_back(callback: CallbackQuery, state: FSMContext):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    bank = database.get_bank_balance()[0]
    channels = database.get_channels()
    close_connection(database)

    channel_text = ''
    for i in range(len(channels)):
        channel_text += f"{i + 1}. {channels[i][1]}\n"

    text = f"""
<b>👨‍💻 Личный кабинет</b>

💵 Общая сумма : {user_info[1]}₽
💸 Стоит на выплате: {user_info[2]}₽
💰 Всего выплачено: {user_info[3]}₽
🏦 Общий банк на выплаты: {bank}₽

<b>Каналы:</b> <a href="https://telegra.ph/Kanaly-07-29-2">👀 Посмотреть 👀</a>

За каждого приглашенного 🧑 человека в один из каналов вы получаете <b>10</b> рублей.

<b>📤 Реферальная ссылка для приглашения в этот бот:</b> 
{user_info[5]}

За каждого приглашенного 👱 человека в бот вы получите <b>15</b> рублей.

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b>
"""

    keyboard = kb.create_keyboard_inline([
        [['👨‍👧‍👦 Реферальные ссылки', f'referal_channels:{sticker_id}']],
        [['💵 Поставить на выплату', f'referal_withdrawal:{sticker_id}']],
        [['🗂️ Истории выплат', f'referal_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть ', f'close:{sticker_id}']]
    ])

    await state.set_state(default_state)
    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


@referal_router.callback_query(F.data[:len('referal_main')] == 'referal_main', StateFilter(default_state))
async def referal_withdrawal_proccess_back(callback: CallbackQuery, state: FSMContext):
    sticker_id = callback.data.split(':')[1]

    create_connection(DB_ROOT, database)
    user_info = database.get_user_info(user_id=callback.from_user.id, type='referal')
    bank = database.get_bank_balance()[0]
    channels = database.get_channels()
    close_connection(database)

    channel_text = ''
    for i in range(len(channels)):
        channel_text += f"{i + 1}. {channels[i][1]}\n"

    text = f"""
<b>👨‍💻 Личный кабинет</b>

💵 Общая сумма : {user_info[1]}₽
💸 Стоит на выплате: {user_info[2]}₽
💰 Всего выплачено: {user_info[3]}₽
🏦 Общий банк на выплаты: {bank}₽

<b>Каналы:</b> <a href="https://telegra.ph/Kanaly-07-29-2">👀 Посмотреть 👀</a>

За каждого приглашенного 🧑 человека в один из каналов вы получаете <b>10</b> рублей.

<b>📤 Реферальная ссылка для приглашения в этот бот:</b> 
{user_info[5]}

За каждого приглашенного 👱 человека в бот вы получите <b>15</b> рублей.

<b>Важно ❌ : За накрутку через сервисы накрутки или подобные, ваш аккаунт будет заблокирован навсегда.</b> 
"""

    keyboard = kb.create_keyboard_inline([
        [['👨‍👧‍👦 Реферальные ссылки', f'referal_channels:{sticker_id}']],
        [['💵 Поставить на выплату', f'referal_withdrawal:{sticker_id}']],
        [['🗂️ Истории выплат', f'referal_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть ', f'close:{sticker_id}']]
    ])

    await state.set_state(default_state)
    await callback.message.edit_text(
        text=text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
