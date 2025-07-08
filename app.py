import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_file, session
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
import time
import re

# --- Custom Modules ---
from config import get_config, Config
from data_processing import (
    normalize_columns,
    process_uploaded_csv,
    get_stats,
    clean_for_json,
    match_with_supabase
)
from map_utils import get_latlon_from_address

# --- Application Factory ---
def create_app(config_name='default'):
    """애플리케이션 팩토리 함수"""
    app = Flask(__name__)
    
    # 설정 로드
    config = get_config(config_name)
    app.config.from_object(config)
    
    # 설정 검증
    try:
        config.validate_config()
    except ValueError as e:
        print(f"[ERROR] 설정 검증 실패: {e}")
        raise
    
    # 업로드 디렉토리 생성
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Supabase 클라이언트 초기화
    supabase = create_client(
        app.config['SUPABASE_URL'],
        app.config['SUPABASE_KEY']
    )
    
    # 애플리케이션 컨텍스트에 클라이언트 저장
    app.supabase = supabase
    
    return app

# --- 애플리케이션 생성 ---
app = create_app(os.environ.get('FLASK_ENV', 'default'))
supabase = app.supabase

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

@app.route('/analysis')
def analysis():
    """분석 결과 페이지 - GET 요청으로만 접근 가능"""
    if 'datafile' not in session:
        return redirect(url_for('index'))
    
    temp_filename = session['datafile']
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(temp_filename))
    
    if not os.path.exists(temp_path):
        return redirect(url_for('index'))
    
    try:
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        columns = df.columns.tolist()
        stats = get_stats(df)
        
        return render_template('analysis.html', 
                             stats=stats, 
                             columns=columns, 
                             analyzed_file=temp_filename)
    except Exception as e:
        print(f"[Analysis Error] {e}")
        return redirect(url_for('index'))

