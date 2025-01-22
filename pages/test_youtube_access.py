import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import NoTranscriptFound, VideoUnavailable

# ページ設定
st.set_page_config(
    page_title="YouTube文字起こし取得ツール",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("YouTube文字起こし取得ツール")


from utils.auth import check_authentication, show_logout_button

# 認証チェック
check_authentication()

# サイドバーにログアウトボタンを表示
show_logout_button()

# ユーザーにYouTube動画IDを入力させる
video_id = st.text_input("YouTube動画のIDを入力してください", placeholder="例: j3_VgCt18fA")

if st.button("情報を取得"):
    if video_id:
        try:
            # トランスクリプトリストを取得
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

            # 自動生成された文字起こしを取得
            try:
                generated_transcript = transcript_list.find_generated_transcript(['en', 'ja'])
                st.subheader("(GENERATED)")
                st.write(f"- {generated_transcript.language} ({generated_transcript.language_code})[{'TRANSLATABLE' if generated_transcript.is_translatable else 'NOT TRANSLATABLE'}]")

                # 文字起こしデータを取得して表示
                st.subheader("文字起こしデータ")
                transcript_data = generated_transcript.fetch()
                transcript_text = "\n".join([item["text"] for item in transcript_data])
                st.code(transcript_text, language="plaintext")

            except Exception:
                st.warning("自動生成された文字起こしは利用できません。")

            # 翻訳可能な言語リストを取得
            try:
                if generated_transcript.is_translatable:
                    translation_languages = generated_transcript.translation_languages
                    st.subheader("(TRANSLATION LANGUAGES)")
                    languages_formatted = [
                        f"- {lang['language_code']} (\"{lang['language']}\")" for lang in translation_languages
                    ]
                    st.code("\n".join(languages_formatted), language="plaintext")
                else:
                    st.info("翻訳可能な言語はありません。")
            except Exception:
                st.warning("翻訳可能な言語リストは取得できませんでした。")

        except NoTranscriptFound:
            st.error("指定された動画には文字起こしが存在しません。")
        except VideoUnavailable:
            st.error("動画が見つからない、または利用できません。")
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.warning("動画IDを入力してください。")
