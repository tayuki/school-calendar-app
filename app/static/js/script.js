/**
 * 学校プリントカレンダー登録アプリケーション
 * 共通JavaScript機能
 */

// DOMコンテンツ読み込み完了時の処理
document.addEventListener('DOMContentLoaded', function() {
    // フォーム送信時の処理
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // 送信ボタンのdisabled属性がある場合は処理しない
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && submitButton.hasAttribute('disabled')) {
                return;
            }
            
            // ファイルアップロード時はローディング表示
            if (form.getAttribute('enctype') === 'multipart/form-data') {
                const fileInput = form.querySelector('input[type="file"]');
                if (fileInput && fileInput.files.length > 0) {
                    showLoading('処理中...');
                    
                    // 送信ボタンを無効化
                    if (submitButton) {
                        submitButton.setAttribute('disabled', 'disabled');
                        const originalText = submitButton.innerHTML;
                        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 処理中...';
                        
                        // フォーム送信完了後に元に戻す（念のため）
                        setTimeout(() => {
                            submitButton.removeAttribute('disabled');
                            submitButton.innerHTML = originalText;
                        }, 30000); // 30秒後
                    }
                }
            }
            
            // イベント登録フォームの場合も処理中表示
            if (form.id === 'eventForm') {
                showLoading('カレンダーに登録中...');
                
                // 送信ボタンを無効化
                if (submitButton) {
                    submitButton.setAttribute('disabled', 'disabled');
                    const originalText = submitButton.innerHTML;
                    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> 登録中...';
                }
            }
        });
    });
    
    // アラートの自動消去（5秒後）
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // ファイル入力のプレビュー（存在する場合）
    const fileInput = document.getElementById('file');
    const preview = document.getElementById('preview');
    
    if (fileInput && preview) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    // 画像表示
                    preview.innerHTML = `<img src="${e.target.result}" class="img-fluid rounded" alt="プレビュー">`;
                    preview.style.display = 'block';
                };
                
                reader.readAsDataURL(this.files[0]);
            } else {
                // ファイルが選択されていない場合はプレビューを非表示
                preview.style.display = 'none';
                preview.innerHTML = '';
            }
        });
    }
    
    // ファイルドラッグ&ドロップエリア（存在する場合）
    const dropArea = document.getElementById('drop-area');
    
    if (dropArea && fileInput) {
        // ドラッグオーバーイベント
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        // ハイライト
        ['dragenter', 'dragover'].forEach(eventName => {
            dropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropArea.addEventListener(eventName, unhighlight, false);
        });
        
        function highlight() {
            dropArea.classList.add('highlight');
        }
        
        function unhighlight() {
            dropArea.classList.remove('highlight');
        }
        
        // ドロップ処理
        dropArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            
            if (files.length > 0) {
                fileInput.files = files;
                // changeイベントを発火
                const event = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(event);
            }
        }
    }
});

/**
 * ローディングオーバーレイを表示
 * @param {string} message - 表示するメッセージ
 */
function showLoading(message = '処理中...') {
    // 既存のローディングオーバーレイを削除
    hideLoading();
    
    // 新しいローディングオーバーレイを作成
    const loadingOverlay = document.createElement('div');
    loadingOverlay.classList.add('loading-overlay');
    loadingOverlay.innerHTML = `
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="loading-text">${message}</p>
        </div>
    `;
    
    // bodyに追加
    document.body.appendChild(loadingOverlay);
    document.body.style.overflow = 'hidden'; // スクロール防止
}

/**
 * ローディングオーバーレイを非表示
 */
function hideLoading() {
    const existingOverlay = document.querySelector('.loading-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
        document.body.style.overflow = ''; // スクロール許可
    }
}

/**
 * 日付の変換: YYYY-MM-DD → YYYY年MM月DD日
 * @param {string} dateStr - YYYY-MM-DD形式の日付文字列
 * @return {string} 変換後の日付文字列
 */
function formatDate(dateStr) {
    if (!dateStr) return '';
    
    const parts = dateStr.split('-');
    if (parts.length !== 3) return dateStr;
    
    return `${parts[0]}年${parseInt(parts[1])}月${parseInt(parts[2])}日`;
}

/**
 * 時間の変換: HH:MM → HH時MM分
 * @param {string} timeStr - HH:MM形式の時間文字列
 * @return {string} 変換後の時間文字列
 */
function formatTime(timeStr) {
    if (!timeStr) return '';
    
    const parts = timeStr.split(':');
    if (parts.length !== 2) return timeStr;
    
    return `${parseInt(parts[0])}時${parseInt(parts[1])}分`;
}
