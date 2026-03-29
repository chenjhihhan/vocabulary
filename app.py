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


# --- 初始化資料 ---
if "vocab" not in st.session_state:
    st.session_state.vocab = load_data()


# --- 新增單字區 ---
with st.container():
    st.subheader("新增單字")

    with st.form("add_vocab_form", clear_on_submit=True):
        english = st.text_input("英文單字", placeholder="例如: irresistible").strip()
        chinese = st.text_input("中文意思", placeholder="例如: 誘人的").strip()
        word_type = st.selectbox("詞性 / 類別", ["請選擇"] + WORD_TYPES)

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
                    st.success(f"成功加入：{english} / {word_type} / {chinese}")
                    st.rerun()

st.divider()

# --- 顯示單字區 ---
st.subheader(f"目前單字庫（{len(st.session_state.vocab)}）")

if not st.session_state.vocab:
    st.info("目前還沒有單字，快去新增一個吧！")
else:
    grouped_vocab = {}

    for item in st.session_state.vocab:
        group = get_group_key(item["english"])
        if group not in grouped_vocab:
            grouped_vocab[group] = []
        grouped_vocab[group].append(item)

    group_order = list(string.ascii_uppercase) + ["#"]

    for group in group_order:
        if group in grouped_vocab:
            st.markdown(f"## {group}")

            for i, item in enumerate(grouped_vocab[group]):
                col1, col2 = st.columns([8, 1])

                text = f"**{item['english']}**　{item.get('type', '')}　{item['chinese']}"
                col1.write(text)

                unique_key = f"{group}_{item['english']}_{i}"
                if col2.button("🗑️", key=unique_key):
                    st.session_state.vocab.remove(item)
                    save_data(st.session_state.vocab)
                    st.rerun()
