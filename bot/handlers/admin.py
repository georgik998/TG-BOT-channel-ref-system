from aiogram import Bot, Router, F
from aiogram.filters import StateFilter, Filter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from datetime import datetime

from project.src.bot.db.database import DB_ROOT, DataBase, ChatHistory, create_connection, close_connection
from project.src.bot.fsm import AdminState
import project.src.bot.keyboards as kb

admin_router = Router()
database = DataBase()
chat_database = ChatHistory()

TEXT_CASH = ''


class Admin(Filter):

    async def __call__(self, message: Message) -> bool:
        create_connection(DB_ROOT, database)
        admins = database.get_admins()
        close_connection(database)

        return (message.from_user.id,) in admins


@admin_router.message(Admin(), F.text == '/admin', StateFilter(default_state))
async def admin(message: Message):
    await message.answer('Вы админ:\n'
                         '/referal_order - обработка заявки на выплату реферал\n'
                         '/video_order - обработка заявки на выплату видео\n'
                         '/change_bank - изменить банк на выплаты\n'
                         '/block_user - забанить/разбанить юзера\n'
                         '/user_history - просмотр истории юзера\n'
                         '/change_text_start - изменить текст\n'
                         '/change_text_video - изменить текст просмотры видео\n'
                         '/change_admin - добавить/удалить админа\n'
                         '/chat - диалог с пользователем\n'
                         '/download - скачать файлы с бд\n'
                         '/users - кол-во человек нажавших кнопку start\n'
                         '/users_stat - статистика посещений\n'
                         '/manage_channel - добавление/удаление каналов\n'
                         '/send_message - Отправка сообщения всем юзерам\n'
                         '/statistic - статистка по выплатам')


# ================================ /referal_order ===============================
@admin_router.message(Admin(), F.text == '/referal_order', StateFilter(default_state))
async def referal_order(message: Message, state: FSMContext):
    await state.set_state(AdminState.order_id_referal)
    await message.answer('Введите id заявки которую хотите обработать.', reply_markup=kb.referal_order)


@admin_router.message(Admin(), StateFilter(AdminState.order_id_referal))
async def referal_order_select(message: Message, state: FSMContext):
    try:
        order_id = int(message.text)
        await message.delete()
        cash = await state.get_data()
        cash['order_id_referal'] = order_id

        create_connection(DB_ROOT, database)
        order = database.get_order(id=order_id, type='referal')
        close_connection(database)

        if order:
            text = f"""
<b>Заявка</b> {order_id}
🔹<b>Юзер</b> - {order[6]}
🔹<b>Дата</b> - {order[3]}
🔹<b>Сумма к выплате</b> - {order[4]}₽
🔹<b>Статус</b> - {order[2]}
"""
            cash['price'] = order[4]
            cash['order_user_id'] = order[1]
            virgin = order[5]
            if virgin:
                await message.answer(text, reply_markup=kb.close, parse_mode='HTML')
            else:
                await message.answer(text, reply_markup=kb.order_filter_referal, parse_mode='HTML')
            await state.set_state(default_state)
        else:
            await message.answer('⚠️Заявки с таким id не сущетсвует, попробуйте еще раз.', reply_markup=kb.close)

        await state.update_data(cash)

    except ValueError:
        await message.answer('⚠️Неверный формат, попробуйте снова', reply_markup=kb.close)


@admin_router.callback_query(Admin(), F.data[:len('order_filter_referal')] == 'order_filter_referal',
                             StateFilter(default_state))
async def referal_order_select(callback: CallbackQuery, state: FSMContext):
    cash = await state.get_data()
    status = callback.data.split(':')[1]
    cash['status'] = status

    message = await callback.message.edit_text('Вы уверены что хотите поставить заявке\n'
                                               f'{status}\n'
                                               'Напишите 1, если уверны\n'
                                               'Напишите 0, если хотите отменить')
    cash['message_id'] = message.message_id
    await state.update_data(cash)
    await state.set_state(AdminState.status_confirm_referal)


@admin_router.message(Admin(), StateFilter(AdminState.status_confirm_referal))
async def status_confirm(message: Message, bot: Bot, state: FSMContext):
    cash = await state.get_data()
    await message.delete()
    if message.text == '1':
        create_connection(DB_ROOT, database)
        database.change_order_status(id=cash['order_id_referal'],
                                     type='referal',
                                     status=cash['status'])
        if cash['status'] == '✅ Выплачено':
            database.change_bank_balance(money=-cash['price'])
            database.change_profile_balance_referal(user_id=cash['order_user_id'],
                                                    balance=0,
                                                    balance_on_output=-cash['price'],
                                                    balance_outputted=cash['price']
                                                    )
            await state.clear()
            await state.set_state(default_state)
        elif cash['status'] == '❌ Отклонено модерацией':

            database.change_profile_balance_referal(user_id=cash['order_user_id'],
                                                    balance=0,
                                                    balance_on_output=-cash['price'],
                                                    balance_outputted=0
                                                    )
            await state.set_state(AdminState.reject_order)
            await message.answer('Пришлите сообщение которое увидит юзер')
        else:

            await state.clear()
            await state.set_state(default_state)
        close_connection(database)

        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=cash['message_id'],
                                    text=f'Статус заявки успешно изменен на {cash["status"]}'
                                    )



    elif message.text == '0':
        create_connection(DB_ROOT, database)
        order = database.get_order(id=cash['order_id_referal'], type='referal')
        close_connection(database)
        text = f"""
<b>Заявка</b> {cash['order_id_referal']}
🔹<b>Юзер</b> - {order[6]}
🔹<b>Дата</b> - {order[3]}
🔹<b>Сумма к выплате</b> - {order[4]}₽
🔹<b>Статус</b> - {order[2]}
        """
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=cash['message_id'],
                                    text=text,
                                    reply_markup=kb.order_filter_referal, parse_mode='HTML'
                                    )
        await state.set_state(default_state)
    else:
        await message.answer(text='⚠️Неверный формат, попробуйте еще раз')
    await state.update_data(cash)


