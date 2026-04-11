import os
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import altair as alt
import sqlite3
import stat_logic.stat

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
    if "chat_identifier" not in st.session_state:
        st.session_state.chat_identifier = ""
    if "chat_name" not in st.session_state:
        st.session_state.chat_name = ""
    if "self_name" not in st.session_state:
        st.session_state.self_name = ""
    chat_identifier = st.text_input("Telephone number of chat with country code and '+'", value = st.session_state.chat_identifier).replace(" ", "")
    chat_name = st.text_input("Optionally a nickname for the chat", value = st.session_state.chat_name)
    self_name = st.text_input("Optionally a nickname for yourself", value = st.session_state.self_name)

    if st.button("Let's go") or chat_identifier != "":
        # save variables to maintain them when other page is accessed
        st.session_state.chat_identifier = chat_identifier
        st.session_state.chat_name = chat_name
        st.session_state.self_name = self_name

        if self_name == "":
            self_name = "me"

        if chat_name == "":
            chat_name = chat_identifier
        chat_identifier = chat_identifier[1:]

        # set all static variables for the stats to work
        stat_logic.stat.Stat.SELF_NAME = self_name
        stat_logic.stat.Stat.CHAT_NAME = chat_name
        stat_logic.stat.Stat.CHAT_IDENTIFIER = chat_identifier
        stat_logic.stat.Stat.CONN = conn

        StatMessageLength = stat_logic.stat.CharsByLengthStat()
        StatMsgByHour = stat_logic.stat.MsgCountByHrStat()
        StatMsgByWeekday = stat_logic.stat.MsgCountByWeekdayStat()
        StatMsgByDate = stat_logic.stat.MsgCountByDateStat()
        StatMsgByMonthDate = stat_logic.stat.MsgCountByMonthDateStat()

        StatMessageLength.render()
        StatMsgByHour.render()
        StatMsgByWeekday.render()
        StatMsgByDate.render()
        StatMsgByMonthDate.render()
