import streamlit as st
from openai import OpenAI
from utils.auth import check_authentication

# ページ設定を最初に記述
st.set_page_config(
    page_title="GPTチャットアプリ",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 認証チェック
check_authentication()

# OpenAI APIのキー設定
client = OpenAI(api_key=st.secrets["openai_api_key"])


# 会話履歴を保存するためのセッションステートを初期化
if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "system", "content": "You are a helpful assistant."}
    ]

st.title("GPTチャット")

# 質問の入力フォーム
question = st.text_input("質問を入力してください:")

if st.button("送信"):
    if question:
        try:
            # ユーザーの質問を履歴に追加
            st.session_state["messages"].append({"role": "user", "content": question})

            # ChatCompletion API を使用
            response = client.chat.completions.create(model=st.secrets["openai_model"],
            messages=st.session_state["messages"],
            max_tokens=2000,
            temperature=0.7)

            # AIの応答を履歴に追加
            answer = response.choices[0].message.content
            st.session_state["messages"].append({"role": "assistant", "content": answer})

            # 応答を表示
            st.write("### 回答")
            st.write(answer)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.warning("質問を入力してください。")

# 会話履歴を表示
if st.session_state["messages"]:
    st.write("---")
    st.write("### 会話履歴")
    for msg in st.session_state["messages"]:
        if msg["role"] == "user":
            st.write(f"**ユーザー**: {msg['content']}")
        elif msg["role"] == "assistant":
            st.write(f"**AI**: {msg['content']}")
