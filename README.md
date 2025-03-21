# 学校プリントカレンダー登録アプリケーション

学校のプリントをアップロードし、OCRとAIによるテキスト解析を使って予定情報を抽出し、Googleカレンダーに登録するWebアプリケーションです。

## 機能

- 学校プリントの画像をアップロード
- Google Cloud Vision APIによるOCR処理
- Google Gemini APIによるテキスト解析
- 抽出された予定情報の確認と編集
- Googleカレンダーへの予定登録

## 必要条件

- Python 3.9以上
- Google Cloud Platformアカウント
- Google Cloud Vision API有効化
- Google Gemini API有効化
- Google OAuth 2.0クライアントID
- Docker（コンテナ化して実行する場合）

## セットアップ

### 環境変数の設定

`.env` ファイルを作成し、以下の環境変数を設定してください（`.env.sample` をコピーして使用可能）：

```
# Google Cloud API credentials
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/google-credentials.json

# Google Cloud Vision API settings
VISION_API_ENABLED=true

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# Google OAuth Client
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# App settings
FLASK_APP=app/main.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

# Logging
LOG_LEVEL=INFO
```

### Google Cloud認証情報の設定

1. Google Cloud Platformで必要なAPIを有効化
   - Google Cloud Vision API
   - Google Calendar API

2. サービスアカウントキーを生成し、`credentials/google-credentials.json` として保存

3. OAuth 2.0クライアントIDを作成
   - リダイレクトURLに `http://localhost:3501/auth/callback` を追加

### ローカル環境での実行

```bash
# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate

# 依存関係をインストール
pip install -r requirements.txt

# アプリケーションを実行
python run.py
```

### Dockerでの実行

```bash
# イメージをビルドして実行
docker-compose up --build
```

## 使い方

1. ブラウザで `http://localhost:3501` にアクセス
2. Googleアカウントでログイン
3. 学校プリントの画像をアップロード
4. 抽出された予定情報を確認・編集
5. 登録先のカレンダーを選択
6. カレンダーに登録

## プロジェクト構造

```
school-calendar-app/
├── .env                    # 環境変数ファイル
├── .gitignore              # Gitで無視するファイル
├── docker-compose.yml      # Dockerコンテナ設定
├── Dockerfile              # アプリケーションのDockerビルド設定
├── requirements.txt        # Pythonの依存パッケージ
├── run.py                  # 開発環境実行スクリプト
├── app/
│   ├── __init__.py
│   ├── main.py             # Flaskアプリのメインファイル
│   ├── ocr.py              # OCR処理モジュール
│   ├── text_analysis.py    # テキスト解析モジュール
│   ├── calendar_api.py     # Googleカレンダー連携モジュール
│   ├── config.py           # 設定ファイル
│   ├── logging_config.py   # ログ設定
│   ├── static/             # 静的ファイル
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── script.js
│   └── templates/          # HTMLテンプレート
│       ├── index.html      # メインページ
│       ├── confirm.html    # 確認ページ
│       └── result.html     # 結果ページ
└── logs/                   # ログ保存ディレクトリ
```

## 注意事項

- このアプリケーションはローカルネットワークでの使用を前提としています
- 本番環境で使用する場合は、セキュリティ設定を適切に行ってください
- アップロードされた画像は一時的にサーバーに保存されます
- Google APIの利用には料金が発生する場合があります
