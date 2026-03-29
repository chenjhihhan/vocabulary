import streamlit as st
import json
import os
import string

# --- 設定頁面 ---
st.set_page_config(page_title="我的雲端單字本", page_icon="📖")
st.title("📖 我的隨身單字本")

# --- 資料設定 ---
DB_FILE = "vocab.json"
WORD_TYPES = ["名詞", "動詞", "形容詞", "副詞", "片語", "代名詞", "介系詞", "連接詞", "感嘆詞"]

# 中文詞性 -> 英文縮寫
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


# --- 資料處理函數 ---
def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            converted = []
            for item in data:
                if isinstance(item, str):
                    converted.append({
                        "english": item.strip(),
                        "chinese": "",
                        "type": ""
                    })
                elif isinstance(item, dict):
                    converted.append({
                        "english": item.get("english", "").strip(),
                        "chinese": item.get("chinese", "").strip(),
                        "type": item.get("type", "").strip()
                    })
            return converted
    return []


def save_data(data):
    data.sort(key=lambda x: x["english"].lower())
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_group_key(word):
    if not word:
        return "#"
    first_char = word[0].upper()
    if first_char in string.ascii_uppercase:
        return first_char
    return "#"


def get_display_type(word_type):
    return TYPE_MAP.get(word_type, word_type)


# --- 初始化資料 ---
if "vocab" not in st.session_state:
    st.session_state.vocab = load_data()


# --- 編輯視窗 ---
@st.dialog("編輯單字")
def edit_vocab_dialog(idx):
    item = st.session_state.vocab[idx]

    with st.form(f"edit_form_{idx}"):
        new_english = st.text_input(
            "英文單字",
            value=item["english"]
        ).strip()

        current_type = item.get("type", "")
        if current_type in WORD_TYPES:
            type_index = WORD_TYPES.index(current_type)
        else:
            type_index = 0

        new_type = st.selectbox(
            "詞性 / 類別",
            options=WORD_TYPES,
            index=type_index,
            format_func=lambda x: get_display_type(x)
        )

        new_chinese = st.text_input(
            "中文意思",
            value=item["chinese"]
        ).strip()

        submitted = st.form_submit_button("儲存修改", use_container_width=True)

        if submitted:
            if not new_english:
                st.error("請輸入英文單字")
            elif not new_chinese:
                st.error("請輸入中文意思")
            else:
                duplicate = any(
                    i != idx and vocab_item["english"].lower() == new_english.lower()
                    for i, vocab_item in enumerate(st.session_state.vocab)
                )

                if duplicate:
                    st.warning(f"單字 {new_english} 已經存在，不能重複")
                else:
                    st.session_state.vocab[idx] = {
                        "english": new_english,
                        "chinese": new_chinese,
                        "type": new_type
                    }
                    save_data(st.session_state.vocab)
                    st.success(
                        f"已更新：{new_english} / {get_display_type(new_type)} / {new_chinese}"
                    )
                    st.rerun()


# --- 新增單字區 ---
with st.container():
    st.subheader("新增單字")

    with st.form("add_vocab_form", clear_on_submit=True):
        english = st.text_input("英文單字", placeholder="例如: irresistible").strip()
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
            else:
                exists = any(
                    item["english"].lower() == english.lower()
                    for item in st.session_state.vocab
                )

                if exists:
                    st.warning("這個英文單字已經在清單中囉！")
                else:
                    st.session_state.vocab.append({
                        "english": english,
                        "chinese": chinese,
                        "type": word_type
                    })
                    save_data(st.session_state.vocab)
                    st.success(
                        f"成功加入：{english} / {get_display_type(word_type)} / {chinese}"
                    )
                    st.rerun()

st.divider()

# --- 顯示單字區 ---
st.subheader(f"目前單字庫（{len(st.session_state.vocab)}）")

if not st.session_state.vocab:
    st.info("目前還沒有單字，快去新增一個吧！")
else:
    grouped_vocab = {}

    for idx, item in enumerate(st.session_state.vocab):
        group = get_group_key(item["english"])
        if group not in grouped_vocab:
            grouped_vocab[group] = []
        grouped_vocab[group].append((idx, item))

    group_order = list(string.ascii_uppercase) + ["#"]

    for group in group_order:
        if group in grouped_vocab:
            st.markdown(f"## {group}")

            for idx, item in grouped_vocab[group]:
                col1, col2, col3 = st.columns([8, 1, 1])

                display_text = f"**{item['english']}** ｜ {get_display_type(item.get('type', ''))} ｜ {item['chinese']}"
                col1.write(display_text)

                if col2.button("✏️", key=f"edit_{idx}"):
                    edit_vocab_dialog(idx)

                if col3.button("🗑️", key=f"delete_{idx}"):
                    st.session_state.vocab.pop(idx)
                    save_data(st.session_state.vocab)
                    st.rerun()
