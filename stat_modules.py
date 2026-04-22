from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

import altair as alt
import pandas as pd
import streamlit as st

from db_interface import DBManager

WEEKDAY_MAPPING = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


class Stat(ABC):
    def __init__(self, id: str, name: str, db_man: DBManager, desc: str = "", categories=None):
        self.id = id
        self.name = name
        self.desc = desc
        self.db_man = db_man
        self.categories = categories or []

    def save_in_session(self, key: str, data):
        st.session_state[f"stat_{self.id}_{key}"] = data

    def get_from_session(self, key: str):
        return st.session_state.get(f"stat_{self.id}_{key}")

    def load_data(self) -> pd.DataFrame:
        return self.db_man.get_msg_data().copy()

    @abstractmethod
    def prepare(self, df: pd.DataFrame):
        raise NotImplementedError

    @abstractmethod
    def display(self, prepared):
        raise NotImplementedError

    def render(self):
        st.subheader(self.name)
        if self.desc:
            st.caption(self.desc)

        prepared = self.prepare(self.load_data())
        self.display(prepared)


class CharsByLengthStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("charsbylengthstat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        text_df = df[df["text_data"].notna()].copy()
        text_df["len"] = text_df["text_data"].apply(len)

        text_df["cumlen"] = (
            text_df.sort_values(["sender", "len"], ascending=[True, False])
            .groupby("sender")["len"]
            .cumsum()
        )

        df_result = text_df.loc[text_df.groupby(["sender", "len"])["cumlen"].idxmax()]

        return alt.Chart(df_result).mark_line().encode(
            x=alt.X("len", title="min. length of messages"),
            y=alt.Y("cumlen", title="total chars"),
            color=alt.Color("sender", title="Sender"),
            tooltip=["len", "cumlen", "sender"],
        ).properties(title="# of chars by min. message length")

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class MsgCountByHrStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("msgcountbyhrstat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["hour"] = df["time"].dt.hour

        activity = df.groupby(["hour", "sender"]).size().reset_index(name="count")

        return alt.Chart(activity).mark_bar().encode(
            x=alt.X("hour:O", title="hour"),
            y=alt.Y("count:Q", title="# of messages"),
            color=alt.Color("sender:N", title="Sender"),
            tooltip=["hour", "sender", "count"],
        ).properties(title="total # of messages by hour")

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class MsgCountByWeekdayStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("msgcountbyweekdaystat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["weekday"] = df["time"].dt.weekday.map(WEEKDAY_MAPPING)

        activity = df.groupby(["weekday", "sender"]).size().reset_index(name="count")

        return alt.Chart(activity).mark_bar().encode(
            x=alt.X("weekday:O", title="weekday", sort=list(WEEKDAY_MAPPING.values())),
            y=alt.Y("count:Q", title="# of messages"),
            color=alt.Color("sender:N", title="Sender"),
            tooltip=["weekday", "sender", "count"],
        ).properties(title="total # of messages by weekday")

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class MsgCountByDateStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("msgcountbydatestat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        min_msgs = self.get_from_session("min_msgs") or 1
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["date"] = df["time"].dt.date

        max_val = df.groupby(["date", "sender"]).size().max()
        minimum_msgs = st.slider(
            "min amount of messages to consider a day",
            min_value=1,
            max_value=max_val,
            value=min_msgs,
            key="msgcountbydatestat_minmsgperdateslider",
        )
        self.save_in_session("min_msgs", minimum_msgs)

        return (
            df.groupby(["date", "sender"])
            .filter(lambda x: len(x) >= minimum_msgs)
            .groupby(["date", "sender"])
            .size()
            .reset_index(name="count")
        )

    def display(self, chart_data):
        st.line_chart(
            chart_data,
            x="date",
            x_label="date",
            y="count",
            y_label="# of messages",
            color="sender",
            width="stretch",
        )


class MsgCountByMonthDateStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("msgcountbymonthdatestat", name, db_man, desc, categories)

    def prepare(self, df: pd.DataFrame):
        df["time"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["month"] = pd.to_datetime(df["time"].dt.to_period("M").dt.start_time)

        activity = df.groupby(["month", "sender"]).size().reset_index(name="count")
        highlight = alt.selection_point(name="highlight", on="pointerover", empty=False)

        return alt.Chart(activity).mark_point().encode(
            x=alt.X("month:T", title="Month"),
            y=alt.Y("count:Q", title="# of messages"),
            color=alt.Color("sender:N", title="Sender"),
            tooltip=["month", "sender", "count"],
        ).properties(title="Activity").add_params(highlight)

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


class AudioDurationStat(Stat):
    def __init__(self, name: str, db_man: DBManager, desc="", categories=None):
        super().__init__("audiodurationstat", name, db_man, desc, categories)

    def load_data(self) -> pd.DataFrame:
        return self.db_man.get_voice_messages().copy()

    def prepare(self, df: pd.DataFrame):
        activity = df.groupby(["sender"])["media_duration"].sum().reset_index()
        activity["duration_formatted"] = activity["media_duration"].apply(
            lambda x: f"{x // 3600}h {(x % 3600) // 60}m {x % 60}s"
        )

        return alt.Chart(activity).mark_bar().encode(
            y=alt.Y(
                "media_duration:Q",
                title="duration of messages",
                axis=alt.Axis(
                    title="duration",
                    format=".0f",
                    labelExpr="datum.value == 0 ? 0 : floor(datum.value / 3600) + 'h ' + floor(datum.value % 3600 / 60) + 'm ' + datum.value % 60 + 's'",
                ),
            ),
            text="duration_formatted",
            color=alt.Color("sender:N", title="Sender"),
            tooltip=["duration_formatted"],
        ).properties(title="audio duration")

    def display(self, chart):
        st.altair_chart(chart, width="stretch")


def create_stats(db_man: DBManager):
    stat_factories: list[Callable[[DBManager], Stat]] = [
        lambda manager: CharsByLengthStat(
            "Chars by message length",
            manager,
            desc="Cumulative character volume by minimum message length.",
            categories=["length", "volume"],
        ),
        lambda manager: MsgCountByHrStat(
            "Messages by hour",
            manager,
            desc="Number of messages sent each hour of the day.",
            categories=["time", "volume"],
        ),
        lambda manager: MsgCountByWeekdayStat(
            "Messages by weekday",
            manager,
            desc="Message volume for each weekday.",
            categories=["time", "volume"],
        ),
        lambda manager: MsgCountByDateStat(
            "Messages by date",
            manager,
            desc="Daily message volume over time.",
            categories=["time", "volume"],
        ),
        lambda manager: MsgCountByMonthDateStat(
            "Messages by month",
            manager,
            desc="Monthly message activity.",
            categories=["time", "volume"],
        ),
        lambda manager: AudioDurationStat("Audio duration", manager),
    ]
    return [factory(db_man) for factory in stat_factories]
