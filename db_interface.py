import sqlite3

import pandas as pd


class DBManager:
    def __init__(self, conn: sqlite3.Connection, chat_id: str, chat_name: str, self_name: str):
        self.conn = conn
        self.msg_df = None
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.self_name = self_name

    def update_msg_data(self):
        if self.msg_df is not None:
            return

        df = pd.read_sql_query(
            f"""
            SELECT m.*
            FROM message m
            JOIN chat c ON m.chat_row_id = c._id
            JOIN jid j ON c.jid_row_id = j._id
            WHERE j.user = {self.chat_id}
            ORDER BY m.timestamp;
            """,
            self.conn,
        )
        df['sender'] = df['from_me'].apply(lambda x: self.self_name if x == 1 else self.chat_name)
        self.msg_df = df

    def get_msg_data(self):
        self.update_msg_data()
        return self.msg_df