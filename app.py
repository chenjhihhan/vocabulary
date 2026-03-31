import streamlit as st
import string
from supabase import create_client, Client

st.set_page_config(page_title="我的雲端單字本", page_icon="📖")
st.title("📖 我的隨身單字本")

# --- CSS 微調 ---
st.markdown("""
<style>
[class*="st-key-vocab_row_"] {
    display: flex !important;
    flex-wrap: nowrap !important;
    align-items: center !important;
    gap: 0.45rem !important;
    width: 100% !important;
    border-bottom: 1px solid #eeeeee !important;
    padding: 0.45rem 0 !important;
}

[class*="st-key-vocab_row_"] > div:first-child {
    flex: 1 1 auto !important;
    min-width: 0 !important;
}

[class*="st-key-vocab_row_"] p {
    margin: 0 !important;
}

[class*="st-key-vocab_row_"] button {
    min-width: 2.2rem !important;
    width: 2.2rem !important;
    height: 2.2rem !important;
    padding: 0 !important;
    border-radius: 8px !important;
    font-size: 0.95rem !important;
}

.word-line {
    font-size: 1rem;
    line-height: 1.45;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.word-line .english-word {
    color: #2c7be5;
    font-weight: 700;
}

.delete-box {
    background: #fff8f8;
    border: 1px solid #f3caca;
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
    margin: 0.35rem 0 0.7rem 0;
}
</style>
""", unsafe_allow_html=True)

# --- 設定 ---
WORD_TYPES = ["名詞", "動詞", "形容詞", "副詞", "片語", "代名詞", "介系詞", "連接詞", "感嘆詞"]

TYPE_MAP = {
    "名詞": "n.",
    "動詞": "v.",
    "形容詞": "adj.",
    "副詞": "adv.",
    "片語": "phr.",
    "代名詞": "pron.",
    "介系詞": "prep.",
    "連接詞": "conj.",
    "感嘆詞": "interj."
}

# --- 連線 Supabase ---
@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# --- 工具函式 ---
def get_group_key(word):
    if not word:
        return "#"
    first_char = word[0].upper()
    return first_char if first_char in string.ascii_uppercase else "#"

def get_display_type(word_type):
    return TYPE_MAP.get(word_type, word_type)

def load_data():
    response = (
        supabase.table("vocab")
        .select("id, english, chinese, type")
        .order("english")
        .execute()
    )
    return response.data or []

def insert_word(english, chinese, word_type):
    supabase.table("vocab").insert({
        "english": english.strip(),
        "chinese": chinese.strip(),
        "type": word_type.strip()
    }).execute()

def update_word(row_id, english, chinese, word_type):
    supabase.table("vocab").update({
        "english": english.strip(),
        "chinese": chinese.strip(),
        "type": word_type.strip()
    }).eq("id", row_id).execute()

def delete_word(row_id):
    supabase.table("vocab").delete().eq("id", row_id).execute()

def english_exists(english, exclude_id=None):
    rows = (
        supabase.table("vocab")
        .select("id, english")
        .ilike("english", english.strip())
        .execute()
        .data
        or []
    )

    if exclude_id is not None:
        rows = [r for r in rows if r["id"] != exclude_id]

    return len(rows) > 0

def refresh_data():
    st.session_state.vocab = load_data()

# --- 初始化資料 ---
if "vocab" not in st.session_state:
    st.session_state.vocab = load_data()

# --- 編輯視窗 ---
@st.dialog("編輯單字")
def edit_vocab_dialog(item):
    row_id = item["id"]

    with st.form(f"edit_form_{row_id}"):
        col1, col2 = st.columns(2)
    
        with col1:
            new_english = st.text_input("英文單字", value=item["english"]).strip()
    
        with col2:
            new_chinese = st.text_input("中文意思", value=item["chinese"]).strip()

        current_type = item.get("type", "")
        type_index = WORD_TYPES.index(current_type) if current_type in WORD_TYPES else 0

        new_type = st.selectbox(
            "詞性 / 類別",
            options=WORD_TYPES,
            index=type_index,
            format_func=lambda x: get_display_type(x)
        )

        submitted = st.form_submit_button("儲存修改", use_container_width=True)

        if submitted:
            if not new_english:
                st.error("請輸入英文單字")
            elif not new_chinese:
                st.error("請輸入中文意思")
            elif english_exists(new_english, exclude_id=row_id):
                st.warning(f"單字 {new_english} 已經存在，不能重複")
            else:
                update_word(row_id, new_english, new_chinese, new_type)
                refresh_data()
                st.rerun()

# --- 新增單字區 ---
with st.container():
    st.subheader("新增單字", anchor=False)

    with st.form("add_vocab_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
    
        with col1:
            english = st.text_input("英文單字", placeholder="例如: irresistible").strip()
    
        with col2:
            chinese = st.text_input("中文意思", placeholder="例如: 誘人的").strip()
    
        word_type = st.selectbox(
            "詞性 / 類別",
            ["請選擇"] + WORD_TYPES,
            format_func=lambda x: x if x == "請選擇" else get_display_type(x)
        )

        submitted = st.form_submit_button("➕ 新增到清單", use_container_width=True)

        if submitted:
            if not english:
                st.error("請輸入英文單字")
            elif not chinese:
                st.error("請輸入中文意思")
            elif word_type == "請選擇":
                st.error("請選擇詞性 / 類別")
            elif english_exists(english):
                st.warning("這個英文單字已經在清單中囉！")
            else:
                insert_word(english, chinese, word_type)
                refresh_data()
                st.rerun()

st.divider()

# --- 重新整理按鈕 ---
if st.button("🔄 重新整理資料"):
    refresh_data()
    st.rerun()

# --- 目前單字庫 ---
st.subheader(f"目前單字庫（{len(st.session_state.vocab)}）", anchor=False)

if not st.session_state.vocab:
    st.info("目前還沒有單字，快去新增一個吧！")
else:
    grouped_vocab = {}

    for item in st.session_state.vocab:
        group = get_group_key(item["english"])
        grouped_vocab.setdefault(group, []).append(item)

    group_order = list(string.ascii_uppercase) + ["#"]

    for group in group_order:
        if group in grouped_vocab:
            st.subheader(group, anchor=False)

            for item in grouped_vocab[group]:
                row_id = item["id"]
                display_type = get_display_type(item.get("type", ""))

                with st.container(key=f"vocab_row_{row_id}", horizontal=True):
                    st.markdown(
                        f"""
                        <div class='word-line'>
                            <span class='english-word'>{item['english']}</span>
                            ｜ {display_type} ｜ {item['chinese']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button("✏️", key=f"edit_{row_id}", type="tertiary"):
                        edit_vocab_dialog(item)

                    if st.button("🗑️", key=f"delete_{row_id}", type="tertiary"):
                        st.session_state[f"confirm_delete_{row_id}"] = True

                if st.session_state.get(f"confirm_delete_{row_id}", False):
                    st.markdown("<div class='delete-box'>確定要刪除這個單字嗎？</div>", unsafe_allow_html=True)

                    confirm_col, cancel_col = st.columns(2)

                    with confirm_col:
                        if st.button("確認刪除", key=f"confirm_delete_btn_{row_id}", use_container_width=True):
                            delete_word(row_id)
                            st.session_state.pop(f"confirm_delete_{row_id}", None)
                            refresh_data()
                            st.rerun()

                    with cancel_col:
                        if st.button("取消", key=f"cancel_delete_btn_{row_id}", use_container_width=True):
                            st.session_state.pop(f"confirm_delete_{row_id}", None)
                            st.rerun()
