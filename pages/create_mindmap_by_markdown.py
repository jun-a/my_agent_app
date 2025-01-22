import streamlit as st
from streamlit_markmap import markmap

# ページ設定
st.set_page_config(
    page_title="markdownファイルからマインドマップ生成",
    page_icon="🗺️",
    layout="wide",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

st.title("Markdown to Mind Map Viewer")

st.write("""
このアプリでは、Markdownファイルをアップロードすると、その内容をマインドマップとして表示します。
""")

# ファイルアップロード
uploaded_file = st.file_uploader("Markdownファイルをアップロードしてください", type=["md"])

if uploaded_file:
    # Markdownの内容を読み込む
    markdown_content = uploaded_file.read().decode("utf-8")
    
    # マインドマップを表示
    st.subheader("マインドマップ")
    markmap(markdown_content)
    
    # アップロードされたMarkdownの内容を表示
    st.subheader("Markdownの内容")
    st.code(markdown_content, language="markdown")