# ================================ /video_order ===============================
@admin_router.message(Admin(), F.text == '/video_order', StateFilter(default_state))
async def video_order(message: Message, state: FSMContext):
    await state.set_state(AdminState.order_id_video)
    await message.answer('Введите id заявки которую хотите обработать.', reply_markup=kb.referal_order)


@admin_router.message(Admin(), StateFilter(AdminState.order_id_video))
async def videol_order_select(message: Message, state: FSMContext):
    try:
        order_id = int(message.text)
        await message.delete()
        cash = await state.get_data()
        cash['order_id_video'] = order_id

        create_connection(DB_ROOT, database)
        order = database.get_order(id=order_id, type='video')
        close_connection(database)

        if order:

            text = f"""
Заявка {order[0]}
🔹Юзер - {order[5]}
🔹Дата - {order[2]}
🔹Просмотры - {order[8]}
🔹Платформа - {order[6]}
🔹Видео - 
{order[7]}
🔹 Cумма к выпалате - {order[3]}
🔹Статус - {order[1]}
"""

            cash['order_user_id'] = order[4]

            if order[9]:
                await message.answer(text, reply_markup=kb.close, parse_mode='HTML', disable_web_page_preview=True)

            else:
                await message.answer(text, reply_markup=kb.order_filter_video, parse_mode='HTML',
                                     disable_web_page_preview=True)

            await state.set_state(default_state)
        else:
            await message.answer('⚠️Заявки с таким id не сущетсвует, попробуйте еще раз.', reply_markup=kb.close)

        await state.update_data(cash)

    except ValueError:
        await message.answer('⚠️Неверный формат, попробуйте снова', reply_markup=kb.close)


@admin_router.callback_query(Admin(), F.data[:len('order_filter_video')] == 'order_filter_video',
                             StateFilter(default_state))
async def referal_order_select(callback: CallbackQuery, state: FSMContext):
    cash = await state.get_data()
    status = callback.data.split(':')[1]
    cash['status'] = status
    if status == '❌ Отклонено модерацией':
        message = await callback.message.edit_text('Вы уверены что хотите поставить заявке\n'
                                                   f'{status}\n'
                                                   'Напишите 1, если уверны\n'
                                                   'Напишите 0, если хотите отменить')
        cash['message_id'] = message.message_id

        await state.set_state(AdminState.status_confirm_video)
    elif status == '💸 Ожидает выплаты':
        message = await callback.message.edit_text('Вы уверены что хотите поставить заявке\n'
                                                   f'{status}\n'
                                                   'Напишите 1, если уверны\n'
                                                   'Напишите 0, если хотите отменить')
        cash['message_id'] = message.message_id

        await state.set_state(AdminState.status_confirm_video)
    else:
        message = await callback.message.edit_text('Напишите сумму которую юзер получит за выплату.')
        cash['message_id'] = message.message_id

        await state.set_state(AdminState.pay_for_video)

    await state.update_data(cash)


@admin_router.message(Admin(), StateFilter(AdminState.pay_for_video))
async def video_pay_for_video(message: Message, state: FSMContext):
    try:
        price = int(message.text)

        cash = await state.get_data()
        status = cash['status']
        cash['price'] = price

        message = await message.answer('Вы уверены что хотите поставить заявке\n'
                                       f'{status}\n'
                                       f'И выплату в размере\n'
                                       f'{price}₽\n'
                                       'Напишите 1, если уверны\n'
                                       'Напишите 0, если хотите отменить')
        cash['message_id'] = message.message_id
        await state.update_data(cash)
        await state.set_state(AdminState.status_confirm_video)
    except ValueError:
        await message.answer('⚠️Неверный формат, попробуйте снова', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.status_confirm_video))
async def status_confirm(message: Message, bot: Bot, state: FSMContext):
    cash = await state.get_data()
    await message.delete()
    if message.text == '1':
        create_connection(DB_ROOT, database)
        database.change_order_status(id=cash['order_id_video'],
                                     type='video',
                                     status=cash['status'])
        if cash['status'] == '✅ Выплачено':
            database.change_bank_balance(money=-cash['price'])
            database.change_profile_balance_video(user_id=cash['order_user_id'], money=cash['price'])
            database.change_video_order_price(order_id=cash['order_id_video'], price=cash['price'])
            await state.clear()
            await state.set_state(default_state)
        elif cash['status'] == '❌ Отклонено модерацией':
            await state.set_state(AdminState.reject_order)
            await message.answer('Введите сообщение причины отмены')
        else:
            await state.clear()
            await state.set_state(default_state)
        close_connection(database)

        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=cash['message_id'],
                                    text=f'Статус заявки успешно изменен на {cash["status"]}'
                                    )



    elif message.text == '0':
        create_connection(DB_ROOT, database)
        order = database.get_order(id=cash['order_id_video'], type='video')
        close_connection(database)
        text = f"""
Заявка {order[0]}
🔹Юзер - {order[5]}
🔹Дата - {order[2]}
🔹Просмотры - {order[8]}
🔹Платформа - {order[6]}
🔹Видео - 
{order[7]}
🔹 Cумма к выпалате - {order[3]}
🔹Статус - {order[1]}
"""
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=cash['message_id'],
                                    text=text,
                                    reply_markup=kb.order_filter_video, parse_mode='HTML',
                                    disable_web_page_preview=True
                                    )
        await state.set_state(default_state)
    else:
        await message.answer(text='Неверный формат, попробуйте еще раз')
    await state.update_data(cash)


