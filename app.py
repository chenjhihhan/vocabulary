import streamlit as st
import json
import os
import string
import pandas as pd

# --- 設定頁面 ---
st.set_page_config(page_title="我的雲端單字本", page_icon="📖")
st.title("📖 我的隨身單字本")

# --- 資料設定 ---
DB_FILE = "vocab.json"
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

REVERSE_TYPE_MAP = {v: k for k, v in TYPE_MAP.items()}


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
    return first_char if first_char in string.ascii_uppercase else "#"


def get_display_type(word_type):
    return TYPE_MAP.get(word_type, word_type)


def to_editor_df(vocab_list):
    rows = []
    for item in vocab_list:
        rows.append({
            "刪除": False,
            "英文": item.get("english", ""),
            "詞性": get_display_type(item.get("type", "")),
            "中文": item.get("chinese", "")
        })
    return pd.DataFrame(rows)


def from_editor_df(df):
    records = []
    for _, row in df.iterrows():
        english = str(row["英文"]).strip()
        chinese = str(row["中文"]).strip()
        type_display = str(row["詞性"]).strip()

        if not english:
            continue

        records.append({
            "english": english,
            "chinese": chinese,
            "type": REVERSE_TYPE_MAP.get(type_display, "")
        })
    return records


def validate_vocab(data):
    seen = set()
    for item in data:
        english = item["english"].strip()
        chinese = item["chinese"].strip()
        word_type = item["type"].strip()

        if not english:
            return False, "英文單字不能空白"
        if not chinese:
            return False, f"{english} 的中文意思不能空白"
        if word_type not in WORD_TYPES:
            return False, f"{english} 的詞性不正確"
        key = english.lower()
        if key in seen:
            return False, f"英文單字 {english} 重複了"
        seen.add(key)

    return True, ""


# --- 初始化資料 ---
if "vocab" not in st.session_state:
    st.session_state.vocab = load_data()


# --- 新增單字區 ---
with st.container():
    st.subheader("新增單字", anchor=False)

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
                    st.rerun()

st.divider()

# --- 顯示單字庫 ---
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

            group_data = grouped_vocab[group]
            editor_df = to_editor_df(group_data)

            edited_df = st.data_editor(
                editor_df,
                hide_index=True,
                use_container_width=True,
                num_rows="fixed",
                key=f"editor_{group}",
                column_config={
                    "刪除": st.column_config.CheckboxColumn(
                        "刪除",
                        help="勾選後可刪除"
                    ),
                    "英文": st.column_config.TextColumn(
                        "英文",
                        required=True
                    ),
                    "詞性": st.column_config.SelectboxColumn(
                        "詞性",
                        options=list(TYPE_MAP.values()),
                        required=True
                    ),
                    "中文": st.column_config.TextColumn(
                        "中文",
                        required=True
                    ),
                },
                disabled=[]
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"💾 儲存 {group} 區", key=f"save_{group}", use_container_width=True):
                    new_group_data = from_editor_df(edited_df)

                    valid, message = validate_vocab(new_group_data)
                    if not valid:
                        st.error(message)
                    else:
                        other_data = [
                            item for item in st.session_state.vocab
                            if get_group_key(item["english"]) != group
                        ]

                        merged_data = other_data + new_group_data
                        valid_all, message_all = validate_vocab(merged_data)

                        if not valid_all:
                            st.error(message_all)
                        else:
                            st.session_state.vocab = merged_data
                            save_data(st.session_state.vocab)
                            st.success(f"{group} 區已儲存")
                            st.rerun()

            with col2:
                if st.button(f"🗑️ 刪除勾選的 {group}", key=f"delete_{group}", use_container_width=True):
                    remaining_df = edited_df[edited_df["刪除"] == False].copy()
                    remaining_df["刪除"] = False

                    new_group_data = from_editor_df(remaining_df)

                    valid, message = validate_vocab(new_group_data)
                    if not valid:
                        st.error(message)
                    else:
                        other_data = [
                            item for item in st.session_state.vocab
                            if get_group_key(item["english"]) != group
                        ]
                        st.session_state.vocab = other_data + new_group_data
                        save_data(st.session_state.vocab)
                        st.success(f"已刪除 {group} 區勾選的單字")
                        st.rerun()
