import streamlit as st
from streamlit_markmap import markmap
from openai import OpenAI
import io
import textwrap

# ページ設定
st.set_page_config(
    page_title="マインドマップ生成",
    page_icon="🗺️",
    layout="wide",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# OpenAI API キーの設定
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("文字起こしデータからマインドマップを生成")

# セッション状態を初期化
if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""

if "full_mindmap_data" not in st.session_state:
    st.session_state.full_mindmap_data = ""

# ファイルアップロード
uploaded_file = st.file_uploader("文字起こしデータをアップロード（.txt）", type="txt")

if uploaded_file is not None:
    try:
        # アップロードされたファイルをテキストとして読み取る
        st.session_state.transcript_text = uploaded_file.read().decode("utf-8")

        st.write("アップロードされた文字起こしデータ:")
        st.text_area("内容", st.session_state.transcript_text, height=200)

        # プロンプトを外部ファイルから読み込む
        try:
            with open("prompts/mindmap.txt", "r", encoding="utf-8") as file:
                prompt_template = file.read()
        except FileNotFoundError:
            st.error("プロンプトファイルが見つかりません。`prompts/mindmap.txt` を確認してください。")
            st.stop()

        # トークン制限を考慮して文字起こしデータを分割
        chunk_size = 2000  # 各チャンクの文字数
        transcript_chunks = textwrap.wrap(st.session_state.transcript_text, chunk_size)

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
        st.session_state.full_mindmap_data = "- テーマ: 文字起こしのマインドマップ\n"
        st.session_state.full_mindmap_data += "\n".join([f"    {summary}" for summary in summaries])

    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {e}")

# マインドマップの表示
if st.session_state.full_mindmap_data:
    st.write("### マインドマップの構造")
    st.text_area("マインドマップ", st.session_state.full_mindmap_data, height=300)

    st.write("### マインドマップの可視化")
    markmap(st.session_state.full_mindmap_data)

    # マインドマップをダウンロードするボタン
    markdown_file_name = "mindmap.md"
    st.download_button(
        label="マインドマップをダウンロード（Markdown形式）",
        data=st.session_state.full_mindmap_data,
        file_name=markdown_file_name,
        mime="text/markdown",
    )

    # 文字起こしデータをテキストファイルとしてダウンロード
    transcript_file_name = "transcript.txt"
    st.download_button(
        label="文字起こしをダウンロード（テキスト形式）",
        data=st.session_state.transcript_text,
        file_name=transcript_file_name,
        mime="text/plain",
    )
