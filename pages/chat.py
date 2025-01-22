import streamlit as st
from openai import OpenAI
from utils.auth import check_authentication

# ページ設定を最初に記述
st.set_page_config(
    page_title="Streamlit App",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 認証チェック
check_authentication()

# OpenAI クライアントの初期化
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("GPTチャット")

# 質問の入力フォーム
question = st.text_input("質問を入力してください:")

if st.button("送信"):
    try:
        # ChatCompletion API を使用
        response = client.chat.completions.create(model=st.secrets["openai_model"],
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ],
        max_tokens=100,
        temperature=0.7)
        # 回答の抽出
        answer = response.choices[0].message.content
        st.write("### 回答")
        st.write(answer)

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
