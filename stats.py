import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import altair as alt
import sqlite3

load_dotenv()

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
    chat_user = st.session_state.chat_user
    chat_user = st.text_input("Telephone number of chat with country code and '+'", value = chat_user)

    if st.button("Let's go"):
        chat_user = chat_user[1:]
        st.session_state.chat_user = chat_user
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
        df['sender'] = df['from_me'].apply(lambda x: 'me' if x == 1 else chat_user)
        df['hour'] = df['time'].dt.hour

        # Gruppieren & zurück in langes Format
        activity = (
            df.groupby(['hour', 'sender'])
            .size()
            .reset_index(name='count')
        )

        st.title("Nachrichtenaktivität nach Stunde")

        chart = alt.Chart(activity).mark_bar().encode(
            x=alt.X('hour:O', title='Stunde des Tages'),
            y=alt.Y('count:Q', title='Anzahl Nachrichten'),
            color=alt.Color('sender:N', title='Sender'),
            tooltip=['hour', 'sender', 'count']
        )

        st.altair_chart(chart, use_container_width=True)
