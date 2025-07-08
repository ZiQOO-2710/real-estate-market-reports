import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
import tempfile
import shutil
from datetime import datetime
import io
import requests
from typing import Optional
import hashlib
from map_utils import get_latlon_from_address
import time
import re

# --- Custom Modules ---
from data_processing import (
    normalize_columns,
    process_uploaded_csv,
    get_stats,
    clean_for_json,
    match_with_supabase
)

# --- Initializations ---
load_dotenv()

app = Flask(__name__)

# --- Configurations ---
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# --- Supabase Client ---
url: Optional[str] = os.environ.get("SUPABASE_URL")
key: Optional[str] = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url or "", key or "")

# --- 신규 아파트 DB 추가 함수 ---
def insert_new_apartments_to_supabase(df, supabase):
    # 위도/경도 없는(매칭 안 된) 단지만 추출
    new_apts = df[df['위도'].isna() | df['경도'].isna()].copy()
    # 시군구+번지 조합 컬럼 생성
    new_apts['lnno_adres'] = new_apts.apply(lambda row: f"{row.get('시군구', '')} {row.get('번지', '')}", axis=1)
    # 단지명, 도로명, lnno_adres, 건축년도 기준으로 중복 제거
    deduped = new_apts.drop_duplicates(subset=['단지명', '도로명', 'lnno_adres', '건축년도'])
    for _, row in deduped.iterrows():
        data = {
            'apt_nm': row.get('단지명', ''),
            'rdnmadr': row.get('도로명', ''),
            'use_aprv_yr': row.get('건축년도', ''),
            'lnno_adres': row.get('lnno_adres', ''),
        }
        supabase.table('apt_master_info').insert(data).execute()

# ------------------- Routes -------------------

@app.route('/')
def index():
    return render_template('index.html')

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if not file or not file.filename or not file.filename.endswith('.csv'):
        return redirect(request.url)
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    print(f"[UPLOAD] File saved to: {file_path}")

    # 파일 해시로 분석 결과 캐싱
    file_hash = get_file_hash(file_path)
    analyzed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_hash}_분석완료.csv')
    try:
        if os.path.exists(analyzed_path):
            print(f"[UPLOAD] 분석 캐시 파일 존재: {analyzed_path}")
            df = pd.read_csv(analyzed_path, encoding='utf-8-sig')
            columns = df.columns.tolist()
            temp_path = analyzed_path
        else:
            print("[UPLOAD] Calling process_uploaded_csv...")
            temp_path, columns = process_uploaded_csv(file_path)
            print(f"[UPLOAD] process_uploaded_csv returned temp_path: {temp_path}")
            df = pd.read_csv(temp_path, encoding='utf-8-sig')
            print(f"[UPLOAD] DataFrame loaded from temp_path. Columns: {df.columns.tolist()}")
            print(f"[UPLOAD] DataFrame head:\n{df.head()}")
            print("[UPLOAD] Calling match_with_supabase...")
            df = match_with_supabase(df, supabase)
            print(f"[UPLOAD] match_with_supabase returned. Columns: {df.columns.tolist()}")
            print(f"[UPLOAD] DataFrame head after Supabase match:\n{df.head()}")
            # --- 여기서 DB에서 la, lo를 다시 읽어와 최신 좌표로 덮어쓰기 ---
            for idx, row in df.iterrows():
                apt_nm = row.get('단지명', '')
                rdnmadr = row.get('도로명', '')
                lnno_adres = f"{row.get('시군구', '')} {row.get('번지', '')}"
                use_aprv_yr = row.get('건축년도', '')
                # DB에서 해당 단지의 la, lo 조회 (4개 컬럼 모두 일치)
                res = supabase.table('apt_master_info')\
                    .select('la,lo')\
                    .eq('apt_nm', apt_nm)\
                    .eq('rdnmadr', rdnmadr)\
                    .eq('lnno_adres', lnno_adres)\
                    .eq('use_aprv_yr', use_aprv_yr)\
                    .limit(1).execute()
                if res.data and res.data[0].get('la') and res.data[0].get('lo'):
                    df.at[idx, '위도'] = res.data[0]['la']
                    df.at[idx, '경도'] = res.data[0]['lo']
            # 매칭 안 된 아파트 신규 DB 추가
            insert_new_apartments_to_supabase(df, supabase)
            # 분석 결과를 캐시 파일로 저장
            df.to_csv(analyzed_path, index=False, encoding='utf-8-sig')
            temp_path = analyzed_path
            print(f"[UPLOAD] 분석 결과 캐시 파일 저장: {analyzed_path}")
        session['datafile'] = os.path.basename(temp_path)
        print(f"[UPLOAD] Processed file saved to session: {session['datafile']}")
        stats = get_stats(df)
        print("[UPLOAD] Stats generated. Rendering analysis.html...")
        return render_template('analysis.html', stats=stats, columns=columns, analyzed_file=filename)
    except Exception as e:
        print(f"[Upload Error] {e}")
        stats = {'total_count': 0, 'area_avg': 0, 'price_avg': 0, 'regions': {}, 'complexes': {}}
        return render_template('analysis.html', stats=stats, columns=[], message=f"파일 처리 중 오류: {e}")

