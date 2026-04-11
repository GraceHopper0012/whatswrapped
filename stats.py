import os
import streamlit as st
from dotenv import load_dotenv
import sqlite3

import db_interface
import stat_modules

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
        db_man = db_interface.DBManager(conn, int(chat_identifier), chat_name, self_name)

        StatMessageLength = stat_modules.CharsByLengthStat("chars by message length", db_man)
        StatMsgByHour = stat_modules.MsgCountByHrStat("messages by hr", db_man)
        StatMsgByWeekday = stat_modules.MsgCountByWeekdayStat("messages by weekday", db_man)
        StatMsgByDate = stat_modules.MsgCountByDateStat("messages by date", db_man)
        StatMsgByMonthDate = stat_modules.MsgCountByMonthDateStat("messages by month", db_man)

        StatMessageLength.render()
        StatMsgByHour.render()
        StatMsgByWeekday.render()
        StatMsgByDate.render()
        StatMsgByMonthDate.render()
