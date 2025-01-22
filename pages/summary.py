import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from openai import OpenAI

client = OpenAI(api_key=st.secrets["openai_api_key"])
import io
from utils.auth import check_authentication

# ページ設定
st.set_page_config(
    page_title="YouTube 動画要約",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 認証チェック
check_authentication()

# OpenAI API キーの設定

st.title("YouTube 動画要約")

# 入力フォーム
video_url = st.text_input("YouTube 動画の URL:", placeholder="例: https://www.youtube.com/watch?v=XXXXXX")
email = st.text_input("要約を送信するメールアドレス（任意）:")

if st.button("実行"):
    try:
        # 1. YouTube の動画 ID を抽出
        try:
            video_id = video_url.split("v=")[-1]
            if not video_id:
                raise ValueError("有効な YouTube 動画の URL を入力してください。")
        except Exception:
            st.error("YouTube 動画の URL を正しく入力してください。")
            st.stop()

        # 2. 日本語または英語の文字起こしを取得
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
            transcript_text = " ".join([x["text"] for x in transcript])
        except NoTranscriptFound:
            st.error("指定された動画には利用可能な文字起こしがありません。")
            st.stop()
        except Exception as e:
            st.error(f"文字起こしの取得中にエラーが発生しました: {e}")
            st.stop()

        # 3. プロンプトファイルを読み込む
        try:
            with open("prompts/summary.txt", "r", encoding="utf-8") as file:
                prompt_template = file.read()
            prompt = prompt_template.format(transcript=transcript_text)
        except FileNotFoundError:
            st.error("プロンプトファイルが見つかりません。`prompts/summary.txt` を確認してください。")
            st.stop()
        except Exception as e:
            st.error(f"プロンプトの読み込み中にエラーが発生しました: {e}")
            st.stop()

        # 4. OpenAI API を使用して要約を生成
        try:
            response = client.chat.completions.create(model=st.secrets["openai_model"],
            messages=[
                {"role": "system", "content": "あなたは動画の文字起こしを要約するアシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.5)
            summary = response.choices[0].message.content
        except Exception as e:
            st.error(f"要約の生成中にエラーが発生しました: {e}")
            st.stop()

        # 5. 要約のタイトルを抽出（2行目）
        try:
            title = summary.split("\n")[1].strip()
        except IndexError:
            st.error("要約のタイトルを取得できませんでした。")
            st.stop()

        # 6. 要約結果を表示
        st.write("### 要約結果")
        st.write(summary)

        # 7. Markdown ファイルを作成してダウンロード
        markdown_file_name = f"{title}.md"
        markdown_data = io.StringIO(summary)
        st.download_button(
            label="要約をダウンロード（Markdown形式）",
            data=markdown_data.getvalue(),
            file_name=markdown_file_name,
            mime="text/markdown",
        )

        # 8. 文字起こしファイルを作成してダウンロード
        transcript_file_name = f"{title}.txt"
        transcript_data = io.StringIO(transcript_text)
        st.download_button(
            label="文字起こしをダウンロード（テキスト形式）",
            data=transcript_data.getvalue(),
            file_name=transcript_file_name,
            mime="text/plain",
        )

        # 9. メール送信（任意）
        if email:
            import yagmail
            try:
                yag = yagmail.SMTP(st.secrets["email_user"], st.secrets["email_password"])
                subject = f"動画要約: {title}"  # 件名に要約のタイトルを含める
                yag.send(
                    to=email,
                    subject=subject,
                    contents=[
                        summary,
                        f"文字起こしデータを添付しました。"
                    ],
                    attachments={
                        markdown_file_name: markdown_data.getvalue(),
                        transcript_file_name: transcript_data.getvalue(),
                    },
                )
                st.success(f"要約と文字起こしデータをメール送信しました！件名: {subject}")
            except Exception as e:
                st.error(f"メール送信中にエラーが発生しました: {e}")
    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {e}")