# ================================ /regect_order ===============================
@admin_router.message(Admin(), StateFilter(AdminState.reject_order))
async def reject_order_referal(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    cash = await state.get_data()
    await bot.send_message(chat_id=cash['order_user_id'],
                           text=text)
    await state.set_state(default_state)
    await state.clear()
    await message.answer('Сообщение было отправлено')


# ================================ /change_bank ===============================
@admin_router.message(Admin(), F.text == '/change_bank', StateFilter(default_state))
async def change_bank(message: Message):
    create_connection(DB_ROOT, database)
    bank = database.get_bank_balance()[0]
    close_connection(database)

    text = ('Текущий баланса банка выплат\n'
            f'{bank}₽')
    await message.answer(text, reply_markup=kb.change_bank)


@admin_router.callback_query(Admin(), F.data == 'bank_change_balance', StateFilter(default_state))
async def bank_change_balance(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.bank_balance_wait)
    await callback.message.edit_text('Пришлите сумму которую хотите <b><i>прибавить</i></b> к балансу банка',
                                     parse_mode='HTML')


@admin_router.message(Admin(), StateFilter(AdminState.bank_balance_wait))
async def change_bank_balance(message: Message, state: FSMContext):
    try:
        price = int(message.text)

        create_connection(DB_ROOT, database)
        database.change_bank_balance(money=price)
        close_connection(database)

        await state.set_state(default_state)
        await message.answer('Баланс банка был изменен на\n'
                             f'{price}₽')
    except ValueError:
        await message.answer('Неверный формат, попробуйте снова', reply_markup=kb.close)


# /block_user

@admin_router.message(Admin(), F.text == '/block_user', StateFilter(default_state))
async def block_user(message: Message):
    await message.answer('Выберите дейтсвие', reply_markup=kb.block_user)


@admin_router.callback_query(Admin(), F.data == 'block', StateFilter(default_state))
async def block(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.block)
    await callback.message.edit_text('Напиште id юзера которого хотите забанить.')


@admin_router.message(Admin(), StateFilter(AdminState.block))
async def block_process(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)

        create_connection(DB_ROOT, database)
        database.block_user(user_id=user_id)
        close_connection(database)
        await state.set_state(default_state)
        await message.answer(f'Юзер {user_id} был заблокирован в боте.')

    except ValueError:
        await message.answer('Неверный id, попробуйте снова', reply_markup=kb.close)


@admin_router.callback_query(Admin(), F.data == 'unblock', StateFilter(default_state))
async def unblock(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.unblock)
    await callback.message.edit_text('Напиште id юзера которого хотите разбанить.')


@admin_router.message(Admin(), StateFilter(AdminState.unblock))
async def unblock_process(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)

        create_connection(DB_ROOT, database)
        database.unblock_user(user_id=user_id)
        close_connection(database)

        await state.set_state(default_state)

        await message.answer(f'Юзер {user_id} был разблокирован в боте.')

    except ValueError:
        await message.answer('Неверный id, попробуйте снова', reply_markup=kb.close)


# ================================================================
# /change_text
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/change_text_video')
async def change_text(message: Message, state: FSMContext):
    await state.set_state(AdminState.change_text_video)
    await message.answer('Пришлите новый текст для команды Просмотры видео', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.change_text_video))
async def give_text_send_to_confirm(message: Message, state: FSMContext):
    text = message.text
    cash = await state.get_data()
    cash['text'] = text
    await state.update_data(cash)
    await state.set_state(default_state)
    await message.answer(text)
    await message.answer('Вы уверены что хотите поставить такой текст?', reply_markup=kb.create_keyboard_inline([
        [['Да', 'text_confirm_video:1'], ['Нет', 'text_confirm_video:0']],
        [['💢 Закрыть', 'close']]
    ]))


@admin_router.callback_query(Admin(), F.data[:len('text_confirm_video')] == 'text_confirm_video')
async def text_confirm(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(':')[1]
    print('21312')
    cash = await state.get_data()
    if answer == '1':

        text = cash['text']

        create_connection(DB_ROOT, database)
        database.change_text(type='video', text=text)
        close_connection(database)

        await callback.message.edit_text('Текст успешно изменен.')
        await state.update_data(cash)
    else:
        await callback.message.edit_text('Действие было отменено.')


@admin_router.message(Admin(), StateFilter(default_state), F.text == '/change_text_start')
async def change_text(message: Message, state: FSMContext):
    await state.set_state(AdminState.change_text)
    await message.answer('Пришлите новый текст для команды start', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.change_text))
async def give_text_send_to_confirm(message: Message, state: FSMContext):
    text = message.text
    cash = await state.get_data()
    cash['text'] = text
    await state.update_data(cash)
    await state.set_state(default_state)
    await message.answer(text)
    await message.answer('Вы уверены что хотите поставить такой текст?', reply_markup=kb.text_confirm)


@admin_router.callback_query(Admin(), F.data[:len('text_confirm')] == 'text_confirm')
async def text_confirm(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(':')[1]
    cash = await state.get_data()
    if answer == '1':

        cash = await state.get_data()
        text = cash['text']

        create_connection(DB_ROOT, database)
        database.change_text(type='start', text=text)
        close_connection(database)

        await callback.message.edit_text('Текст успешно изменен.')
        await state.update_data(cash)
    else:
        await callback.message.edit_text('Действие было отменено.')


# ================================================================   / user history
@admin_router.message(Admin(), F.text == '/user_history')
async def user_history(message: Message, state: FSMContext):
    await state.set_state(AdminState.user_info_id)
    await message.answer('Напишите id юзера, чью историю хотите просмотреть', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.user_info_id))
async def give_user_id_for_history(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)

        await state.update_data({
            'user_id': user_id
        })

        await state.set_state(default_state)
        await message.answer('Выберите тип истории', reply_markup=kb.user_history)

    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова.', reply_markup=kb.close)


