import os
import tomllib
import random
import streamlit as st
import pymysql

# ===========================
# Streamlit 기본 설정
# ===========================
# - 페이지 제목/아이콘/레이아웃(와이드) 고정
# - set_page_config는 Streamlit 앱에서 가장 먼저 실행되는 것이 권장됨
st.set_page_config(page_title="랜덤 자리배정", page_icon="🎲", layout="wide")

# ===========================
# DB 설정 로드
# ===========================
def load_mysql_cfg():
    """
    MySQL 접속 정보를 로드하는 함수

    우선순위:
    1) st.secrets["mysql"] (Streamlit Cloud / 로컬 .streamlit/secrets.toml 자동 로드)
    2) (대안) pages/.streamlit/secrets.toml을 직접 읽어서 로드

    이렇게 해두면:
    - Streamlit Cloud 배포 시 secrets 관리가 쉬움
    - 로컬에서도 pages 내부에서 실행하는 경우를 커버 가능
    """
    # 1) Streamlit secrets에서 먼저 시도
    # - Streamlit Cloud는 st.secrets에 등록해두면 자동으로 주입됨
    # - 로컬도 프로젝트 루트의 .streamlit/secrets.toml이 있으면 st.secrets로 접근 가능
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
        # secrets가 없거나 키가 없을 때는 2번 방식으로 넘어감
        pass

    # 2) pages/.streamlit/secrets.toml 직접 로드
    # - 멀티페이지 구조에서 "pages 폴더에서 직접 실행"하는 상황을 대비
    base_dir = os.path.dirname(__file__)  # 현재 파일 기준(= pages 폴더)
    secrets_path = os.path.join(base_dir, ".streamlit", "secrets.toml")

    if not os.path.exists(secrets_path):
        # 배포/로컬 어디서든 secrets 파일이 없으면 바로 중단
        st.error(f"secrets.toml 없음: {secrets_path}")
        st.stop()

    # tomllib: Python 3.11+ 내장 TOML 파서
    with open(secrets_path, "rb") as f:
        data = tomllib.load(f)

    if "mysql" not in data:
        # [mysql] 섹션이 없으면 커넥션 정보가 없으므로 중단
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

    주요 포인트:
    - DictCursor: fetch 결과를 dict로 받아서 r["seat_code"] 같은 접근이 가능
    - autocommit=True: DML(INSERT/DELETE) 후 commit을 따로 호출하지 않아도 바로 반영
      (좌석 배정/리뷰 저장 같은 단순 트랜잭션에 편리)
    - timeout 설정: 네트워크/클라우드 환경에서 무한 대기 방지
    """
    cfg = load_mysql_cfg()
    return pymysql.connect(
        host=cfg["host"],
        port=cfg["port"],
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        charset="utf8mb4",  # 한글/이모지 저장을 포함한 안전한 UTF-8 설정
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
    """
    활성 학생 목록 조회
    - is_active=1: 실제 운영에서 비활성 학생(휴강/중도포기 등) 제외 가능
    - ORDER BY name: UI 노출 시 안정적인 정렬
    """
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
    """
    활성 좌석 목록 조회
    - row_no/col_no로 정렬하면 좌석 배치 렌더링과 동일한 순서 유지 가능
    """
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

    설계 의도:
    - seat_assignments만 삭제해서 "현재 배정표"만 리셋
    - seat_reviews는 seat_id 기반으로 별도 테이블에 누적 저장되므로 리뷰 데이터는 유지됨

    참고:
    - AUTO_INCREMENT를 1로 재설정하면 배정 히스토리 테이블이 아니라 "현황 테이블"로 운용하는 느낌이 됨
    - 만약 배정 기록(회차별)을 남기고 싶다면 DELETE 대신 assignment_round 컬럼 추가 설계가 더 적합
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM seat_assignments;")
        cur.execute("ALTER TABLE seat_assignments AUTO_INCREMENT = 1;")
    conn.close()

def insert_assignments(pairs):
    """
    (student_id, seat_id) 리스트를 seat_assignments에 저장

    - executemany: 다건 INSERT 시 루프 돌며 execute 하는 것보다 빠르고 코드도 간결
    - pairs 예시: [(1, 12), (2, 3), ...]
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO seat_assignments (student_id, seat_id) VALUES (%s, %s);",
            pairs
        )
    conn.close()

