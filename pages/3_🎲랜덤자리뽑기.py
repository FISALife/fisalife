import os
import tomllib
import random
import streamlit as st
import pymysql

# ===========================
# Streamlit 기본 설정
# ===========================
st.set_page_config(page_title="랜덤 자리배정", page_icon="🎲", layout="wide")

# ===========================
# DB 설정 로드
# ===========================
def load_mysql_cfg():
    """
    MySQL 접속 정보를 로드
    1) Streamlit secrets (st.secrets) 우선
    2) 없으면 pages/.streamlit/secrets.toml 직접 로드
    """
    # 1) Streamlit Cloud 또는 로컬 secrets
    try:
        cfg = st.secrets["mysql"]
        return {
            "host": cfg["host"],
            "port": int(cfg.get("port", 3306)),
            "user": cfg["user"],
            "password": cfg["password"],
            "database": cfg["database"],
        }
    except Exception:
        pass

    # 2) pages/.streamlit/secrets.toml 직접 로드
    base_dir = os.path.dirname(__file__)  # pages 폴더
    secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")

    if not os.path.exists(secrets_path):
        st.error(f"secrets.toml 없음: {secrets_path}")
        st.stop()

    with open(secrets_path, "rb") as f:
        data = tomllib.load(f)

    if "mysql" not in data:
        st.error("secrets.toml에 [mysql] 섹션이 없습니다.")
        st.stop()

    cfg = data["mysql"]
    return {
        "host": cfg["host"],
        "port": int(cfg.get("port", 3306)),
        "user": cfg["user"],
        "password": cfg["password"],
        "database": cfg["database"],
    }

def get_conn():
    """
    MySQL DB 커넥션 생성
    - DictCursor 사용
    - autocommit 활성화
    """
    cfg = load_mysql_cfg()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
        connect_timeout=5,
        read_timeout=10,
        write_timeout=10,
    )

# ===========================
# DB: 학생/좌석/배정
# ===========================
def fetch_students():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT student_id, name
            FROM seat_students
            WHERE is_active = 1
            ORDER BY name;
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_seats():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT seat_id, seat_code, row_no, col_no
            FROM seats
            WHERE is_active = 1
            ORDER BY row_no, col_no;
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def clear_assignments():
    """
    현재 배정 상태만 초기화
    - seat_assignments만 비움
    - 리뷰(seat_reviews)는 seat_id 기반으로 별도 저장이므로 영향 없음
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM seat_assignments;")
        cur.execute("ALTER TABLE seat_assignments AUTO_INCREMENT = 1;")
    conn.close()

def insert_assignments(pairs):
    """
    (student_id, seat_id) 리스트를 seat_assignments에 저장
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO seat_assignments (student_id, seat_id) VALUES (%s, %s);",
            pairs
        )
    conn.close()

def fetch_assignments_view():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
              st.name AS student_name,
              se.seat_code,
              se.row_no,
              se.col_no,
              a.assigned_at
            FROM seat_assignments a
            JOIN seat_students st ON st.student_id = a.student_id
            JOIN seats se ON se.seat_id = a.seat_id
            ORDER BY se.row_no, se.col_no;
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_assignments_map():
    """
    seat_code -> student_name (좌석 렌더링용)
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT se.seat_code, st.name AS student_name
            FROM seat_assignments a
            JOIN seat_students st ON st.student_id = a.student_id
            JOIN seats se ON se.seat_id = a.seat_id;
        """)
        rows = cur.fetchall()
    conn.close()
    return {r["seat_code"]: r["student_name"] for r in rows}

# ===========================
# DB: 리뷰 (신버전: seat_id 기반)
# ===========================
def fetch_seat_id_by_seat_code(seat_code: str):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT seat_id FROM seats WHERE seat_code=%s LIMIT 1;", (seat_code,))
        row = cur.fetchone()
    conn.close()
    return None if not row else row["seat_id"]

