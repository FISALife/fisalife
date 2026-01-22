import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="슬기로운 우리 FISA 생활",
    page_icon="🏫",
    layout="wide",
)

# 이미지 로드
logo = Image.open("assets/wise_fisa_life_logo.png")

# 중앙 정렬용 컬럼
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image(logo, use_container_width=True)

st.markdown(
    """
    <div style="text-align:center; font-size:18px; color:gray; margin-top:20px;">
        사이드바에서 원하는 기능을 선택하세요 👈
    </div>
    """,
    unsafe_allow_html=True
)
