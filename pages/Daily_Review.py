import streamlit as st
import datetime
import sys
import os
import re
from collections import Counter

# =========================
# db.py import 경로 설정
# =========================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

st.set_page_config(
    page_title="오늘의 한 줄 리뷰",
    layout="centered"
)

st.title("📘 오늘의 수업을 요약해주세요")

# =========================
# 입력 폼
# =========================
with st.form(key="daily_review_form", clear_on_submit=True):

    review_date = st.date_input(
        "📅 수업 날짜",
        value=datetime.date.today()
    )

    review_text = st.text_area(
        "✍️ 오늘 수업에 대한 한 줄 요약",
        max_chars=200,
        placeholder="오늘은 SQL JOIN과 Streamlit 멀티페이지 구조를 배웠다."
    )

    difficulty = st.radio(
        "😄 오늘의 난이도",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: ["😀 쉬움", "😄 보통", "😅 약간 어려움", "😰 어려움", "🤯 매우 어려움"][x-1],
        horizontal=True 
    )

    submitted = st.form_submit_button("제출")

    if submitted:
        if not review_text.strip():
            st.warning("리뷰 내용을 입력해주세요!")
        else:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO daily_reviews (review_date, review, difficulty)
                VALUES (%s, %s, %s)
                """,
                (review_date, review_text, difficulty)
            )
            conn.commit()
            conn.close()

            st.success("오늘의 리뷰가 저장되었습니다 ✨")

st.divider()

# =========================
# 날짜별 리뷰 조회
# =========================
st.subheader("📅 지난 수업 리뷰 조회")

selected_date = st.date_input("조회할 날짜 선택")

conn = get_connection()
cur = conn.cursor()
cur.execute(
    """
    SELECT review, difficulty
    FROM daily_reviews
    WHERE review_date = %s
    """,
    (selected_date,)
)
rows = cur.fetchall()
conn.close()

# =========================
# 키워드 추출 함수
# =========================
def normalize_korean_token(token):
    # 자주 나오는 어미/조사 패턴
    endings = [
        "하는", "했다", "하였다", "해서", "하여",
        "되는", "되었다", "배웠다", "배우는",
        "사용하는", "활용하는",
        "이다", "였다", "였다",
        "에서", "으로", "에게",
        "을", "를", "은", "는", "이", "가"
    ]

    for end in endings:
        if token.endswith(end):
            token = token[:-len(end)]
            break

    return token

def clean_token(token):
    # 자주 붙는 조사/어미 제거
    suffixes = [
        "을", "를", "이", "가", "은", "는", "에서", "으로",
        "하다", "하는", "했다", "배웠다", "방법", "등의"
    ]
    for suf in suffixes:
        if token.endswith(suf):
            token = token.replace(suf, "")
    return token

def extract_keywords(texts, top_n=5):
    stopwords = {
        "오늘", "오늘은", "수업", "정말", "너무",
        "조금", "같다", "것", "방법", "등"
    }

    words = []

    for text in texts:
        cleaned = re.sub(r"[^가-힣a-zA-Z ]", "", text)
        tokens = cleaned.split()

        for token in tokens:
            token = normalize_korean_token(token)

            if (
                len(token) >= 2
                and len(token) <= 6
                and token not in stopwords
            ):
                words.append(token)

    counter = Counter(words)
    return [word for word, _ in counter.most_common(top_n)]


# =========================
# 날짜별 키워드 출력
# =========================
st.subheader("🔑 주요 키워드")

if rows:
    texts = [r[0] for r in rows]
    keywords = extract_keywords(texts, top_n=5)

    month = selected_date.month
    day = selected_date.day

    if keywords:
        st.markdown(
            f"""
            ### #{month}월 {day}일의 주요 키워드  
            {'  '.join(keywords)}
            """
        )
    else:
        st.info("키워드를 추출할 수 없어요.")
else:
    st.info("해당 날짜에 작성된 리뷰가 없어요.")
    
st.divider()

# =========================
# 선택 날짜 리뷰 조회
# =========================
st.subheader("📚 선택한 날짜의 리뷰")

conn = get_connection()
cur = conn.cursor()
cur.execute(
    """
    SELECT review_date, review, difficulty
    FROM daily_reviews
    WHERE review_date = %s
    ORDER BY created_at DESC
    """,
    (selected_date,)
)
filtered_rows = cur.fetchall()
conn.close()

emoji_map = {
    1: "😀",
    2: "😄",
    3: "😅",
    4: "😰",
    5: "🤯"
}

if filtered_rows:
    for date, review, diff in filtered_rows:
        with st.container():
            st.markdown(f"**📅 {date} | 난이도 {emoji_map[diff]}**")
            st.write(review)
            st.divider()
else:
    st.info("선택한 날짜에 작성된 리뷰가 없어요.")

