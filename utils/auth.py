import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager
import hashlib
import time

# Initialize cookies manager
cookies = EncryptedCookieManager(prefix="auth_", password=st.secrets["cookie_password"])  # 安全なキーを使用してください
if not cookies.ready():
    st.stop()

# トークン生成
def generate_token(username: str) -> str:
    return hashlib.sha256(f"{username}{time.time()}".encode()).hexdigest()

# ログイン処理
def authenticate():
    """ログインフォームを表示し、認証を処理します。"""
    st.title("ログイン")
    username = st.text_input("ユーザー名:", key="auth_username")
    password = st.text_input("パスワード:", type="password", key="auth_password")

    if st.button("ログイン"):
        if username == st.secrets["auth_user"] and password == st.secrets["auth_pass"]:
            token = generate_token(username)
            cookies["auth_token"] = token
            cookies["auth_username"] = username
            cookies["auth_expiry"] = str(int(time.time()) + 30 * 24 * 60 * 60)  # 30日間有効
            cookies.save()
            st.session_state.authenticated = True
            st.success("ログインに成功しました！")
            return True
        else:
            st.error("ユーザー名またはパスワードが間違っています。")
    return False

# 認証状態の確認
def check_authentication():
    """認証状態を確認し、認証されていない場合はログインフォームを表示します。"""
    # セッションの状態を確認
    if "authenticated" in st.session_state and st.session_state.authenticated:
        return

    # クッキーを確認
    if "auth_token" in cookies:
        expiry_time_str = cookies.get("auth_expiry", "0")  # デフォルト値を文字列"0"に設定
        if expiry_time_str and expiry_time_str.isdigit():  # 値がNoneまたは空文字でないか確認
            expiry_time = int(expiry_time_str)
            if time.time() < expiry_time:
                st.session_state.authenticated = True
                return

    # ログインフォームを表示
    if not authenticate():
        st.stop()  # 認証されるまでページを停止


def logout():
    """ユーザーをログアウトします。"""
    # クッキーの値を空文字列に設定して削除
    cookies["auth_token"] = ""
    cookies["auth_username"] = ""
    cookies["auth_expiry"] = ""
    cookies.save()  # 変更を保存
    st.session_state.authenticated = False
    st.rerun()


# サイドバーにログアウトボタンを表示
def show_logout_button():
    if st.sidebar.button("ログアウト"):
        logout()
