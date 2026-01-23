import mysql.connector
import streamlit as st
import pymysql


def get_connection():
    cfg = st.secrets["mysql"]
    return pymysql.connect(
        host=cfg["host"],
        port=int(cfg.get("port", 3306)),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,  # ✅ 이거 꼭!
        autocommit=True,
    )
