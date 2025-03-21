"""
学校プリントOCR & カレンダー登録アプリケーション
メインアプリケーションモジュール
"""
import os
import json
import logging
import uuid
import tempfile
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime
from google_auth_oauthlib.flow import Flow  # Flow クラスのインポートを追加
from flask_session import Session  # Flask-Sessionをインポート

# 自作モジュールのインポート
from app.config import (
    SECRET_KEY, UPLOAD_FOLDER, ALLOWED_EXTENSIONS, GOOGLE_APPLICATION_CREDENTIALS,
    VISION_API_ENABLED, GEMINI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SCOPES, APP_BASE_URL,
    SESSION_TYPE, PERMANENT_SESSION_LIFETIME
)
from app.logging_config import setup_logging
from app.ocr import OCRProcessor
from app.text_analysis import TextAnalyzer
from app.calendar_api import CalendarService

# Flaskアプリケーションの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# セッション設定
app.config['SESSION_TYPE'] = SESSION_TYPE
app.config['SESSION_FILE_DIR'] = os.path.join(tempfile.gettempdir(), 'flask_session')
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = PERMANENT_SESSION_LIFETIME

# セッションの初期化
Session(app)

# ロギングの設定
setup_logging(app)
logger = logging.getLogger(__name__)

# セッションディレクトリの作成
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)
logger.info(f"セッションディレクトリ: {app.config['SESSION_FILE_DIR']}")

# サービスの初期化
ocr_processor = None
text_analyzer = None
calendar_service = None

