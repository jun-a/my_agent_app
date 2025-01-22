# Streamlit アプリケーション

## 必要環境
- Python 3.10 以上

## セットアップ手順

### 仮想環境の作成
```bash
make create-env
```

### アプリケーションの起動
```bash
make run
```

### ファイル構成
```
.
├── Makefile
├── README.md
├── app.py
├── config.toml
├── pages
│   ├── chat.py
│   ├── mindmap.py
│   ├── multi_summary.py
│   └── summary.py
├── prompts
│   ├── mindmap.txt
│   └── summary.txt
├── requirements.txt
└── utils
    ├── __pycache__
    │   └── auth.cpython-312.pyc
    └── auth.py 
```