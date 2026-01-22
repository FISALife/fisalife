import streamlit as st
import pymysql
import pandas as pd

# =========================
# 1. DB 설정
# =========================
db_config = {
    'host': '118.67.131.22',
    'user': 'fisaai6',
    'password': 'Woorifisa!6',
    'db': 'fisa_life',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

st.set_page_config(
    page_title="카페인 대시보드",
    page_icon="📊",
    layout="wide"
)

st.title("📊 스마트 카페인 관리 대시보드")
st.write("오늘 마신 음료를 선택하면 섭취 현황을 시각화해 드립니다.")

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
    # 4. 사이드바 입력 (key 필수!)
    # =========================
    st.sidebar.header("🥤 음료 선택")

    selected_drinks = st.sidebar.multiselect(
        "마신 음료를 골라주세요",
        df["drink_name"].tolist(),
        key="selected_drinks"   # ⭐ 핵심
    )

    drink_counts = {}
    for drink in selected_drinks:
        drink_counts[drink] = st.sidebar.number_input(
            f"{drink} (잔)",
            min_value=1,
            value=1,
            key=f"count_{drink}"   # ⭐ 핵심
        )

    # =========================
    # 5. 버튼 (트리거만 담당)
    # =========================
    if st.sidebar.button("분석 결과 업데이트", use_container_width=True):
        st.session_state.show_result = True

    # =========================
    # 6. 결과 렌더링
    # =========================
    if st.session_state.show_result:

        if not selected_drinks:
            st.warning("먼저 왼쪽 사이드바에서 음료를 선택해주세요!")
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

            col1, col2 = st.columns(2)

            # 🔹 권장량 게이지
            with col1:
                st.subheader("🚩 권장량 대비 섭취 현황")

                limit = 400
                ratio = min(total_caffeine / limit, 1.0)

                st.metric(
                    "현재 총 섭취량",
                    f"{total_caffeine} mg",
                    delta=f"{total_caffeine - limit} mg"
                    if total_caffeine > limit else None,
                    delta_color="inverse"
                )

                st.progress(
                    ratio,
                    text=f"일일 권장량의 {int(ratio * 100)}% 섭취 중"
                )

                if total_caffeine <= 150:
                    st.success("✅ 안전: 아직 여유가 있습니다.")
                elif total_caffeine <= 400:
                    st.warning("⚠️ 주의: 권장량에 근접했습니다! 물을 한 잔 마시세요")
                else:
                    st.error("🚨 위험: 권장량을 초과했습니다! 섭취를 중단하세요.")

            # 🔹 음료별 카페인 차트
            with col2:
                st.subheader("📈 음료별 카페인 비중")

                chart_df = pd.DataFrame(chart_data).set_index("음료")

                st.bar_chart(
                    chart_df,
                    y="카페인(mg)",
                    use_container_width=True
                )

except Exception as e:
    st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")