@app.route('/filter', methods=['POST'])
def filter_data():
    address = request.form.get('address')
    radius_km = float(request.form.get('radius', 10))
    radius_m = radius_km * 1000

    if not address:
        return render_template('map.html', error='주소를 입력해주세요.', data=[], columns=[], center_lat=None, center_lon=None, radius=radius_m)

    if 'datafile' not in session:
        center_lat, center_lon = get_latlon_from_address(address)
        if center_lat is None or center_lon is None:
            return render_template('map.html', error='입력하신 주소로 좌표를 찾을 수 없습니다. 주소를 더 정확히 입력해 주세요.', data=[], columns=[], center_lat=None, center_lon=None, radius=radius_m)
        return render_template('map.html', data=[], columns=[], message='검색 결과 없음', center_lat=center_lat, center_lon=center_lon, radius=radius_m)

    try:
        temp_filename = session['datafile']
        # 항상 uploads 폴더에서만 찾도록 경로 고정
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(temp_filename))
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        columns = df.columns.tolist()

        center_lat, center_lon = get_latlon_from_address(address)
        if center_lat is None or center_lon is None:
            return render_template('map.html', error='입력하신 주소로 좌표를 찾을 수 없습니다. 주소를 더 정확히 입력해 주세요.', data=[], columns=columns, center_lat=None, center_lon=None, radius=radius_m)

        # 번지 컬럼 정규화: 숫자+하이픈만 남기고 문자열로 변환
        if '번지' in df.columns:
            df['번지'] = df['번지'].astype(str).str.replace(r'[^0-9\-]', '', regex=True)

        # Filter by distance
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        from geopy.distance import geodesic
        if not df.empty:
            df['거리'] = df.apply(lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).meters, axis=1)
        else:
            df['거리'] = np.nan
        filtered_df = df[df['거리'] <= radius_m].copy()
        avg_price = filtered_df['거래금액'].mean() if not filtered_df.empty else None
        data_records = filtered_df.to_dict(orient='records')  # type: ignore
        data_records = clean_for_json(data_records)
        return render_template(
            'map.html',
            data=data_records,
            columns=columns,
            avg_price=avg_price,
            count=len(filtered_df),
            no_data=(len(filtered_df) == 0),
            message='필터 조건에 맞는 데이터가 없습니다.' if len(filtered_df) == 0 else '',
            center_lat=center_lat,
            center_lon=center_lon,
            radius=radius_m
        )
    except Exception as e:
        print(f"[Filter Error] {e}")
        return render_template('map.html', error=f'필터링 중 오류: {e}', data=[], columns=[], center_lat=None, center_lon=None, radius=radius_m)

