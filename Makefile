# Python 仮想環境の作成と依存関係のインストール
create-env:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt

run:
	. .venv/bin/activate && streamlit run app.py

clean:
	rm -rf .venv