import os
import tomllib
import random
import streamlit as st
import pymysql


# 스트림릿 기본 설정 
st.set_page_config(page_title="랜덤 자리배정", page_icon="🎲", layout="wide")
# ---------------
# DB 설정 로드
# ---------------

#MySQL 접속 정보를 로드하는 함수
#1. Streamlit secrets (st.secrets) 우선 사용
#2. 없으면 pages/.streamlit/secrets.toml 직접 로드

def load_mysql_cfg():

    # 1) Streamlit Cloud 또는 로컬 secrets 사용 시
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
    MySQL DB 커넥션 생성 함수
    - DictCursor 사용 (컬럼명 접근)
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

# ---------------------------
# DB 조회 / 조작함수 
# ---------------------------
def fetch_students():
    # 활성화된 학생 목록 조회
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
    # 활성화된 좌석 목록 조회
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
    기존 자리 배정 결과 초기화
    - assignment 테이블 비우기
    - AUTO_INCREMENT 리셋
    """
       
    conn = get_conn()
    with conn.cursor() as cur:
        # 배정만 초기화
        cur.execute("DELETE FROM seat_assignments;")
        cur.execute("ALTER TABLE seat_assignments AUTO_INCREMENT = 1;")
    conn.close()



def insert_assignments(pairs):
    """
    (student_id, seat_id) 튜플 리스트를
    seat_assignments 테이블에 일괄 저장
    """    
    conn = get_conn()
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO seat_assignments (student_id, seat_id) VALUES (%s, %s);",
            pairs
        )
    conn.close()

def fetch_assignments_view():
    # 좌석 배정 결과 조회(화면 출력용)
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
    seat_code -> student_name 형태의 매핑 생성
    (좌석 UI 렌더링용)
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

def render_section(title, start_row, end_row, cols=4, seat_map=None):
    """
    자리 배치 시각화 함수
    - start_row ~ end_row: row_no 범위
    - cols: 한 행당 좌석 개수
    - seat_map: seat_code -> student_name
    """
    st.markdown(f"### {title}")
    seat_map = seat_map or {}

    # 예: start_row=1, end_row=4 -> A~D (row_no 1~4)
    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            # seat_code는 우리가 A~I로 넣었으니 row_no -> 문자 변환
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
            LEFT JOIN seat_assignments a ON a.seat_id = se.seat_id
            LEFT JOIN seat_reviews r ON r.assignment_id = a.assignment_id
            GROUP BY se.seat_code;
        """)
        rows = cur.fetchall()
    conn.close()
    return {r["seat_code"]: (float(r["avg_rating"]) if r["avg_rating"] is not None else None, int(r["cnt"])) for r in rows}

def fetch_recent_reviews_tooltip_map(limit_per_seat: int = 3):
    """
    seat_code -> tooltip_text (최근 리뷰 몇 개 + 평균)
    간단 호버용 텍스트
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
            se.seat_code,
            r.rating,
            r.comment,
            r.created_at
            FROM seat_reviews r
            JOIN seat_assignments a ON a.assignment_id = r.assignment_id
            JOIN seats se ON se.seat_id = a.seat_id
            ORDER BY se.seat_code, r.created_at DESC;
        """)
        rows = cur.fetchall()
    conn.close()

    # seat_code별로 최근 limit개만 모으기
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

    # 문자열로 합치기
    out = {}
    for sc, lines in tooltips.items():
        out[sc] = "\n".join(lines)
    return out

# ===========================
#  좌석별 전체 리뷰 조회
# ===========================

def fetch_all_reviews_for_seat(seat_code: str):

    """
    특정 좌석(seat_code)에 달린 모든 리뷰를 최신순으로 조회
    - 별점, 한줄평, 작성 시각, 작성 학생 이름 포함
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
            r.rating,
            r.comment,
            r.created_at,
            st.name AS student_name
            FROM seat_reviews r
            JOIN seat_assignments a ON a.assignment_id = r.assignment_id
            JOIN seat_students st ON st.student_id = a.student_id
            JOIN seats se ON se.seat_id = a.seat_id
            WHERE se.seat_code = %s
            ORDER BY r.created_at DESC;
        """, (seat_code,))
        rows = cur.fetchall()
    conn.close()
    return rows

# ===========================
# 리뷰용 좌석 선택 UI
# ===========================

def render_review_section(title, start_row, end_row, cols, avg_map, tooltip_map):
    """
    좌석 리뷰 선택용 UI 렌더링
    - 좌석 버튼 클릭 시 session_state에 selected_seat 저장
    - hover 시 평균 별점 + 최근 리뷰 미리보기 제공
    """
    st.markdown(f"### {title}")

    if "selected_seat" not in st.session_state:
        st.session_state["selected_seat"] = None

    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            seat_code = f"{chr(ord('A') + (r - 1))}{c}"
            avg, cnt = avg_map.get(seat_code, (None, 0))

            # 호버에 보여줄 텍스트 구성 
            tip_lines = []
            if avg is None:
                tip_lines.append("평균 별점: 없음")
            else:
                tip_lines.append(f"평균 별점: {avg:.2f} (리뷰 {cnt}개)")

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
                    use_container_width=True,
                    help=hover_text  # 마우스 hover 시만 표시 
                ):
                    st.session_state["selected_seat"] = seat_code


# ===========================
#  학생 기준 배정 좌석 조회
# ===========================

