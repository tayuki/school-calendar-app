"""
OCR処理モジュール
Google Cloud Vision APIを使用して画像からテキストを抽出します
"""
import logging
import os
from google.cloud import vision
from PIL import Image
import io

logger = logging.getLogger(__name__)

class OCRProcessor:
    def __init__(self, credentials_path=None):
        """
        OCR処理クラスの初期化
        
        Args:
            credentials_path: Google Cloud認証情報のパス
        """
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        
        self.client = None
        try:
            self.client = vision.ImageAnnotatorClient()
            logger.info("Vision APIクライアントの初期化に成功しました")
        except Exception as e:
            logger.error(f"Vision APIクライアントの初期化に失敗しました: {e}")
            raise
    
    def process_image(self, image_path):
        """
        画像からテキストを抽出する
        
        Args:
            image_path: 処理する画像のパス
            
        Returns:
            抽出されたテキスト
        """
        if not self.client:
            logger.error("Vision APIクライアントが初期化されていません")
            return ""
        
        try:
            # 画像ファイルの読み込み
            with open(image_path, "rb") as image_file:
                content = image_file.read()
            
            # Vision APIで解析するためのリクエスト作成
            image = vision.Image(content=content)
            
            # テキスト検出リクエスト
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                logger.warning("画像からテキストが検出されませんでした")
                return ""
            
            # 最初の要素は画像全体のテキスト
            full_text = texts[0].description
            logger.info(f"テキスト抽出に成功しました: {len(full_text)} 文字")
            
            # エラーチェック
            if response.error.message:
                logger.error(f"テキスト検出中にエラーが発生しました: {response.error.message}")
                return ""
            
            return full_text
        
        except Exception as e:
            logger.error(f"テキスト抽出中にエラーが発生しました: {e}")
            return ""
    
    def process_image_bytes(self, image_bytes):
        """
        画像のバイトデータからテキストを抽出する
        
        Args:
            image_bytes: 処理する画像のバイトデータ
            
        Returns:
            抽出されたテキスト
        """
        if not self.client:
            logger.error("Vision APIクライアントが初期化されていません")
            return ""
        
        try:
            # Vision APIで解析するためのリクエスト作成
            image = vision.Image(content=image_bytes)
            
            # テキスト検出リクエスト
            response = self.client.text_detection(image=image)
            texts = response.text_annotations
            
            if not texts:
                logger.warning("画像からテキストが検出されませんでした")
                return ""
            
            # 最初の要素は画像全体のテキスト
            full_text = texts[0].description
            logger.info(f"テキスト抽出に成功しました: {len(full_text)} 文字")
            
            # エラーチェック
            if response.error.message:
                logger.error(f"テキスト検出中にエラーが発生しました: {response.error.message}")
                return ""
            
            return full_text
        
        except Exception as e:
            logger.error(f"テキスト抽出中にエラーが発生しました: {e}")
            return ""
    
    def preprocess_image(self, image_path, output_path=None):
        """
        OCR前に画像を前処理する
        
        Args:
            image_path: 処理する画像のパス
            output_path: 処理結果を保存するパス（Noneの場合は元の画像を上書き）
            
        Returns:
            処理された画像のパス
        """
        try:
            # 画像を開く
            with Image.open(image_path) as img:
                # グレースケールに変換
                img_gray = img.convert('L')
                
                # コントラスト強調
                # ここでは簡易的な処理のみ実装。必要に応じて調整可能
                
                # 保存パスが指定されていなければ元の画像を上書き
                save_path = output_path if output_path else image_path
                img_gray.save(save_path)
                
                logger.info(f"画像の前処理が完了しました: {save_path}")
                return save_path
                
        except Exception as e:
            logger.error(f"画像の前処理中にエラーが発生しました: {e}")
            return image_path  # エラー時は元の画像を返す