def fetch_assignments_view():
    """
    배정 결과를 좌석 순서대로 조회

    - seat_assignments(배정) + seat_students(학생) + seats(좌석) 조인
    - ORDER BY row_no, col_no: 화면 렌더링과 동일한 좌석 순서로 결과를 얻기 위함
    """
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
    seat_code -> student_name 매핑 생성(좌석 렌더링용)

    이유:
    - UI에서 좌석을 그릴 때는 "좌석코드별 현재 학생"을 빠르게 lookup하는 dict가 편함
    - DB 결과(rows)를 그대로 쓰면 매번 검색 비용이 들 수 있어 dict로 변환
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
    """
    seat_code(A1 같은 화면용 코드) -> seat_id(DB PK) 변환

    설계 의도:
    - 리뷰는 좌석의 고유키(seat_id)에 귀속시키는 것이 정규화 관점에서 안전함
    - seat_code가 변경되더라도 seat_id가 유지되면 리뷰 데이터는 안정적으로 남음
    """
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute("SELECT seat_id FROM seats WHERE seat_code=%s LIMIT 1;", (seat_code,))
        row = cur.fetchone()
    conn.close()
    return None if not row else row["seat_id"]

def insert_review(seat_code: str, rating: int, comment: str):
    """
    배정 여부와 상관없이 좌석 리뷰 저장

    핵심:
    - 배정 테이블과 리뷰 테이블을 분리해서 "리뷰는 누적 자산"으로 관리
    - seat_code는 UI 입력값이므로 DB 저장 시 seat_id로 변환해서 저장
    """
    seat_id = fetch_seat_id_by_seat_code(seat_code)
    if seat_id is None:
        # 존재하지 않는 좌석코드가 들어오면 데이터 무결성이 깨지므로 예외 처리
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

    주의:
    - 현재 스키마에서는 리뷰 작성자를 저장하지 않으므로 student_name 조인 불가
    - 작성자를 남기고 싶다면 seat_reviews에 작성자(익명 닉네임/학생ID) 컬럼을 추가하는 방식이 필요
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

    - LEFT JOIN: 리뷰가 없는 좌석도 포함시키기 위해 사용
    - AVG는 리뷰가 없으면 NULL이 나오므로 Python에서 None 처리 필요
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

    구현 포인트:
    - Streamlit의 button help 파라미터를 활용해 hover tooltip로 정보를 제공
    - 좌석별 최신 리뷰 N개만 보여주기 위해 Python에서 limit 로직 수행
      (DB에서 좌석별 top-N을 바로 뽑는 쿼리도 가능하지만 구현 난이도가 올라감)
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

        # 좌석별 최근 limit개까지만 누적
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
    """
    배정 결과(좌석표) 렌더링

    - 좌석코드 생성 규칙:
      row: A,B,C... / col: 1,2,3...
      예) A1, A2, ... / B1, ...
    - seat_map에 값이 없으면 '—'로 표시
    """
    st.markdown(f"### {title}")
    seat_map = seat_map or {}

    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            seat_code = f"{chr(ord('A') + (r - 1))}{c}"
            student = seat_map.get(seat_code, "—")

            # HTML/CSS로 카드 형태 좌석 UI 구성
            # unsafe_allow_html=True: Streamlit 기본 마크다운 제약을 넘기 위해 사용
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

    동작:
    - 좌석 버튼 클릭 -> st.session_state["selected_seat"]에 선택 좌석 저장
    - hover(help) -> 평균 별점/리뷰 수/최근 한줄평을 tooltip로 표시

    session_state를 쓰는 이유:
    - Streamlit은 위젯 상호작용 시 스크립트를 위에서부터 재실행
    - 선택 상태를 유지하려면 session_state 같은 상태 저장소가 필요
    """
    st.markdown(f"### {title}")

    if "selected_seat" not in st.session_state:
        st.session_state["selected_seat"] = None

    for r in range(start_row, end_row + 1):
        row_cols = st.columns(cols, gap="small")
        for c in range(1, cols + 1):
            seat_code = f"{chr(ord('A') + (r - 1))}{c}"
            avg, cnt = avg_map.get(seat_code, (None, 0))

            # tooltip 내용 구성: 평균 + 최근 리뷰
            tip_lines = []
            tip_lines.append("평균 별점: 없음" if avg is None else f"평균 별점: {avg:.2f} (리뷰 {cnt}개)")

            tip = tooltip_map.get(seat_code)
            if tip:
                tip_lines.append("")
                tip_lines.append("최근 한줄평")
                tip_lines.append(tip)

            hover_text = "\n".join(tip_lines)

            with row_cols[c - 1]:
                # key는 위젯 ID 충돌을 막기 위해 필수(특히 반복문에서 버튼 생성 시)
                # width="stretch": 전체 너비 확장(버전별 use_container_width 대체)
                if st.button(
                    seat_code,
                    key=f"seatbtn_review_{seat_code}",
                    width="stretch",
                    help=hover_text
                ):
                    st.session_state["selected_seat"] = seat_code

# ===========================
# UI 시작
# ===========================
st.title("🎲 두근두근 랜덤 자리뽑기")

# 학생 / 좌석 로드
# - DB 연결 실패 시 앱이 계속 실행되면 이후 로직도 줄줄이 실패하므로 초기에 중단 처리
try:
    students = fetch_students()
    seats = fetch_seats()
except Exception as e:
    st.error("DB 조회 실패")
    st.exception(e)
    st.stop()

# 상단 통계
# - metric으로 핵심 수치(학생 수/좌석 수/남는 좌석)를 한눈에 보여줌
colA, colB, colC = st.columns(3)
colA.metric("학생 수", len(students))
colB.metric("활성 좌석 수", len(seats))
colC.metric("남는 좌석 수", len(seats) - len(students))

# 좌석이 부족하면 배정을 할 수 없으므로 즉시 중단
if len(seats) < len(students):
    st.error("좌석 수가 학생 수보다 적어요. seats 데이터를 확인하세요.")
    st.stop()

st.divider()

# ===========================
# 랜덤 자리 배정
# ===========================
# - 클릭 시 기존 배정 초기화 후, 학생/좌석을 각각 셔플해서 1:1로 매핑
# - 완료 후 st.rerun()으로 즉시 화면을 최신 상태로 갱신
if st.button("🎲 랜덤 자리 뽑기 !!", width="stretch"):
    try:
        clear_assignments()

        random.shuffle(students)   # 학생 순서 랜덤화
        seat_pool = seats[:]       # 원본 보존을 위해 복사
        random.shuffle(seat_pool)  # 좌석도 랜덤화

        pairs = [(stu["student_id"], seat_pool[i]["seat_id"]) for i, stu in enumerate(students)]
        insert_assignments(pairs)

        st.success("랜덤 배정 완료!")
        st.rerun()
    except Exception as e:
        st.error("랜덤 배정 실패")
        st.exception(e)

st.divider()
st.subheader("🧑‍🧑‍🧒‍🧒 자리 배정 결과")

# 배정 결과 조회
rows = fetch_assignments_view()
if not rows:
    st.info("아직 배정 결과가 없습니다. 위 버튼으로 배정을 실행하세요.")
else:
    # 좌석표 렌더링은 seat_code -> student_name 매핑이 편하므로 dict 형태로 변환해 사용
    seat_map = fetch_assignments_map()

    left_col, right_col = st.columns([1, 1], gap="large")
    with left_col:
        render_section("2분단", start_row=5, end_row=9, cols=4, seat_map=seat_map)
    with right_col:
        render_section("1분단(사물함쪽)", start_row=1, end_row=4, cols=4, seat_map=seat_map)

# ===========================
# 리뷰 섹션
# ===========================
st.divider()
st.subheader("⭐ 좌석 리뷰")

# 좌석별 평균 별점/리뷰 수, 그리고 tooltip용 최근 리뷰를 미리 계산
# - UI 렌더링 중 매 좌석마다 DB 조회를 하면 느려질 수 있으니 한번에 가져와 map으로 사용
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
    render_review_section("1분단(사물함쪽)", 1,4,4, avg_map, tooltip_map)

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
            # 최신순으로 가져온 리뷰를 리스트 형태로 출력
            for rv in all_reviews:
                st.markdown(f"- **{rv['rating']}점** · {rv['comment']}")

with right:
    st.markdown("### ✍️ 리뷰 작성")
    sel = st.session_state.get("selected_seat")

    if not sel:
        st.info("위 좌석표에서 먼저 좌석을 선택해주세요!")
    else:
        st.success(f"선택 좌석: {sel}")

        # slider: 별점 입력(1~5)
        # text_area: 200자 제한
        rating = st.slider("별점", 1, 5, 5, 1, key="review_rating_by_seat")
        comment = st.text_area(
            "한줄평",
            placeholder="예) 집중 잘 됨 / 꿀잠 가능 / 건조함 ...",
            max_chars=200,
            key="review_comment_by_seat"
        )

        # 저장 버튼 클릭 시:
        # - 공백 리뷰 방지
        # - 저장 후 rerun으로 즉시 반영
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