def get_file_hash(file_path):
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        file = request.files.get('file')
        if not file or not file.filename or not file.filename.endswith('.csv'):
            return jsonify({'error': '유효한 CSV 파일을 선택해주세요.'}), 400
        
        # 파일 크기 검증
        if file.content_length and file.content_length > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({'error': f'파일 크기가 너무 큽니다. 최대 {app.config["MAX_CONTENT_LENGTH"]//1024//1024}MB까지 업로드 가능합니다.'}), 400
        
        # 전용면적 구간 선택값 받기
        area_range = request.form.get('area_range', 'all')
        session['area_range'] = area_range
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"[UPLOAD] File saved to: {file_path}")

        # 파일 해시로 분석 결과 캐싱
        file_hash = get_file_hash(file_path)
        analyzed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_hash}_분석완료.csv')
        
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
    except FileNotFoundError as e:
        print(f"[Upload Error - File Not Found] {e}")
        return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
    except pd.errors.EmptyDataError as e:
        print(f"[Upload Error - Empty Data] {e}")
        return jsonify({'error': '빈 파일이거나 유효한 데이터가 없습니다.'}), 400
    except pd.errors.ParserError as e:
        print(f"[Upload Error - Parser Error] {e}")
        return jsonify({'error': 'CSV 파일 형식이 올바르지 않습니다.'}), 400
    except MemoryError as e:
        print(f"[Upload Error - Memory Error] {e}")
        return jsonify({'error': '파일이 너무 커서 처리할 수 없습니다.'}), 413
    except Exception as e:
        print(f"[Upload Error] {e}")
        return jsonify({'error': f'파일 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/filter', methods=['POST'])
def filter_data():
    # POST 데이터를 세션에 저장하고 GET으로 리다이렉트 (PRG 패턴)
    session['filter_params'] = {
        'address': request.form.get('address'),
        'radius': float(request.form.get('radius', 10)),
        'area_range': request.form.get('area_range', session.get('area_range', 'all')),
        'build_year': request.form.get('build_year', session.get('build_year', 'all')),
        'sort_col': request.form.get('sort_col'),
        'sort_order': request.form.get('sort_order', 'desc')
    }
    return redirect(url_for('show_filtered_results'))

@app.route('/results')
def show_filtered_results():
    # 세션에서 필터 파라미터 가져오기
    filter_params = session.get('filter_params')
    if not filter_params:
        return redirect(url_for('index'))
    
    address = filter_params.get('address')
    radius_km = filter_params.get('radius', 10)
    radius_m = radius_km * 1000
    area_range = filter_params.get('area_range', 'all')
    sort_col = filter_params.get('sort_col')
    sort_order = filter_params.get('sort_order', 'desc')
    
    # 페이지네이션 파라미터
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))  # 기본 20개씩

    # 전용면적 구간 세션에 저장
    session['area_range'] = area_range

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

        # --- 전용면적 구간 필터링 ---
        area_col = None
        for col in ['전용면적(㎡)', '전용면적(\u33A1)']:
            if col in df.columns:
                area_col = col
                break
        if area_col:
            if area_range == 'le60':
                df = df[df[area_col] <= 60]
            elif area_range == 'gt60le85':
                df = df[(df[area_col] > 60) & (df[area_col] <= 85)]
            elif area_range == 'gt85le102':
                df = df[(df[area_col] > 85) & (df[area_col] <= 102)]
            elif area_range == 'gt102le135':
                df = df[(df[area_col] > 102) & (df[area_col] <= 135)]
            elif area_range == 'gt135':
                df = df[df[area_col] > 135]
            # 'all'은 필터링 없음

        # --- 건축년도 필터링 ---
        build_year = filter_params.get('build_year', 'all')
        if build_year != 'all' and '건축년도' in df.columns:
            current_year = datetime.now().year
            df['건축년도'] = pd.to_numeric(df['건축년도'], errors='coerce')
            df = df.dropna(subset=['건축년도'])
            
            if build_year == 'recent5':
                df = df[df['건축년도'] >= (current_year - 5)]
            elif build_year == 'recent10':
                df = df[df['건축년도'] >= (current_year - 10)]
            elif build_year == 'recent15':
                df = df[df['건축년도'] >= (current_year - 15)]
            elif build_year == 'over15':
                df = df[df['건축년도'] < (current_year - 15)]

        # Filter by distance
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        from geopy.distance import geodesic
        if not df.empty:
            df['중심점과의거리'] = df.apply(lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).meters / 1000, axis=1)  # km 단위
        else:
            df['중심점과의거리'] = np.nan
            
        filtered_df = df[df['중심점과의거리'] <= radius_km].copy()

        # --- 정렬 기능 추가 ---
        if sort_col and sort_col in filtered_df.columns:
            # 숫자/문자 구분 없이 정렬
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=(sort_order=='asc'), na_position='last')

        # 평균 거래금액 계산 (안전하게)
        avg_price = 0
        if not filtered_df.empty and '거래금액' in filtered_df.columns:
            price_series = pd.to_numeric(filtered_df['거래금액'], errors='coerce')
            avg_price = price_series.mean() if not price_series.isna().all() else 0
        
        # --- 페이지네이션 적용 ---
        total_count = len(filtered_df)
        total_pages = (total_count + per_page - 1) // per_page  # 올림 계산
        
        # 페이지 범위 검증
        if page < 1:
            page = 1
        elif page > total_pages and total_pages > 0:
            page = total_pages
        
        # 현재 페이지 데이터 추출
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_df = filtered_df.iloc[start_idx:end_idx]
        
        data_records = paginated_df.to_dict(orient='records')  # type: ignore
        # --- 숫자 포맷팅: 번지, 거래금액 제외 모든 숫자에 쉼표 추가 ---
        def format_number(val):
            try:
                if val is None or val == '' or (isinstance(val, float) and pd.isna(val)):
                    return ''
                if isinstance(val, (int, float)):
                    return '{:,}'.format(int(val))
                if isinstance(val, str) and val.replace(',', '').replace('.', '', 1).isdigit():
                    return '{:,}'.format(int(float(val)))
                return val
            except Exception:
                return val
        for row in data_records:
            for col in columns:
                # 거래금액만 쉼표, 계약년월은 원본 그대로, 전용면적(㎡)은 소수점 둘째자리까지
                if col == '거래금액' and col in row and (isinstance(row[col], (int, float)) or (isinstance(row[col], str) and row[col].replace(',', '').replace('.', '', 1).isdigit())):
                    row[col] = format_number(row[col])
                if (col == '전용면적(㎡)' or col == '전용면적(㎡)') and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):.2f}"
                    except Exception:
                        pass
                if col == '전용평' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):.2f}"
                    except Exception:
                        pass
        data_records = clean_for_json(data_records)
        
        # 페이지네이션 정보 계산
        pagination_info = {
            'page': page,
            'per_page': per_page,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None,
            'start_item': start_idx + 1 if total_count > 0 else 0,
            'end_item': min(end_idx, total_count),
            'page_range': list(range(max(1, page - 2), min(total_pages + 1, page + 3)))
        }
        
        # 안전한 데이터 준비
        safe_data = {
            'data': data_records or [],
            'columns': columns or [],
            'avg_price': float(avg_price) if avg_price and not pd.isna(avg_price) else 0,
            'count': total_count,
            'no_data': total_count == 0,
            'message': '필터 조건에 맞는 데이터가 없습니다.' if total_count == 0 else '',
            'center_lat': float(center_lat) if center_lat else 36.815,
            'center_lon': float(center_lon) if center_lon else 127.1138,
            'radius': radius_m,
            'first_lat': float(data_records[0].get('위도', 0)) if data_records else None,
            'first_lon': float(data_records[0].get('경도', 0)) if data_records else None,
            'pagination': pagination_info
        }
        
        return render_template('results.html', **safe_data)
    except Exception as e:
        print(f"[Filter Error] {e}")
        error_pagination = {
            'page': 1,
            'per_page': per_page,
            'total_count': 0,
            'total_pages': 0,
            'has_prev': False,
            'has_next': False,
            'prev_page': None,
            'next_page': None,
            'start_item': 0,
            'end_item': 0,
            'page_range': []
        }
        error_data = {
            'error': f'필터링 중 오류: {e}',
            'data': [],
            'columns': [],
            'avg_price': 0,
            'count': 0,
            'no_data': True,
            'message': '필터링 중 오류가 발생했습니다.',
            'center_lat': 36.815,
            'center_lon': 127.1138,
            'radius': radius_m,
            'first_lat': None,
            'first_lon': None,
            'pagination': error_pagination
        }
        return render_template('results.html', **error_data)

