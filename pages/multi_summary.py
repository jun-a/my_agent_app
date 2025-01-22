import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound
from openai import OpenAI
import io
import tempfile
import os
import yagmail

# ページ設定
st.set_page_config(
    page_title="複数動画の要約生成",
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

st.title("複数動画の要約生成")

# URL の入力欄（複数行入力、最大10行）
st.write("YouTube 動画の URL を最大10件貼り付けてください（1行に1つの URL）。")
urls = st.text_area(
    "動画 URL を入力してください:",
    height=150,
    placeholder="https://www.youtube.com/watch?v=XXXXXX\nhttps://www.youtube.com/watch?v=YYYYYY",
).strip().split("\n")
urls = [url.strip() for url in urls if url.strip()]  # 空行を削除

# セッション状態を初期化
if "all_summaries" not in st.session_state:
    st.session_state.all_summaries = []

if "full_summary" not in st.session_state:
    st.session_state.full_summary = ""

# 入力された URL の数を確認
if len(urls) > 10:
    st.error("最大10件までの URL を入力してください。")
else:
    email = st.text_input("要約を送信するメールアドレス（任意）:")

    if st.button("実行"):
        if not urls:
            st.error("URL が入力されていません。")
        else:
            try:
                yag = None

                # メール送信用に yagmail を設定（メールアドレスが入力されている場合）
                if email:
                    try:
                        yag = yagmail.SMTP(st.secrets["email_user"], st.secrets["email_password"])
                    except Exception as e:
                        st.error(f"メール送信設定中にエラーが発生しました: {e}")
                        st.stop()

                # 各動画 URL を処理
                for idx, video_url in enumerate(urls, start=1):
                    try:
                        st.write(f"### 動画 {idx}: {video_url}")

                        # YouTube の動画 ID を抽出
                        video_id = video_url.split("v=")[-1]
                        if not video_id:
                            raise ValueError("有効な動画 URL ではありません。")

                        # 文字起こしを取得
                        try:
                            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en','ja'])
                            transcript_text = " ".join([x["text"] for x in transcript])
                        except NoTranscriptFound:
                            st.warning(f"動画 {idx}: 利用可能な文字起こしが見つかりません。スキップします。")
                            continue

                        # プロンプトファイルを読み込む
                        try:
                            with open("prompts/summary.txt", "r", encoding="utf-8") as file:
                                prompt_template = file.read()
                            prompt = prompt_template.format(transcript=transcript_text)
                        except FileNotFoundError:
                            st.error("プロンプトファイルが見つかりません。")
                            st.stop()

                        # 要約を生成
                        response = client.chat.completions.create(
                            model=st.secrets["openai_model"],
                            messages=[
                                {"role": "system", "content": "あなたは動画の文字起こしを要約するアシスタントです。"},
                                {"role": "user", "content": prompt},
                            ],
                            max_tokens=3000,
                            temperature=0.5)
                        summary = response.choices[0].message.content

                        # 要約のタイトルを抽出
                        title = summary.split("\n")[1].strip()

                        # 要約結果を表示
                        st.write("#### 要約結果")
                        st.write(summary)

                        # 区切り線を追加
                        st.divider()

                        # Markdown ファイルとしてダウンロード
                        markdown_file_name = f"{title}.md"
                        markdown_data = io.StringIO(summary)
                        st.download_button(
                            label=f"動画 {idx} の要約をダウンロード（Markdown形式）",
                            data=markdown_data.getvalue(),
                            file_name=markdown_file_name,
                            mime="text/markdown",
                        )

                        # 文字起こしファイルとしてダウンロード
                        transcript_file_name = f"{title}.txt"
                        transcript_data = io.StringIO(transcript_text)
                        st.download_button(
                            label=f"動画 {idx} の文字起こしをダウンロード（テキスト形式）",
                            data=transcript_data.getvalue(),
                            file_name=transcript_file_name,
                            mime="text/plain",
                        )

                        # メール送信部分の修正
                        if yag:
                            try:
                                with tempfile.NamedTemporaryFile(delete=False) as markdown_temp:
                                    markdown_temp.write(markdown_data.getvalue().encode("utf-8"))
                                    markdown_temp_path = markdown_temp.name

                                with tempfile.NamedTemporaryFile(delete=False) as transcript_temp:
                                    transcript_temp.write(transcript_data.getvalue().encode("utf-8"))
                                    transcript_temp_path = transcript_temp.name

                                # メールの件名
                                subject = f"動画 {idx} の要約: {title}"

                                # メール送信
                                yag.send(
                                    to=email,
                                    subject=subject,
                                    contents=[
                                        summary,
                                        "文字起こしデータを添付しました。",
                                    ],
                                    attachments=[markdown_temp_path, transcript_temp_path]
                                )
                                st.success(f"動画 {idx} の要約と文字起こしデータをメール送信しました！件名: {subject}")

                                # 一時ファイルを削除
                                os.unlink(markdown_temp_path)
                                os.unlink(transcript_temp_path)

                            except Exception as e:
                                st.error(f"動画 {idx} のメール送信中にエラーが発生しました: {e}")

                        # 全体の要約に追加
                        st.session_state.all_summaries.append(f"### 動画 {idx}: {title}\n{summary}")

                    except Exception as e:
                        st.error(f"動画 {idx} の処理中にエラーが発生しました: {e}")

                # 全体の要約をセッションに保存
                if st.session_state.all_summaries:
                    st.session_state.full_summary = "\n\n".join(st.session_state.all_summaries)

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

        # 全体の要約を表示
        if st.session_state.full_summary:
            st.write("### 全体の要約")
            st.text_area("全体の要約", st.session_state.full_summary, height=300)

            # 全体の要約をダウンロード
            st.download_button(
                label="全体の要約をダウンロード（テキスト形式）",
                data=st.session_state.full_summary,
                file_name="all_summaries.txt",
                mime="text/plain",
            )
