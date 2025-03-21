"""
Google Calendar API連携モジュール
"""
import logging
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

logger = logging.getLogger(__name__)

class CalendarService:
    def __init__(self, client_id, client_secret, redirect_uri, scopes):
        """
        Google Calendar APIサービスの初期化
        
        Args:
            client_id: Google OAuth クライアントID
            client_secret: Google OAuth クライアントシークレット
            redirect_uri: 認証後のリダイレクトURI
            scopes: 要求するOAuthスコープのリスト
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.scopes = scopes
        self.credentials = None
        self.service = None
    
    def get_auth_url(self):
        """
        認証URLを取得する
        
        Returns:
            認証URL
        """
        try:
            # クライアントシークレットファイルを使用してフローを作成
            client_secrets_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials', 'client_secret.json')
            flow = Flow.from_client_secrets_file(
                client_secrets_file=client_secrets_file,
                scopes=self.scopes
            )
            flow.redirect_uri = self.redirect_uri
            
            # クライアント側でサーバー状態を保持するために、オフライン・アクセスを要求
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return auth_url, flow
        
        except Exception as e:
            logger.error(f"認証URL取得中にエラーが発生しました: {e}")
            raise

    def get_credentials_from_code(self, flow, code):
        """
        認証コードからCredentialsを取得する
        
        Args:
            flow: 認証フロー
            code: 認証コード
            
        Returns:
            認証情報
        """
        try:
            # フローのリダイレクトURIを設定
            flow.redirect_uri = self.redirect_uri
            
            # 認証コードからトークンを取得
            flow.fetch_token(code=code)
            self.credentials = flow.credentials
            return self.credentials
        
        except Exception as e:
            logger.error(f"認証情報取得中にエラーが発生しました: {e}")
            raise
    
    def build_service(self, credentials):
        """
        認証情報からCalendarサービスを構築する
        
        Args:
            credentials: 認証情報
            
        Returns:
            Calendarサービス
        """
        try:
            self.credentials = credentials
            self.service = build('calendar', 'v3', credentials=credentials)
            logger.info("Google Calendar APIサービスの構築に成功しました")
            return self.service
        
        except Exception as e:
            logger.error(f"Calendar APIサービス構築中にエラーが発生しました: {e}")
            raise
    
    def get_calendar_list(self):
        """
        ユーザーのカレンダーリストを取得する
        
        Returns:
            カレンダー情報のリスト
        """
        if not self.service:
            logger.error("Calendar APIサービスが初期化されていません")
            return []
        
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = calendar_list.get('items', [])
            
            # 必要な情報のみ抽出
            result = []
            for calendar in calendars:
                result.append({
                    'id': calendar['id'],
                    'summary': calendar['summary'],
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'accessRole': calendar.get('accessRole', '')
                })
            
            logger.info(f"{len(result)}件のカレンダーを取得しました")
            return result
        
        except Exception as e:
            logger.error(f"カレンダーリスト取得中にエラーが発生しました: {e}")
            return []
    
    def create_event(self, calendar_id, event_data):
        """
        カレンダーにイベントを作成する
        
        Args:
            calendar_id: イベントを作成するカレンダーID
            event_data: イベント情報
            
        Returns:
            作成されたイベント情報
        """
        if not self.service:
            logger.error("Calendar APIサービスが初期化されていません")
            return None
        
        try:
            # デバッグ用にイベントデータをログ出力
            logger.debug(f"イベント作成データ: {event_data}")
            
            # イベントデータの整形
            event = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'location': event_data.get('location', '')
            }
            
            # all_dayフィールドが文字列の場合、booleanに変換
            if isinstance(event_data.get('all_day'), str):
                event_data['all_day'] = event_data['all_day'].lower() == 'true'
            
            # 終日イベントかどうかで日付の設定方法を変える
            if event_data.get('all_day', True):
                # 終日イベントの場合はdate形式で設定
                start_date = event_data['start_date']
                end_date = event_data.get('end_date', start_date)
                
                # 終日イベントはGoogleカレンダーAPIでは終了日が翌日になるので調整
                # （実際のカレンダー表示では元の日付で表示）
                end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
                end_date_obj = end_date_obj + timedelta(days=1)
                end_date = end_date_obj.strftime('%Y-%m-%d')
                
                event['start'] = {'date': start_date}
                event['end'] = {'date': end_date}
            else:
                # 時間指定イベントはdateTime形式で設定
                start_date = event_data['start_date']
                end_date = event_data.get('end_date', start_date)
                
                # 時間情報の確認
                start_time = event_data.get('start_time')
                end_time = event_data.get('end_time')
                
                # 時間情報が不完全な場合のデフォルト設定
                if not start_time:
                    start_time = '00:00'
                if not end_time:
                    # 終了時間がない場合は開始時間の1時間後をデフォルトにする
                    if start_time:
                        start_time_obj = datetime.strptime(start_time, '%H:%M')
                        end_time_obj = start_time_obj + timedelta(hours=1)
                        end_time = end_time_obj.strftime('%H:%M')
                    else:
                        end_time = '01:00'  # デフォルトの終了時間
                
                # タイムゾーン設定（日本時間）
                tz = 'Asia/Tokyo'
                start_datetime = f"{start_date}T{start_time}:00"
                end_datetime = f"{end_date}T{end_time}:00"
                
                event['start'] = {'dateTime': start_datetime, 'timeZone': tz}
                event['end'] = {'dateTime': end_datetime, 'timeZone': tz}
            
            # イベント作成APIの呼び出し前にデバッグログ
            logger.debug(f"Googleカレンダーに送信するイベントデータ: {event}")
            
            # イベント作成APIの呼び出し
            created_event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
            
            logger.info(f"イベントが作成されました: {created_event['id']}")
            return created_event
        
        except Exception as e:
            logger.error(f"イベント作成中にエラーが発生しました: {e}")
            logger.error(f"問題のあるイベントデータ: {event_data}")
            return None
    
    def batch_create_events(self, calendar_id, event_data_list):
        """
        複数のイベントをバッチで作成する
        
        Args:
            calendar_id: イベントを作成するカレンダーID
            event_data_list: イベント情報のリスト
            
        Returns:
            作成されたイベント情報のリスト
        """
        results = []
        success_count = 0
        
        for event_data in event_data_list:
            try:
                # イベントデータのバリデーション
                if not self._validate_event_data(event_data):
                    raise ValueError("イベントデータが不正です")
                
                result = self.create_event(calendar_id, event_data)
                if result:
                    success_count += 1
                    results.append({
                        'success': True,
                        'event': result,
                        'original_data': event_data
                    })
                else:
                    results.append({
                        'success': False,
                        'error': '不明なエラー',
                        'original_data': event_data
                    })
            except Exception as e:
                logger.error(f"イベント作成エラー: {e}, イベントデータ: {event_data}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'original_data': event_data
                })
        
        logger.info(f"{len(event_data_list)}件中{success_count}件のイベント作成に成功しました")
        return results
    
    def _validate_event_data(self, event_data):
        """
        イベントデータのバリデーションを行う
        
        Args:
            event_data: バリデーションするイベントデータ
            
        Returns:
            バリデーション結果（True/False）
        """
        try:
            # 必須フィールドの確認
            if 'title' not in event_data or not event_data['title']:
                logger.error("イベントタイトルが設定されていません")
                return False
            
            if 'start_date' not in event_data or not event_data['start_date']:
                logger.error("開始日が設定されていません")
                return False
            
            # 日付形式の確認
            try:
                start_date = datetime.strptime(event_data['start_date'], '%Y-%m-%d')
                
                if 'end_date' in event_data and event_data['end_date']:
                    end_date = datetime.strptime(event_data['end_date'], '%Y-%m-%d')
                    # 終了日が開始日より前の場合
                    if end_date < start_date:
                        logger.error("終了日が開始日より前になっています")
                        # 自動修正
                        event_data['end_date'] = event_data['start_date']
            except ValueError:
                logger.error("日付形式が不正です")
                return False
            
            # 時間形式の確認
            if 'all_day' in event_data and not event_data['all_day']:
                if 'start_time' in event_data and event_data['start_time']:
                    try:
                        datetime.strptime(event_data['start_time'], '%H:%M')
                    except ValueError:
                        logger.error("開始時間の形式が不正です")
                        # 自動修正
                        event_data['start_time'] = '00:00'
                
                if 'end_time' in event_data and event_data['end_time']:
                    try:
                        datetime.strptime(event_data['end_time'], '%H:%M')
                    except ValueError:
                        logger.error("終了時間の形式が不正です")
                        # 自動修正
                        event_data['end_time'] = '01:00'
            
            return True
        
        except Exception as e:
            logger.error(f"イベントデータのバリデーション中にエラーが発生しました: {e}")
            return False
    
    def credentials_to_dict(self, credentials):
        """
        認証情報をJSON保存用の辞書に変換する
        
        Args:
            credentials: 変換する認証情報
            
        Returns:
            辞書形式の認証情報
        """
        return {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
    
    def credentials_from_dict(self, credentials_dict):
        """
        辞書から認証情報を復元する
        
        Args:
            credentials_dict: 辞書形式の認証情報
            
        Returns:
            復元された認証情報
        """
        return Credentials(
            token=credentials_dict['token'],
            refresh_token=credentials_dict['refresh_token'],
            token_uri=credentials_dict['token_uri'],
            client_id=credentials_dict['client_id'],
            client_secret=credentials_dict['client_secret'],
            scopes=credentials_dict['scopes']
        )
