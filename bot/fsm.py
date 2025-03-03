from aiogram.fsm.state import StatesGroup, State


class Cash(StatesGroup):
    page = State()
    message_id = State()


class VideoState(StatesGroup):
    url = State()
    platform = State()
    views = State()
    video_url_question = State()
    views_question = State()
    user_name_question = State()


class ReferalState(StatesGroup):
    profile = State()

    sum_to_output = State()


class AdminState(StatesGroup):
    order_id_referal = State()
    status_confirm_referal = State()
    status = State()

    order_id_video = State()
    status_confirm_video = State()
    pay_for_video = State()
    reject_order = State()

    bank_balance_wait = State()

    block = State()
    unblock = State()

    change_text = State()

    user_info_id = State()

    wait_add_admin = State()
    wait_del_admin = State()

    wait_channel_id = State()
    wait_channel_name = State()
    wait_channel_theme = State()
    wait_channel_confirm = State()
    wait_channel_id_delete = State()
    wait_channel_dog = State()

    wait_message_to_spam = State()
    wait_message_to_spam_confirm = State()

    wait_channel_name_edit = State()
    wait_channel_descr_edit = State()
    wait_channel_url_edit = State()

    change_text_video = State()
    users_stat_date_wait = State()

class Chat(StatesGroup):
    wait_for_user_id_to_start_chat = State()

    chat = State()
