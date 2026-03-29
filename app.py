import streamlit as st
import json
import os
import string

# --- 設定頁面 ---
st.set_page_config(page_title="我的雲端單字本", page_icon="📖")
st.title("📖 我的隨身單字本")

# --- 資料處理 ---
DB_FILE = "vocab.json"


def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

            # 相容舊資料：如果以前是純字串，轉成新格式
            converted = []
            for item in data:
                if isinstance(item, str):
                    converted.append({
                        "english": item,
                        "chinese": ""
                    })
                elif isinstance(item, dict):
                    converted.append({
                        "english": item.get("english", "").strip(),
                        "chinese": item.get("chinese", "").strip()
                    })
            return converted
    return []


def save_data(data):
    # 依英文排序（不分大小寫）
    data.sort(key=lambda x: x["english"].lower())
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_group_key(word):
    """依英文首字母分組，非 A-Z 的歸類到 #"""
    if not word:
        return "#"
    first_char = word[0].upper()
    if first_char in string.ascii_uppercase:
        return first_char
    return "#"


# 初始化資料
if "vocab" not in st.session_state:
    st.session_state.vocab = load_data()

# --- 新增單字區 ---
with st.container():
    st.subheader("新增單字")

    english = st.text_input("英文單字", placeholder="例如: apple").strip()
    chinese = st.text_input("中文意思", placeholder="例如: 蘋果").strip()

    if st.button("➕ 新增到清單", use_container_width=True):
        if not english:
            st.error("請輸入英文單字")
        elif not chinese:
            st.error("請輸入中文意思")
        else:
            # 檢查是否重複（以英文為主，不分大小寫）
            exists = any(item["english"].lower() == english.lower() for item in st.session_state.vocab)

            if exists:
                st.warning("這個英文單字已經在清單中囉！")
            else:
                st.session_state.vocab.append({
                    "english": english,
                    "chinese": chinese
                })
                save_data(st.session_state.vocab)
                st.success(f"成功加入：{english} / {chinese}")
                st.rerun()

st.divider()

# --- 顯示單字區 ---
st.subheader(f"目前單字庫（{len(st.session_state.vocab)}）")

if not st.session_state.vocab:
    st.info("目前還沒有單字，快去新增一個吧！")
else:
    # 建立分組
    grouped_vocab = {}

    for item in st.session_state.vocab:
        group = get_group_key(item["english"])
        if group not in grouped_vocab:
            grouped_vocab[group] = []
        grouped_vocab[group].append(item)

    # 顯示分組：A-Z，再顯示 #
    group_order = list(string.ascii_uppercase) + ["#"]

    for group in group_order:
        if group in grouped_vocab:
            st.markdown(f"## {group}")

            for i, item in enumerate(grouped_vocab[group]):
                col1, col2 = st.columns([6, 1])
                col1.write(f"**{item['english']}**　—　{item['chinese']}")

                unique_key = f"{group}_{item['english']}_{i}"
                if col2.button("🗑️", key=unique_key):
                    st.session_state.vocab.remove(item)
                    save_data(st.session_state.vocab)
                    st.rerun()
