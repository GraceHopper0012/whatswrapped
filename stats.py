import os
import sqlite3

import streamlit as st

import db_interface
import stat_modules
from config import load_config

try:
    cfg = load_config()
except ValueError as exc:
    st.error(str(exc))
else:
    if not os.path.exists(cfg.db_path):
        st.page_link("upload.py", label="You have to first upload your DB")
    else:
        conn = sqlite3.connect(cfg.db_path)
        if "chat_identifier" not in st.session_state:
            st.session_state.chat_identifier = ""
        if "chat_name" not in st.session_state:
            st.session_state.chat_name = ""
        if "self_name" not in st.session_state:
            st.session_state.self_name = ""
        if "selected_stats" not in st.session_state:
            st.session_state.selected_stats = []

        chat_identifier = st.text_input(
            "Telephone number of chat with country code and '+'",
            key="phone_input",
            value=st.session_state.chat_identifier,
        ).replace(" ", "")
        chat_name = st.text_input("Optionally a nickname for the chat", key="chat_name_input",
                                  value=st.session_state.chat_name)
        self_name = st.text_input("Optionally a nickname for yourself", key="self_name_input",
                                  value=st.session_state.self_name)

        if st.button("Let's go") or chat_identifier != "":
            st.session_state.chat_identifier = chat_identifier
            st.session_state.chat_name = chat_name
            st.session_state.self_name = self_name

            if self_name == "":
                self_name = "me"

            if chat_name == "":
                chat_name = chat_identifier

            if chat_identifier.startswith("+"):
                chat_identifier = chat_identifier[1:]

            db_man = db_interface.DBManager(conn, chat_identifier, chat_name, self_name)
            if db_man.test_msg_data():
                available_stats = stat_modules.create_stats(db_man)
                stat_options = [stat.name for stat in available_stats]

                if st.button("Select all"):
                    selected_stats = stat_options

                default_selection = (
                    stat_options if not st.session_state.selected_stats else st.session_state.selected_stats
                )
                selected_stats = st.multiselect(
                    "Choose stats to show",
                    stat_options,
                    default=default_selection,
                    key="selected_stats_multiselect"
                )
                st.session_state.selected_stats = selected_stats

                if selected_stats:
                    for stat in available_stats:
                        if stat.name in selected_stats:
                            stat.render()
                else:
                    st.info("Pick one or more stats to display.")
