"""
テキスト解析モジュール
Google Gemini APIを使用してOCRで抽出されたテキストから
カレンダー予定情報を抽出します
"""
import logging
import json
import google.generativeai as genai
from datetime import datetime, timedelta
import pytz
import re

logger = logging.getLogger(__name__)

class TextAnalyzer:
    def __init__(self, api_key):
        """
        テキスト解析クラスの初期化
        
        Args:
            api_key: Google Gemini APIのAPIキー
        """
        self.api_key = api_key
        
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-pro')
            logger.info("Gemini APIの初期化に成功しました")
        except Exception as e:
            logger.error(f"Gemini APIの初期化に失敗しました: {e}")
            raise

    def extract_events(self, text):
        """
        テキストから予定情報を抽出する
        
        Args:
            text: 解析するテキスト
            
        Returns:
            抽出された予定情報のリスト
            [
                {
                    'title': 'イベントタイトル',
                    'description': '説明',
                    'start_date': '2025-03-15',
                    'start_time': '10:00',  # オプション
                    'end_date': '2025-03-15',  # 省略時はstart_dateと同じ
                    'end_time': '11:00',  # オプション
                    'all_day': True/False,
                    'location': '場所',  # オプション
                    'confidence': 0.95  # AIの確信度
                },
                ...
            ]
        """
        if not text.strip():
            logger.warning("解析するテキストが空です")
            return []
        
        try:
            # プロンプトの作成
            prompt = f"""
            あなたは学校のプリントから日程情報を抽出するAIアシスタントです。
            以下のOCRで読み取られたテキストから、カレンダーに登録すべきイベント・予定を全て特定してください。

            # 抽出ルール：
            - 日付、イベント名、時間（ある場合）、場所（ある場合）を抽出
            - 日本の日付表記（2025年3月21日、3/21など）を解析
            - 「明日」「来週木曜日」などの相対的な日付表現は、現在日付（{datetime.now().strftime('%Y年%m月%d日')}）から計算
            - 時間があれば開始・終了時間を特定（13:00～15:00、午後1時から3時まで、など）
            - 時間がない場合は終日イベントと判断

            # 出力形式：
            - JSONフォーマットで出力
            - 次のキーを持つオブジェクトの配列: title, description, start_date, start_time, end_date, end_time, all_day, location, confidence
            - 日付は'YYYY-MM-DD'形式（例: 2025-03-21）
            - 時間は'HH:MM'の24時間形式（例: 13:30）
            - all_dayは時間指定がなければtrue、あればfalse
            - confidence（確信度）は0.0～1.0の数値で、この情報がイベントとして正しい確率
            - description（説明）はイベントの詳細情報
            - 必須キー: title, start_date, all_day, confidence

            # OCRテキスト:
            {text}

            JSONデータのみを出力してください。説明や前置きは不要です。
            """
            
            # Gemini APIでテキスト解析
            response = self.model.generate_content(prompt)
            response_text = response.text
            
            # JSONデータの抽出（余分なテキストがある場合に対応）
            json_match = re.search(r'```json\n([\s\S]*?)\n```', response_text)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text.strip()
            
            # JSON文字列からデータを解析
            try:
                events = json.loads(json_str)
                logger.info(f"{len(events)}件のイベントが抽出されました")
                return events
            except json.JSONDecodeError as e:
                logger.error(f"JSONパースエラー: {e}")
                logger.debug(f"解析対象文字列: {json_str}")
                return []
                
        except Exception as e:
            logger.error(f"テキスト解析中にエラーが発生しました: {e}")
            return []

    def validate_event(self, event):
        """
        抽出されたイベント情報のバリデーションを行う
        
        Args:
            event: バリデーションするイベント情報
            
        Returns:
            バリデーション結果（True/False）とエラーメッセージ
        """
        errors = []
        
        # 必須フィールドのチェック
        required_fields = ['title', 'start_date']
        for field in required_fields:
            if field not in event or not event[field]:
                errors.append(f"{field}は必須項目です")
        
        # 日付フォーマットのチェック
        date_fields = ['start_date', 'end_date']
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for field in date_fields:
            if field in event and event[field]:
                if not date_pattern.match(event[field]):
                    errors.append(f"{field}は'YYYY-MM-DD'形式である必要があります")
                else:
                    try:
                        datetime.strptime(event[field], '%Y-%m-%d')
                    except ValueError:
                        errors.append(f"{field}が無効な日付です")
        
        # 時間フォーマットのチェック
        time_fields = ['start_time', 'end_time']
        time_pattern = re.compile(r'^\d{2}:\d{2}$')
        for field in time_fields:
            if field in event and event[field]:
                if not time_pattern.match(event[field]):
                    errors.append(f"{field}は'HH:MM'形式である必要があります")
                else:
                    try:
                        datetime.strptime(event[field], '%H:%M')
                    except ValueError:
                        errors.append(f"{field}が無効な時間です")
        
        # 終了日付のチェック（開始日付以降であること）
        if 'end_date' in event and event['end_date'] and 'start_date' in event and event['start_date']:
            try:
                start = datetime.strptime(event['start_date'], '%Y-%m-%d')
                end = datetime.strptime(event['end_date'], '%Y-%m-%d')
                if end < start:
                    errors.append("終了日は開始日以降である必要があります")
            except ValueError:
                # 日付フォーマットのエラーは上記で既にチェック済み
                pass
        
        # オプションフィールドのデフォルト値設定
        if 'all_day' not in event:
            event['all_day'] = 'start_time' not in event or not event['start_time']
        
        if 'end_date' not in event or not event['end_date']:
            event['end_date'] = event['start_date']
        
        return len(errors) == 0, errors
