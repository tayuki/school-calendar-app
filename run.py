"""
開発環境での実行用スクリプト
"""
from app.main import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3501, debug=True)