def create_history_text_referal(orders, page) -> str:
    TEXT = ''
    number = (page - 1) * 10 + 1
    for item in orders:
        TEXT += f"""
<b>{number}.</b>\t{item[3]} - {item[4]}₽\t{item[2]}
"""
        number += 1
    return TEXT


def create_history_text_video(orders, info, bank, page, user_id) -> str:
    TEXT = (f'🗓<b>История выплат {user_id}</b>\n'
            '\n'
            f'💰<b>Всего выплачено:</b> {info}\n'
            f'🏦<b>Общий банк:</b> {bank}\n')

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


@admin_router.callback_query(Admin(), F.data[:len('admin_select_user_history')] == 'admin_select_user_history',
                             StateFilter(default_state))
async def admin_select_user_history(callback: CallbackQuery):
    await callback.message.edit_text('Выберите тип истории', reply_markup=kb.user_history)


@admin_router.callback_query(Admin(), F.data[:len('user_history')] == 'user_history', StateFilter(default_state))
async def user_history(callback: CallbackQuery, state: FSMContext):
    answer = callback.data.split(':')[1]

    cash = await state.get_data()
    user_id = cash['user_id']

    if answer == 'referal':

        create_connection(DB_ROOT, database)
        orders = database.get_user_orders(user_id=user_id, type='referal')
        user_info = database.get_user_info(user_id=user_id, type='referal')
        close_connection(database)

        if user_info:
            text = create_history_text_referal(orders[:10], page=1)
            text = (f'🗓 <b>История по выплатама {user_id}</b>\n\n'
                    f'<b>Общая сумма выплачена: {user_info[3]}</b>\n'
                    '') + text
            keyboard = kb.create_keyboard_inline([
                [[' ⬅️', 'admin_referal_user_history:-1:1'], ['➡️ ', 'admin_referal_user_history:1:1']],
                [['НАЗАД', f'admin_select_user_history:{user_id}']],
                [['💢 Закрыть', 'close']]
            ])
            await callback.message.edit_text(
                text=text,
                reply_markup=keyboard, parse_mode='HTML')
        else:
            text = 'Такого юзера нет.'
            await callback.message.edit_text(
                text=text)
    else:

        create_connection(DB_ROOT, database)
        orders = database.get_user_orders(user_id=user_id, type='video')
        info = database.get_user_info(user_id=user_id, type='video')[1]
        bank = database.get_bank_balance()[0]
        close_connection(database)

        text = create_history_text_video(orders[:7], info, bank=bank, page=1, user_id=user_id)
        keyboard = kb.create_keyboard_inline([
            [[' ⬅️', 'admin_video_user_history:-1:1'], ['➡️ ', 'admin_video_user_history:1:1']],
            [['НАЗАД', f'admin_select_user_history:{user_id}']],
            [['💢 Закрыть', 'close']]
        ])
        await callback.message.edit_text(text=text,
                                         reply_markup=keyboard,
                                         parse_mode='HTML',
                                         disable_web_page_preview=True
                                         )

    await state.update_data(cash)


@admin_router.callback_query(Admin(), F.data[:len('admin_referal_user_history')] == 'admin_referal_user_history',
                             StateFilter(default_state))
async def user_history_admin(callback: CallbackQuery, state: FSMContext):
    cash = await state.get_data()
    user_id = cash['user_id']
    page = int(callback.data.split(':')[2]) + int(callback.data.split(':')[1])
    create_connection(DB_ROOT, database)
    orders = database.get_user_orders(user_id=user_id, type='referal')
    user_info = database.get_user_info(user_id=user_id, type='referal')
    close_connection(database)

    text = create_history_text_referal(orders[(page - 1) * 10:page * 10], page=page)

    if text:
        text = (f'🗓 <b>История по выплатама {user_id}</b>\n\n'
                f'<b>Общая сумма выплачена: {user_info[3]}</b>\n'
                '') + text

        keyboard = kb.create_keyboard_inline([
            [[' ⬅️', f'admin_referal_user_history:-1:{page}'], ['➡️ ', f'admin_referal_user_history:1:{page}']],
            [['НАЗАД', f'admin_select_user_history:{user_id}']],
            [['💢 Закрыть', 'close']]
        ])

        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard, parse_mode='HTML')


@admin_router.callback_query(Admin(), F.data[:len('admin_video_user_history')] == 'admin_video_user_history',
                             StateFilter(default_state))
async def user_history_admin_video(callback: CallbackQuery, state: FSMContext):
    cash = await state.get_data()

    page = int(callback.data.split(':')[2]) + int(callback.data.split(':')[1])
    user_id = cash['user_id']

    create_connection(DB_ROOT, database)
    orders = database.get_user_orders(user_id=user_id, type='video')
    info = database.get_user_info(user_id=user_id, type='video')[1]
    bank = database.get_bank_balance()[0]
    close_connection(database)
    orders = orders[(page - 1) * 7:page * 7]
    if orders:
        text = create_history_text_video(orders, info, bank, page, user_id=user_id)
        keyboard = kb.create_keyboard_inline([
            [[' ⬅️', f'admin_video_user_history:-1:{page}'], ['➡️ ', f'admin_video_user_history:1:{page}']],
            [['НАЗАД', f'admin_select_user_history:{user_id}']],
            [['💢 Закрыть', 'close']]
        ])
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML', disable_web_page_preview=True)


# change_admin
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/change_admin')
async def change_admin(message: Message):
    await message.answer('Выберите дейтсвие', reply_markup=kb.change_admin)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('change_admin')] == 'change_admin')
