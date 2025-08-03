import os
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash
from supabase import create_client, Client

# .env 파일 로드
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"[ENV] .env 파일 로드 완료. KAKAO_REST_API_KEY: {'설정됨' if os.environ.get('KAKAO_REST_API_KEY') else '없음'}")
except ImportError:
    print("[ENV] python-dotenv 패키지가 없습니다. 환경변수가 수동으로 설정되어야 합니다.")
except Exception as e:
    print(f"[ENV] .env 파일 로드 중 오류: {e}")
import pandas as pd
import numpy as np
from werkzeug.utils import secure_filename
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
from map_utils import get_latlon_from_address, clear_cache

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
    
    # 파일 크기 초과 오류 핸들러
    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash('파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.', 'error')
        return redirect(url_for('index'))
    
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
    # 템플릿 렌더링 전에 플래시 메시지 확인
    print(f"[DEBUG] Flash messages: {session.get('_flashes', [])}")
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
        print(f"[UPLOAD] 🚀 === 데이터 분석 시작 ===")
        print(f"[UPLOAD] 📝 요청 정보: {request.method} - {request.content_type}")
        print(f"[UPLOAD] 📁 파일 키: {list(request.files.keys())}")
        print(f"[UPLOAD] 🔄 단계 1/6: 파일 업로드 시작...")
        
        # 'file' 키가 있는지 확인
        if 'file' not in request.files:
            print("[UPLOAD] 'file' key not in request.files")
            flash('파일 업로드 요청에 파일이 포함되지 않았습니다.', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        print(f"[UPLOAD] File object: {file}")
        print(f"[UPLOAD] File filename: {getattr(file, 'filename', 'NO_FILENAME')}")
        
        if not file or not file.filename:
            print("[UPLOAD] No file or no filename")
            flash('CSV 파일을 선택해주세요.', 'error')
            return redirect(url_for('index'))
            
        if not file.filename.endswith('.csv'):
            print(f"[UPLOAD] Invalid file extension: {file.filename}")
            flash('CSV 파일만 업로드 가능합니다. (.csv 확장자 필요)', 'error')
            return redirect(url_for('index'))
        
        print(f"[UPLOAD] File validation passed: {file.filename}")
        
        # 파일 크기 검증
        if file.content_length and file.content_length > app.config.get('MAX_CONTENT_LENGTH', 50*1024*1024):
            flash(f'파일 크기가 너무 큽니다. 최대 50MB까지 업로드 가능합니다.', 'error')
            return redirect(url_for('index'))
        
        # 전용면적 구간 선택값 받기
        area_range = request.form.get('area_range', 'all')
        session['area_range'] = area_range
        
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        print(f"[UPLOAD] 💾 파일 저장: {file_path}")
        print(f"[UPLOAD] 📏 파일 크기: {os.path.getsize(file_path):,} bytes")
        print(f"[UPLOAD] ✅ 단계 1/6: 파일 업로드 완료")

        # 파일 해시로 분석 결과 캐싱
        file_hash = get_file_hash(file_path)
        analyzed_path = os.path.join(app.config['UPLOAD_FOLDER'], f'{file_hash}_분석완료.csv')
        
        if os.path.exists(analyzed_path):
            print(f"[UPLOAD] 🎯 캐시 파일 발견: {analyzed_path}")
            print(f"[UPLOAD] 📊 캐시 파일 크기: {os.path.getsize(analyzed_path):,} bytes")
            print(f"[UPLOAD] ⚡ 캐시 파일 사용으로 빠른 처리")
            df = pd.read_csv(analyzed_path, encoding='utf-8-sig')
            columns = df.columns.tolist()
            temp_path = analyzed_path
        else:
            print("[UPLOAD] 🔄 단계 2/6: 데이터 전처리 시작...")
            temp_path, columns = process_uploaded_csv(file_path)
            print(f"[UPLOAD] ✅ 단계 2/6: 데이터 전처리 완료 - 처리된 파일: {temp_path}")
            df = pd.read_csv(temp_path, encoding='utf-8-sig')
            print(f"[UPLOAD] 📊 데이터 로드 완료 - 행 수: {len(df)}, 컬럼 수: {len(df.columns)}")
            print(f"[UPLOAD] 📋 컬럼 목록: {df.columns.tolist()}")
            
            print("[UPLOAD] 🔄 단계 3/6: Supabase DB 좌표 조회 시작...")
            df = match_with_supabase(df, supabase)  # 재활성화
            print("[UPLOAD] ✅ 단계 3/6: Supabase DB 좌표 조회 완료")
            
            # 신규 아파트 정보 DB 저장
            print("[UPLOAD] 🔄 단계 4/6: 신규 아파트 정보 DB 저장 시작...")
            try:
                insert_new_apartments_to_supabase(df, supabase)
                print("[UPLOAD] ✅ 단계 4/6: 신규 아파트 정보 DB 저장 완료")
            except Exception as e:
                print(f"[UPLOAD] ❌ 단계 4/6: 신규 아파트 정보 DB 저장 실패: {e}")
            
            # 좌표 변환 및 DB 저장 완료
            print("[UPLOAD] 🔄 단계 5/6: 데이터 분석 시작...")
            coord_count = df[['위도', '경도']].dropna().shape[0]
            print(f"[UPLOAD] 📍 좌표 보유 데이터: {coord_count}건 / 전체 {len(df)}건")
            print("[UPLOAD] ✅ 단계 5/6: 데이터 분석 완료")
            
            # 분석 결과를 캐시 파일로 저장
            print("[UPLOAD] 🔄 단계 6/6: 결과 파일 생성 시작...")
            df.to_csv(analyzed_path, index=False, encoding='utf-8-sig')
            temp_path = analyzed_path
            print(f"[UPLOAD] 💾 결과 파일 저장: {analyzed_path}")
            print("[UPLOAD] ✅ 단계 6/6: 결과 파일 생성 완료")
            
        session['datafile'] = os.path.basename(temp_path)
        print(f"[UPLOAD] 🎉 === 데이터 분석 완료 === 총 {len(df) if 'df' in locals() else 0}건 처리")
        print(f"[UPLOAD] Processed file saved to session: {session['datafile']}")
        stats = get_stats(df)
        print("[UPLOAD] Stats generated. Rendering analysis.html...")
        return render_template('analysis.html', stats=stats, columns=columns, analyzed_file=filename)
    except FileNotFoundError as e:
        print(f"[Upload Error - File Not Found] {e}")
        flash('파일을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    except pd.errors.EmptyDataError as e:
        print(f"[Upload Error - Empty Data] {e}")
        flash('빈 파일이거나 유효한 데이터가 없습니다.', 'error')
        return redirect(url_for('index'))
    except pd.errors.ParserError as e:
        print(f"[Upload Error - Parser Error] {e}")
        flash('CSV 파일 형식이 올바르지 않습니다.', 'error')
        return redirect(url_for('index'))
    except MemoryError as e:
        print(f"[Upload Error - Memory Error] {e}")
        flash('파일이 너무 커서 처리할 수 없습니다.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"[Upload Error] {e}")
        flash(f'파일 처리 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('index'))

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
    
    print(f"[DEBUG] 필터 파라미터 확인:")
    print(f"  - address: '{address}'")
    print(f"  - radius_km: {radius_km}")
    print(f"  - area_range: {area_range}")
    print(f"  - sort_col: {sort_col}")
    print(f"  - sort_order: {sort_order}")
    print(f"  - session datafile: {session.get('datafile', 'NOT_FOUND')}")
    print(f"  - filter_params: {filter_params}")
    
    # 페이지네이션 파라미터
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))  # 기본 20개씩

    # 전용면적 구간 세션에 저장
    session['area_range'] = area_range

    if not address:
        print(f"[ERROR] 주소가 비어있음: '{address}'")
        return render_template('map.html', error='주소를 입력해주세요.', data=[], columns=[], center_lat=None, center_lon=None, radius=radius_m)

    if 'datafile' not in session:
        print(f"[ERROR] 세션에 datafile이 없음 - 업로드된 파일이 없거나 세션 만료")
        print(f"[INFO] 자동으로 가장 최근 분석 파일 사용 시도")
        
        # 가장 최근 분석 파일 찾기
        import glob
        analysis_files = glob.glob('uploads/*_분석완료.csv')
        if analysis_files:
            latest_file = max(analysis_files, key=os.path.getmtime)
            session['datafile'] = os.path.basename(latest_file)
            print(f"[INFO] 자동 복구된 세션 파일: {session['datafile']}")
        else:
            center_lat, center_lon = get_latlon_from_address(address)
            if center_lat is None or center_lon is None:
                return render_template('map.html', error='입력하신 주소로 좌표를 찾을 수 없습니다. 주소를 더 정확히 입력해 주세요.', data=[], columns=[], center_lat=None, center_lon=None, radius=radius_m)
            return render_template('map.html', data=[], columns=[], message='검색 결과 없음 - 먼저 CSV 파일을 업로드해주세요.', center_lat=center_lat, center_lon=center_lon, radius=radius_m)

    try:
        temp_filename = session['datafile']
        # 항상 uploads 폴더에서만 찾도록 경로 고정
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(temp_filename))
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        columns = df.columns.tolist()

        print(f"[DEBUG] 주소 좌표 변환 요청: '{address}'")
        center_lat, center_lon = get_latlon_from_address(address)
        print(f"[DEBUG] 좌표 변환 결과: lat={center_lat}, lon={center_lon}")
        
        if center_lat is None or center_lon is None:
            print(f"[ERROR] 좌표 변환 실패 - 주소: '{address}'")
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
                # 금액, 보증금, 월세 등 '금액'이 포함된 모든 숫자 컬럼에 쉼표 추가
                if ('금액' in col or '보증금' in col or '월세' in col) and col in row and (isinstance(row[col], (int, float)) or (isinstance(row[col], str) and str(row[col]).replace(',', '').replace('.', '', 1).isdigit())):
                    row[col] = format_number(row[col])
                elif col == '계약년월' and col in row and row[col] is not None and row[col] != '':
                    try:
                        # 계약년월은 정수로 변환 (소수점 제거)
                        row[col] = str(int(float(row[col])))
                    except Exception:
                        pass
                elif (col == '전용면적(㎡)' or col == '전용면적(㎡)') and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):.2f}"
                    except Exception:
                        pass
                elif col == '전용평' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):.2f}"
                    except Exception:
                        pass
                elif col == '층' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = str(int(float(row[col])))  # 정수로 변환
                    except Exception:
                        pass
                elif col == '건축년도' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = str(int(float(row[col])))  # 정수로 변환
                    except Exception:
                        pass
                elif col == '전용평당' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):,.2f}"  # 쉼표와 소수점 둘째자리
                    except Exception:
                        pass
                elif col == '공급평당' and col in row and row[col] is not None and row[col] != '':
                    try:
                        row[col] = f"{float(row[col]):,.2f}"  # 쉼표와 소수점 둘째자리
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
            'center_lat': float(center_lat) if center_lat else 37.5665,  # 서울시청 좌표
            'center_lon': float(center_lon) if center_lon else 126.978,
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
    if 'datafile' not in session or 'filter_params' not in session:
        flash('다운로드할 데이터가 없거나 필터 조건이 설정되지 않았습니다.', 'error')
        return redirect(request.referrer or url_for('index'))

    temp_filename = session['datafile']
    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)

    if not os.path.exists(temp_path):
        flash('분석 데이터 파일을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))

    try:
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        
        # 세션에서 모든 필터 파라미터 가져오기
        filter_params = session.get('filter_params', {})
        address = filter_params.get('address')
        radius_km = filter_params.get('radius', 10.0)
        area_range = filter_params.get('area_range', 'all')
        build_year = filter_params.get('build_year', 'all')

        if not address:
            flash('다운로드를 위해 주소를 먼저 설정해야 합니다.', 'error')
            return redirect(request.referrer or url_for('index'))

        # --- show_filtered_results와 동일한 필터링 로직 적용 ---
        
        # 1. 주소 -> 좌표 변환
        center_lat, center_lon = get_latlon_from_address(address)
        if center_lat is None or center_lon is None:
            flash('주소의 좌표를 찾을 수 없어 다운로드할 수 없습니다.', 'error')
            return redirect(request.referrer or url_for('index'))

        # 2. 전용면적 필터링
        area_col = next((col for col in ['전용면적(㎡)', '전용면적(\u33A1)'] if col in df.columns), None)
        if area_col:
            df[area_col] = pd.to_numeric(df[area_col], errors='coerce')
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

        # 3. 건축년도 필터링
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
        
        # 4. 거리 필터링
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        from geopy.distance import geodesic
        if not df.empty:
            df['중심점과의거리(km)'] = df.apply(
                lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).kilometers,
                axis=1
            )
            df = df[df['중심점과의거리(km)'] <= radius_km].copy()
        else:
            df['중심점과의거리(km)'] = np.nan

        # 다운로드 파일 생성
        output = io.BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        download_name = f'filtered_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        return send_file(output, as_attachment=True, download_name=download_name, mimetype='text/csv')

    except Exception as e:
        print(f"[Download Error] {e}")
        flash(f'다운로드 중 오류가 발생했습니다: {e}', 'error')
        return redirect(request.referrer or url_for('index'))

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
    # 8001번 포트에서 실행
    app.run(debug=True, port=8004, host='0.0.0.0')