import streamlit as st
import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY")
AIR_KOREA_KEY = os.getenv("AIR_KOREA_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# --- 페이지 설정 ---
st.set_page_config(page_title="상암동 환기 요정", page_icon="🌬️")


# --- 데이터 수집 함수 ---
def get_realtime_data():
    temp, pm10, pm25 = 20, 0, 0
    try:
        # 날씨
        w_url = f"https://api.openweathermap.org/data/2.5/weather?q=Seoul&appid={OPENWEATHER_KEY}&units=metric"
        w_res = requests.get(w_url).json()
        temp = w_res['main']['temp']
        
        # 미세먼지
        a_url = "http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getMsrstnAcctoRltmMesureDnsty"
        a_params = {
            'serviceKey': AIR_KOREA_KEY, 'returnType': 'json', 
            'stationName': '마포구', 'dataTerm': 'DAILY', 'ver': '1.0'
        }
        a_res = requests.get(a_url, params=a_params).json()
        item = a_res['response']['body']['items'][0]
        pm10 = int(item['pm10Value']) if item['pm10Value'].isdigit() else 0
        pm25 = int(item['pm25Value']) if item['pm25Value'].isdigit() else 0
    except Exception as e:
        st.error(f"데이터 수집 오류: {e}")
    return temp, pm10, pm25

# --- 메인 화면 ---
st.title("🌬️ FISA 환기 요정")
st.markdown(f"**현재 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 데이터 로드
t, p10, p25 = get_realtime_data()

# 환기 점수 계산 로직
score = 100
deductions = []
if t < 0: score -= 30; deductions.append(f"❄️ 영하권 추위({t}°C)")
if p10 > 30: score -= 10; deductions.append(f"☁️ 미세먼지 보통 이상({p10})")
if p25 > 15: score -= 20; deductions.append(f"⚠️ 초미세먼지 주의({p25})")
score = max(0, score)

# 상단 메트릭
col1, col2, col3 = st.columns(3)
col1.metric("온도", f"{t} °C")
col2.metric("미세먼지(PM10)", f"{p10} μg/m³")
col3.metric("초미세(PM2.5)", f"{p25} μg/m³")

st.divider()

# 점수 결과 표시
if score >= 70:
    st.success(f"### 환기 추천 점수: {score}점 ✨")
    status = "지금이 환기 골든타임! 창문을 활짝 열어주세요."
elif score >= 40:
    st.warning(f"### 환기 추천 점수: {score}점 🌤️")
    status = "짧게(3분 내외) 환기하는 것을 권장합니다."
else:
    st.error(f"### 환기 추천 점수: {score}점 🚫")
    status = "외부 공기가 좋지 않습니다. 창문을 닫아주세요."

st.info(status)

with st.expander("🔎 점수 산출 근거 확인"):
    if deductions:
        for d in deductions:
            st.write(d)
    else:
        st.write("감점 사유 없음. 공기 질이 아주 좋습니다!")

# --- 슬랙 전송 섹션 ---
st.divider()
st.subheader("📢 팀원들에게 알림 보내기")
comment = st.text_input("추가 한마디 (선택)", placeholder="예: 3번 강의실 창문 열게요!")

if st.button("🚀 슬랙으로 공지 발송"):
    payload = {
        "attachments": [{
            "color": "#2eb886" if score >= 70 else "#e8ad0e" if score >= 40 else "#e01e5a",
            "title": "🌬️ 상암동 환기 요정 알림",
            "text": f"*{status}*\n{comment if comment else ''}",
            "fields": [
                {"title": "📊 점수", "value": f"{score}점", "short": True},
                {"title": "🌡️ 기온", "value": f"{t}°C", "short": True}
            ],
            "footer": "익명의 팀원이 환기를 요청했습니다. 💨"
        }]
    }
    
    with st.spinner("알림 발송 중..."):
        # 여기서 4번 섹션에서 배운 익명성 딜레이 로직을 원한다면 time.sleep() 추가 가능
        res = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
        if res.status_code == 200:
            st.balloons()
            st.success("슬랙 채널에 성공적으로 공지되었습니다!")
        else:
            st.error("발송 실패. 웹훅 URL을 확인하세요.")