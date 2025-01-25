from openai import OpenAI
import streamlit as st

# ページ設定を最初に記述
st.set_page_config(
    page_title="チャット",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# アプリのタイトルと説明
st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by OpenAI")

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# OpenAI APIキーとモデルを設定
api_key = st.secrets["openai_api_key"]
model_name = st.secrets["openai_model"]

# メッセージ履歴の初期化
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "お手伝いできることはありますか?"}]

# チャット履歴の表示
st.write("---")  # 見た目を区切るライン
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):  # メッセージの役割に応じたUI
        st.write(msg["content"])

# ユーザー入力欄を表示
if prompt := st.chat_input("GPTにメッセージを送信する"):
    # ユーザーのメッセージを履歴に追加
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # OpenAI APIを呼び出して応答を取得
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=st.session_state.messages,
        )
        bot_message = response.choices[0].message.content

        # アシスタントの応答を履歴に追加
        st.session_state.messages.append({"role": "assistant", "content": bot_message})
        with st.chat_message("assistant"):
            st.write(bot_message)
    except Exception as e:
        # エラーが発生した場合は表示
        st.error(f"An error occurred: {e}")
