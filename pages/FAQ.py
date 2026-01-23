import streamlit as st

st.title("❓ 자주 묻는 질문 (FAQ)")
st.caption("슬기로운 우리 FISA 생활 서비스 사용 중 자주 나오는 질문들을 정리했습니다.")

st.markdown("---")

# =========================
# calcaffeine
# =========================
st.subheader("☕️ calcaffeine")

with st.expander("☕ calcaffeine은 어떤 서비스인가요?"):
    st.write("""
    **calcaffeine**은 하루 동안 마신 음료를 입력하면  
    내가 섭취한 **총 카페인 양을 계산**해주는 서비스입니다.
    
    과도한 카페인 섭취를 줄이고  
    건강한 수업 루틴을 돕는 것을 목표로 합니다.
    """)

with st.expander("☕ 카페인 수치는 어디서 가져오나요?"):
    st.write("""
    카페인 함량 정보는  
    **2025년 4월 23일 소셜타임즈 기사**를 참고했습니다.
    
    https://www.esocialtimes.com/news/articleView.html?idxno=39860
    """)

with st.expander("☕ 어떤 음료를 계산할 수 있나요?"):
    st.write("""
    현재 측정 가능한 음료는 다음과 같습니다.
    
    - 아메리카노  
    - 카페라떼  
    - 아샷추  
    - 녹차  
    - 녹차라떼  
    - 바닐라라떼  
    - 몬스터
    """)

with st.expander("☕ 적정 카페인 기준은 무엇인가요?"):
    st.write("""
    적정 카페인 기준은  
    **식약처 보도자료 기준 성인 1일 권장 섭취량**을 참고했습니다.
    
    https://impfood.mfds.go.kr/CFBBB02F02/getCntntsDetail?cntntsSn=281601
    """)

st.markdown("---")

# =========================
# freshair
# =========================
st.subheader("🌿 freshair")

with st.expander("🌿 freshair는 어떤 서비스인가요?"):
    st.write("""
    **freshair**는 현재 대기질과 날씨 정보를 기반으로  
    **지금 환기해도 괜찮은 타이밍인지** 알려주는 서비스입니다.
    """)

with st.expander("🌿 어떤 데이터를 사용하나요?"):
    st.write("""
    다음 데이터를 활용합니다.
    
    - 미세먼지: 한국환경공단 에어코리아 (공공데이터포털)  
      https://www.data.go.kr/data/15073861/openapi.do
    
    - 날씨: OpenWeatherMap  
      https://openweathermap.org/
    """)

with st.expander("🌿 기준 위치는 어디인가요?"):
    st.write("""
    학원이 위치한 **상암 IT 타워 좌표 기준**으로  
    대기질 및 날씨 데이터를 받아옵니다.
    """)

with st.expander("🌿 알림도 오나요?"):
    st.write("""
    공기질이 나쁠 경우  
    **Slack으로 알림이 전송되기도 합니다.**
    """)

st.markdown("---")

# =========================
# daily review
# =========================
st.subheader("📘 daily review")

with st.expander("📘 daily review는 무엇인가요?"):
    st.write("""
    **daily review**는  
    하루 수업을 한 줄로 요약하고  
    난이도를 함께 기록하는 리뷰 서비스입니다.
    """)

with st.expander("📘 키워드는 어떻게 추출하나요?"):
    st.write("""
    키워드 분석은 다음 방식으로 진행됩니다.
    
    - 한글/영문 외 문자 제거  
    - 조사·어미 등 불필요한 단어 제거  
    - 자주 등장하는 단어를 기준으로 키워드 선정  
    
    형태소 분석기나 외부 API 대신  
    **문자열 규칙 기반 전처리 방식**을 사용했습니다.
    """)

st.markdown("---")

# =========================
# 복복복
# =========================
st.subheader("💌 복복복")

with st.expander("💌 복복복은 어떤 서비스인가요?"):
    st.write("""
    **복복복**은  
    지친 친구들에게 **익명으로 칭찬과 응원의 메시지**를 보낼 수 있는 공간입니다.
    """)

with st.expander("💌 익명은 보장되나요?"):
    st.write("""
    네.  
    메시지는 **익명으로 저장 및 노출**되며  
    작성자를 확인할 수 없습니다.
    """)

with st.expander("💌 메시지는 어떻게 보여지나요?"):
    st.write("""
    저장된 메시지는  
    랜덤으로 출력되며 워드 클라우드를 통해 많이 사용된 희망적인 단어들을 보여줍니다.
    누군가의 하루에 작은 힘이 되기를 바라는 서비스입니다 💙
    """)

st.markdown("---")
st.caption("🛠 Built with Streamlit · FISA Life Project")
