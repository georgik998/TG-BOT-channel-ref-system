from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup



def create_keyboard_inline(text) -> InlineKeyboardMarkup:
    keyboard = []
    for layers in text:
        layer = []
        for elements in layers:
            if elements[1][:len('https://')] == 'https://':
                layer.append(InlineKeyboardButton(text=elements[0], url=elements[1]))
            else:
                layer.append(InlineKeyboardButton(text=elements[0], callback_data=elements[1]))

        keyboard.append(layer)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def create_keyboard_menu(text) -> ReplyKeyboardMarkup:
    keyboard = []
    for layers in text:
        layer = []
        for elements in layers:
            layer.append(KeyboardButton(text=elements))
        keyboard.append(layer)
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)





close = create_keyboard_inline([
    [['💢 Закрыть', 'close']],
])
# ================================Main================================
start = create_keyboard_menu([
    ['👨‍👧‍👦 Реферальная программа' ], ['🤩 Просмотры видео']
])

help = create_keyboard_inline([
    [['Написать', 'https://t.me/CashEazyHelp_bot']],
    [['💢 Закрыть', 'close']]
])

info = create_keyboard_inline([
    [['💢 Закрыть', 'close']]
])
# ================================Admin================================


bank = create_keyboard_inline([
    [['💢 Закрыть', 'close']],
    [['Изменить баланс', 'change']]
])

referal_order = create_keyboard_inline([
    [['💢 Закрыть', 'close']],
])

order_filter_referal = create_keyboard_inline([
    [['❌ Отклонено модерацией', 'order_filter_referal:❌ Отклонено модерацией']],
    [['💸 Ожидает выплаты', 'order_filter_referal:💸 Ожидает выплаты']],
    [['✅ Выплачено', 'order_filter_referal:✅ Выплачено']],
    [['💢 Закрыть', 'close']]
])

order_filter_video = create_keyboard_inline([
    [['❌ Отклонено модерацией', 'order_filter_video:❌ Отклонено модерацией']],
    [['💸 Ожидает выплаты', 'order_filter_video:💸 Ожидает выплаты']],
    [['✅ Выплачено', 'order_filter_video:✅ Выплачено']],
    [['💢 Закрыть', 'close']]
])

change_bank = create_keyboard_inline([
    [['Изменить баланс', 'bank_change_balance']],
    [['💢 Закрыть', 'close']]
])

block_user = create_keyboard_inline([
    [['Заблокировать юзера', 'block'], ['Разблокировать юзера', 'unblock']],
    [['💢 Закрыть', 'close']]
])

text_confirm = create_keyboard_inline([
    [['Да', 'text_confirm:1'], ['Нет', 'text_confirm:0']],
    [['💢 Закрыть', 'close']]
])


user_history = create_keyboard_inline([
    [['Реферальная программа', 'user_history:referal'], ['Видео', 'user_history:video']]
])
user_history_admin_referal = create_keyboard_inline([
    [[' ⬅️', 'admin_referal_user_history:-1'], ['➡️ ', 'admin_referal_user_history:1']],
    [['💢 Закрыть', 'close']]
])

user_history_admin_video = create_keyboard_inline([
    [[' ⬅️', 'admin_video_user_history:-1'], ['➡️ ', 'admin_video_user_history:1']],
    [['💢 Закрыть', 'close']]
])

change_admin = create_keyboard_inline([
    [['Добавить админа', 'change_admin:add'], ['Удалить админа', 'change_admin:del']],
    [['Посмотреть список админов', 'change_admin:see']]

])



сhatting = create_keyboard_inline([
    [['Сообщение от юзера', '-']]
])

statictic_pick = create_keyboard_inline([
    [['Видео', 'pick_statistic:video']],
    [['Реферальная система', 'pick_statistic:referal']],
    [['💢 Закрыть', 'close']]

])

statictic_video = create_keyboard_inline([
    [['Количество людей ожидающих выплату (видео)', 'video_statistic:way_to_pay_people']],
    [['Общая сумма ожидающая выплату (видео)', 'video_statistic:wait_to_pay_cash']],
    [['Выплачено за все время (видео)', 'video_statistic:all_time_pay']],
    [['Выплачено за определенный месяц (видео)', 'video_statistic:month']],
    [['Топ 20 по выплатам (видео)', 'video_statistic:leader']],
    [['⬅️ Назад', '/statistic']],
    [['💢 Закрыть', 'close']]

])
statictic_referal = create_keyboard_inline([
    [['Количество людей ожидающих выплату (реферал)', 'referal_statistic:way_to_pay_people']],
    [['Общая сумма ожидающая выплату (реферал)', 'referal_statistic:wait_to_pay_cash']],
    [['Выплачено за все время (реферал)', 'referal_statistic:all_time_pay']],
    [['Выплачено за определенный месяц (реферал)', 'referal_statistic:month']],
    [['Топ 20 по выплатам (реферал)', 'referal_statistic:leader']],
    [['⬅️ Назад', '/statistic']],
    [['💢 Закрыть', 'close']]
])

