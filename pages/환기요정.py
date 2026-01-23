import streamlit as st
import os
import requests
import json
import plotly.graph_objects as go
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


# --- 커스텀 시각화 함수 (그래프) ---
def get_air_quality_percentage(pm_value, pm_type='PM10'):
    """미세먼지 수치를 백분위로 변환"""
    if pm_type == 'PM10':
        if pm_value <= 30:
            return (pm_value / 30) * 25, '좋음'
        elif pm_value <= 80:
            return 25 + ((pm_value - 30) / 50) * 25, '보통'
        elif pm_value <= 150:
            return 50 + ((pm_value - 80) / 70) * 25, '나쁨'
        else:
            return min(75 + ((pm_value - 150) / 50) * 25, 100), '매우나쁨'
    else:  # PM2.5
        if pm_value <= 15:
            return (pm_value / 15) * 25, '좋음'
        elif pm_value <= 35:
            return 25 + ((pm_value - 15) / 20) * 25, '보통'
        elif pm_value <= 75:
            return 50 + ((pm_value - 35) / 40) * 25, '나쁨'
        else:
            return min(75 + ((pm_value - 75) / 25) * 25, 100), '매우나쁨'


def get_level_color(level):
    """등급별 색상 반환"""
    color_map = {
        '좋음': '#00bfff',
        '보통': '#92d050',
        '나쁨': '#ffa500',
        '매우나쁨': '#ff0000'
    }
    return color_map.get(level, '#999999')


def draw_thin_gradient_bar(pm10_value, pm25_value):
    """정확한 위치의 그라데이션 바"""
    
    try:
        # 백분위 계산
        pm10_percent, pm10_level = get_air_quality_percentage(pm10_value, 'PM10')
        pm25_percent, pm25_level = get_air_quality_percentage(pm25_value, 'PM2.5')
        
        fig = go.Figure()
        
        # 200개 세그먼트로 부드러운 그라데이션
        num_segments = 200
        
        for i in range(num_segments):
            progress = i / num_segments * 100
            
            # 부드러운 색상 보간
            if progress < 25:  # 좋음 (파랑 계열)
                ratio = progress / 25
                r = int(0 + (146 - 0) * ratio)
                g = int(191 + (208 - 191) * ratio)
                b = int(255 + (80 - 255) * ratio)
            elif progress < 50:  # 보통 (초록 계열)
                ratio = (progress - 25) / 25
                r = int(146)
                g = int(208)
                b = int(80)
            elif progress < 75:  # 나쁨 (주황 계열)
                ratio = (progress - 50) / 25
                r = int(146 + (255 - 146) * ratio)
                g = int(208 + (165 - 208) * ratio)
                b = int(80 + (0 - 80) * ratio)
            else:  # 매우나쁨 (빨강 계열)
                ratio = (progress - 75) / 25
                r = int(255)
                g = int(165 - (165 * ratio))
                b = int(0)
            
            color = f'rgb({r},{g},{b})'
            
            fig.add_trace(go.Bar(
                x=[100/num_segments],
                y=[2],
                orientation='h',
                marker=dict(
                    color=color,
                    line=dict(width=0)
                ),
                width=0.8,
                showlegend=False,
                hoverinfo='skip',
                base=i * (100/num_segments)
            ))
        
        # 양쪽 끝 둥글게
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=-2, y0=1.6, x1=2, y1=2.4,
            fillcolor='rgb(0,191,255)',
            line=dict(width=0)
        )
        
        fig.add_shape(
            type="circle",
            xref="x", yref="y",
            x0=98, y0=1.6, x1=102, y1=2.4,
            fillcolor='rgb(255,0,0)',
            line=dict(width=0)
        )
                
        # 레이아웃 설정
        fig.update_layout(
            barmode='stack',
            height=150,
            margin=dict(l=10, r=10, t=60, b=0),
            xaxis=dict(
                range=[-3, 103],
                showticklabels=False,
                showgrid=False,
                zeroline=False
            ),
            yaxis=dict(
                showticklabels=False,
                showgrid=False,
                fixedrange=True,
                range=[-0.3, 3]
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            bargap=0
        )
                
        # 등급 구분선
        for x in [25, 50, 75]:
            fig.add_shape(
                type="line",
                x0=x, y0=1.6, x1=x, y1=2.4,
                line=dict(color="rgba(255,255,255,0.8)", width=2, dash="dash")
            )
        
        # 상단 이모지 + 등급
        emoji_labels = [
            ('😊', '좋음', 12.5),
            ('🙂', '보통', 37.5),
            ('😷', '나쁨', 62.5),
            ('🚨', '매우나쁨', 87.5)
        ]
        
        for emoji, label, pos in emoji_labels:
            fig.add_annotation(
                x=pos, y=3.0,
                text=f'<span style="font-size:15px">{emoji}</span><br><span style="font-size:12px">{label}</span>',
                showarrow=False,
                xref='x', yref='y'
            )
        
        # 중단 기준치 숫자
        thresholds = [
            (0, '0', 'left'),
            (25, '30/15', 'center'),
            (50, '80/35', 'center'),
            (75, '150/75', 'center')
        ]
        
        for pos, text, align in thresholds:
            fig.add_annotation(
                x=pos, y=2.5,
                text=f'<span style="font-size:12px; color:#666">{text}</span>',
                showarrow=False,
                xref='x', yref='y',
                xanchor=align
            )
        
        # 바 아래 화살표
        fig.add_trace(go.Scatter(
            x=[pm10_percent],
            y=[1],
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=20,
                color='#ff9800',
                line=dict(color='white', width=2)
            ),
            showlegend=False,
            hoverinfo='skip',
            name='PM10'
        ))
        
        fig.add_trace(go.Scatter(
            x=[pm25_percent],
            y=[0.85],
            mode='markers',
            marker=dict(
                symbol='triangle-up',
                size=20,
                color='#9c27b0',
                line=dict(color='white', width=2)
            ),
            showlegend=False,
            hoverinfo='skip',
            name='PM2.5'
        ))
        
        # 우측 하단 범례
        fig.add_annotation(
            x=100, y=1,
            text='<span style="color:#ff9800; font-size:14px">▲</span> <span style="font-size:9px">미세먼지(PM10)</span>  '
                 '<span style="color:#9c27b0; font-size:14px">▲</span> <span style="font-size:9px">초미세먼지(PM2.5)</span>',
            showarrow=False,
            xref='x', yref='y',
            xanchor='right'
        )
        
        return fig, pm10_level, pm25_level
    
    except Exception as e:
        st.error(f"그래프 생성 오류: {e}")
        return None, '좋음', '좋음'