def allowed_file(filename):
    """
    アップロードを許可するファイルかチェックする
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_services():
    """
    各種サービスを初期化する
    """
    global ocr_processor, text_analyzer, calendar_service
    
    try:
        # OCRサービスの初期化
        if VISION_API_ENABLED:
            ocr_processor = OCRProcessor(GOOGLE_APPLICATION_CREDENTIALS)
        
        # テキスト解析サービスの初期化
        if GEMINI_API_KEY:
            text_analyzer = TextAnalyzer(GEMINI_API_KEY)
        
        # カレンダーサービスの初期化
        if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
            redirect_uri = f"{APP_BASE_URL}/auth/callback"
            calendar_service = CalendarService(
                GOOGLE_CLIENT_ID, 
                GOOGLE_CLIENT_SECRET, 
                redirect_uri, 
                SCOPES
            )
        
        logger.info("サービスの初期化が完了しました")
        
    except Exception as e:
        logger.error(f"サービスの初期化中にエラーが発生しました: {e}")

# アプリケーション起動時にサービスを初期化
init_services()

@app.route('/')
def index():
    """
    メインページ
    """
    # 認証チェック
    if 'credentials' not in session:
        return render_template('index.html', authenticated=False)
    
    return render_template('index.html', authenticated=True)

@app.route('/upload', methods=['POST'])
def upload():
    """
    画像アップロードとOCR処理
    """
    # 認証チェック
    if 'credentials' not in session:
        flash('Googleアカウントでの認証が必要です', 'error')
        return redirect(url_for('index'))
    
    if 'file' not in request.files:
        flash('ファイルがアップロードされていません', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('ファイルが選択されていません', 'error')
        return redirect(url_for('index'))
    
    if not allowed_file(file.filename):
        flash('このファイル形式はサポートされていません', 'error')
        return redirect(url_for('index'))
    
    try:
        # 一意のファイル名を生成
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        
        # ファイルを保存
        file.save(file_path)
        logger.info(f"ファイルが保存されました: {file_path}")
        
        # OCR処理
        if not ocr_processor:
            flash('OCRサービスが設定されていません', 'error')
            return redirect(url_for('index'))
        
        # 必要に応じて画像の前処理
        file_path = ocr_processor.preprocess_image(file_path)
        
        # OCRでテキスト抽出
        extracted_text = ocr_processor.process_image(file_path)
        
        if not extracted_text:
            flash('テキストを抽出できませんでした', 'error')
            return redirect(url_for('index'))
        
        # テキスト解析
        if not text_analyzer:
            flash('テキスト解析サービスが設定されていません', 'error')
            return redirect(url_for('index'))
        
        events = text_analyzer.extract_events(extracted_text)
        
        if not events:
            flash('予定情報を抽出できませんでした', 'error')
            return redirect(url_for('index'))
        
        # セッションにデータを保存
        session['extracted_text'] = extracted_text
        session['events'] = events
        session['file_path'] = file_path
        
        # 確認ページへリダイレクト
        return redirect(url_for('confirm'))
        
    except Exception as e:
        logger.error(f"処理中にエラーが発生しました: {e}")
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/confirm')
def confirm():
    """
    予定情報の確認ページ
    """
    # セッションデータのチェック
    if 'events' not in session or 'extracted_text' not in session:
        flash('処理されたデータがありません', 'error')
        return redirect(url_for('index'))
    
    # カレンダーリストの取得
    if not calendar_service:
        flash('カレンダーサービスが設定されていません', 'error')
        return redirect(url_for('index'))
    
    try:
        # カレンダーサービスの再構築
        credentials_dict = session['credentials']
        credentials = calendar_service.credentials_from_dict(credentials_dict)
        calendar_service.build_service(credentials)
        
        calendars = calendar_service.get_calendar_list()
        
        return render_template(
            'confirm.html',
            events=session['events'],
            extracted_text=session['extracted_text'],
            calendars=calendars
        )
        
    except Exception as e:
        logger.error(f"カレンダー情報取得中にエラーが発生しました: {e}")
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/register', methods=['POST'])
def register():
    """
    Googleカレンダーへの予定登録
    """
    # セッションデータのチェック
    if 'events' not in session:
        flash('登録するイベントがありません', 'error')
        return redirect(url_for('index'))
    
    # カレンダーIDの取得
    calendar_id = request.form.get('calendar_id')
    if not calendar_id:
        flash('カレンダーが選択されていません', 'error')
        return redirect(url_for('confirm'))
    
    # イベントの選択状態を取得
    events = session['events']
    selected_indices = request.form.getlist('selected_events')
    
    # 修正されたイベント情報を取得
    for i, event in enumerate(events):
        str_i = str(i)
        if str_i in selected_indices:
            event['title'] = request.form.get(f'title_{i}', event.get('title', ''))
            event['description'] = request.form.get(f'description_{i}', event.get('description', ''))
            event['start_date'] = request.form.get(f'start_date_{i}', event.get('start_date', ''))
            event['end_date'] = request.form.get(f'end_date_{i}', event.get('end_date', ''))
            event['start_time'] = request.form.get(f'start_time_{i}', event.get('start_time', ''))
            event['end_time'] = request.form.get(f'end_time_{i}', event.get('end_time', ''))
            event['location'] = request.form.get(f'location_{i}', event.get('location', ''))
            event['all_day'] = f'all_day_{i}' in request.form
    
    # 選択されたイベントのみを抽出
    selected_events = [events[int(i)] for i in selected_indices]
    
    if not selected_events:
        flash('登録するイベントが選択されていません', 'error')
        return redirect(url_for('confirm'))
    
    try:
        # カレンダーサービスの再構築
        credentials_dict = session['credentials']
        credentials = calendar_service.credentials_from_dict(credentials_dict)
        calendar_service.build_service(credentials)
        
        # イベントの一括登録
        results = calendar_service.batch_create_events(calendar_id, selected_events)
        
        # 結果をセッションに保存
        session['register_results'] = results
        
        # 成功数をカウント
        success_count = sum(1 for r in results if r['success'])
        
        flash(f'{len(selected_events)}件中{success_count}件のイベントがカレンダーに登録されました', 'success')
        return redirect(url_for('result'))
        
    except Exception as e:
        logger.error(f"イベント登録中にエラーが発生しました: {e}")
        flash(f'エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('confirm'))

@app.route('/result')
def result():
    """
    登録結果ページ
    """
    # セッションデータのチェック
    if 'register_results' not in session:
        flash('登録結果がありません', 'error')
        return redirect(url_for('index'))
    
    return render_template('result.html', results=session['register_results'])

@app.route('/auth')
def auth():
    """
    Google認証の開始
    """
    if not calendar_service:
        flash('カレンダーサービスが設定されていません', 'error')
        return redirect(url_for('index'))
    
    try:
        # 認証URLの取得
        auth_url, flow = calendar_service.get_auth_url()
        
        # オリジナルのフローオブジェクトを保存する必要がありますが、JSONに変換できません
        # 代わりに必要な情報だけを保存
        session['client_secrets_file'] = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'credentials', 'client_secret.json')
        session['redirect_uri'] = flow.redirect_uri
        # スコープを設定ファイルから直接保存（flow.scopes ではなく）
        session['scopes'] = SCOPES  # 修正: flow.scopes の代わりに設定ファイルの SCOPES を使用
        
        # 認証URLにリダイレクト
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"認証URL取得中にエラーが発生しました: {e}")
        flash(f'認証エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/auth/callback')
def auth_callback():
    """
    Google認証のコールバック
    """
    if 'client_secrets_file' not in session or 'redirect_uri' not in session or 'scopes' not in session:
        flash('認証セッションが無効です', 'error')
        return redirect(url_for('index'))
    
    # エラーチェック
    if 'error' in request.args:
        flash(f'認証エラー: {request.args.get("error")}', 'error')
        return redirect(url_for('index'))
    
    # 認証コードの取得
    code = request.args.get('code')
    if not code:
        flash('認証コードが取得できませんでした', 'error')
        return redirect(url_for('index'))
    
    try:
        # フローを再建する
        client_secrets_file = session['client_secrets_file']
        redirect_uri = session['redirect_uri']
        scopes = session['scopes']  # session に保存された scopes を使用
        
        # フローを作成
        flow = Flow.from_client_secrets_file(
            client_secrets_file=client_secrets_file,
            scopes=scopes
        )
        flow.redirect_uri = redirect_uri
        
        # 認証情報を取得
        credentials = calendar_service.get_credentials_from_code(flow, code)
        
        # 認証情報をセッションに保存
        session['credentials'] = calendar_service.credentials_to_dict(credentials)
        
        flash('Googleアカウントでの認証が完了しました', 'success')
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"認証情報取得中にエラーが発生しました: {e}")
        flash(f'認証エラーが発生しました: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/logout')
def logout():
    """
    ログアウト処理
    """
    # 認証情報をセッションから削除
    if 'credentials' in session:
        del session['credentials']
    
    flash('ログアウトしました', 'success')
    return redirect(url_for('index'))

@app.route('/api/calendars')
def api_calendars():
    """
    カレンダーリストを取得するAPI
    """
    # 認証チェック
    if 'credentials' not in session:
        return jsonify({'error': '認証が必要です'}), 401
    
    try:
        # カレンダーサービスの再構築
        credentials_dict = session['credentials']
        credentials = calendar_service.credentials_from_dict(credentials_dict)
        calendar_service.build_service(credentials)
        
        # カレンダーリストの取得
        calendars = calendar_service.get_calendar_list()
        
        return jsonify(calendars)
        
    except Exception as e:
        logger.error(f"カレンダーリスト取得中にエラーが発生しました: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_event', methods=['POST'])
def api_update_event():
    """
    イベント情報を更新するAPI
    """
    # セッションデータのチェック
    if 'events' not in session:
        return jsonify({'error': 'イベントデータがありません'}), 400
    
    # リクエストデータの取得
    data = request.json
    if not data or 'index' not in data:
        return jsonify({'error': '無効なリクエストデータです'}), 400
    
    try:
        # イベント情報の更新
        index = int(data['index'])
        events = session['events']
        
        if index < 0 or index >= len(events):
            return jsonify({'error': '無効なイベントインデックスです'}), 400
        
        # 更新可能なフィールド
        update_fields = [
            'title', 'description', 'start_date', 'end_date', 
            'start_time', 'end_time', 'location', 'all_day'
        ]
        
        # フィールドの更新
        for field in update_fields:
            if field in data:
                events[index][field] = data[field]
        
        # バリデーション
        validator = text_analyzer
        is_valid, errors = validator.validate_event(events[index])
        
        if not is_valid:
            return jsonify({'error': 'バリデーションエラー', 'details': errors}), 400
        
        # 更新したイベントリストをセッションに保存
        session['events'] = events
        
        return jsonify({'success': True, 'event': events[index]})
        
    except Exception as e:
        logger.error(f"イベント更新中にエラーが発生しました: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def page_not_found(e):
    """
    404エラーハンドラ
    """
    return render_template('error.html', error='ページが見つかりません'), 404

@app.errorhandler(500)
def internal_server_error(e):
    """
    500エラーハンドラ
    """
    return render_template('error.html', error='サーバーエラーが発生しました'), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3501, debug=True)