statictic_referal_month = create_keyboard_inline([
    [['Январь', 'referal_month:01:Январь'], ['Февраль', 'referal_month:02:Февраль'], ['Март', 'referal_month:03:Март'],
     ['Апрель', 'referal_month:04:Апрель']],
    [['Май', 'referal_month:05:Май'], ['Июнь', 'referal_month:06:Июнь'], ['Июль', 'referal_month:07:Июль'],
     ['Август', 'referal_month:08:Август']],
    [['Сентябрь', 'referal_month:09:Сентябрь'], ['Октябрь', 'referal_month:10:Октябрь'],
     ['Ноябрь', 'referal_month:11:Ноябрь'], ['Декабрь', 'referal_month:12:Декабрь']],
    [['⬅️ Назад', 'pick_statistic:referal']],
    [['💢 Закрыть', 'close']]
])

statictic_video_month = create_keyboard_inline([
    [['Январь', 'video_month:01:Январь'], ['Февраль', 'video_month:02:Февраль'], ['Март', 'video_month:03:Март'],
     ['Апрель', 'video_month:04:Апрель']],
    [['Май', 'video_month:05:Май'], ['Июнь', 'video_month:06:Июнь'], ['Июль', 'video_month:07:Июль'],
     ['Август', 'video_month:08:Август']],
    [['Сентябрь', 'video_month:09:Сентябрь'], ['Октябрь', 'video_month:10:Октябрь'],
     ['Ноябрь', 'video_month:11:Ноябрь'], ['Декабрь', 'video_month:12:Декабрь']],
    [['⬅️ Назад', 'pick_statistic:video']],
    [['💢 Закрыть', 'close']]
])

# ================================Video================================
video = create_keyboard_inline([
    [['💰 Поставить на выплату ', 'video_withdrawal']],
    [['🗓️ История выплат', 'video_history_withdrawal']],
    [['💢 Закрыть', 'close']]
])

video_withdrawal = create_keyboard_inline([
    [['TikTok', 'video_platform:TikTok']],
    [['YouTube Shorts', 'video_platform:YouTube Shorts']],
    [['Insta Reels', 'video_platform:Insta Reels']],
    [[' ⬅️ Назад', 'video_home']]
])

video_history = create_keyboard_inline([
    [[' ⬅️', 'video_pagination:-1'], ['➡️ ', 'video_pagination:1']],
    [['💢 Закрыть ', 'close']],
    [[' ⬅️ Назад', 'video_home']]
])

back_close = create_keyboard_inline([

    [['❌ Закрыть', 'close']],
    [['⬅️ Назад ', 'video_home']]
])

video_url_back = create_keyboard_inline([
    [[' ⬅️ Назад', 'video_withdrawal_back_url']]
])

video_views_back = create_keyboard_inline([
    [[' ⬅️ Назад', 'video_views_back']]
])

# ================================Referal================================
referal = create_keyboard_inline([
    [['👨‍👧‍👦 Реферальные ссылки', 'referal_channels']],
    [['💵 Поставить на выплату', 'referal_withdrawal']],
    [['🗂️ Истории выплат', 'referal_history_withdrawal']],
    [['💢 Закрыть ', 'close']]
])

referal_channel_info = create_keyboard_inline([
    [['🏠 На главную', 'referal_main']],
    [['⬅️ Назад ', 'back_channels_info']],
    [['💢 Закрыть ', 'close']]
])

referal_withdrawal_history = create_keyboard_inline([
    [[' ⬅️', 'referal_pagination:-1'], ['➡️ ', 'referal_pagination:1']],
    [['💢 Закрыть ', 'close']],
    [[' ⬅️ Назад', 'referal_main']]
])

referal_withdrawal = create_keyboard_inline([
    [[' ⬅️ Назад', 'referal_main']],
    [['💢 Закрыть ', 'close']]
])

referal_withdrawal_finish = create_keyboard_inline([
    [[' ⬅️ Назад', 'referal_main']]
])

referal_withdrawal_proccess = create_keyboard_inline([
    [[' ⬅️ Назад', 'referal_withdrawal']]
])

manage_channels = create_keyboard_inline([
    [['Добавить канал', 'add_channel'], ['Удалить канал', 'del_channel']],
    [['Изменить данные о канале', 'edit_channel']],
    [['💢 Закрыть ', 'close']]
])

channel_confirm = create_keyboard_inline([
    [['ДА', '1'], ['НЕТ', '0']]
])
