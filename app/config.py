"""
アプリケーション設定
"""
import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Google APIの設定
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
VISION_API_ENABLED = os.getenv('VISION_API_ENABLED', 'true').lower() == 'true'
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Google OAuth設定
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Google APIスコープ
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid'
]

# アプリケーション設定
SECRET_KEY = os.getenv('SECRET_KEY', 'default-dev-key')
DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'

# アップロードされたファイルの設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

# API設定
API_TIMEOUT = 30  # API呼び出しのタイムアウト（秒）

# キャッシュの設定
CACHE_TIMEOUT = 300  # キャッシュのタイムアウト（秒）

# ログ設定
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')

# アプリケーションのURLベース（リダイレクトに使用）
APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://localhost:3501')

# セッション設定
SESSION_TYPE = 'filesystem'
PERMANENT_SESSION_LIFETIME = 3600  # 1時間

# 確保すべきアップロードディレクトリの確認と作成
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
