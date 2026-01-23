import re
import streamlit as st
from db import get_connection

st.set_page_config(page_title="집단지성", page_icon="🔗", layout="wide")
st.title("🔗 집단지성")

# ---------------------------
# DB 함수
# ---------------------------
def fetch_categories():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT category_id, category_key, category_name
            FROM useful_categories
            WHERE is_active = 1
            ORDER BY sort_order, category_id;
        """)
        rows = cur.fetchall()
    conn.close()
    return rows

def fetch_links_by_category(category_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT link_id, title, url, description, created_by, created_at
            FROM useful_links
            WHERE is_active = 1 AND category_id = %s
            ORDER BY created_at DESC;
        """, (category_id,))
        rows = cur.fetchall()
    conn.close()
    return rows

def insert_link(category_id: int, title: str, url: str, description: str | None, created_by: str | None):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO useful_links (category_id, title, url, description, created_by)
            VALUES (%s, %s, %s, %s, %s);
        """, (category_id, title, url, description, created_by))
    conn.close()


# ---------------------------
# UI 컴포넌트
# ---------------------------
def render_cards(items, cols=3):
    if not items:
        st.info("아직 등록된 링크가 없어요. 위에서 추가해보세요!")
        return

    rows = (len(items) + cols - 1) // cols
    idx = 0

    for _ in range(rows):
        c = st.columns(cols, gap="large")
        for j in range(cols):
            if idx >= len(items):
                break

            it = items[idx]
            with c[j]:
                desc = it["description"] if it["description"] else "설명 없음"
                author = it["created_by"] if it["created_by"] else "익명"

                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #e5e7eb;
                        border-radius: 14px;
                        padding: 16px;
                        background: white;
                        min-height: 150px;
                    ">
                        <div style="font-size: 16px; font-weight: 800; margin-bottom: 6px;">
                            {it['title']}
                        </div>
                        <div style="font-size: 13px; color: #374151; margin-bottom: 10px;">
                            {desc}
                        </div>
                        <div style="font-size: 12px; color: #6b7280; margin-bottom: 10px;">
                            작성자: {author}
                        </div>
                        <a href="{it['url']}" target="_blank" style="font-size: 13px;">
                            🔗 바로가기
                        </a>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            idx += 1


# ---------------------------
# 메인 로직
# ---------------------------
try:
    categories = fetch_categories()
except Exception as e:
    st.error("❌ 카테고리 로드 실패 (DB 확인 필요)")
    st.exception(e)
    st.stop()

if not categories:
    st.warning("활성 카테고리가 없습니다. useful_categories 테이블을 확인하세요.")
    st.stop()

cat_name_list = [c["category_name"] for c in categories]
cat_map = {c["category_name"]: c["category_id"] for c in categories}
cat_key_map = {c["category_name"]: c["category_key"] for c in categories}

# ---------------------------
# 링크 추가 폼
# ---------------------------
with st.expander("➕ 링크 추가하기", expanded=True):
    st.markdown("- 카테고리를 고르고 사이트/자료/플리 링크를 등록해요.")
    st.markdown("- 같은 카테고리에서 **동일 URL은 중복 저장되지 않아요.**")

    with st.form("add_link_form", clear_on_submit=True):
        cat_name = st.selectbox("카테고리", cat_name_list)
        cat_key = cat_key_map[cat_name]

        # 카테고리에 따라 안내 문구만 살짝 다르게
        if cat_key == "playlist":
            title_ph = "예) 코딩할 때 듣는 플레이리스트 / 집중 OST / lo-fi 모음"
            desc_ph = "예) 밤샘용 / 집중용 / 멘탈회복 / 면접 전 긴장 풀기"
        else:
            title_ph = "예) 공공데이터포털 / SQLD 기출 모음 / 테디노트 ..."
            desc_ph = "예) 프로젝트에 도움됨 / 기출 모음 / 최신 이슈 정리"

        title = st.text_input("제목(사이트/플리/자료 이름)", placeholder=title_ph)
        url = st.text_input("링크(URL)", placeholder="https:// 로 시작 (유튜브/스포티파이/웹사이트)")
        description = st.text_input("간단 설명(선택)", placeholder=desc_ph)
        created_by = st.text_input("작성자(선택)", placeholder="예) 짱구 / 익명 가능")

        submitted = st.form_submit_button(" ✚ 추가하기 ✚ ", use_container_width=True)

    if submitted:
        title = title.strip()
        url = url.strip()
        description = description.strip() if description and description.strip() else None
        created_by = created_by.strip() if created_by and created_by.strip() else None

        if not title:
            st.warning("제목을 입력해줘!")
        elif not url:
            st.warning("URL을 입력해줘!")
        elif not re.match(r"^https?://", url):
            st.warning("URL은 http:// 또는 https:// 로 시작해야 해요.")
        else:
            try:
                insert_link(
                    category_id=cat_map[cat_name],
                    title=title,
                    url=url,
                    description=description,
                    created_by=created_by
                )
                st.success("저장 완료! 아래 목록에 반영됐어요.")
                st.rerun()
            except Exception as e:
                st.error("저장 실패: 이미 등록된 링크이거나 DB 오류일 수 있어요.")
                st.exception(e)

st.divider()

# ---------------------------
# 카테고리별 탭 출력
# ---------------------------
tabs = st.tabs(cat_name_list)

for tab, cinfo in zip(tabs, categories):
    with tab:
        try:
            items = fetch_links_by_category(cinfo["category_id"])
        except Exception as e:
            st.error("❌ 링크 조회 실패")
            st.exception(e)
            continue

        # 플리 탭은 카드 2열로(가독성)
        if cinfo["category_key"] == "playlist":
            render_cards(items, cols=2)
        else:
            render_cards(items, cols=3)
