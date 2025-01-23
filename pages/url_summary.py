import os
import requests
import streamlit as st
from openai import OpenAI
from requests.adapters import HTTPAdapter, Retry

# ページ設定
st.set_page_config(
    page_title="ウェブコンテンツから分析",
    page_icon="🌐",
    layout="wide",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# OpenAI API キーの設定
client = OpenAI(api_key=st.secrets["openai_api_key"])


def fetch_web_content(url: str) -> str:
    # リトライとタイムアウト設定を含むセッションを作成
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[500, 502, 503, 504]
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def chunk_text(text: str, max_chars: int = 3000):
    chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        chunks.append(text[start:end])
        start = end
    return chunks

def summarize_text(text_chunk: str, prompt_file_path: str) -> str:
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    prompt = prompt_template.format(text_chunk)

    response = client.chat.completions.create(model=st.secrets["openai_model"],
    messages=[
        {"role": "system", "content": "You are a highly skilled financial analyst."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.5,
    max_tokens=3000)
    return response.choices[0].message.content

def summarize_long_text(text: str, prompt_file_path: str) -> str:
    chunks = chunk_text(text, max_chars=3000)
    partial_summaries = []

    for chunk in chunks:
        summary = summarize_text(chunk, prompt_file_path)
        partial_summaries.append(summary)

    combined_summary_text = "\n".join(partial_summaries)
    return summarize_text(combined_summary_text, prompt_file_path)

def main():
    st.title("ウェブコンテンツから分析")

    web_url = st.text_input("ウェブページのURLを入力してください", "")

    if st.button("要約を実行"):
        if not web_url.strip():
            st.warning("URLを入力してください。")
            return

        # 既存の要約結果をクリア
        st.session_state["summary_output"] = None

        with st.spinner("ウェブページを取得しています..."):
            try:
                web_content = fetch_web_content(web_url.strip())
            except requests.exceptions.RequestException as e:
                st.error(f"ウェブコンテンツの取得に失敗しました: {e}")
                return

        if not web_content.strip():
            st.error("ウェブコンテンツを取得できませんでした。")
            return

        with st.spinner("要約しています..."):
            summary_output = summarize_long_text(web_content, "prompts/url_summary.txt")
            st.session_state["summary_output"] = summary_output

    # 要約結果が存在する場合のみ表示
    if "summary_output" in st.session_state and st.session_state["summary_output"]:
        st.subheader("要約結果")
        st.write(st.session_state["summary_output"])

        # テキストファイルとしてダウンロード
        st.download_button(
            label="要約をテキストファイルでダウンロード",
            data=st.session_state["summary_output"],
            file_name="summary.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
