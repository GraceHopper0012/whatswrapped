import pandas as pd
import altair as alt
import streamlit as st

from db_interface import DBManager


class Stat:
    SELF_NAME = ""
    CHAT_NAME = ""
    CHAT_IDENTIFIER = None
    CONN = None

    def __init__(self, name: str, db_man: DBManager, desc: str = "", categories = None):
        if categories is None:
            categories = []
        self.categories = categories
        self.name = name
        self.desc = desc
        self.db_man = db_man
        pass

    def load_data(self):
        return self.db_man.get_msg_data()

    '''def sql_query(self):
        df = pd.read_sql_query(f"""
        SELECT m.*
        FROM message m
        JOIN chat c
        ON m.chat_row_id = c._id
        JOIN jid j
        ON c.jid_row_id = j._id
        WHERE j.user = '{Stat.CHAT_IDENTIFIER}'
        ORDER BY m.timestamp;
        """, Stat.CONN)
        df['sender'] = df['from_me'].apply(lambda x: Stat.SELF_NAME if x == 1 else Stat.CHAT_NAME)
        return df'''

    def prep_data(self, df: pd.DataFrame):
        pass

    def show_stat(self, data):
        pass

    def render(self):
        df = self.load_data()
        data = self.prep_data(df)
        self.show_stat(data)

class CharsByLengthStat(Stat):

    def prep_data(self, df: pd.DataFrame):
        df['len'] = df['text_data'].dropna().apply(len)

        df['cumlen'] = (
            df.sort_values(['sender', 'len'], ascending=[True, False])
            .groupby('sender')['len']
            .cumsum()
        )

        df_result = df.loc[df.groupby(['sender', 'len'])['cumlen'].idxmax()]

        chart = alt.Chart(df_result).mark_line().encode(
            x=alt.X('len', title="min. length of messages"),
            y=alt.Y('cumlen', title="total chars"),
            color=alt.Color('sender', title="Sender"),
            tooltip=['len', 'cumlen', 'sender']
        ).properties(title="# of chars by min. message length")

        return chart

    def show_stat(self, chart):
        st.altair_chart(chart, width='stretch')

class MsgCountByHrStat(Stat):

    def prep_data(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['hour'] = df['time'].dt.hour

        activity = (
            df.groupby(['hour', 'sender'])
            .size()
            .reset_index(name='count')
        )

        chart = alt.Chart(activity).mark_bar().encode(
            x=alt.X('hour:O', title='hour'),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['hour', 'sender', 'count']
        ).properties(title="total # of messages by hour")

        return chart

    def show_stat(self, chart):
        st.altair_chart(chart, width="stretch")

class MsgCountByWeekdayStat(Stat):
    def __init__(self, name, db_man, desc = "", categories = None):
        super().__init__(name, db_man, desc, categories)
        self.WEEKDAY_MAPPING = {
            0: "Mon",
            1: "Tue",
            2: "Wed",
            3: "Thu",
            4: "Fri",
            5: "Sat",
            6: "Sun"
        }

    def prep_data(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['weekday'] = df['time'].dt.weekday.map(self.WEEKDAY_MAPPING)

        activity = (
            df.groupby(['weekday', 'sender'])
            .size()
            .reset_index(name='count')
        )

        chart = alt.Chart(activity).mark_bar().encode(
            x=alt.X('weekday:O', title='weekday', sort=self.WEEKDAY_MAPPING.values()),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['weekday', 'sender', 'count']
        ).properties(title="total # of messages by weekday")

        return chart

    def show_stat(self, chart):
        st.altair_chart(chart, width="stretch")

class MsgCountByDateStat(Stat):
    def prep_data(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['time'].dt.date
        chart_data = (
            df.groupby(['date', 'sender'])
            .size()
            .reset_index(name='count')
        )

        return chart_data

    def show_stat(self, chart_data):
        st.line_chart(chart_data, x="date", x_label="month", y='count', y_label="# of messages", color="sender",
                      width='stretch')

class MsgCountByMonthDateStat(Stat):
    def prep_data(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['month'] = pd.to_datetime(df['time'].dt.to_period("M").dt.start_time)

        month_activity = (
            df.groupby(['month', 'sender'])
            .size()
            .reset_index(name='count')
        )

        highlight = alt.selection_point(name="highlight", on="pointerover", empty=False)

        chart = alt.Chart(month_activity).mark_point().encode(
            x=alt.X('month:T', title='Month'),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['month', 'sender', 'count']
        ).properties(title="Activity").add_params(highlight)

        return chart

    def show_stat(self, chart):
        st.altair_chart(chart, width="stretch")