def insert_review(seat_code: str, rating: int, comment: str):
    """
    배정 여부와 상관없이 좌석 리뷰 저장
    (seat_reviews는 seat_id 기반)
    """
    seat_id = fetch_seat_id_by_seat_code(seat_code)
    if seat_id is None:
        raise ValueError(f"존재하지 않는 좌석 코드: {seat_code}")

    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO seat_reviews (seat_id, rating, comment)
            VALUES (%s, %s, %s);
        """, (seat_id, rating, comment))
    conn.close()

def fetch_all_reviews_for_seat(seat_code: str):
    """
    특정 좌석의 전체 리뷰(최신순)
    - 신버전 구조에서는 student_name을 DB에서 조인할 근거가 없음(배정과 분리)
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT r.rating, r.comment, r.created_at
            FROM seat_reviews r
            JOIN seats se ON se.seat_id = r.seat_id
            WHERE se.seat_code = %s
            ORDER BY r.created_at DESC;
        """, (seat_code,))
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_avg_rating_map():
    """
    seat_code -> (평균 별점, 리뷰 개수)
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT se.seat_code,
                   AVG(r.rating) AS avg_rating,
                   COUNT(r.review_id) AS cnt
            FROM seats se
            LEFT JOIN seat_reviews r ON r.seat_id = se.seat_id
            GROUP BY se.seat_code;
        """)
        rows = cur.fetchall()
    conn.close()
    return {
        r["seat_code"]: (
            float(r["avg_rating"]) if r["avg_rating"] is not None else None,
            int(r["cnt"])
        )
        for r in rows
    }

def fetch_recent_reviews_tooltip_map(limit_per_seat: int = 3):
    """
    seat_code -> tooltip_text (최근 리뷰 limit개)
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT se.seat_code, r.rating, r.comment, r.created_at
            FROM seat_reviews r
            JOIN seats se ON se.seat_id = r.seat_id
            ORDER BY se.seat_code, r.created_at DESC;
        """)
        rows = cur.fetchall()
    conn.close()

    tooltips = {}
    counts = {}
    for r in rows:
        sc = r["seat_code"]
        counts.setdefault(sc, 0)
        if counts[sc] >= limit_per_seat:
            continue
        counts[sc] += 1
        tooltips.setdefault(sc, [])
        tooltips[sc].append(f"• {int(r['rating'])}점: {r['comment']}")
    return {sc: "\n".join(lines) for sc, lines in tooltips.items()}

# ===========================
# UI: 좌석 렌더링
# ===========================
def render_section(title, start_row, end_row, cols=4, seat_map=None):
    st.markdown(f"### {title}")
    seat_map = seat_map or {}

    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            seat_code = f"{chr(ord('A') + (r - 1))}{c}"
            student = seat_map.get(seat_code, "—")

            with row_cols[c - 1]:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #e5e7eb;
                        border-radius: 14px;
                        padding: 14px;
                        min-height: 78px;
                        background: white;
                    ">
                        <div style="font-size: 16px; font-weight: 700;">{seat_code}</div>
                        <div style="margin-top: 6px; font-size: 14px;">{student}</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

def render_review_section(title, start_row, end_row, cols, avg_map, tooltip_map):
    """
    좌석 리뷰 선택 UI
    - 클릭 시 selected_seat 저장
    - hover: 평균 별점 + 최근 리뷰
    """
    st.markdown(f"### {title}")

    if "selected_seat" not in st.session_state:
        st.session_state["selected_seat"] = None

    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            seat_code = f"{chr(ord('A') + (r - 1))}{c}"
            avg, cnt = avg_map.get(seat_code, (None, 0))

            tip_lines = []
            tip_lines.append("평균 별점: 없음" if avg is None else f"평균 별점: {avg:.2f} (리뷰 {cnt}개)")

            tip = tooltip_map.get(seat_code)
            if tip:
                tip_lines.append("")
                tip_lines.append("최근 한줄평")
                tip_lines.append(tip)

            hover_text = "\n".join(tip_lines)

            with row_cols[c - 1]:
                if st.button(
                    seat_code,
                    key=f"seatbtn_review_{seat_code}",
                    width="stretch",          # ✅ use_container_width=True 대체
                    help=hover_text
                ):
                    st.session_state["selected_seat"] = seat_code

# ===========================
# UI 시작
# ===========================
st.title("🎲 두근두근 랜덤 자리뽑기")

# 학생 / 좌석 로드
try:
    students = fetch_students()
    seats = fetch_seats()
except Exception as e:
    st.error("DB 조회 실패")
    st.exception(e)
    st.stop()

# 상단 통계
colA, colB, colC = st.columns(3)
colA.metric("학생 수", len(students))
colB.metric("활성 좌석 수", len(seats))
colC.metric("남는 좌석 수", len(seats) - len(students))

if len(seats) < len(students):
    st.error("좌석 수가 학생 수보다 적어요. seats 데이터를 확인하세요.")
    st.stop()

st.divider()

# ===========================
# 랜덤 자리 배정
# ===========================
if st.button("🎲 랜덤 자리 뽑기 !!", width="stretch"):
    try:
        clear_assignments()

        random.shuffle(students)
        seat_pool = seats[:]
        random.shuffle(seat_pool)

        pairs = [(stu["student_id"], seat_pool[i]["seat_id"]) for i, stu in enumerate(students)]
        insert_assignments(pairs)

        st.success("랜덤 배정 완료!")
        st.rerun()
    except Exception as e:
        st.error("랜덤 배정 실패")
        st.exception(e)

st.divider()
st.subheader("🧑‍🧑‍🧒‍🧒 자리 배정 결과")

rows = fetch_assignments_view()
if not rows:
    st.info("아직 배정 결과가 없습니다. 위 버튼으로 배정을 실행하세요.")
else:
    seat_map = fetch_assignments_map()

    left_col, right_col = st.columns([1, 1], gap="large")
    with left_col:
        render_section("2분단", start_row=5, end_row=9, cols=4, seat_map=seat_map)
    with right_col:
        render_section("1분단", start_row=1, end_row=4, cols=4, seat_map=seat_map)

# ===========================
# 리뷰 섹션
# ===========================
st.divider()
st.subheader("⭐ 좌석 리뷰")

try:
    avg_map = fetch_avg_rating_map()
    tooltip_map = fetch_recent_reviews_tooltip_map(limit_per_seat=3)
except Exception as e:
    st.error("리뷰 통계 조회 실패 (DB 스키마/컬럼 확인 필요)")
    st.exception(e)
    st.stop()

l, r = st.columns([1, 1], gap="large")
with l:
    render_review_section("2분단", 5, 9, 4, avg_map, tooltip_map)
with r:
    render_review_section("1분단", 1, 4, 4, avg_map, tooltip_map)

st.divider()

# 좌측: 전체 리뷰 / 우측: 리뷰 작성
left, right = st.columns([1.2, 0.8], gap="large")

with left:
    st.markdown("### 📝 선택 좌석 전체 리뷰")
    sel = st.session_state.get("selected_seat")

    if not sel:
        st.info("위 좌석표에서 좌석 버튼을 클릭하면, 해당 좌석의 전체 리뷰가 여기에 보여요.")
    else:
        st.markdown(f"**선택 좌석: {sel}**")
        all_reviews = fetch_all_reviews_for_seat(sel)

        if not all_reviews:
            st.warning("아직 리뷰가 없습니다.")
        else:
            for rv in all_reviews:
                st.markdown(f"- **{rv['rating']}점** · {rv['comment']}")

with right:
    st.markdown("### ✍️ 리뷰 작성")
    sel = st.session_state.get("selected_seat")

    if not sel:
        st.info("위 좌석표에서 먼저 좌석을 선택해주세요!")
    else:
        st.success(f"선택 좌석: {sel}")

        rating = st.slider("별점", 1, 5, 5, 1, key="review_rating_by_seat")
        comment = st.text_area(
            "한줄평",
            placeholder="예) 집중 잘 됨 / 꿀잠 가능 / 건조함 ...",
            max_chars=200,
            key="review_comment_by_seat"
        )

        if st.button("💾 리뷰 저장", width="stretch", key="review_save_by_seat"):
            if not comment.strip():
                st.warning("한줄평을 입력해줘!")
            else:
                try:
                    insert_review(sel, rating, comment.strip())
                    st.success("저장 완료! (리뷰는 누적됩니다)")
                    st.rerun()
                except Exception as e:
                    st.error("리뷰 저장 실패")
                    st.exception(e)
