import sqlite3 as sql

DB_ROOT = 'bot/db/db.db'
CHAT_ROOT = 'bot/db/chat.db'


def create_connection(path, obj) -> None:
    obj.connection = sql.connect(path)
    obj.cursor = obj.connection.cursor()


def close_connection(obj) -> None:
    obj.connection.close()


class DataBase:
    connection: sql.Connection
    cursor: sql.Cursor

    def update_user_action(self, user_id):
        with self.connection:
            self.cursor.execute("""UPDATE statistic SET days_messages = days_messages + 1 WHERE user_id = ?""",
                                (user_id,))

    def query_execute(self, query):
        with self.connection:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    # stat
    def update_user_action(self, user_id):
        with self.connection:
            self.cursor.execute("""UPDATE statistic SET days_messages = days_messages + 1 WHERE user_id = ?""",
                                (user_id,))

    def update_statistic(self):
        with self.connection:
            self.cursor.execute("""UPDATE statistic SET days_messages = 0""")

    def get_statistic(self):
        with self.connection:
            self.cursor.execute('SELECT  *  FROM statistic WHERE days_messages >= 5')
            return self.cursor.fetchall()

    def get_users(self):
        query = """SELECT user_id FROM users_info_referal"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def add_new_user(self, user_id, links, channels, bot_invite_link, father=0) -> None:
        query0 = f"""SELECT * FROM users_info_referal WHERE user_id = {user_id}"""
        query1 = f"""INSERT INTO users_info_referal (user_id, father, invite_link) VALUES ({user_id}, {father}, "{bot_invite_link}")"""
        query2 = f"""INSERT INTO users_info_video (user_id) VALUES ({user_id})"""
        query3 = f"""INSERT INTO statistic (user_id) VALUES ({user_id})"""

        with self.connection:
            self.cursor.execute(query0)

            if not self.cursor.fetchall():
                self.cursor.execute(query1)
                self.cursor.execute(query2)
                self.cursor.execute(query3)
                for link, channel_id in zip(links, channels):
                    self.cursor.execute(
                        f"""INSERT INTO referal_info (link, user_id, channel_id) VALUES (?, ?, ?)""",
                        (link, user_id, channel_id[0]))
                self.cursor.execute(
                    f"""UPDATE users_info_referal SET balance = balance + 15 WHERE user_id = {father}""")
                self.cursor.execute(f"UPDATE users_info_referal SET invites = invites + 1 WHERE user_id = {father}")

    def get_user_info(self, user_id, type) -> tuple:
        query = f"""SELECT * FROM users_info_{type} WHERE user_id={user_id}"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def get_user_orders(self, user_id, type) -> list:
        query = f"""SELECT * FROM requests_{type} WHERE user_id={user_id}"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def get_orders(self, type, status):
        query = f"""SELECT * FROM requests_{type} WHERE status = '{status}'"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def get_all_orders(self, type, status) -> list:
        query = f"""SELECT * FROM requests_{type} WHERE status='{status}'"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def get_order(self, id, type) -> tuple:
        query = f"""SELECT * FROM requests_{type} WHERE id = {id}"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def change_order_status(self, id, type, status):
        if status == '💸 Ожидает выплаты':
            query = f"""UPDATE requests_{type} SET status = '{status}' WHERE id = {id}"""
        else:
            query = f"""UPDATE requests_{type} SET status = '{status}', virgin = 1 WHERE id = {id}"""

        with self.connection:
            self.cursor.execute(query)

    # video
    def add_order_video(self, date, user_id, user_name, platform, url, views) -> None:
        query = """INSERT INTO requests_video (date,  user_id, user_name, platform, url, views) VALUES(?, ?, ?, ?, ?, ?)"""
        with self.connection:
            self.cursor.execute(query, (date, user_id, user_name, platform, url, str(views)))

    def set_requests_status_video(self, id, status, price=False):
        if price:
            query = f"""UPDATE requests_video SET  price={price} WHERE id = {id}"""
        else:
            query = f"""UPDATE requests_video SET status = '{status}' WHERE id = {id}"""
        with self.connection:
            self.cursor.execute(query)

    def change_profile_balance_video(self, user_id, money):
        query = f"""UPDATE users_info_video SET outputted_balance=outputted_balance+{money} WHERE user_id = {user_id}"""
        with self.connection:
            self.cursor.execute(query)

    def get_all_time_paid_video(self):
        query = """SELECT outputted_balance FROM users_info_video"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def change_video_order_price(self, order_id, price):
        query = f"""UPDATE requests_video SET price = {price} WHERE id = {order_id}"""
        with self.connection:
            self.cursor.execute(query)

    # referal
    def add_referal(self, link, channel) -> int:
        query = f"""UPDATE referal_info SET users_invite = users_invite + 1 WHERE link = ? AND  channel_id={channel}"""
        query2 = f"""SELECT user_id FROM referal_info WHERE link = ?"""

        with self.connection:
            self.cursor.execute(query, (link,))
            self.cursor.execute(query2, (link,))
            return self.cursor.fetchone()

    def add_new_channel(self, link, channel_id, user_id):

        query = f"""INSERT INTO referal_info (link, user_id, channel_id) VALUES (?, ?, ?)"""

        with self.connection:
            self.cursor.execute(query, (link, user_id, channel_id))

    def get_user_channel_info(self, user_id, channel) -> tuple:
        query = f"""SELECT * FROM referal_info WHERE user_id = {user_id} AND channel_id = {channel}"""

        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def add_order_referal(self, user_id, sum, date, user_name):
        query = f"""INSERT INTO requests_referal (user_id, price, date,  user_name) VALUES (?, ?, ?, ?)"""
        with self.connection:
            self.cursor.execute(query, (user_id, sum, date, user_name,))

    def change_profile_balance_referal(self, user_id, balance, balance_on_output, balance_outputted):
        query1 = f"""UPDATE users_info_referal SET balance = balance + ?, balance_on_output = balance_on_output + ?, balance_outputted =  balance_outputted +? WHERE user_id = {user_id}"""

        with self.connection:
            self.cursor.execute(query1, (balance, balance_on_output, balance_outputted,))

    def change_output_money_referal(self, user_id, output, outputted):
        query = f"""