async def change_admin_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(':')[1]

    if action == 'see':
        create_connection(DB_ROOT, database)
        admins = database.get_admins()
        close_connection(database)

        text = f'Список админов (их id)\n'
        for item in admins:
            text += str(item[0]) + '\n'

        await callback.message.edit_text(text)
    elif action == 'add':
        await state.set_state(AdminState.wait_add_admin)
        await callback.message.edit_text('Напишите id админа, которого хотите добавить', reply_markup=kb.close)
    else:
        await state.set_state(AdminState.wait_del_admin)
        await callback.message.edit_text('Напишите id админа, которого хотите удалить', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.wait_add_admin))
async def add_admin(message: Message, state: FSMContext):
    try:
        id = int(message.text)

        create_connection(DB_ROOT, database)
        database.add_admin(user_id=id)
        close_connection(database)

        await state.set_state(default_state)
        await message.answer(f'Юзер - {id} был добавлен в список админов')
    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.wait_del_admin))
async def del_admin(message: Message, state: FSMContext):
    try:
        id = int(message.text)

        create_connection(DB_ROOT, database)
        database.del_admin(user_id=id)
        close_connection(database)

        await state.set_state(default_state)
        await message.answer(f'Юзер - {id} был удален из списка админов')
    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова', reply_markup=kb.close)


# /chat


# /download
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/download')
async def download(message: Message):
    await message.answer_document(FSInputFile('bot/db/db.db', 'main_database'))
    await message.answer_document(FSInputFile('bot/db/chat.db', 'chat_history_database'))


# /users
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/users')
async def users(message: Message):
    date = datetime.now().strftime("%d.%m.%Y").split(':')

    create_connection(DB_ROOT, database)
    users = len(database.get_statistic())
    total_user = len(database.get_users())
    close_connection(database)

    await message.answer(f'Активных пользователей на {date}\n'
                         f'{users}\n'
                         f'Всего пользователей:\n'
                         f'{total_user}')


# ================================================================ /change_channel
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/manage_channel')
async def manage_channel(message: Message):
    await message.answer('Выберите действие',
                         reply_markup=kb.manage_channels)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data == 'manage_channel')
async def manage_channel(callback: CallbackQuery):
    await callback.message.edit_text(
        'Выберите действие',
        reply_markup=kb.manage_channels)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data == 'add_channel')
async def add_channel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.wait_channel_id)
    await callback.message.edit_text('Введите id канала для добавления...', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_id))
async def wait_channel_id(message: Message, state: FSMContext):
    try:
        channel_id = int(message.text)

        create_connection(DB_ROOT, database)
        channel = database.get_channel(channel_id=channel_id)
        close_connection(database)
        if not channel:
            await state.update_data({'channel_id': channel_id})
            await state.set_state(AdminState.wait_channel_name)
            await message.answer('Теперь пришлите название канала, оно будет отоброжаться при выборе каналов')
        else:
            await state.set_state(default_state)
            await message.answer('Такой канал уже есть в базе-.')
    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_name))
async def wait_channel_name(message: Message, state: FSMContext):
    channel_name = message.text
    await state.update_data({'channel_name': channel_name})
    await state.set_state(AdminState.wait_channel_theme)
    await message.answer('Теперь пришлите описание канала')


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_theme))
async def wait_channel_name(message: Message, state: FSMContext):
    await state.update_data({'channel_theme': message.text})
    await state.set_state(AdminState.wait_channel_dog)
    await message.answer('Теперь пришлите общую ссылку на канал')


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_dog))
async def wait_channel_dog(message: Message, state: FSMContext):
    await state.update_data({'channel_url': message.text})
    cash = await state.get_data()
    await state.set_state(AdminState.wait_channel_confirm)
    await message.answer('Описание канала:\n'
                         f'{cash["channel_theme"]}')
    await message.answer('Вы уверены что хотите поставить канал с такими параметрами:\n'
                         f'id канала:\n{cash["channel_id"]}\n'
                         f'имя канала:\n'
                         f'{cash["channel_name"]}\n'
                         'ссылка на канал:\n'
                         f'{cash["channel_url"]}',
                         reply_markup=kb.channel_confirm)


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_confirm))
async def wait_channel_confirm(message: Message):
    await message.answer('Нажмите кнопку выбора.')


@admin_router.callback_query(Admin(), StateFilter(AdminState.wait_channel_confirm))
async def wait_channel_confirm(callback: CallbackQuery, state: FSMContext, bot: Bot):
    answer = bool(int(callback.data))
    if not answer:
        await state.clear()
        await state.set_state(default_state)
        await callback.message.edit_text('Дейстиве отменено')
    else:
        await callback.answer('Подождите загрузку, бот может тормозить...')

        cash = await state.get_data()
        channel_id = cash['channel_id']
        channel_theme = cash['channel_theme']
        channel_name = cash['channel_name']
        channel_url = cash['channel_url']
        try:
            link = await bot.create_chat_invite_link(chat_id=channel_id, expire_date=None)

            create_connection(DB_ROOT, database)
            database.add_channel(channel_id=channel_id,
                                 name=channel_name,
                                 theme=channel_theme,
                                 url=channel_url
                                 )
            users_id = database.get_users()
            for user_id in users_id:
                link = await bot.create_chat_invite_link(chat_id=channel_id, expire_date=None)
                database.add_new_channel(link.invite_link, channel_id, user_id[0])
            close_connection(database)

            await state.clear()
            await state.set_state(default_state)
            await callback.message.edit_text('Каналы добавлены!')
        except TelegramBadRequest:
            await state.set_state(default_state)
            await callback.message.edit_text('Чат не найден.\nВозможно бота нет в канале или вы ввели неправильный id')


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data == 'del_channel')
async def del_channel(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.wait_channel_id_delete)
    await callback.message.edit_text('Введите id канала для удаления', reply_markup=kb.close)


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_id_delete))
async def wait_channel_id_delete(message: Message, state: FSMContext):
    try:
        id = int(message.text)

        create_connection(DB_ROOT, database)
        database.del_channel_from_channel_inf(channel_id=id)
        database.del_channel_from_referal_info(channel_id=id)
        close_connection(database)

        await state.set_state(default_state)
        await message.answer('Канал был удален')

    except ValueError:
        await message.answer('Неверный формат id, попробуйте снова', reply_markup=kb.close)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data == 'edit_channel')
