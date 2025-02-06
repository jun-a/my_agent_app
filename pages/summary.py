import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from openai import OpenAI
import io
import tempfile
import os
import yagmail
from gtts import gTTS

# ページ設定
st.set_page_config(
    page_title="YouTube 動画要約",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# OpenAI API キーの設定
client = OpenAI(api_key=st.secrets["openai_api_key"])

st.title("YouTube 動画要約")

# セッション状態を初期化
if "summary" not in st.session_state:
    st.session_state.summary = ""

if "transcript_text" not in st.session_state:
    st.session_state.transcript_text = ""

if "title" not in st.session_state:
    st.session_state.title = ""

# 入力フォーム
video_url = st.text_input("YouTube 動画の URL:", placeholder="例: https://www.youtube.com/watch?v=XXXXXX")
email = st.text_input("要約を送信するメールアドレス（任意）:")

if st.button("実行"):
    try:
        # URL に v= が含まれているかを確認し、含まれていない場合はエラー
        if "v=" not in video_url:
            raise ValueError("有効な YouTube 動画の URL を入力してください。")

        # 1. "v=" で分割して後ろの部分を取得
        video_id_part = video_url.split("v=")[1]

        # 2. "&" がある場合は分割して先頭の要素を取り出す
        video_id = video_id_part.split("&")[0]

        if not video_id:
            raise ValueError("有効な YouTube 動画の URL を入力してください。")

        # 2. 日本語または英語の文字起こしを取得
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en','ja'])
            st.session_state.transcript_text = " ".join([x["text"] for x in transcript])
        except NoTranscriptFound:
            st.error("指定された動画には字幕が無効です。別の動画を選択してください。")
            st.stop()
        except Exception as e:
            st.error(f"文字起こしの取得中にエラーが発生しました: {e}")
            st.stop()

        # 3. プロンプトファイルを読み込む
        try:
            with open("prompts/summary.txt", "r", encoding="utf-8") as file:
                prompt_template = file.read()
            prompt = prompt_template.format(transcript=st.session_state.transcript_text)
        except FileNotFoundError:
            st.error("プロンプトファイルが見つかりません。`prompts/summary.txt` を確認してください。")
            st.stop()
        except Exception as e:
            st.error(f"プロンプトの読み込み中にエラーが発生しました: {e}")
            st.stop()

        # 4. OpenAI API を使用して要約を生成
        try:
            response = client.chat.completions.create(
                model=st.secrets["openai_model"],
                messages=[
                    {"role": "system", "content": "あなたは動画の文字起こしを要約するアシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3000,
                temperature=0.5
            )
            st.session_state.summary = response.choices[0].message.content
        except Exception as e:
            st.error(f"要約の生成中にエラーが発生しました: {e}")
            st.stop()

        # 5. 要約のタイトルを抽出（2行目）
        try:
            st.session_state.title = st.session_state.summary.split("\n")[1].strip()
        except IndexError:
            st.session_state.title = "要約結果"

    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {e}")

# 要約結果の表示
if st.session_state.summary:
    st.write("### 要約結果")
    st.write(st.session_state.summary)

    # Markdown ファイルを作成してダウンロード
    markdown_file_name = f"{st.session_state.title}.md"
    markdown_data = io.StringIO(st.session_state.summary)
    st.download_button(
        label="要約をダウンロード（Markdown形式）",
        data=markdown_data.getvalue(),
        file_name=markdown_file_name,
        mime="text/markdown",
    )

    # 文字起こしファイルを作成してダウンロード
    transcript_file_name = f"{st.session_state.title}.txt"
    transcript_data = io.StringIO(st.session_state.transcript_text)
    st.download_button(
        label="文字起こしをダウンロード（テキスト形式）",
        data=transcript_data.getvalue(),
        file_name=transcript_file_name,
        mime="text/plain",
    )

    # 音声で読み上げる機能を追加
    tts = gTTS(st.session_state.summary, lang='ja')
    tts.save("summary.mp3")

    audio_file = open("summary.mp3", "rb")
    audio_bytes = audio_file.read()

    st.audio(audio_bytes, format="audio/mp3")

    # 音声ファイルをダウンロード
    st.download_button(
        label="要約をダウンロード（音声形式）",
        data=audio_bytes,
        file_name="summary.mp3",
        mime="audio/mp3",
    )

    # メール送信（任意）
    if email:
        try:
            with tempfile.NamedTemporaryFile(delete=False) as markdown_temp:
                markdown_temp.write(markdown_data.getvalue().encode("utf-8"))
                markdown_temp_path = markdown_temp.name

            with tempfile.NamedTemporaryFile(delete=False) as transcript_temp:
                transcript_temp.write(transcript_data.getvalue().encode("utf-8"))
                transcript_temp_path = transcript_temp.name

            yag = yagmail.SMTP(st.secrets["email_user"], st.secrets["email_password"])
            subject = f"動画要約: {st.session_state.title}"  # 件名に要約のタイトルを含める
            yag.send(
                to=email,
                subject=subject,
                contents=[
                    st.session_state.summary,
                    "文字起こしデータを添付しました。"
                ],
                attachments=[markdown_temp_path, transcript_temp_path]
            )
            st.success(f"要約と文字起こしデータをメール送信しました！件名: {subject}")

            # 一時ファイルを削除
            os.unlink(markdown_temp_path)
            os.unlink(transcript_temp_path)

        except Exception as e:
            st.error(f"メール送信中にエラーが発生しました: {e}")
