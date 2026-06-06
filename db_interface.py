import sqlite3

import pandas as pd


class DBManager:
    def __init__(self, conn: sqlite3.Connection, chat_id: str, chat_name: str, self_name: str):
        self.conn = conn
        self.msg_df = None
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.self_name = self_name
        self.jids = self.get_all_jids(self.chat_id)

    def get_all_jids(self, chat_id):
        df = pd.read_sql_query(
            f"""
            SELECT j._id
            FROM jid j
            WHERE
            (
                j.server = 'lid'
                AND EXISTS (
                    SELECT 1
                    FROM jid_map jm
                    JOIN jid AS j2
                        ON j2._id = jm.jid_row_id
                    WHERE jm.lid_row_id = j._id
                      AND j2.user = {self.chat_id}
                )
            )
            OR
            (
                j.server != 'lid'
                AND j.user = {self.chat_id}
            )""",
            self.conn,
        )
        return df['_id'].tolist()

    def test_msg_data(self):
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
        if len(df) == 0:
            return False
        return True

    def get_edits(self):
        df = pd.read_sql_query(
            f"""
            SELECT mei.*, m.from_me
            FROM message m
            JOIN chat c ON m.chat_row_id = c._id
            JOIN jid j ON c.jid_row_id = j._id
            JOIN message_edit_info mei ON m._id = mei.message_row_id
            WHERE
            (
                j.server = 'lid'
                AND EXISTS (
                    SELECT 1
                    FROM jid_map jm
                    JOIN jid AS j2
                        ON j2._id = jm.jid_row_id
                    WHERE jm.lid_row_id = j._id
                      AND j2.user = {self.chat_id}
                )
            )
            OR
            (
                j.server != 'lid'
                AND j.user = {self.chat_id}
            )
            ORDER BY mei.edited_timestamp;""",
            self.conn,
        )

        df['sender'] = df['from_me'].apply(lambda x: self.self_name if x == 1 else self.chat_name)
        return df

    def update_msg_data(self):
        if self.msg_df is not None:
            return

        df = pd.read_sql_query(
            f"""
            SELECT m.*
            FROM message m
            JOIN chat c ON m.chat_row_id = c._id
            JOIN jid j ON c.jid_row_id = j._id
            WHERE
            (
                j.server = 'lid'
                AND EXISTS (
                    SELECT 1
                    FROM jid_map jm
                    JOIN jid AS j2
                        ON j2._id = jm.jid_row_id
                    WHERE jm.lid_row_id = j._id
                      AND j2.user = {self.chat_id}
                )
            )
            OR
            (
                j.server != 'lid'
                AND j.user = {self.chat_id}
            )
            ORDER BY m.timestamp;
            """,
            self.conn,
        )
        df['sender'] = df['from_me'].apply(lambda x: self.self_name if x == 1 else self.chat_name)
        self.msg_df = df

    def get_voice_messages(self):
        df = pd.read_sql_query(
            f"""
            SELECT m.*, m_med.media_duration
            FROM message m
            JOIN chat c ON m.chat_row_id = c._id
            JOIN jid j ON c.jid_row_id = j._id
            JOIN message_media m_med ON m._id = m_med.message_row_id
            WHERE
            (
                j.server = 'lid'
                AND EXISTS (
                    SELECT 1
                    FROM jid_map jm
                    JOIN jid AS j2
                        ON j2._id = jm.jid_row_id
                    WHERE jm.lid_row_id = j._id
                      AND j2.user = {self.chat_id}
                )
            )
            OR
            (
                j.server != 'lid'
                AND j.user = {self.chat_id}
            )
            AND (m.message_type = 2 OR m.message_type = 81)
            ORDER BY m.timestamp;""",
            self.conn,
        )
        df['sender'] = df['from_me'].apply(lambda x: self.self_name if x == 1 else self.chat_name)
        return df

    def get_calls(self):
        df = pd.read_sql_query(
            f"""
            SELECT cl.*
            FROM call_log cl
            JOIN jid j ON cl.jid_row_id = j._id
            WHERE
            (
                j.server = 'lid'
                AND EXISTS (
                    SELECT 1
                    FROM jid_map jm
                    JOIN jid AS j2
                        ON j2._id = jm.jid_row_id
                    WHERE jm.lid_row_id = j._id
                      AND j2.user = {self.chat_id}
                )
            )
            OR
            (
                j.server != 'lid'
                AND j.user = {self.chat_id}
            )
            ORDER BY cl.timestamp;""",
            self.conn,
        )
        df['sender'] = df['from_me'].apply(lambda x: self.self_name if x == 1 else self.chat_name)
        return df

    def get_msg_data(self):
        self.update_msg_data()
        return self.msg_df