async def edit_channel(callback: CallbackQuery):
    create_connection(DB_ROOT, database)
    channels = database.get_channels()
    close_connection(database)

    keyboard = []
    for channel in channels:
        keyboard.append([
            [channel[1], f'edit_channel:{channel[0]}']
        ])
    keyboard.append(
        [['⬅️ Назад', 'manage_channel']]
    )

    await callback.message.edit_text(
        text='Выебрите канал', reply_markup=kb.create_keyboard_inline(keyboard)
    )


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('edit_channel:')] == 'edit_channel:')
async def edit_channel_process(callback: CallbackQuery):
    id = int(callback.data.split(':')[1])
    create_connection(DB_ROOT, database)
    channel = database.get_channel(channel_id=id)
    close_connection(database)

    text = f"""
<b>Имя канала:</b>
{channel[1]}
<b>Описание канала:</b>
{channel[2]}
<b>Ссылка канала:</b>
{channel[3]}
"""

    keyboard = kb.create_keyboard_inline([
        [['Изменить название', f'change_channel_name:{id}']],
        [['Изменить описание', f'change_channel_descr:{id}']],
        [['Изменить ссылку', f'change_channel_url:{id}']],
        [['⬅️ Назад', 'edit_channel']]
    ])

    await callback.message.edit_text(
        text, reply_markup=keyboard, parse_mode='HTML'
    )


@admin_router.callback_query(Admin(), StateFilter(default_state),
                             F.data[:len('change_channel_name')] == 'change_channel_name')
async def edit_channel_process(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        {'channel_id': int(callback.data.split(':')[1])}
    )
    await state.set_state(AdminState.wait_channel_name_edit)
    await callback.message.edit_text(
        'Пришлите новое имя канала.'
    )


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_name_edit))
async def wait_channel_name_edit(message: Message, state: FSMContext):
    name = message.text
    cash = await state.get_data()
    id = cash['channel_id']

    create_connection(DB_ROOT, database)
    database.edit_channel_name(channel_id=id, name=name)
    channel = database.get_channel(channel_id=id)
    close_connection(database)

    text = f"""
<b>Имя канала:</b>
{name}
<b>Описание канала:</b>
{channel[2]}
<b>Ссылка канала:</b>
{channel[3]}
    """

    keyboard = kb.create_keyboard_inline([
        [['Изменить название', f'change_channel_name:{id}']],
        [['Изменить описание', f'change_channel_descr:{id}']],
        [['Изменить ссылку', f'change_channel_url:{id}']],
        [['⬅️ Назад', 'edit_channel']]
    ])

    await state.clear()
    await message.answer(
        text, reply_markup=keyboard, parse_mode='HTML'
    )


@admin_router.callback_query(Admin(), StateFilter(default_state),
                             F.data[:len('change_channel_descr')] == 'change_channel_descr')
async def change_channel_descr(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        {'channel_id': int(callback.data.split(':')[1])}
    )
    await state.set_state(AdminState.wait_channel_descr_edit)
    await callback.message.edit_text(
        'Пришлите новое описание канала'
    )


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_descr_edit))
async def wait_channel_descr_edit_process(message: Message, state: FSMContext):
    descr = message.text
    cash = await state.get_data()
    id = cash['channel_id']

    create_connection(DB_ROOT, database)
    database.edit_channel_descr(channel_id=id, descr=descr)
    channel = database.get_channel(channel_id=id)
    close_connection(database)

    text = f"""
<b>Имя канала:</b>
{channel[1]}
<b>Описание канала:</b>
{descr}
<b>Ссылка канала:</b>
{channel[3]}
    """

    keyboard = kb.create_keyboard_inline([
        [['Изменить название', f'change_channel_name:{id}']],
        [['Изменить описание', f'change_channel_descr:{id}']],
        [['Изменить ссылку', f'change_channel_url:{id}']],
        [['⬅️ Назад', 'edit_channel']]
    ])

    await state.clear()
    await message.answer(
        text, reply_markup=keyboard, parse_mode='HTML'
    )


@admin_router.callback_query(Admin(), StateFilter(default_state),
                             F.data[:len('change_channel_url')] == 'change_channel_url')
async def change_channel_url(callback: CallbackQuery, state: FSMContext):
    await state.update_data(
        {'channel_id': int(callback.data.split(':')[1])}
    )
    await state.set_state(AdminState.wait_channel_url_edit)
    await callback.message.edit_text(
        'Пришлите новую ссылку для канала'
    )


@admin_router.message(Admin(), StateFilter(AdminState.wait_channel_url_edit))
async def wait_channel_url_edit_process(message: Message, state: FSMContext):
    url = message.text
    cash = await state.get_data()
    id = cash['channel_id']

    create_connection(DB_ROOT, database)
    database.edit_channel_url(channel_id=id, url=url)
    channel = database.get_channel(channel_id=id)
    close_connection(database)

    text = f"""
<b>Имя канала:</b>
{channel[1]}
<b>Описание канала:</b>
{channel[2]}
<b>Ссылка канала:</b>
{url}
    """

    keyboard = kb.create_keyboard_inline([
        [['Изменить название', f'change_channel_name:{id}']],
        [['Изменить описание', f'change_channel_descr:{id}']],
        [['Изменить ссылку', f'change_channel_url:{id}']],
        [['⬅️ Назад', 'edit_channel']]
    ])

    await state.clear()
    await message.answer(
        text, reply_markup=keyboard, parse_mode='HTML'
    )


