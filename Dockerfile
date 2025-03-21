FROM python:3.9-slim

WORKDIR /app

# 日本語フォントとタイムゾーン設定をインストール
RUN apt-get update && apt-get install -y \
    fonts-ipafont \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# タイムゾーンを日本に設定
ENV TZ=Asia/Tokyo

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# アップロードディレクトリを作成
RUN mkdir -p /app/app/uploads

# 環境変数を設定
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app/main.py

# ポート3501を公開
EXPOSE 3501

# アプリケーションを起動
CMD ["gunicorn", "--bind", "0.0.0.0:3501", "--workers", "2", "--timeout", "120", "app.main:app"]
