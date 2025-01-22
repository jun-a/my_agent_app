import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI
import io
import textwrap
from utils.auth import check_authentication

client = OpenAI(api_key=st.secrets["openai_api_key"])

# ページ設定
st.set_page_config(
    page_title="マインドマップ生成",
    page_icon="🗺️",
    layout="wide",
)

# 認証チェック
check_authentication()

# OpenAI API キーの設定

st.title("文字起こしデータからマインドマップを生成")

# ファイルアップロード
uploaded_file = st.file_uploader("文字起こしデータをアップロード（.txt）", type="txt")

if uploaded_file is not None:
    try:
        # アップロードされたファイルをテキストとして読み取る
        transcript_text = uploaded_file.read().decode("utf-8")

        st.write("アップロードされた文字起こしデータ:")
        st.text_area("内容", transcript_text, height=200)

        # プロンプトを外部ファイルから読み込む
        try:
            with open("prompts/mindmap.txt", "r", encoding="utf-8") as file:
                prompt_template = file.read()
        except FileNotFoundError:
            st.error("プロンプトファイルが見つかりません。`prompts/mindmap.txt` を確認してください。")
            st.stop()

        # トークン制限を考慮して文字起こしデータを分割
        chunk_size = 2000  # 各チャンクの文字数
        transcript_chunks = textwrap.wrap(transcript_text, chunk_size)

        # 各チャンクの要約を生成
        summaries = []
        for i, chunk in enumerate(transcript_chunks):
            st.write(f"チャンク {i + 1} を処理中...")
            prompt = prompt_template.format(chunk=chunk)  # プレースホルダー `{chunk}` を使用
            try:
                response = client.chat.completions.create(model=st.secrets["openai_model"],
                messages=[
                    {"role": "system", "content": "あなたは文字起こしデータを解析してマインドマップを生成するアシスタントです。"},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
                temperature=0.5)
                summaries.append(response.choices[0].message.content)
            except Exception as e:
                st.error(f"チャンク {i + 1} の処理中にエラーが発生しました: {e}")
                st.stop()

        # すべての部分要約を統合
        full_mindmap_data = "- テーマ: 文字起こしのマインドマップ\n"
        full_mindmap_data += "\n".join([f"    {summary}" for summary in summaries])

        # マインドマップを表示
        st.write("### マインドマップの構造")
        st.text_area("マインドマップ", full_mindmap_data, height=300)

        st.write("### マインドマップの可視化")
        markmap(full_mindmap_data)

        # マインドマップをダウンロードするボタン
        markdown_file_name = "mindmap.md"
        st.download_button(
            label="マインドマップをダウンロード（Markdown形式）",
            data=full_mindmap_data,
            file_name=markdown_file_name,
            mime="text/markdown",
        )

        # 文字起こしデータをテキストファイルとしてダウンロード
        transcript_file_name = "transcript.txt"
        st.download_button(
            label="文字起こしをダウンロード（テキスト形式）",
            data=transcript_text,
            file_name=transcript_file_name,
            mime="text/plain",
        )
    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {e}")
