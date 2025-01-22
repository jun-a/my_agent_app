import streamlit as st

def authenticate():
    """ログインフォームを表示し、認証を処理します。"""
    st.title("ログイン")
    username = st.text_input("ユーザー名:", key="auth_username")
    password = st.text_input("パスワード:", type="password", key="auth_password")

    if st.button("ログイン"):
        if username == st.secrets["auth_user"] and password == st.secrets["auth_pass"]:
            st.session_state.authenticated = True
            st.success("ログインに成功しました！")
            return True
        else:
            st.error("ユーザー名またはパスワードが間違っています。")
    return False

def check_authentication():
    """認証チェックを行い、未認証の場合はログインフォームを表示します。"""
    if "authenticated" not in st.session_state or not st.session_state.authenticated:
        if not authenticate():
            st.stop()  # 認証が成功するまでページの処理を停止

def basic_auth():
    username = st.text_input("ユーザー名を入力してください:")
    password = st.text_input("パスワードを入力してください:", type="password")
    if st.button("ログイン"):
        if username == st.secrets["auth_user"] and password == st.secrets["auth_pass"]:
            st.session_state.authenticated = True
        else:
            st.error("ユーザー名またはパスワードが正しくありません。")