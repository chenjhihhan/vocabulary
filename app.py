import streamlit as st
import json
import os

# --- 設定頁面 ---
st.set_page_config(page_title="我的雲端單字本", page_icon="📖")
st.title("📖 我的隨身單字本")

# --- 資料處理函數 ---
DB_FILE = "vocab.json"

def load_data():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    # 存檔前先按字母順序排列 (不分大小寫)
    data.sort(key=str.lower)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 初始化資料
if 'vocab' not in st.session_state:
    st.session_state.vocab = load_data()

# --- 介面設計 ---

# 1. 新增單字區
with st.container():
    new_word = st.text_input("輸入新單字 (英文):", placeholder="例如: Apple").strip()
    if st.button("➕ 新增到清單", use_container_width=True):
        if new_word:
            if new_word not in st.session_state.vocab:
                st.session_state.vocab.append(new_word)
                save_data(st.session_state.vocab)
                st.success(f"成功加入: {new_word}")
                st.rerun() # 重新整理頁面以更新排序
            else:
                st.warning("這個單字已經在清單中囉！")
        else:
            st.error("請輸入單字內容")

st.divider()

# 2. 顯示清單區
st.subheader(f"目前單字庫 ({len(st.session_state.vocab)})")

if not st.session_state.vocab:
    st.info("目前還沒有單字，快去新增一個吧！")
else:
    # 建立表格顯示，並提供刪除按鈕
    for i, word in enumerate(st.session_state.vocab):
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{i+1}. {word}**")
        if col2.button("🗑️", key=f"del_{word}"):
            st.session_state.vocab.remove(word)
            save_data(st.session_state.vocab)
            st.rerun()