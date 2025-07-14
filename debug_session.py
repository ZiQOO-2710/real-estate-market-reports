#!/usr/bin/env python3
"""
세션 및 필터링 문제 직접 디버깅
"""

import pandas as pd
import glob
import os
from map_utils import get_latlon_from_address
from geopy.distance import geodesic
from flask import Flask, session, request
import json

def debug_session_issue():
    """세션 문제 디버깅"""
    print("🔍 세션 문제 디버깅 시작")
    
    # 1. 업로드된 파일 확인
    print("\n1. 업로드된 파일 확인:")
    upload_files = glob.glob('uploads/*.csv')
    analysis_files = glob.glob('uploads/*_분석완료.csv')
    
    print(f"  - 전체 업로드 파일: {len(upload_files)}개")
    print(f"  - 분석 완료 파일: {len(analysis_files)}개")
    
    for f in analysis_files:
        mtime = os.path.getmtime(f)
        size = os.path.getsize(f)
        print(f"    • {f} (수정시간: {mtime}, 크기: {size} bytes)")
    
    if not analysis_files:
        print("  ❌ 분석 완료 파일이 없습니다!")
        return False
    
    # 2. 가장 최근 파일 테스트
    latest_file = max(analysis_files, key=os.path.getmtime)
    print(f"\n2. 가장 최근 파일: {latest_file}")
    
    try:
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        print(f"  ✅ 파일 읽기 성공: {len(df)}행")
        print(f"  컬럼: {list(df.columns)}")
        
        # 좌표 데이터 확인
        coord_count = len(df.dropna(subset=['위도', '경도']))
        print(f"  좌표 데이터: {coord_count}행")
        
    except Exception as e:
        print(f"  ❌ 파일 읽기 실패: {e}")
        return False
    
    # 3. 주소 좌표 변환 테스트
    print("\n3. 주소 좌표 변환 테스트:")
    address = "서초동 1326-17"
    center_lat, center_lon = get_latlon_from_address(address)
    print(f"  주소: {address}")
    print(f"  결과: lat={center_lat}, lon={center_lon}")
    
    if center_lat is None or center_lon is None:
        print("  ❌ 좌표 변환 실패!")
        return False
    
    # 4. 필터링 테스트
    print("\n4. 필터링 테스트:")
    radius_km = 5
    
    # 좌표 데이터 전처리
    df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
    df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
    df = df.dropna(subset=['위도', '경도'])
    
    # 거리 계산
    df['중심점과의거리'] = df.apply(
        lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).meters / 1000, 
        axis=1
    )
    
    # 반경 필터링
    filtered_df = df[df['중심점과의거리'] <= radius_km]
    
    print(f"  전체 데이터: {len(df)}행")
    print(f"  반경 {radius_km}km 내: {len(filtered_df)}행")
    
    if len(filtered_df) == 0:
        print("  ❌ 필터링 결과가 없습니다!")
        # 가장 가까운 데이터 찾기
        closest_idx = df['중심점과의거리'].idxmin()
        closest_dist = df.loc[closest_idx, '중심점과의거리']
        closest_name = df.loc[closest_idx, '단지명']
        print(f"  가장 가까운 데이터: {closest_name} ({closest_dist:.2f}km)")
        return False
    
    # 5. 템플릿 데이터 형태 확인
    print("\n5. 템플릿 데이터 형태:")
    data_records = filtered_df.to_dict('records')
    
    template_data = {
        'center_lat': center_lat,
        'center_lon': center_lon,
        'data': data_records,
        'count': len(data_records)
    }
    
    print(f"  center_lat: {template_data['center_lat']} (type: {type(template_data['center_lat'])})")
    print(f"  center_lon: {template_data['center_lon']} (type: {type(template_data['center_lon'])})")
    print(f"  data length: {len(template_data['data'])}")
    
    # 샘플 데이터
    if template_data['data']:
        sample = template_data['data'][0]
        print(f"  샘플 데이터: {sample.get('단지명', 'N/A')} (위도: {sample.get('위도')}, 경도: {sample.get('경도')})")
    
    return True

def create_mock_session():
    """모의 세션 생성"""
    app = Flask(__name__)
    app.secret_key = 'test-key'
    
    with app.test_request_context():
        # 최신 분석 파일 설정
        analysis_files = glob.glob('uploads/*_분석완료.csv')
        if analysis_files:
            latest_file = max(analysis_files, key=os.path.getmtime)
            session['datafile'] = os.path.basename(latest_file)
            
            # 필터 파라미터 설정
            session['filter_params'] = {
                'address': '서초동 1326-17',
                'radius': 5,
                'area_range': 'all',
                'sort_col': None,
                'sort_order': 'desc'
            }
            
            print(f"📄 모의 세션 생성 완료:")
            print(f"  datafile: {session['datafile']}")
            print(f"  filter_params: {session['filter_params']}")
            
            return True
        else:
            print("❌ 분석 파일이 없어 모의 세션 생성 실패")
            return False

if __name__ == "__main__":
    print("🚀 세션 및 필터링 문제 디버깅")
    print("=" * 50)
    
    success = debug_session_issue()
    
    if success:
        print("\n✅ 모든 테스트 통과!")
        print("문제는 Flask 세션 관리에 있을 수 있습니다.")
        
        # 모의 세션 생성
        create_mock_session()
        
        print("\n💡 해결책:")
        print("1. 브라우저 캐시/쿠키 삭제")
        print("2. 새 브라우저 탭에서 CSV 파일 재업로드")
        print("3. 또는 http://localhost:8005/quick_filter?address=서초동 1326-17&radius=5 사용")
        
    else:
        print("\n❌ 테스트 실패!")
        print("데이터나 좌표 변환에 문제가 있습니다.")