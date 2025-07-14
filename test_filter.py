#!/usr/bin/env python3
"""
필터링 과정 테스트 스크립트
"""

import pandas as pd
from map_utils import get_latlon_from_address
from geopy.distance import geodesic
import numpy as np

def test_filtering():
    """실제 필터링 과정 테스트"""
    
    # 서초동 데이터 로드
    df = pd.read_csv('uploads/fb9c229e64ffb426c2b555a0d4bf1365_분석완료.csv', encoding='utf-8-sig')
    print(f'📁 데이터 로드 완료: {len(df)}건')
    
    # 필터 파라미터 (실제 사용자 입력)
    address = '서초동 1326-17'
    radius_km = 5
    
    print(f'\n🔍 필터링 조건:')
    print(f'  - 주소: {address}')
    print(f'  - 반경: {radius_km}km')
    
    # 1. 주소 좌표 변환
    print(f'\n📍 1단계: 주소 좌표 변환')
    center_lat, center_lon = get_latlon_from_address(address)
    print(f'  결과: lat={center_lat}, lon={center_lon}')
    
    if center_lat is None or center_lon is None:
        print('❌ 좌표 변환 실패!')
        return None, None, None
    
    # 2. 데이터 전처리
    print(f'\n🔧 2단계: 데이터 전처리')
    columns = df.columns.tolist()
    print(f'  컬럼: {columns}')
    
    # 좌표 데이터 정리
    df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
    df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
    df = df.dropna(subset=['위도', '경도'])
    print(f'  좌표 유효 데이터: {len(df)}건')
    
    # 3. 거리 계산
    print(f'\n📏 3단계: 거리 계산')
    if not df.empty:
        df['중심점과의거리'] = df.apply(
            lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).meters / 1000, 
            axis=1
        )
        print(f'  거리 계산 완료')
        
        # 거리 통계
        min_dist = df['중심점과의거리'].min()
        max_dist = df['중심점과의거리'].max()
        avg_dist = df['중심점과의거리'].mean()
        print(f'  거리 통계: 최소={min_dist:.2f}km, 최대={max_dist:.2f}km, 평균={avg_dist:.2f}km')
    else:
        print('❌ 유효한 데이터가 없습니다!')
        return None, None, None
    
    # 4. 반경 필터링
    print(f'\n🎯 4단계: 반경 필터링')
    filtered_df = df[df['중심점과의거리'] <= radius_km].copy()
    print(f'  반경 {radius_km}km 내 데이터: {len(filtered_df)}건')
    
    # 5. 결과 데이터 준비
    print(f'\n📊 5단계: 결과 데이터 준비')
    if len(filtered_df) > 0:
        # 결과를 딕셔너리 리스트로 변환 (템플릿에서 사용할 형태)
        data = filtered_df.to_dict('records')
        print(f'  결과 데이터: {len(data)}건')
        
        # 샘플 데이터 출력
        print(f'\n📋 샘플 데이터:')
        for i, item in enumerate(data[:3]):
            print(f'  {i+1}. {item.get("단지명", "N/A")} - {item.get("중심점과의거리", 0):.2f}km')
            
        return data, center_lat, center_lon
    else:
        print('❌ 필터링 결과가 없습니다!')
        
        # 가장 가까운 데이터 찾기
        closest_idx = df['중심점과의거리'].idxmin()
        closest = df.loc[closest_idx]
        print(f'  가장 가까운 데이터: {closest["단지명"]} ({closest["중심점과의거리"]:.2f}km)')
        
        return [], center_lat, center_lon

def test_template_data():
    """템플릿에 전달될 데이터 형태 테스트"""
    data, center_lat, center_lon = test_filtering()
    
    if data is not None:
        print(f'\n🌐 템플릿 데이터 형태:')
        print(f'  center_lat: {center_lat} (type: {type(center_lat)})')
        print(f'  center_lon: {center_lon} (type: {type(center_lon)})')
        print(f'  data length: {len(data)}')
        
        if data:
            sample = data[0]
            print(f'  샘플 아이템 키: {list(sample.keys())}')
            print(f'  위도: {sample.get("위도")} (type: {type(sample.get("위도"))})')
            print(f'  경도: {sample.get("경도")} (type: {type(sample.get("경도"))})')
        
        # JavaScript 코드 시뮬레이션
        print(f'\n💻 JavaScript 변수 시뮬레이션:')
        print(f'  centerLat = {center_lat if center_lat is not None else 37.5665};')
        print(f'  centerLon = {center_lon if center_lon is not None else 126.978};')
        
        if data:
            print(f'  aptList = [')
            for i, item in enumerate(data[:3]):
                lat = item.get('위도', 0)
                lon = item.get('경도', 0)
                name = item.get('단지명', '')
                dist = item.get('중심점과의거리', 0) * 1000 if item.get('중심점과의거리') else 0
                print(f'    {{ name: "{name}", lat: {lat}, lon: {lon}, distance: {dist:.0f} }},')
            print(f'  ];')

if __name__ == "__main__":
    test_template_data()