UPDATE users_info_referal SET balance_on_output=balance_on_output-?, balance_outputted=balance_outputted+? WHERE user_id = {user_id}"""
        with self.connection:
            self.cursor.execute(query, (output, outputted,))

    # Admin
    def get_bank_balance(self) -> tuple:
        query = """SELECT * FROM bank"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchone()

    def change_bank_balance(self, money):
        query = f"""UPDATE bank SET balance = balance + ?"""
        with self.connection:
            self.cursor.execute(query, (money,))

    def block_user(self, user_id):
        query = f"""INSERT INTO block_users (user_id) VALUES ({user_id})"""
        with self.connection:
            self.cursor.execute(query)

    def unblock_user(self, user_id):
        query1 = f"""SELECT * FROM block_users WHERE user_id = {user_id}"""
        query2 = f"""DELETE FROM block_users WHERE user_id = {user_id}"""
        with self.connection:
            self.cursor.execute(query1)
            if self.cursor.fetchall():
                self.cursor.execute(query2)
                return True
            return False

    def get_block_user(self, user_id):
        query = f"""SELECT * FROM block_users WHERE user_id = {user_id}"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def add_admin(self, user_id):
        query1 = f"""SELECT * FROM admin WHERE user_id = {user_id}"""
        query2 = f"""INSERT INTO admin (user_id) VALUES ({user_id})"""
        with self.connection:
            self.cursor.execute(query1)
            if not self.cursor.fetchall():
                self.cursor.execute(query2)

    def del_admin(self, user_id):
        query = f"""DELETE  FROM admin WHERE user_id = {user_id}"""
        with self.connection:
            self.cursor.execute(query)

    def get_admins(self) -> list:
        query = """SELECT * FROM admin"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    # Text
    def get_text(self, text):
        sql_query = f"""SELECT * FROM text_{text}"""
        with self.connection:
            self.cursor.execute(sql_query)
            return self.cursor.fetchone()[0]

    def change_text(self, type, text):
        query = f"""UPDATE text_{type} SET text = ?"""
        with self.connection:
            self.cursor.execute(query, (text,))

    # channel
    def get_channels(self):
        query = """SELECT * FROM channel_info"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def add_channel(self, channel_id, name, theme, url):
        query1 = f"""SELECT * FROM channel_info WHERE channel_id = {channel_id}"""
        query2 = f"""INSERT INTO channel_info (channel_id, name, theme, url) VALUES (?, ?, ?, ?)"""
        with self.connection:
            self.cursor.execute(query1)
            if not self.cursor.fetchall():
                self.cursor.execute(query2, (channel_id, name, theme, url))

    def del_channel_from_channel_inf(self, channel_id):
        query = f"""DELETE  FROM channel_info WHERE channel_id = {channel_id}"""
        with self.connection:
            self.cursor.execute(query)

    def del_channel_from_referal_info(self, channel_id):
        query = f"""DELETE  FROM referal_info WHERE channel_id = {channel_id}"""
        with self.connection:
            self.cursor.execute(query)

    def get_channels_id(self):
        query = """SELECT channel_id FROM channel_info"""
        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def get_channel(self, channel_id):
        query1 = f"""SELECT * FROM channel_info WHERE channel_id = {channel_id}"""
        with self.connection:
            return self.cursor.execute(query1).fetchone()

    def edit_channel_name(self, channel_id, name):
        query1 = f"""UPDATE channel_info SET name = ? WHERE channel_id = {channel_id}"""
        with self.connection:
            return self.cursor.execute(query1, (name,)).fetchone()

    def edit_channel_descr(self, channel_id, descr):
        query1 = f"""UPDATE channel_info SET theme = ? WHERE channel_id = {channel_id}"""
        with self.connection:
            return self.cursor.execute(query1, (descr,)).fetchone()

    def edit_channel_url(self, channel_id, url):

        query1 = f"""UPDATE channel_info SET url = ? WHERE channel_id = {channel_id}"""
        with self.connection:
            return self.cursor.execute(query1, (url,)).fetchone()

    def add_activity_date(self, date):
        query = f"INSERT INTO activity VALUES ('{date}')"
        with self.connection: self.cursor.execute(query)

    def activity_change(self, date, pepople):
        query = f"INSERT INTO activity VALUES ('{date}', {pepople})"
        with self.connection: self.cursor.execute(query)

    def get_activity(self, date):
        query = f'SELECT * FROM activity WHERE date="{date}"'

        with self.connection:
            self.cursor.execute(query)
            return self.cursor.fetchall()

    def get_subscribers(self, channel_id):
        query = f'SELECT subscribers FROM channel_info WHERE channel_id = {channel_id}'
        with self.connection:
            self.cursor.execute(query)
            return eval(self.cursor.fetchone()[0])

    def add_subscribers(self, channel_id, subscribers):
        query = f"UPDATE channel_info SET subscribers = '{subscribers}' WHERE channel_id = {channel_id}"
        with self.connection:
            self.cursor.execute(query)


class ChatHistory:
    connection: sql.Connection
    cursor: sql.Cursor

    def write_new_chat(self, partner_id, date, text):
        query = f"""INSERT INTO history (partner_id, date, text) VALUES (?, ?, ?)"""
        with self.connection:
            self.cursor.execute(query, (partner_id, date, text,))
