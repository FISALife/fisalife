import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="슬기로운 우리 FISA 생활",
    page_icon="🏫",
    layout="wide",
)

# =========================
# 로고
# =========================
logo = Image.open("assets/wise_fisa_life_logo.png")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(logo, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# =========================
# 서비스 한 줄 소개
# =========================
st.markdown(
    """
    <div style="text-align:center; font-size:20px; color:#444;">
        우리 FISA 에서의 하루를  
        <b>조금 더 편하고, 건강하고, 따뜻하게</b> 만들어주는 서비스입니다 🌱
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<br><br>", unsafe_allow_html=True)

# =========================
# 서비스 카드 영역
# =========================
st.markdown(
    """
    <style>
    .service-card {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 25px;
        margin: 20px;  /* ⭐ 카드 간 간격 */
        box-shadow: 0px 4px 12px rgba(0,0,0,0.08);
        height: 100%;
    }
    .service-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 10px;
    }
    .service-desc {
        font-size: 16px;
        color: #555;
        line-height: 1.6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

row1_col1, row1_col2 = st.columns(2)
row2_col1, row2_col2 = st.columns(2)

with row1_col1:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">☕ calcaffeine</div>
            <div class="service-desc">
                하루 동안 마신 커피와 음료를 바탕으로<br>
                <b>내가 얼마나 많은 카페인을 섭취했는지</b> 알려주는 계산기입니다.<br><br>
                과한 카페인 섭취를 줄이고,<br>
                건강한 하루를 만들어보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with row1_col2:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">🌬 freshair</div>
            <div class="service-desc">
                현재 대기 중 공기질 정보를 바탕으로<br>
                <b>지금 환기해도 괜찮은 타이밍인지</b> 알려줍니다.<br><br>
                집중이 안 될 때,<br>
                창문을 열어도 되는지 바로 확인해보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with row2_col1:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">📘 daily review</div>
            <div class="service-desc">
                친구들과 함께 그날의 수업을<br>
                <b>한 줄로 요약하고 난이도를 공유</b>할 수 있습니다.<br><br>
                오늘 수업이 어땠는지,<br>
                키워드와 그래프로 한눈에 확인해보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with row2_col2:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">💌 복복복</div>
            <div class="service-desc">
                지친 친구들에게<br>
                <b>익명으로 칭찬과 응원의 메시지</b>를 보낼 수 있는 공간입니다.<br><br>
                말 한마디가 힘이 되는 순간,<br>
                복복복으로 마음을 전해보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

st.markdown("<br><br>", unsafe_allow_html=True)

# =========================
# FAQ 안내
# =========================
st.markdown(
    """
    <div style="text-align:center; font-size:17px; color:#666;">
        각 기능의 자세한 사용 방법은  
        <b>FAQ 게시판</b>에서 확인하실 수 있습니다 📌<br><br>
        <b>왼쪽 사이드바에서 원하는 기능을 선택해주세요</b> 👈
    </div>
    """,
    unsafe_allow_html=True
)
