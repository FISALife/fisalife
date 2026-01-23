import streamlit as st
import pymysql
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =========================
# 1. DB 설정
# =========================
db_config = {
    "host": st.secrets["mysql"]["host"],
    "user": st.secrets["mysql"]["user"],
    "password": st.secrets["mysql"]["password"],
    "db": st.secrets["mysql"]["database"],
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

st.set_page_config(
    page_title="카페인 대시보드",
    page_icon="☕️",
    layout="wide"
)

st.markdown(
    """
    <style>
    .caffeine-card {
        padding: 24px;
        background-color: #FFFDF9;
        margin-bottom: 8px;
    }

    .caffeine-title {
        font-size: 22px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .caffeine-sub {
        color: #666;
        margin-bottom: 12px;
    }

    .caffeine-value {
        font-size: 36px;
        font-weight: 800;
        margin-bottom: 12px;
    }

    /* 프로그래스바 굵기 */
    .stProgress > div > div {
        height: 18px;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


st.title("☕️ 스마트 카페인 관리 대시보드")
st.write("오늘 커피를 몇 잔 마셨나요? 섭취한 카페인을 시각화 해드릴게요.")

# =========================
# 2. session_state 초기화
# =========================
if "show_result" not in st.session_state:
    st.session_state.show_result = False

# =========================
# 3. DB 데이터 로드
# =========================
try:
    with pymysql.connect(**db_config) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT drink_name, caffeine_mg FROM caffeine")
            data = cursor.fetchall()

    df = pd.DataFrame(data)

    # =========================
    # 4. 사이드바 입력
    # =========================
    st.sidebar.header("☕️ 음료 선택")

    selected_drinks = st.sidebar.multiselect(
        "마신 음료를 골라주세요",
        df["drink_name"].tolist(),
        key="selected_drinks"
    )

    drink_counts = {}
    for drink in selected_drinks:
        drink_counts[drink] = st.sidebar.number_input(
            f"{drink} (잔)",
            min_value=1,
            value=1,
            key=f"count_{drink}"
        )

    # =========================
    # 5. 버튼
    # =========================
    if st.sidebar.button("☕️ 분석 결과 업데이트", use_container_width=True):
        st.session_state.show_result = True

    # =========================
    # 6. 결과 렌더링
    # =========================
    if st.session_state.show_result:

        if not selected_drinks:
            st.warning("☕️ 먼저 왼쪽 사이드바에서 음료를 선택해주세요!")
        else:
            total_caffeine = 0
            chart_data = []

            for drink, count in drink_counts.items():
                unit_mg = df.loc[df["drink_name"] == drink, "caffeine_mg"].values[0]
                subtotal = unit_mg * count
                total_caffeine += subtotal

                chart_data.append({
                    "음료": drink,
                    "카페인(mg)": subtotal
                })

            limit = 400
            remaining = limit - total_caffeine

            # ... (상단 로직 생략)

            st.divider()

            # 3개의 컬럼 생성
            col_m1, col_m2, col_m3 = st.columns(3)

            with col_m1:
                st.markdown("### **📊 현재 총 섭취량**")
                # 권장량 초과 여부에 따른 색상 변화를 위해 delta 설정
                delta_val = f"{total_caffeine - limit} mg 초과" if total_caffeine > limit else f"{limit - total_caffeine} mg 남음"
                st.metric(label="Total Intake", value=f"{total_caffeine} mg", delta=delta_val, delta_color="inverse")

            with col_m2:
                st.markdown("### **🎯 일일 권장량**")
                st.metric(label="Daily Limit", value=f"{limit} mg")

            with col_m3:
                st.markdown("### **📢 현재 상태**")
                
                # 하단 로직과 동일하게 상태 텍스트 세분화
                a = limit - total_caffeine
                
                if a > 100:
                    status_text = "**여유 있음**"
                    status_value = "Safe"
                elif 50 <= a <= 99:
                    status_text = "**주의 단계**"
                    status_value = "Warning"
                elif 1 <= a < 50:
                    status_text = "**권장량 임박**"
                    status_value = "Caution"
                else: # a <= 0
                    status_text = "**권장량 초과**"
                    status_value = "Danger"
                
                # 메트릭 표시
                st.metric(label="Status", value=status_value)
                st.markdown(f"현재 당신은 {status_text} 상태입니다.")
                

            st.divider()

            col1, col2 = st.columns(2)

            # 🔹 권장량 게이지
            with col1:
                #limit = 400

                fig = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=total_caffeine,
                    number={
                        "suffix": " mg",
                        "font": {"size": 30}
                    },
                    title={
                        "text": "☕️ 권장량 대비 섭취 현황",
                        "font": {"size": 18,
                        'weight': 'bold'}
                    },
                    gauge={
                        "axis": {"range": [0, limit]},
                        "bar": {"color": "#4B2E2B"},
                        "steps": [
                            {"range": [0, 150], "color": "#F5E6CC"},
                            {"range": [150, limit], "color": "#D2B48C"}
                        ],
                        "threshold": {
                            "line": {"color": "red", "width": 3},
                            "thickness": 0.75,
                            "value": limit
                        }
                    }
                ))

                fig.update_layout(
                    height=260,                     # ⬅️ 너무 크지도 작지도 않게
                    margin=dict(
                        t=50,   # ⬅️ 위 여백 늘림 (잘림 방지 핵심)
                        b=20,
                        l=20,
                        r=20
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # total_caffeine 수치를 기준으로 조건부 메시지 출력
                if total_caffeine < (limit - 100):
                    # a > 100 상황 (예: 400 - 250 = 150)
                    st.success("✅ **여유 있음**: 아직 카페인을 더 즐기셔도 좋습니다.")

                elif (limit - 99) <= total_caffeine <= (limit - 50):
                    # 50 <= a <= 99 상황 (예: 301mg ~ 350mg 섭취 시)
                    st.warning("⚠️ **일일 카페인 권장량이 얼마 남지 않았어요. 주의하세요!**")

                elif (limit - 49) <= total_caffeine < limit:
                    # 1 <= a < 49 상황 (예: 351mg ~ 399mg 섭취 시)
                    st.error("🚨 **일일 카페인 권장량 임박! 물을 한잔 마시세요.**")

                elif total_caffeine >= limit:
                    # a <= 0 상황
                    st.error("❌ **일일 권장량 초과!!!** 더 이상의 카페인 섭취는 위험할 수 있습니다.")


            # 🔹 음료별 카페인 차트
            # 🔹 음료별 카페인 차트
            # 🔹 음료별 카페인 차트
            with col2:
                chart_df = pd.DataFrame(chart_data)

                # 색상 팔레트
                coffee_colors = ["#D2B48C", "#F5E6CC", "#4B2E2B", "#A67B5B"]

                # go.Pie 사용
                fig = go.Figure(data=[go.Pie(
                    labels=chart_df["음료"],
                    values=chart_df["카페인(mg)"],
                    hole=0.4,
                    marker=dict(colors=coffee_colors),
                    textinfo="percent",
                    textposition="inside",
                    hoverinfo="label+value"
                )])

                fig.update_layout(
                    # 왼쪽 게이지(go.Indicator)와 타이틀 형식 및 위치를 완벽히 통일
                    title={
                        "text": "☕️ 음료별 카페인 비중",
                        "font": {
                            "size": 18,           # 권장량 타이틀과 동일한 크기
                            "color": "#58595B", 
                               # 권장량 타이틀과 동일한 색상
                        },
                        "x": 0.5,                 # 가로 가운데 정렬
                        "xanchor": "center",
                        "y": 0.9                  # 세로 위치 (게이지 차트 타이틀 높이와 일치)
                    },
                    height=260,
                    margin=dict(t=50, b=20, l=20, r=20),
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="middle",
                        y=0.5,
                        xanchor="left",
                        x=1.05
                    ),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )

                st.plotly_chart(fig, use_container_width=True)


except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")