# ================================================================ /send_message
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/send_message')
async def send_message(message: Message, state: FSMContext):
    await state.set_state(AdminState.wait_message_to_spam)
    await message.answer('Пришлите сообщение для рассылки\n'
                         '(Текст, текст + фото, фото, текст + видео, видео)')


@admin_router.message(Admin(), StateFilter(AdminState.wait_message_to_spam))
async def send_message_get_text(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        photo_id = photo.file_id
        try:
            caption = message.caption
            await state.update_data({'photo': [photo_id, caption]})
            await message.answer_photo(photo=photo_id,
                                       caption=caption,
                                       parse_mode='HTML')
        except AttributeError:
            await state.update_data({'photo': [photo_id]})
            await message.answer_photo(photo=photo_id)

        await message.answer('Вы  уверены что хотите отправить такой текст?\n'
                             'Пришлите да/нет', reply_markup=kb.close)

    elif message.video:
        video = message.video
        video_id = video.file_id
        try:
            caption = message.caption
            await state.update_data({'video': [video_id, caption]})
            await message.answer_video(video=video_id,
                                       caption=caption,
                                       parse_mode='HTML')
        except AttributeError:
            await state.update_data({'video': [video_id]})
            await message.answer_video(video=video_id)

        await message.answer('Вы  уверены что хотите отправить такой текст?\n'
                             'Пришлите да/нет', reply_markup=kb.close)
    else:
        await state.update_data({'text': message.text})

        await message.answer(message.text)
        await message.answer('Вы  уверены что хотите отправить такой текст?\n'
                             'Пришлите да/нет', parse_mode='HTML', reply_markup=kb.close)
    await state.set_state(AdminState.wait_message_to_spam_confirm)


@admin_router.message(Admin(), StateFilter(AdminState.wait_message_to_spam_confirm))
async def send_message_get_text(message: Message, state: FSMContext, bot: Bot):
    if message.text == 'да':
        cash = await state.get_data()
        await state.clear()
        create_connection(DB_ROOT, database)
        user_ids = database.get_users()
        close_connection(database)
        try:
            text = cash['text']
            for user_id in user_ids:
                try:
                    await bot.send_message(chat_id=user_id[0],
                                           text=text, parse_mode='HTML')
                except TelegramForbiddenError:
                    pass
        except  KeyError:
            try:
                try:
                    photo = cash['photo'][0]
                    text = cash['photo'][1]

                    for user_id in user_ids:
                        try:
                            await bot.send_photo(chat_id=user_id[0], photo=photo,
                                                 caption=text, parse_mode='HTML')
                        except TelegramForbiddenError:
                            pass
                except IndexError:
                    for user_id in user_ids:
                        try:
                            await bot.send_photo(chat_id=user_id[0], photo=photo)
                        except TelegramForbiddenError:
                            pass


            except  KeyError:
                try:
                    video = cash['video'][0]
                    text = cash['video'][1]

                    for user_id in user_ids:
                        try:
                            await bot.send_video(chat_id=user_id[0], video=video,
                                                 caption=text, parse_mode='HTML')
                        except TelegramForbiddenError:
                            pass
                except IndexError:
                    for user_id in user_ids:
                        try:
                            await bot.send_video(chat_id=user_id[0], video=video)
                        except TelegramForbiddenError:
                            pass

        await state.clear()
        await message.answer('Все прошло успешно!')
    elif message.text == 'нет':
        await state.clear()
        await message.answer('Дейстиве отменено')
    else:
        await message.answer('Ой-ой, что-то пошло не так, попробуйте снова\n'
                             'Пришлите да/нет', reply_markup=kb.close)


# ================================ /statistic ===============================
@admin_router.message(Admin(), StateFilter(default_state), F.text == '/statistic')
async def statictic(message: Message):
    await message.answer('Выберите программу для статистики', reply_markup=kb.statictic_pick)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data == '/statistic')
async def statictic(callback: CallbackQuery):
    await callback.message.edit_text('Выберите программу для статистики', reply_markup=kb.statictic_pick)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('pick_statistic')] == 'pick_statistic')
async def statisctic_pick(callback: CallbackQuery):
    answer = callback.data.split(':')[1]
    if answer == 'video':
        keyboard = kb.statictic_video
        text = 'Выберите действие для видео'
    else:
        keyboard = kb.statictic_referal
        text = 'Выберите действие для реферальной программы'
    await callback.message.edit_text(text=text, reply_markup=keyboard)


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('video_statistic')] == 'video_statistic')
async def statisctic_check(callback: CallbackQuery):
    keyboard = kb.statictic_video
    answer = callback.data.split(':')[1]
    create_connection(DB_ROOT, database)
    if answer == 'way_to_pay_people':
        video_orders = database.get_orders(type='video', status='💸 Ожидает выплаты')
        people = len(video_orders)
        text = ('Количество людей ожидающих выплату\n'
                f'{people}')
    elif answer == 'wait_to_pay_cash':
        video_orders = database.get_orders(type='video', status='💸 Ожидает выплаты')
        to_pay = 0
        for item in video_orders:
            to_pay += item[3]
        text = ('Общая сумма ожидающая выплату\n'
                f'{to_pay}₽')
    elif answer == 'all_time_pay':
        video_orders = database.get_orders(type='video', status='✅ Выплачено')
        to_pay = 0
        for item in video_orders:
            to_pay += item[3]
        text = ('Общая сумма выплаченная за все время\n'
                f'{to_pay}₽')
    elif answer == 'leader':

        await callback.answer('Загрузка... Бот может тормозить...')
        user_ids = database.get_users()
        users_price = {}
        for id in user_ids:
            users_price.update({
                id[0]: 0
            })
            user_order = database.get_user_orders(user_id=id[0], type='video')
            if user_order:
                for item in user_order:
                    if item[1] == '✅ Выплачено':
                        users_price[id[0]] += item[3]
            if users_price[id[0]] == 0:
                del users_price[id[0]]

        users_price_keys = sorted(users_price)
        users_price_keys = users_price_keys[:20]
        text = '<b>Топ 20 по выплатам видео</b>\n'
        for i in range(len(users_price_keys)):
            text += (f'{i + 1}. Юзер {users_price_keys[i]}\n'
                     f'💸Выплаты {users_price[users_price_keys[i]]}₽\n')
    elif answer == 'month':
        text = 'Выбери месяц'
        keyboard = kb.statictic_video_month
    close_connection(database)

    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('video_month')] == 'video_month')
