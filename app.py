import streamlit as st

# ページ設定を最初に記述
st.set_page_config(
    page_title="Streamlit App",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()