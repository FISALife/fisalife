import streamlit as st
import datetime
import sys
import os
import re
from collections import Counter
import matplotlib.pyplot as plt
import koreanize_matplotlib

# =========================
# db.py import 경로 설정
# =========================
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

emoji_map = {
    1: "😀",
    2: "😄",
    3: "😅",
    4: "😰",
    5: "🤯"
}

st.set_page_config(
    page_title="오늘의 한 줄 리뷰",
    layout="centered"
)

st.title("📘 오늘의 수업을 요약해주세요")

# =========================
# 입력 폼
# =========================
with st.form(key="daily_review_form", clear_on_submit=True):

    review_date = st.date_input("📅 수업 날짜", value=datetime.date.today())

    review_text = st.text_area(
        "✍️ 오늘 수업 한 줄 요약",
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
# 키워드 추출
# =========================
def normalize_korean_token(token):
    endings = [
        "하는", "했다", "하였다", "해서", "하여", "하고",
        "되는", "되었다", "배웠다", "배우는",
        "사용하는", "활용하는",
        "이다", "였다",
        "에서", "으로", "에게",
        "을", "를", "은", "는", "이", "가"
    ]
    for end in endings:
        if token.endswith(end):
            return token[:-len(end)]
    return token


def extract_keywords(texts, top_n=5):
    stopwords = {
        "오늘", "오늘은", "수업", "정말", "너무", "조금",
        "같다", "것", "방법", "등", "등의",
        "하고", "및", "또", "또는", "그리고"
    }

    words = []

    for text in texts:
        cleaned = re.sub(r"[^가-힣a-zA-Z ]", "", text)
        for token in cleaned.split():
            token = normalize_korean_token(token)
            if 2 <= len(token) <= 6 and token not in stopwords:
                words.append(token)

    return [w for w, _ in Counter(words).most_common(top_n)]

st.subheader("🔑 주요 키워드")

if rows:
    keywords = extract_keywords([r["review"] for r in rows])
    st.markdown(f"### #{selected_date.month}월 {selected_date.day}일의 주요 키워드  \n{'  '.join(keywords)}")
else:
    st.info("해당 날짜에 작성된 리뷰가 없어요.")

st.divider()

# =========================
# 선택 날짜 리뷰 + 그래프
# =========================
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

st.subheader("📚 선택한 날짜의 리뷰")
left, right = st.columns([6, 4])

with left:
    if filtered_rows:
        for r in filtered_rows:
            st.markdown(f"**📅 {r['review_date']} | 난이도 {emoji_map[r['difficulty']]}**")
            st.write(r["review"])
            st.divider()
    else:
        st.info("리뷰가 없어요.")

with right:
    st.markdown("### 수업 난이도 분포")
    if filtered_rows:
        diff_counter = Counter([r["difficulty"] for r in filtered_rows])

        labels_map = {1:"쉬움",2:"보통",3:"약간 어려움",4:"어려움",5:"매우 어려움"}
        colors_map = {1:"#B8E1DD",2:"#C7D8F2",3:"#FFF1A8",4:"#FFD6A5",5:"#FFADAD"}

        labels, sizes, colors = [], [], []
        for k in sorted(diff_counter):
            labels.append(labels_map[k])
            sizes.append(diff_counter[k])
            colors.append(colors_map[k])

        fig, ax = plt.subplots(figsize=(4,4))
        ax.pie(sizes, labels=labels, colors=colors, autopct="%1.0f%%", startangle=90)
        ax.axis("equal")
        st.pyplot(fig)
        plt.close(fig)
    else:
        st.info("그래프를 표시할 데이터가 없어요.")
