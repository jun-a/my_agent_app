import streamlit as st
from openai import OpenAI
from streamlit_markmap import markmap

# OpenAI APIキーを設定
client = OpenAI(api_key=st.secrets["openai_api_key"])

# プロンプトの読み込み関数
def load_prompt(filepath):
    with open(filepath, "r", encoding="utf-8") as file:
        return file.read()

# Streamlitアプリのレイアウト
st.title("戦略立案アプリ")
st.write("以下の項目を入力し、戦略とマインドマップを生成してください。")

# ユーザー入力
keywords = st.text_area("キーワード（複数可、カンマ区切り）", placeholder="例: 不労所得, サブスクリプション, ノーコード")
goal = st.text_input("ゴール", placeholder="例: 毎月1万円の収益")
period = st.text_input("期間", placeholder="例: 12か月")
cost = st.text_input("コスト", placeholder="例: 10万円")

# ボタンで戦略生成
if st.button("戦略を生成"):
    if not keywords or not goal or not period or not cost:
        st.warning("すべての項目を入力してください。")
    else:
        # プロンプトを外部ファイルから読み込み
        try:
            base_prompt = load_prompt("prompts/strategy.txt")
        except FileNotFoundError:
            st.error("プロンプトファイルが見つかりませんでした。'prompts/strategy.txt' を確認してください。")
        else:
            # 動的プロンプトの生成
            prompt = base_prompt.format(
                keywords=', '.join(keywords.split(',')),
                goal=goal,
                period=period,
                cost=cost
            )

            # OpenAI API経由で戦略を生成
            try:
                response = client.chat.completions.create(model=st.secrets["openai_model"],
                messages=[
                    {"role": "system", "content": "あなたは優れた戦略アナリストです。"},
                    {"role": "user", "content": prompt},
                ])
                result = response.choices[0].message.content

                # 戦略の出力
                st.subheader("生成された戦略")
                st.markdown(result)

                # マインドマップ用データ抽出（マークダウン部分のみ）
                if "マインドマップ用マークダウン形式" in result:
                    mindmap_data = result.split("マインドマップ用マークダウン形式")[1].strip()
                    st.subheader("マインドマップ")
                    markmap(mindmap_data)
                else:
                    st.warning("マインドマップデータが見つかりませんでした。")

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")
