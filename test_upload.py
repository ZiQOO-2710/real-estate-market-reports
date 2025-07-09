#!/usr/bin/env python3
"""
간단한 파일 업로드 테스트용 Flask 앱
"""
from flask import Flask, render_template, request, redirect, url_for, flash, render_template_string
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB

# uploads 디렉터리 생성
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>파일 업로드 테스트</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>파일 업로드 테스트</h1>
        
        <!-- Flask 플래시 메시지 -->
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div style="color: red; margin: 10px 0; padding: 10px; border: 1px solid red;">
                        <strong>{{ '오류:' if category == 'error' else '알림:' }}</strong> {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <form action="/upload" method="post" enctype="multipart/form-data">
            <p>
                <label for="file">CSV 파일 선택:</label>
                <input type="file" id="file" name="file" accept=".csv" required>
            </p>
            <p>
                <button type="submit">업로드</button>
            </p>
        </form>
    </body>
    </html>
    ''')

@app.route('/upload', methods=['POST'])
def upload_file():
    print(f"[TEST] === 업로드 요청 디버깅 ===")
    print(f"[TEST] Request method: {request.method}")
    print(f"[TEST] Request content type: {request.content_type}")
    print(f"[TEST] Request files keys: {list(request.files.keys())}")
    print(f"[TEST] Request files: {request.files}")
    
    # 'file' 키가 있는지 확인
    if 'file' not in request.files:
        print("[TEST] 'file' key not in request.files")
        flash('파일 업로드 요청에 파일이 포함되지 않았습니다.', 'error')
        return redirect(url_for('index'))
    
    file = request.files['file']
    print(f"[TEST] File object: {file}")
    print(f"[TEST] File filename: {getattr(file, 'filename', 'NO_FILENAME')}")
    
    if not file or not file.filename:
        print("[TEST] No file or no filename")
        flash('CSV 파일을 선택해주세요.', 'error')
        return redirect(url_for('index'))
        
    if not file.filename.endswith('.csv'):
        print(f"[TEST] Invalid file extension: {file.filename}")
        flash('CSV 파일만 업로드 가능합니다.', 'error')
        return redirect(url_for('index'))
    
    print(f"[TEST] 업로드 성공: {file.filename}")
    flash(f'파일 업로드 성공: {file.filename}', 'success')
    return redirect(url_for('index'))

@app.errorhandler(413)
def request_entity_too_large(error):
    flash('파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=8003, host='0.0.0.0')