# --- 메인 화면 ---
st.title("🌬️ FISA 환기 요정")
st.markdown(f"**현재 시각:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# 데이터 로드
t, p10, p25 = get_realtime_data()

# 등급 계산 (배지용)
pm10_percent, pm10_level = get_air_quality_percentage(p10, 'PM10')
pm25_percent, pm25_level = get_air_quality_percentage(p25, 'PM2.5')
pm10_color = get_level_color(pm10_level)
pm25_color = get_level_color(pm25_level)

# 환기 점수 계산 로직
score = 100
deductions = []

# 온도 체크
if t < -10:
    score -= 40
    deductions.append(f"🥶 매우 추움({t}°C) → **환기는 1분 이내**로 제한하세요!")
elif t < 0:
    score -= 30
    deductions.append(f"❄️ 영하권 추위({t}°C) → 공기가 차니 **짧게 3분만** 환기하세요!")
elif t < 5:
    score -= 10
    deductions.append(f"🌡️ 쌀쌀함({t}°C) → **5분 정도** 환기하면 적당해요.")

# 미세먼지 체크
if p10 > 150:
    score -= 30
    deductions.append(f"🚫 미세먼지 매우나쁨({p10}) → **창문을 닫고 공기청정기**를 사용하세요!")
elif p10 > 80:
    score -= 20
    deductions.append(f"😷 미세먼지 나쁨({p10}) → **환기는 피하고 공기청정기**를 사용하세요.")
elif p10 > 30:
    score -= 10
    deductions.append(f"☁️ 미세먼지 보통({p10}) → **창문 10cm만 열고** 환기하세요.")

# 초미세먼지 체크
if p25 > 75:
    score -= 40
    deductions.append(f"🚨 초미세먼지 매우나쁨({p25}) → **외출 자제, 실내에서만** 활동하세요!")
elif p25 > 35:
    score -= 30
    deductions.append(f"⚠️ 초미세먼지 나쁨({p25}) → **환기보다 공기청정기** 사용을 추천해요.")
elif p25 > 15:
    score -= 20
    deductions.append(f"😐 초미세먼지 보통({p25}) → **환기 시 공기청정기를 함께** 사용하세요.")

score = max(0, score)
# 상단 메트릭 (색깔 배지 포함)
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div>
        <div style="color: #666; font-size: 14px;">온도</div>
        <div style="font-size: 36px; font-weight: bold;">{t} °C</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <span style="color: #666; font-size: 14px;">미세먼지(PM10)</span>
            <span style="background-color: {pm10_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">
                {pm10_level}
            </span>
        </div>
        <div style="font-size: 36px; font-weight: bold;">{p10} μg/m³</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div>
        <div style="display: flex; align-items: center; gap: 5px;">
            <span style="color: #666; font-size: 14px;">초미세(PM2.5)</span>
            <span style="background-color: {pm25_color}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: bold;">
                {pm25_level}
            </span>
        </div>
        <div style="font-size: 36px; font-weight: bold;">{p25} μg/m³</div>
    </div>
    """, unsafe_allow_html=True)

# --- 얇은 그라데이션 바 그래프 추가 ---
result = draw_thin_gradient_bar(p10, p25)
if result[0] is not None:
    fig, _, _ = result
    st.plotly_chart(fig, width='stretch')
else:
    st.warning("그래프를 불러올 수 없습니다.")

# 여백 줄이기
st.markdown("<style>div.stPlotlyChart {margin-bottom: -10px;}</style>", unsafe_allow_html=True)
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

# 제목과 버튼을 같은 행에 배치
col_title, col_spacer, col_button = st.columns([2, 0.1, 1])

with col_title:
    st.subheader("📢 팀원들에게 알림 보내기")

with col_spacer:
    st.write("")  # 간격용 빈 컬럼

with col_button:
    st.write("")  # 수직 정렬
    send_button = st.button("🚀 슬랙 메세지 발송")

comment = st.text_input("추가 한마디 (선택)", placeholder="예: 창문 열고 정신 한 번 차립시다!")

if send_button:
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
        res = requests.post(SLACK_WEBHOOK_URL, data=json.dumps(payload))
        if res.status_code == 200:
            st.balloons()
            st.success("슬랙 채널에 성공적으로 공지되었습니다!")
        else:
            st.error("발송 실패. 웹훅 URL을 확인하세요.")
