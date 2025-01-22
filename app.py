import streamlit as st
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