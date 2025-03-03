from aiogram import Bot, Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, CallbackQuery

from datetime import datetime
from math import ceil
import project.src.bot.keyboards as kb
from project.src.bot.db.database import DB_ROOT, DataBase, create_connection, close_connection
from project.src.bot.fsm import *

video_router = Router()
database = DataBase()


@video_router.message(F.text == '🤩 Просмотры видео', StateFilter(default_state))
async def video(message: Message, bot: Bot):
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    create_connection(DB_ROOT, database)
    text = database.get_text(text='video')
    close_connection(database)


    sticker_id = await message.answer_sticker(
        sticker='CAACAgEAAxkBAAEMB41mMTrptszvuCJ7rWsbYLAHYdM7NwACtAIAAv1TMUdi6Si4KNBSqzQE')
    sticker_id = sticker_id.message_id
    keyboard = kb.create_keyboard_inline([
        [['💰 Поставить на выплату ', f'video_withdrawal:{sticker_id}']],
        [['🗓️ История выплат', f'video_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть', f'close:{sticker_id}']]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


@video_router.callback_query(F.data[:len('video_withdrawal')] == 'video_withdrawal', StateFilter(default_state))
async def video_withdrawal(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]
    keyboard = kb.create_keyboard_inline([
        [['TikTok', f'video_platform:TikTok:{sticker_id}']],
        [['YouTube Shorts', f'video_platform:YouTube Shorts:{sticker_id}']],
        [['Insta Reels', f'video_platform:Insta Reels:{sticker_id}']],
        [[' ⬅️ Назад', f'video_home:{sticker_id}']]
    ])
    await callback.message.edit_text(
        text='🤩 Выберите, на какой из видео-платформ вы набрали просмотры.',
        reply_markup=keyboard
    )


def create_history_text(orders, info, bank, page) -> str:
    TEXT = ('🗓 <b>История выплат</b>\n'
            '\n'
            f'💰 <b>Всего выплачено:</b> {info}₽\n'
            f'🏦 <b>Общий банк:</b> {bank}₽\n')

    text = """
<b>number. date
url
Статус: status
Выплачено: price₽</b>
"""
    number = (page - 1) * 7 + 1
    for item in orders:
        TEXT += text.replace('number', str(number)).replace('date', item[2]).replace('url', item[7]).replace('status',
                                                                                                             item[
                                                                                                                 1]).replace(
            'price', str(item[3]))
        number += 1
    return TEXT


@video_router.callback_query(F.data[:len('video_history_withdrawal')] == 'video_history_withdrawal',
                             StateFilter(default_state))
async def video_history_withdrawal(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]
    create_connection(DB_ROOT, database)
    orders = database.get_user_orders(user_id=callback.from_user.id, type='video')
    info = database.get_user_info(user_id=callback.from_user.id, type='video')[1]
    bank = database.get_bank_balance()[0]
    close_connection(database)
    orders = orders[::-1]
    text = create_history_text(orders[:7], info, bank=bank, page=1)

    pages = ceil(len(orders) / 7)
    if pages == 0 or pages == 1:
        keyboard = kb.create_keyboard_inline([
            [[f'1/1', '-']],
            [['💢 Закрыть ', f'close:{sticker_id}']],
            [[' ⬅️ Назад', f'video_home:{sticker_id}']]
        ])
    else:
        keyboard = kb.create_keyboard_inline([
            [[f'1/{ceil(len(orders) / 7)}', '-'], ['➡️ ', f'video_pagination:1:1:{sticker_id}']],
            [['💢 Закрыть ', f'close:{sticker_id}']],
            [[' ⬅️ Назад', f'video_home:{sticker_id}']]
        ])
    await callback.message.edit_text(text=text,
                                     reply_markup=keyboard,
                                     parse_mode='HTML',
                                     disable_web_page_preview=True
                                     )


@video_router.callback_query(F.data[:len('video_pagination')] == 'video_pagination', StateFilter(default_state))
async def video_history_swipe(callback: CallbackQuery):
    data = callback.data.split(':')
    sticker_id = data[3]
    page = int(data[2]) + int(data[1])
    if page >= 1:
        create_connection(DB_ROOT, database)
        orders = database.get_user_orders(user_id=callback.from_user.id, type='video')
        info = database.get_user_info(user_id=callback.from_user.id, type='video')[1]
        bank = database.get_bank_balance()[0]
        close_connection(database)
        orders = orders[::-1]

        if orders:
            text = create_history_text(orders[(page - 1) * 7:page * 7], info, bank, page)
            if page == ceil(len(orders) / 7):
                keyboard = kb.create_keyboard_inline([
                    [[' ⬅️', f'video_pagination:-1:{page}:{sticker_id}'], [f'{page}/{ceil(len(orders) / 7)}', '-']],
                    [['💢 Закрыть ', f'close:{sticker_id}']],
                    [[' ⬅️ Назад', f'video_home:{sticker_id}']]
                ])
            elif page == 1:
                keyboard = kb.create_keyboard_inline([
                    [[f'{page}/{ceil(len(orders) / 7)}', '-'], ['➡️ ', f'video_pagination:1:{page}:{sticker_id}']],
                    [['💢 Закрыть ', f'close:{sticker_id}']],
                    [[' ⬅️ Назад', f'video_home:{sticker_id}']]
                ])
            else:
                keyboard = kb.create_keyboard_inline([
                    [[' ⬅️', f'video_pagination:-1:{page}:{sticker_id}'], [f'{page}/{ceil(len(orders) / 7)}', '-'],
                     ['➡️ ', f'video_pagination:1:{page}:{sticker_id}']],
                    [['💢 Закрыть ', f'close:{sticker_id}']],
                    [[' ⬅️ Назад', f'video_home:{sticker_id}']]
                ])
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML', disable_web_page_preview=True)


# Platform
@video_router.callback_query(F.data[:len('video_home')] == 'video_home', StateFilter(default_state))
async def platform_back(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]
    create_connection(DB_ROOT, database)
    text = database.get_text(text='video')
    close_connection(database)


    keyboard = kb.create_keyboard_inline([
        [['💰 Поставить на выплату ', f'video_withdrawal:{sticker_id}']],
        [['🗓️ История выплат', f'video_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть', f'close:{sticker_id}']]
    ])
    await callback.message.edit_text(
        text=text,
        reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)


@video_router.callback_query(F.data[:len('video_platform')] == 'video_platform', StateFilter(default_state))
async def platform_select(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VideoState.video_url_question)
    data = callback.data.split(':')
    keyboard = kb.create_keyboard_inline([
        [[' ⬅️ Назад', f'video_withdrawal_back_url:{data[2]}']]
    ])
    message = await callback.message.edit_text(text='Пришлите ссылку на видео:', reply_markup=keyboard)

    await state.update_data({'message_id': message.message_id,
                             'platform': data[1],
                             'sticker_id': data[2]})


@video_router.callback_query(F.data[:len('video_withdrawal_back_url')] == 'video_withdrawal_back_url',
                             StateFilter(VideoState.video_url_question))
async def video_withdrawal_back_url(callback: CallbackQuery, state: FSMContext):
    await state.set_state(default_state)
    cash = await state.get_data()
    sticker_id = cash['sticker_id']
    keyboard = kb.create_keyboard_inline([
        [['TikTok', f'video_platform:TikTok:{sticker_id}']],
        [['YouTube Shorts', f'video_platform:YouTube Shorts:{sticker_id}']],
        [['Insta Reels', f'video_platform:Insta Reels:{sticker_id}']],
        [[' ⬅️ Назад', f'video_home:{sticker_id}']]
    ])
    await callback.message.edit_text(
        text='🤩 Выберите, на какой из видео-платформ вы набрали просмотры.',
        reply_markup=keyboard
    )


@video_router.message(StateFilter(VideoState.video_url_question))
async def platform_select(message: Message, bot: Bot, state: FSMContext):


    cash = await state.get_data()
    cash['url'] = message.text
    create_connection(DB_ROOT, database)
    res = database.query_execute(f"""SELECT * FROM videos WHERE url = "{cash['url']}" """)
    close_connection(database)

    message_id = cash['message_id']
    sticker_id = cash['sticker_id']

    if not res:
        keyboard = kb.create_keyboard_inline([
            [[' ⬅️ Назад', f'video_views_back:{sticker_id}']]
        ])
        await state.set_state(VideoState.views_question)
        await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

        message = await message.answer(text='Напишите сколько просмотров у вашего видео:', reply_markup=keyboard)
        cash['message_id'] = message.message_id
        await state.update_data(cash)
    else:
        keyboard = kb.create_keyboard_inline([
            [[' ⬅️ Назад', f'video_withdrawal_back_url:{sticker_id}']]
        ])

        await message.answer("""Это видео уже ранее подавалось на выплату.""", reply_markup=keyboard)



@video_router.callback_query(StateFilter(VideoState.views_question),
                             F.data[:len('video_views_back')] == 'video_views_back')
async def video_views_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VideoState.video_url_question)
    sticker_id = callback.data.split(':')[1]
    keyboard = kb.create_keyboard_inline([
        [[' ⬅️ Назад', f'video_withdrawal_back_url:{sticker_id}']]
    ])
    await callback.message.edit_text(text='Пришлите ссылку на видео:', reply_markup=keyboard)


@video_router.message(StateFilter(VideoState.views_question))
async def views_question(message: Message, bot: Bot, state: FSMContext):
    views = message.text
    cash = await state.get_data()
    if all(char.isdigit() for char in views):
        if int(views) >= 8000:
            platform = cash['platform']
            url = cash['url']
            message_id = cash['message_id']
            sticker_id = cash['sticker_id']
            await state.set_state(VideoState.user_name_question)

            text = """
<b>Видео платформу вы выбрали:</b> platform

<b>Просмотров набрал ваш видео ролик:</b> views

<b>Видео:</b>
url

<b>Внимание:</b> Вы завершаете оформление заявки на выплату. Если вы предоставили неверные данные, например, значительно завышенное количество просмотров (например, указали 5000 просмотров, вместо фактических 100 просмотров), или загрузили запрещенное видео 18+  для нарушения работы нашего бота,
пожалуйста, нажмите кнопку ❌ Закрыть, чтобы избежать блокировки в нашем боте. После отправки вашего ника видео будет проверено.
Если вы допустили ошибку в информации, рекомендуем вернуться кнопкой ⬅️ Назад и указать корректные данные. Если указана неверная видео-платформа, это не критично, главное, чтобы количество просмотров не было существенно завышено.
Так же если у вас несколько роликов, вы можете поставить сразу после оформления этой  заявки на выплату , другой видеоролик

<b>Напишите, пожалуйста свой ник Telegram для контакта:</b>
    """
            text = text.replace('platform', platform).replace('views', views).replace('url', url)

            await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
            keyboard = kb.create_keyboard_inline([
                [['❌ Закрыть', f'close:{sticker_id}']],
                [['⬅️ Назад ', f'video_home:{sticker_id}']]
            ])
            message = await message.answer(
                text=text,
                reply_markup=keyboard,
                disable_web_page_preview=True,
                parse_mode='HTML'
            )
            cash['views'] = views
            cash['message_id'] = message.message_id
            await state.update_data(cash)
        else:
            await state.clear()
            keyboard = kb.create_keyboard_inline([
                [['⬅️ На главную', f'views_low_back']]
            ])
            await message.answer('<b>На вашем видео, должно быть минимум 8000 просмотров</b>', reply_markup=keyboard,
                                 parse_mode='HTML')
    else:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await message.answer('Неверные данные. Попробуйте еще раз')
    await state.update_data(cash)


@video_router.callback_query(StateFilter(VideoState.user_name_question), F.data[:len('video_home')] == 'video_home')
async def user_name_question_back(callback: CallbackQuery, state: FSMContext):
    await state.set_state(VideoState.views_question)
    keyboard = kb.create_keyboard_inline([
        [[' ⬅️ Назад', f'video_views_back:{callback.data.split(":")[1]}']]
    ])
    await callback.message.edit_text(text='Напишите сколько просмотров у вашего видео:',
                                     reply_markup=keyboard)


# User_name
@video_router.message(StateFilter(VideoState.user_name_question))
async def user_name_question(message: Message, bot: Bot, state: FSMContext):
    await state.set_state(default_state)
    cash = await state.get_data()
    message_id = cash['message_id']
    sticker_id = cash['sticker_id']
    create_connection(DB_ROOT, database)
    database.add_order_video(date=datetime.now().strftime('%d.%m.%y').rstrip('0'),
                             user_id=message.from_user.id,
                             user_name=message.text,
                             platform=cash['platform'],
                             url=cash['url'],
                             views=cash['views'])
    database.query_execute(f"""INSERT INTO videos (url) VALUES("{cash['url']}")""")
    close_connection(database)

    await bot.delete_message(chat_id=message.chat.id, message_id=message_id)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    keyboard = kb.create_keyboard_inline([
        [['❌ Закрыть', f'close:{sticker_id}']],
        [['⬅️ Назад ', f'video_home:{sticker_id}']]
    ])
    await message.answer(
        text='<b>Ваш запрос на выплату, будет обработан.\nСледите за статусом заявки, в 🗓️ Историях выплат.</b>',
        reply_markup=keyboard,
        parse_mode='HTML'
    )

    await state.clear()
    await state.set_state(default_state)


@video_router.callback_query(F.data[:len('back')] == 'back', StateFilter(VideoState.user_name_question))
async def back_user_name_wait(callback: CallbackQuery):
    sticker_id = callback.data.split(':')[1]
    keyboard = kb.create_keyboard_inline([
        [['TikTok', f'video_platform:TikTok:{sticker_id}']],
        [['YouTube Shorts', f'video_platform:YouTube Shorts:{sticker_id}']],
        [['Insta Reels', f'video_platform:Insta Reels:{sticker_id}']],
        [[' ⬅️ Назад', f'video_home:{sticker_id}']]
    ])
    await callback.message.edit_text(
        text='🤩 Выберите, на какой из видео-платформ вы набрали просмотры.',
        reply_markup=keyboard
    )


@video_router.callback_query(F.data == 'views_low_back', StateFilter(default_state))
async def views_low_back(callback: CallbackQuery):
    await callback.message.delete()
    create_connection(DB_ROOT, database)
    text = database.get_text(text='video')
    close_connection(database)


    sticker_id = await callback.message.answer_sticker(
        sticker='CAACAgEAAxkBAAEMB41mMTrptszvuCJ7rWsbYLAHYdM7NwACtAIAAv1TMUdi6Si4KNBSqzQE')
    sticker_id = sticker_id.message_id
    keyboard = kb.create_keyboard_inline([
        [['💰 Поставить на выплату ', f'video_withdrawal:{sticker_id}']],
        [['🗓️ История выплат', f'video_history_withdrawal:{sticker_id}']],
        [['💢 Закрыть', f'close:{sticker_id}']]
    ])
    await callback.message.answer(text, reply_markup=keyboard, parse_mode='HTML', disable_web_page_preview=True)
