import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import altair as alt
import sqlite3

load_dotenv()

WEEKDAY_MAPPING = {
    0: "Mo",
    1: "Di",
    2: "Mi",
    3: "Do",
    4: "Fr",
    5: "Sa",
    6: "So"
}

UPLOAD_DIR = os.getenv("WW_UPLOAD_DIR")
DB_NAME = os.getenv("WW_DB_NAME")
os.makedirs(UPLOAD_DIR, exist_ok=True)
DB_PATH = os.path.join(UPLOAD_DIR, DB_NAME)

if not os.path.exists(DB_PATH):
    #st.button("Please upload your DB at ", onclick=st.switch_page("upload.py"))
    #st.markdown("Please [upload](upload) you DB")
    st.page_link("upload.py", label="You have to first upload your DB")
else:
    conn = sqlite3.connect(DB_PATH)
    if "chat_user" not in st.session_state:
        st.session_state.chat_user = ""
    if "chat_name" not in st.session_state:
        st.session_state.chat_name = ""
    if "self_name" not in st.session_state:
        st.session_state.self_name = ""
    chat_user = st.text_input("Telephone number of chat with country code and '+'", value = st.session_state.chat_user).replace(" ", "")
    chat_name = st.text_input("Optionally a nickname for the chat", value = st.session_state.chat_name)
    self_name = st.text_input("Optionally a nickname for yourself", value = st.session_state.self_name)

    if st.button("Let's go") or chat_user != "":
        # save variables to maintain them when other page is accessed
        st.session_state.chat_user = chat_user
        st.session_state.chat_name = chat_name
        st.session_state.self_name = self_name

        if self_name == "":
            self_name = "me"

        if chat_name == "":
            chat_name = chat_user
        chat_user = chat_user[1:]
        query = f"""
        SELECT m.*
        FROM message m
        JOIN chat c
        ON m.chat_row_id = c._id
        JOIN jid j
        ON c.jid_row_id = j._id
        WHERE j.user = '{chat_user}'
        ORDER BY m.timestamp;
        """

        # Daten wie vorher
        df = pd.read_sql_query(query, conn)
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['sender'] = df['from_me'].apply(lambda x: self_name if x == 1 else chat_name)
        df['hour'] = df['time'].dt.hour
        df['weekday'] = df['time'].dt.weekday.map(WEEKDAY_MAPPING)
        df['date'] = df['time'].dt.date
        df['month'] = pd.to_datetime(df['time'].dt.to_period("M").dt.start_time)
        df['len'] = df['text_data'].dropna().apply(len)

        #df['cumlen'] = df.sort_values(by='len', ascending = False)['len'].cumsum(skipna=True)

        df['cumlen'] = (
            df.sort_values(['sender', 'len'], ascending=[True, False])
            .groupby('sender')['len']
            .cumsum()
        )

        df_result = df.loc[df.groupby(['sender', 'len'])['cumlen'].idxmax()]

        st.line_chart(df_result, x = 'len', x_label="min. length of messages", y = 'cumlen', y_label = "total chars", color="sender")

        # Gruppieren & zurück in langes Format
        activity = (
            df.groupby(['hour', 'sender'])
            .size()
            .reset_index(name='count')
        )

        weekday_activity = (
            df.groupby(['weekday', 'sender'])
            .size()
            .reset_index(name='count')
        )

        month_activity = (
            df.groupby(['month', 'sender'])
            .size()
            .reset_index(name='count')
        )


        chart = alt.Chart(activity).mark_bar().encode(
            x=alt.X('hour:O', title='hour'),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['hour', 'sender', 'count']
        ).properties(title="Activity by hour")

        st.altair_chart(chart, width="stretch")

        weekday_chart = alt.Chart(weekday_activity).mark_bar().encode(
            x=alt.X('weekday:O', title='weekday', sort=WEEKDAY_MAPPING.values()),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['weekday', 'sender', 'count']
        ).properties(title="Activity by weekday")

        st.altair_chart(weekday_chart, width="stretch")

        highlight = alt.selection_point(name="highlight", on="pointerover", empty=False)

        date_chart = alt.Chart(month_activity).mark_point().encode(
            x=alt.X('month:T', title='Month'),
            y=alt.Y('count:Q', title='# of messages'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['month', 'sender', 'count']
        ).properties(title="Activity").add_params(highlight)

        st.altair_chart(date_chart, width = "stretch")

        activity_date = (
            df.groupby(['date', 'sender'])
            .size()
            .reset_index(name='count')
        )

        st.line_chart(activity_date, x = "date", x_label = "month", y = 'count', y_label= "# of messages", color="sender", width = 'stretch')