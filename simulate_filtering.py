#!/usr/bin/env python3
"""
필터링 기능 시뮬레이션 테스트
"""
import pandas as pd
import numpy as np
from map_utils import get_latlon_from_address
from data_processing import process_uploaded_csv, match_with_supabase
from app import create_app
import os

def simulate_filtering_test():
    """필터링 기능 시뮬레이션"""
    print("=== 필터링 기능 시뮬레이션 테스트 ===")
    
    # 1. 실제 데이터 로드
    processed_file = "/home/ksj27/projects/uploads/fb9c229e64ffb426c2b555a0d4bf1365_분석완료.csv"
    if not os.path.exists(processed_file):
        print(f"[INFO] 처리된 파일이 없어 새로 생성합니다.")
        temp_path, _ = process_uploaded_csv("/home/ksj27/projects/uploads/20250704123432.csv")
        processed_file = temp_path
    
    df = pd.read_csv(processed_file, encoding='utf-8-sig')
    print(f"[TEST] 로드된 데이터: {len(df)}행")
    
    # 2. 테스트 시나리오 실행
    test_scenarios = [
        {
            'name': '중산동 3km 반경',
            'address': '인천광역시 중구 중산동',
            'radius': 3.0
        },
        {
            'name': '운서동 5km 반경', 
            'address': '인천 중구 운서동',
            'radius': 5.0
        },
        {
            'name': '인천 중구 전체 10km',
            'address': '인천광역시 중구',
            'radius': 10.0
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n--- 시나리오 {i}: {scenario['name']} ---")
        
        # 주소 → 좌표 변환
        center_lat, center_lon = get_latlon_from_address(scenario['address'])
        if center_lat is None or center_lon is None:
            print(f"[ERROR] 주소 변환 실패: {scenario['address']}")
            continue
        
        print(f"[INFO] 중심 좌표: {center_lat}, {center_lon}")
        
        # 거리 계산 (하버사인 공식)
        def calculate_distance(lat1, lon1, lat2, lon2):
            """두 좌표 간 거리 계산 (km)"""
            R = 6371  # 지구 반지름 (km)
            
            lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
            c = 2 * np.arcsin(np.sqrt(a))
            return R * c
        
        # 필터링 수행
        if '위도' in df.columns and '경도' in df.columns:
            # 위도/경도가 있는 데이터만 필터링
            valid_coords = df.dropna(subset=['위도', '경도'])
            
            # 거리 계산
            distances = []
            for _, row in valid_coords.iterrows():
                dist = calculate_distance(center_lat, center_lon, row['위도'], row['경도'])
                distances.append(dist)
            
            valid_coords = valid_coords.copy()
            valid_coords['거리'] = distances
            
            # 반경 내 데이터 필터링
            filtered_data = valid_coords[valid_coords['거리'] <= scenario['radius']]
            
            print(f"[RESULT] 전체 데이터: {len(df)}건")
            print(f"[RESULT] 좌표 있는 데이터: {len(valid_coords)}건")
            print(f"[RESULT] {scenario['radius']}km 반경 내: {len(filtered_data)}건")
            
            if len(filtered_data) > 0:
                print(f"[RESULT] 평균 거래가: {filtered_data['거래금액'].mean():.0f}만원")
                print(f"[RESULT] 평균 전용면적: {filtered_data['전용면적(㎡)'].mean():.1f}㎡")
                print(f"[RESULT] 최근 거래: {filtered_data['계약년월'].max()}")
                
                # 상위 5개 단지
                top_complexes = filtered_data.groupby('단지명').size().sort_values(ascending=False).head(5)
                print(f"[RESULT] 주요 단지:")
                for complex_name, count in top_complexes.items():
                    print(f"  - {complex_name}: {count}건")
            
        else:
            print(f"[ERROR] 좌표 데이터가 없습니다. 위도/경도 컬럼을 확인해주세요.")
    
    print("\n=== 필터링 시뮬레이션 완료 ===")

if __name__ == "__main__":
    simulate_filtering_test()