def fetch_my_assignment(student_id: int):
    """
    특정 학생의 현재 좌석 배정 정보 조회
    - 배정이 없으면 None 반환
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.assignment_id, se.seat_code, a.assigned_at
            FROM seat_assignments a
            JOIN seats se ON se.seat_id = a.seat_id
            WHERE a.student_id = %s
            LIMIT 1;
        """, (student_id,))
        row = cur.fetchone()
    conn.close()
    return row

# ===========================
# 리뷰 저장
# ===========================

def insert_review(assignment_id: int, rating: int, comment: str):
    """
    좌석 리뷰 저장
    - 리뷰는 누적 저장 (삭제/수정 없음)
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO seat_reviews (assignment_id, rating, comment)
            VALUES (%s, %s, %s);
        """, (assignment_id, rating, comment))
    conn.close()

# ===========================
# 좌석 코드 → assignment_id 조회
# ===========================

def fetch_assignment_id_by_seat_code(seat_code: str):
    """
    현재 해당 좌석에 배정된 assignment_id 반환
    - 아직 배정이 없으면 None
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT a.assignment_id
            FROM seat_assignments a
            JOIN seats se ON se.seat_id = a.seat_id
            WHERE se.seat_code = %s
            LIMIT 1;
        """, (seat_code,))
        row = cur.fetchone()
    conn.close()
    return None if not row else row["assignment_id"]


# ---------------------------
# UI
# ---------------------------
st.title("🎲 두근두근 랜덤 자리배정 ")

# 학생 / 좌석 정보 로드 
try:
    students = fetch_students()
    seats = fetch_seats()
except Exception as e:
    st.error("DB 조회 실패")
    st.exception(e)
    st.stop()

# 상단통계 카드 
colA, colB, colC = st.columns(3)
colA.metric("학생 수", len(students))
colB.metric("활성 좌석 수", len(seats))
colC.metric("남는 좌석 수", len(seats) - len(students))

# 좌석 부족 시 중단 
if len(seats) < len(students):
    st.error("좌석 수가 학생 수보다 적어요. seats 데이터를 확인하세요.")
    st.stop()

st.divider()

left, right = st.columns(2)


# ===========================
# 랜덤 자리 배정 버튼
# ===========================
if st.button("🎲 랜덤 자리 뽑기 !! ", use_container_width=True):
    try:
        # 기존 배정 초기화
        clear_assignments()

        # 학생/좌석 랜덤 섞기
        random.shuffle(students)
        seat_pool = seats[:]
        random.shuffle(seat_pool)

        # (학생,좌석)매칭 
        pairs = []
        for i, stu in enumerate(students):
            pairs.append((stu["student_id"], seat_pool[i]["seat_id"]))

        insert_assignments(pairs)
        st.success("랜덤 배정 완료!")
        st.rerun()
    except Exception as e:
        st.error("랜덤 배정 실패")
        st.exception(e)

st.divider()
st.subheader(" 🧑‍🧑‍🧒‍🧒 자리 배정 결과")

rows = fetch_assignments_view()
if not rows:
    st.info("아직 배정 결과가 없습니다. 위 버튼으로 배정을 실행하세요.")
else:
    seat_map = fetch_assignments_map()

    # ✅ 위치 고정: 왼쪽=1분단, 오른쪽=2분단
    left, right = st.columns([1, 1], gap="large")

    with left:
        render_section("2분단", start_row=5, end_row=9, cols=4, seat_map=seat_map)

    with right:
        render_section("1분단", start_row=1, end_row=4, cols=4, seat_map=seat_map)


# ===========================
# 리뷰 섹션 
# ===========================
st.divider()
st.subheader("⭐ 좌석 리뷰 ")

# 평균별점/호버용 최근리뷰 텍스트
avg_map = fetch_avg_rating_map()
tooltip_map = fetch_recent_reviews_tooltip_map(limit_per_seat=3)

# 리뷰용 좌석표 - 클릭으로 선택
l, r = st.columns([1, 1], gap="large")
with l:
    render_review_section("2분단", 5,9,4, avg_map, tooltip_map)
with r:
    render_review_section("1분단", 1,4,4, avg_map, tooltip_map)

st.divider()

# 아래: 좌석 선택 시 전체 리뷰 / 오른쪽: 리뷰 작성
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
                st.markdown(
                    f"- **{rv['rating']}점** · {rv['comment']}",
                    unsafe_allow_html=True
                )

with right:
    st.markdown("### ✍️ 리뷰 작성")

    sel = st.session_state.get("selected_seat")
    if not sel:
        st.info("위 좌석표에서 먼저 좌석을 선택해주세요!")
    else:
        st.success(f"선택 좌석: {sel}")

        assignment_id = fetch_assignment_id_by_seat_code(sel)
        if assignment_id is None:
            st.error("이 좌석은 현재 배정 정보가 없어서 리뷰를 저장할 수 없어요. (랜덤 배정 먼저!)")
        else:
            rating = st.slider("별점", 1, 5, 5, 1, key="review_rating_by_seat")
            comment = st.text_area(
                "한줄평",
                placeholder="예) 집중 잘 됨 / 꿀잠 가능 / 건조함 ...",
                max_chars=200,
                key="review_comment_by_seat"
            )

            if st.button("💾 리뷰 저장", use_container_width=True, key="review_save_by_seat"):
                if not comment.strip():
                    st.warning("한줄평을 입력해줘!")
                else:
                    insert_review(assignment_id, rating, comment.strip())
                    st.success("저장 완료! (리뷰는 누적됩니다)")
                    st.rerun()




