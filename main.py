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
row3_col1, row3_col2 = st.columns(2) 

with row1_col1:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">📘 오늘의 요약</div>
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
    

with row1_col2:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">🌬 환기요정</div>
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
            <div class="service-title">🎲 랜덤 자리 뽑기</div>
            <div class="service-desc">
                2주에 한 번씩 바뀌는 우리 교실 좌석표에서<br>
                <b>랜덤으로 자리를 뽑을 수 있는 기능</b>입니다.<br><br>
                각 자리마다 남겨진 후기를 통해<br>
                어떤 자리인지 미리 확인하고,<br>
                조금 더 설레는 마음으로 자리를 바꿔보세요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    

with row2_col2:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">🥤 카페인 계산기</div>
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

with row3_col1:
    st.markdown(
        """
        <div class="service-card">
            <div class="service-title">💡 집단 지성</div>
            <div class="service-desc">
                공부하다 보면 매번 다시 찾게 되는 사이트들이 있죠.<br>
                이 페이지는 <b>FISA 과정 중 자주 사용하는 유용한 사이트들을</b><br>
                한 곳에 모아둔 공간입니다 📚<br><br>
                필요할 때마다 꺼내 쓰고,<br>
                공부 흐름이 끊기지 않도록 도와드릴게요.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with row3_col2:
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
    <div style="text-align:center; font-size:17px; color:#666; line-height:1.8;">
        각 기능의 자세한 사용 방법은  
        <a href="FAQ" style="
            font-weight:700;
            color:#4A6CF7;
            text-decoration:none;
        ">
            FAQ 게시판
        </a>
        에서 확인하실 수 있습니다 📌<br><br>
        <b>왼쪽 사이드바에서 원하는 기능을 선택해주세요</b> 👈
    </div>
    """,
    unsafe_allow_html=True
)