async def statisctic_video_month(callback: CallbackQuery):
    date = callback.data.split(':')
    month = date[1]
    month_text = date[2]

    create_connection(DB_ROOT, database)
    orders = database.get_orders(type='video', status='✅ Выплачено')
    close_connection(database)
    to_pay = 0
    for item in orders:
        date = item[2].split('.')[1]
        if date == month:
            to_pay += item[3]
    await callback.message.edit_text(f'За {month_text} было выплачено\n{to_pay}₽',
                                     reply_markup=kb.statictic_video_month)


@admin_router.callback_query(Admin(), StateFilter(default_state),
                             F.data[:len('referal_statistic')] == 'referal_statistic')
async def statisctic_check(callback: CallbackQuery):
    keyboard = keyboard = kb.statictic_referal
    answer = callback.data.split(':')[1]
    create_connection(DB_ROOT, database)
    if answer == 'way_to_pay_people':
        video_orders = database.get_orders(type='referal', status='💸 Ожидает выплаты')
        people = len(video_orders)
        text = ('Количество людей ожидающих выплату\n'
                f'{people}')
    elif answer == 'wait_to_pay_cash':
        video_orders = database.get_orders(type='referal', status='💸 Ожидает выплаты')
        to_pay = 0
        for item in video_orders:
            to_pay += item[4]
        text = ('Общая сумма ожидающая выплату\n'
                f'{to_pay}₽')
    elif answer == 'all_time_pay':
        video_orders = database.get_orders(type='referal', status='✅ Выплачено')
        to_pay = 0
        for item in video_orders:
            to_pay += item[4]
        text = ('Общая сумма выплаченная за все время\n'
                f'{to_pay}₽')
    elif answer == 'leader':
        await callback.answer('Загрузка... Бот может тормозить...')
        user_ids = database.get_users()
        users_price = {}
        for id in user_ids:
            users_price.update({
                id[0]: 0
            })
            user_order = database.get_user_orders(user_id=id[0], type='referal')

            if user_order:
                for item in user_order:
                    if item[2] == '✅ Выплачено':
                        users_price[id[0]] += item[4]
            if users_price[id[0]] == 0:
                del users_price[id[0]]

        users_price_keys = sorted(users_price)
        users_price_keys = users_price_keys[:20]
        text = '<b>Топ 20 по выплатам рефералы</b>\n'
        for i in range(len(users_price_keys)):
            text += (f'{i + 1}. Юзер {users_price_keys[i]}\n'
                     f'💸Выплаты {users_price[users_price_keys[i]]}₽\n')
    elif answer == 'month':
        text = 'Выбери месяц'
        keyboard = kb.statictic_referal_month
    close_connection(database)

    await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode='HTML')


@admin_router.callback_query(Admin(), StateFilter(default_state), F.data[:len('referal_month')] == 'referal_month')
async def statisctic_referal_month(callback: CallbackQuery):
    date = callback.data.split(':')
    month = date[1]
    month_text = date[2]

    create_connection(DB_ROOT, database)
    orders = database.get_orders(type='referal', status='✅ Выплачено')
    close_connection(database)
    to_pay = 0
    for item in orders:
        date = item[3].split('.')[1]
        if date == month:
            to_pay += item[4]
    await callback.message.edit_text(f'За {month_text} было выплачено\n{to_pay}₽',
                                     reply_markup=kb.statictic_referal_month)


@admin_router.message(Admin(), StateFilter(default_state), F.text == '/users_stat')
async def users_stat(message: Message, state: FSMContext):
    await state.set_state(AdminState.users_stat_date_wait)
    await message.answer('Для просмотра количества активных пользователей пришлите дату в формате\n'
                         'день.месяц.год\n'
                         'или\n'
                         'месяц.год')


@admin_router.message(Admin(), StateFilter(AdminState.users_stat_date_wait))
async def users_stat_date_wait(message: Message, state: FSMContext):
    date = message.text.split('.')

    if len(date) == 3:
        date = '.'.join(date)
        create_connection(DB_ROOT, database)
        activity = database.get_activity(date)
        close_connection(database)
        if str(activity) == '[]':
            await message.answer('Такой даты не в записях,попробуйте снова.', reply_markup=kb.close)
        else:
            await state.set_state(default_state)
            await message.answer('Кол-во юзеров на момент\n'
                                 f'{date}\n'
                                 f'{activity[0][1]} человек')
    elif len(date) == 2:
        date = '.'.join(date)
        month_activity = 0
        create_connection(DB_ROOT, database)
        for i in range(0 + 1, 31 + 1):
            i = str(i) + '.'
            if len(i) == 2: i = '0' + i
            activity = database.get_activity(i + date)
            if str(activity) != '[]':
                month_activity += activity[0][1]
        close_connection(database)
        await state.set_state(default_state)
        await message.answer(f'Кол-во юзеров на момент \n'
                             f'{date}\n'
                             f'{month_activity} человек')
    else:
        await message.answer('Неверный формат, попробуйте снова.', reply_markup=kb.close)
