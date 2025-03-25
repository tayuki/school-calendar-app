"""
OCR処理モジュール
Google Cloud Vision APIを使用して画像やPDFファイルからテキストを抽出します
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
            
    def process_pdf(self, pdf_path):
        """
        PDFファイルから直接テキストを抽出する
        
        Args:
            pdf_path (str): PDFファイルのパス
            
        Returns:
            str: 抽出されたテキスト
            
        Raises:
            ValueError: PDFのページ数が5を超える場合
            Exception: その他のエラー
        """
        if not self.client:
            logger.error("Vision APIクライアントが初期化されていません")
            return ""
            
        try:
            # PDFのページ数を確認（制限を超えるかチェック）
            self._check_pdf_page_count(pdf_path)
            
            # ファイルの内容を読み込む
            with open(pdf_path, 'rb') as pdf_file:
                content = pdf_file.read()
            
            # リクエストの作成
            input_config = vision.InputConfig(
                content=content,
                mime_type='application/pdf'
            )
            
            feature = vision.Feature(
                type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION
            )
            
            # ファイル全体に対する処理リクエストを作成
            request = vision.AnnotateFileRequest(
                input_config=input_config,
                features=[feature]
            )
            
            # バッチAPIを呼び出し
            response = self.client.batch_annotate_files(requests=[request])
            
            # レスポンスから結果を取得
            result = ""
            for response_obj in response.responses:
                for page in response_obj.responses:
                    result += page.full_text_annotation.text + "\n\n"
            
            if not result.strip():
                logger.warning("PDFからテキストが検出されませんでした")
                return ""
                
            logger.info(f"PDFからのテキスト抽出に成功しました: {len(result)} 文字")
            return result
        
        except ValueError as ve:
            # PDFページ数の制限エラーをそのまま伝播
            logger.error(f"PDF処理中にエラーが発生しました: {str(ve)}")
            raise
        except Exception as e:
            logger.error(f"PDF処理中にエラーが発生しました: {str(e)}")
            return ""
    
    def _check_pdf_page_count(self, pdf_path):
        """
        PDFのページ数を確認し、制限を超える場合はエラーを発生させる
        
        Args:
            pdf_path (str): PDFファイルのパス
            
        Raises:
            ValueError: PDFのページ数が5を超える場合
        """
        try:
            import fitz  # PyMuPDF
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            doc.close()
            
            logger.info(f"PDFのページ数: {page_count}")
            
            if page_count > 5:
                raise ValueError(f"PDFのページ数が制限を超えています（{page_count}ページ/最大5ページ）")
                
            return page_count
        except ImportError:
            logger.warning("PyMuPDFがインストールされていません。PDFページ数のチェックをスキップします。")
            # PyMuPDFがない場合は警告を出すだけで処理を続行
            return None
        except Exception as e:
            logger.error(f"PDFのページ数確認中にエラーが発生しました: {str(e)}")
            raise
