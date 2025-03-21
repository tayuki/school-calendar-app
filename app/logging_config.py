"""
ロギング設定モジュール
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from app.config import LOG_LEVEL, LOG_DIR

def setup_logging(app):
    """
    アプリケーションのロギング設定を行います
    
    Args:
        app: Flaskアプリケーションインスタンス
    """
    # ログレベルの設定
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # ログフォーマットの設定
    log_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
    )
    
    # ルートロガーの設定
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # 既存のハンドラをクリア
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 標準出力ハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # ファイル出力ハンドラの設定
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 1つのファイルは10MBまで、最大5ファイルをローテーション
    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(log_format)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    # Flaskアプリのロガーをセットアップされたロガーにリンクさせる
    app.logger.handlers = root_logger.handlers
    
    # Werkzeugロガーの設定（フラスクの内部ロガー）
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(log_level)
    werkzeug_logger.handlers = root_logger.handlers
    
    app.logger.info("ロギングの設定が完了しました")
