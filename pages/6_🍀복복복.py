import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import random
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from db import get_connection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_PATH = os.path.join(BASE_DIR, "assets", "NanumGothic-Bold.ttf")

st.set_page_config(
    page_title="복복복 칭찬 감옥",
    layout="centered"
)

st.title("☁️ 복복복 칭찬 감옥")

# =========================
# DB에서 칭찬 데이터 가져오기
# =========================
def fetch_compliments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT message FROM compliments")
    rows = cur.fetchall()
    conn.close()
    return [r["message"] for r in rows]   # ✅ 핵심 수정

# =========================
# 랜덤 칭찬
# =========================
st.subheader("🎁 오늘의 랜덤 칭찬")

if st.button("눌러서 칭찬 받기 💙"):
    compliments = fetch_compliments()
    if compliments:
        st.success(random.choice(compliments))
    else:
        st.warning("아직 저장된 칭찬이 없어요!")

st.divider()

# =========================
# WordCloud
# =========================
st.subheader("☁️ 칭찬 구름")

compliments = fetch_compliments()

if compliments:
    text = " ".join(compliments)

    wc = WordCloud(
        font_path=FONT_PATH,
        background_color="white",
        width=800,
        height=400
    ).generate(text)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc)
    ax.axis("off")
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("아직 칭찬 데이터가 없어요!")

st.divider()

# =========================
# 칭찬 입력
# =========================
st.subheader("💌 익명 칭찬 남기기")

with st.form(key="compliment_form", clear_on_submit=True):
    message = st.text_area(
        "같은 반 친구를 위한 응원 한마디를 적어주세요",
        max_chars=200
    )

    submitted = st.form_submit_button("전송 🚀")

    if submitted:
        if not message.strip():
            st.warning("칭찬 내용을 입력해주세요!")
        else:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO compliments (message) VALUES (%s)",
                (message,)
            )
            conn.close()
            st.success("칭찬이 성공적으로 저장됐어요 💙")
