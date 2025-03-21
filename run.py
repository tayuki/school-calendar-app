"""
開発環境での実行用スクリプト
"""
import os
from app.main import app
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 3501))
    app.run(host='0.0.0.0', port=port, debug=True)