@app.route('/download', methods=['GET'])
def download_csv():
    if 'datafile' not in session:
        return "다운로드할 데이터가 없습니다.", 404

    temp_filename = session['datafile']
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

    if not os.path.exists(temp_path):
        return "파일을 찾을 수 없습니다.", 404

    # area_range 및 build_year 세션값에 따라 필터링해서 다운로드
    area_range = session.get('area_range', 'all')
    build_year = session.get('build_year', 'all')
    df = pd.read_csv(temp_path, encoding='utf-8-sig')
    
    # 전용면적 필터링
    area_col = None
    for col in ['전용면적(㎡)', '전용면적(\u33A1)']:
        if col in df.columns:
            area_col = col
            break
    if area_col:
        if area_range == 'le60':
            df = df[df[area_col] <= 60]
        elif area_range == 'gt60le85':
            df = df[(df[area_col] > 60) & (df[area_col] <= 85)]
        elif area_range == 'gt85le102':
            df = df[(df[area_col] > 85) & (df[area_col] <= 102)]
        elif area_range == 'gt102le135':
            df = df[(df[area_col] > 102) & (df[area_col] <= 135)]
        elif area_range == 'gt135':
            df = df[df[area_col] > 135]
        # 'all'은 필터링 없음
    
    # 건축년도 필터링
    if build_year != 'all' and '건축년도' in df.columns:
        current_year = datetime.now().year
        df['건축년도'] = pd.to_numeric(df['건축년도'], errors='coerce')
        df = df.dropna(subset=['건축년도'])
        
        if build_year == 'recent5':
            df = df[df['건축년도'] >= (current_year - 5)]
        elif build_year == 'recent10':
            df = df[df['건축년도'] >= (current_year - 10)]
        elif build_year == 'recent15':
            df = df[df['건축년도'] >= (current_year - 15)]
        elif build_year == 'over15':
            df = df[df['건축년도'] < (current_year - 15)]
    # 임시 파일로 저장해서 다운로드
    from io import BytesIO
    output = BytesIO()
    df.to_csv(output, index=False, encoding='utf-8-sig')
    output.seek(0)
    return send_file(output, as_attachment=True, download_name=f'analyzed_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv', mimetype='text/csv')

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
    # 항상 8001번 포트에서 실행
    app.run(debug=True, port=8001, host='0.0.0.0')