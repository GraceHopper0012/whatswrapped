import altair as alt
import pandas as pd
import streamlit as st

from db_interface import DBManager


class Stat:
    def __init__(self, id, name: str, db_man: DBManager, desc: str = "", categories=None):
        self.id = id
        self.name = name
        self.desc = desc
        self.db_man = db_man
        self.categories = categories or []

    def save_in_session(self, key, data):
        st.session_state["stat_" + self.id + "_" + key] = data

    def get_from_session(self, key):
        compiled_key = "stat_" + self.id + "_" + key
        if compiled_key not in st.session_state:
            return
        return st.session_state[compiled_key]

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
    def __init__(self, name: str, db_man: DBManager, desc=None, categories=None):
        super().__init__("charsbylengthstat", name, db_man, desc, categories)

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
    def __init__(self, name: str, db_man: DBManager, desc=None, categories=None):
        super().__init__("msgcountbyhrstat", name, db_man, desc, categories)

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
        super().__init__("msgcountbyweekdaystat", name, db_man, desc, categories)
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
    def __init__(self, name: str, db_man: DBManager, desc=None, categories=None):
        super().__init__("msgcountbydatestat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        min_msgs = self.get_from_session("min_msgs")
        if min_msgs is None:
            min_msgs = 1
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['date'] = df['time'].dt.date
        grouped = df.groupby(['date', 'sender'])
        max_val = grouped.size().max()
        minimum_msgs = st.slider("min amount of messages to consider a day", min_value=1, max_value=max_val,
                                 value=min_msgs, key="msgcountbydatestat_minmsgperdateslider")
        self.save_in_session("min_msgs", minimum_msgs)
        chart_data = (
            df.groupby(['date', 'sender'])
            .filter(lambda x: len(x) >= minimum_msgs)
            .groupby(['date', 'sender'])
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
    def __init__(self, name: str, db_man: DBManager, desc=None, categories=None):
        super().__init__("msgcountbymonthdatestat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['month'] = pd.to_datetime(df['time'].dt.to_period("M").dt.start_time)

        activity = (
            df.groupby(['month', 'sender'])
            .size()
            .reset_index(name='count')
        )

        highlight = alt.selection_point(name="highlight", on="pointerover", empty=False)

        chart = alt.Chart(activity).mark_point().encode(
            x=alt.X('month:T', title='Month'),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['month', 'sender', 'count']
        ).properties(title="Activity").add_params(highlight)

        return chart

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class AudioDurationStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc=None, categories=None):
        super().__init__("audiodurationstat", name, db_man, desc, categories)

    def load_data(self) -> pd.DataFrame:
        return self.db_man.get_voice_messages()

    def prepare(self, df: pd.DataFrame):
        activity = (
            df.groupby(["sender"])['media_duration']
            .sum()
            .reset_index()
        )

        activity['duration_formatted'] = activity['media_duration'].apply(
            lambda x: f'{x // 3600}h {(x % 3600) // 60}m {x % 60}s')

        chart = alt.Chart(activity).mark_bar().encode(
            # x=alt.X('sender', title='sender'),
            y=alt.Y('media_duration:Q', title='duration of messages', axis=alt.Axis(title='duration', format='.0f',
                                                                                    labelExpr="datum.value == 0 ? 0 : floor(datum.value / 3600) + 'h ' + floor(datum.value % 3600 / 60) + 'm ' + datum.value % 60 + 's'")),
            text="duration_formatted",
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['duration_formatted']
        ).properties(title="audio duration")

        """chart = alt.Chart(activity).mark_bar().encode(
            y='media_duration:Q',  # Dauer als Quantitative Achse
            color='sender',
            tooltip=['sender', 'media_duration', 'duration_formatted']  # Tooltip für Hover
        ).properties(
            title='Dauer in Stunden, Minuten, Sekunden'
        ).encode(
            y=alt.Y('media_duration:Q', axis=alt.Axis(
                title='Dauer',
                format='.0f',  # Formatierung der Achsenwerte
                labelExpr="datum == 0 ? '' : datum + 's'"  # Fügt Sekunden an die Achsenwerte an
            ))
        ) + alt.Chart(activity).mark_text(
            align='center',
            baseline='middle',
            dy=-10  # Text über den Balken verschieben
        ).encode(
            #x='category',
            y='media_duration:Q',
            text='duration_formatted'  # Formatierten Text auf den Balken
        )"""

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
        AudioDurationStat(
            "Audio duration",
            db_man,
        ),
    ]