@app.route('/download', methods=['GET'])
def download_csv():
    if 'datafile' not in session:
        return "다운로드할 데이터가 없습니다.", 404

    temp_filename = session['datafile']
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

    if not os.path.exists(temp_path):
        return "파일을 찾을 수 없습니다.", 404

    return send_file(temp_path, as_attachment=True, download_name=f'analyzed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')

@app.route('/fill_latlon', methods=['GET'])
def fill_latlon():
    log_lines = []
    # 1. 위도/경도 없는 행 자동 채우기
    rows = supabase.table('apt_master_info').select('*').is_('la', None).execute().data
    for row in rows:
        uid = row['uid']
        lat, lon = None, None
        tried = []
        # 1) 도로명(rdnmadr)
        if row.get('rdnmadr'):
            tried.append(f"도로명: {row['rdnmadr']}")
            lat, lon = get_latlon_from_address(row['rdnmadr'])
        # 2) lnno_adres(시군구+번지)
        if (not lat or not lon) and row.get('lnno_adres'):
            tried.append(f"lnno_adres: {row['lnno_adres']}")
            lat, lon = get_latlon_from_address(row['lnno_adres'])
        # 3) 단지명(apt_nm)
        if (not lat or not lon) and row.get('apt_nm'):
            tried.append(f"단지명: {row['apt_nm']}")
            lat, lon = get_latlon_from_address(row['apt_nm'])
        if lat and lon:
            supabase.table('apt_master_info').update({'la': lat, 'lo': lon}).eq('uid', uid).execute()
            log_lines.append(f"[좌표업데이트] uid={uid}, la={lat}, lo={lon} | 시도: {tried}")
        else:
            log_lines.append(f"[좌표실패] uid={uid} | 시도: {tried}")
        time.sleep(0.2)
    # 2. 번지 비정상 행 도로명 기반 자동 보정
    def is_abnormal_bunji(bunji):
        if bunji is None or bunji == '' or str(bunji).startswith('-'):
            return True
        if re.fullmatch(r'\d{5,}', str(bunji)):
            return True
        return False
    rows2 = supabase.table('apt_master_info').select('*').execute().data
    for row in rows2:
        bunji = row.get('lnno_adres') or row.get('번지')
        if is_abnormal_bunji(bunji):
            road_addr = row.get('rdnmadr')
            new_bunji = None
            if road_addr:
                # 카카오맵 API로 도로명 주소 → 번지 추출
                url = 'https://dapi.kakao.com/v2/local/search/address.json'
                headers = {'Authorization': f'KakaoAK {os.environ.get("KAKAO_REST_API_KEY")}' }
                params = {'query': road_addr}
                resp = requests.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    docs = resp.json().get('documents')
                    if docs:
                        addr = docs[0].get('address')
                        if addr:
                            main = addr.get('main_address_no', '')
                            sub = addr.get('sub_address_no', '')
                            new_bunji = f"{main}-{sub}" if sub else main
            if new_bunji:
                supabase.table('apt_master_info').update({'lnno_adres': new_bunji}).eq('uid', row['uid']).execute()
                log_lines.append(f"[번지수정] uid={row['uid']} | {bunji} → {new_bunji} (도로명: {road_addr})")
            else:
                log_lines.append(f"[번지실패] uid={row['uid']} | 도로명으로 번지 찾기 실패 (도로명: {road_addr})")
            time.sleep(0.2)
    # 로그 파일 저장
    log_path = os.path.join('uploads', f"fill_latlon_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(log_path, 'w', encoding='utf-8') as f:
        for line in log_lines:
            f.write(line + '\n')
    return '<br>'.join(log_lines) + f'<br><br>로그 파일: {log_path}'

if __name__ == '__main__':
    # 항상 8000번 포트에서 실행
    app.run(debug=True, port=8000, host='0.0.0.0')