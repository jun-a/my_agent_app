import os
import requests
import pdfplumber
from tempfile import NamedTemporaryFile
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])
from requests.adapters import HTTPAdapter, Retry

# ページ設定
st.set_page_config(
    page_title="決算公告から分析",
    page_icon="🗺️",
    layout="wide",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# OpenAI API キーの設定

def download_and_save_pdf_temporarily(url: str) -> str:
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
        "User-Agent": "Mozilla/5.0 (compatible; MyBot/1.0; +http://example.com/bot)"
    }

    response = session.get(url, headers=headers, timeout=30, stream=True)
    response.raise_for_status()

    with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_pdf.write(chunk)
        temp_file_path = temp_pdf.name

    return temp_file_path

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

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
    st.title("決算公告から分析")

    pdf_url = st.text_input("PDFのURLを入力してください", "")
    summary_output = st.session_state.get("summary_output", None)

    if st.button("要約を実行"):
        if not pdf_url.strip():
            st.warning("URLを入力してください。")
            return

        with st.spinner("PDFをダウンロードしています..."):
            try:
                temp_pdf_path = download_and_save_pdf_temporarily(pdf_url.strip())
            except requests.exceptions.RequestException as e:
                st.error(f"PDFのダウンロードに失敗しました: {e}")
                return

        with st.spinner("PDFのテキストを抽出しています..."):
            text = extract_text_from_pdf(temp_pdf_path)

        try:
            os.remove(temp_pdf_path)
        except Exception as e:
            st.warning(f"一時ファイルの削除に失敗しました: {e}")

        if not text.strip():
            st.error("PDFからテキストを抽出できませんでした。")
            return

        with st.spinner("要約しています..."):
            summary_output = summarize_long_text(text, "prompts/financial_analyst.txt")

        st.session_state["summary_output"] = summary_output

    if summary_output:
        st.subheader("要約結果")
        st.write(summary_output)

        # テキストファイルとしてダウンロード
        st.download_button(
            label="要約をテキストファイルでダウンロード",
            data=summary_output,
            file_name="summary.txt",
            mime="text/plain"
        )

if __name__ == "__main__":
    main()
