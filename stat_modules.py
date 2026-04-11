import pandas as pd
import altair as alt
import streamlit as st

from db_interface import DBManager


class Stat:
    def __init__(self, name: str, db_man: DBManager, desc: str = "", categories=None):
        self.name = name
        self.desc = desc
        self.db_man = db_man
        self.categories = categories or []

    def load_data(self) -> pd.DataFrame:
        return self.db_man.get_msg_data()

    def prepare(self, df: pd.DataFrame):
        raise NotImplementedError("Subclasses must implement prepare()")

    def display(self, prepared):
        raise NotImplementedError("Subclasses must implement display()")

    def render(self):
        st.subheader(self.name)
        if self.desc:
            st.caption(self.desc)

        df = self.load_data()
        prepared = self.prepare(df)
        self.display(prepared)


class CharsByLengthStat(Stat):
    def prepare(self, df: pd.DataFrame):
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

    def display(self, chart):
        st.altair_chart(chart, width='stretch')


class MsgCountByHrStat(Stat):
    def prepare(self, df: pd.DataFrame):
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

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class MsgCountByWeekdayStat(Stat):
    def __init__(self, name, db_man, desc="", categories=None):
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

    def prepare(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['weekday'] = df['time'].dt.weekday.map(self.WEEKDAY_MAPPING)

        activity = (
            df.groupby(['weekday', 'sender'])
            .size()
            .reset_index(name='count')
        )

        chart = alt.Chart(activity).mark_bar().encode(
            x=alt.X('weekday:O', title='weekday', sort=list(self.WEEKDAY_MAPPING.values())),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['weekday', 'sender', 'count']
        ).properties(title="total # of messages by weekday")

        return chart

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class MsgCountByDateStat(Stat):
    def prepare(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['time'].dt.date
        chart_data = (
            df.groupby(['date', 'sender'])
            .size()
            .reset_index(name='count')
        )

        return chart_data

    def display(self, chart_data):
        st.line_chart(
            chart_data,
            x="date",
            x_label="date",
            y='count',
            y_label="# of messages",
            color="sender",
            width='stretch'
        )


class MsgCountByMonthDateStat(Stat):
    def prepare(self, df: pd.DataFrame):
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

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


def create_stats(db_man: DBManager):
    return [
        CharsByLengthStat(
            "Chars by message length",
            db_man,
            desc="Cumulative character volume by minimum message length.",
            categories=["length", "volume"],
        ),
        MsgCountByHrStat(
            "Messages by hour",
            db_man,
            desc="Number of messages sent each hour of the day.",
            categories=["time", "volume"],
        ),
        MsgCountByWeekdayStat(
            "Messages by weekday",
            db_man,
            desc="Message volume for each weekday.",
            categories=["time", "volume"],
        ),
        MsgCountByDateStat(
            "Messages by date",
            db_man,
            desc="Daily message volume over time.",
            categories=["time", "volume"],
        ),
        MsgCountByMonthDateStat(
            "Messages by month",
            db_man,
            desc="Monthly message activity.",
            categories=["time", "volume"],
        ),
    ]
