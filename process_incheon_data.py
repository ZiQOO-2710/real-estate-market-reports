#!/usr/bin/env python3
"""
인천 중구 데이터 처리 및 테스트
"""
import pandas as pd
from data_processing import process_uploaded_csv
from map_utils import get_latlon_from_address, clear_cache
from app import create_app, supabase
import os

def process_incheon_data():
    """인천 중구 데이터 처리"""
    print("=== 인천 중구 데이터 처리 ===")
    
    # 1. 인천 데이터 처리
    incheon_file = "/home/ksj27/projects/uploads/20250704123432.csv"
    
    try:
        # 캐시 클리어
        clear_cache()
        
        # 데이터 처리
        print(f"[INFO] 인천 데이터 처리 시작: {incheon_file}")
        temp_path, columns = process_uploaded_csv(incheon_file)
        print(f"[INFO] 처리 완료: {temp_path}")
        
        # 처리된 데이터 로드
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        print(f"[INFO] 로드된 데이터: {len(df)}행")
        print(f"[INFO] 컬럼: {df.columns.tolist()}")
        
        # 첫 몇 행 확인
        print("\n[INFO] 데이터 샘플:")
        print(df[['시군구', '단지명', '도로명', '거래금액']].head().to_string())
        
        # 2. Supabase 매칭 시뮬레이션
        print("\n=== Supabase 매칭 시뮬레이션 ===")
        
        # 위도/경도 컬럼 추가
        df['위도'] = None
        df['경도'] = None
        
        # 샘플 데이터로 매칭 테스트
        sample_data = df.head(10)  # 처음 10개만 테스트
        
        for idx, row in sample_data.iterrows():
            print(f"\n[TEST] 매칭 테스트 {idx+1}/10:")
            print(f"  단지명: {row['단지명']}")
            print(f"  도로명: {row['도로명']}")
            print(f"  시군구: {row['시군구']}")
            
            # 주소 조합해서 좌표 변환 시도
            full_address = f"{row['시군구']} {row['도로명']}"
            lat, lon = get_latlon_from_address(full_address)
            
            if lat is not None and lon is not None:
                df.at[idx, '위도'] = lat
                df.at[idx, '경도'] = lon
                print(f"  ✓ 좌표 변환 성공: {lat}, {lon}")
            else:
                # 도로명이 없으면 시군구만으로 시도
                address_only = row['시군구']
                lat, lon = get_latlon_from_address(address_only)
                if lat is not None and lon is not None:
                    df.at[idx, '위도'] = lat
                    df.at[idx, '경도'] = lon
                    print(f"  ✓ 시군구 좌표 변환 성공: {lat}, {lon}")
                else:
                    print(f"  ✗ 좌표 변환 실패")
        
        # 3. 매칭 결과 저장
        output_file = "/home/ksj27/projects/uploads/incheon_with_coords.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n[INFO] 좌표 매칭 결과 저장: {output_file}")
        
        # 4. 매칭 통계
        coord_count = df[['위도', '경도']].notna().all(axis=1).sum()
        print(f"[INFO] 좌표 매칭 성공: {coord_count}/{len(df)} ({coord_count/len(df)*100:.1f}%)")
        
        return output_file
        
    except Exception as e:
        print(f"[ERROR] 인천 데이터 처리 실패: {e}")
        return None

def test_incheon_filtering(data_file):
    """인천 데이터 필터링 테스트"""
    print("\n=== 인천 데이터 필터링 테스트 ===")
    
    if not data_file or not os.path.exists(data_file):
        print("[ERROR] 데이터 파일이 없습니다.")
        return
    
    df = pd.read_csv(data_file, encoding='utf-8-sig')
    print(f"[INFO] 로드된 데이터: {len(df)}행")
    
    # 좌표가 있는 데이터만 필터링
    valid_coords = df.dropna(subset=['위도', '경도'])
    print(f"[INFO] 좌표 있는 데이터: {len(valid_coords)}행")
    
    if len(valid_coords) == 0:
        print("[ERROR] 좌표 데이터가 없습니다.")
        return
    
    # 인천 중구 중심으로 테스트
    center_address = "인천광역시 중구"
    center_lat, center_lon = get_latlon_from_address(center_address)
    
    if center_lat is None or center_lon is None:
        print(f"[ERROR] 중심 좌표 변환 실패: {center_address}")
        return
    
    print(f"[INFO] 중심 좌표: {center_lat}, {center_lon}")
    
    # 반경별 테스트
    radius_tests = [5, 10, 15, 20]
    
    for radius in radius_tests:
        print(f"\n--- {radius}km 반경 테스트 ---")
        
        # 하버사인 공식으로 거리 계산
        def haversine_distance(lat1, lon1, lat2, lon2):
            import math
            R = 6371  # 지구 반지름 (km)
            
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            return R * c
        
        # 거리 계산
        distances = []
        for _, row in valid_coords.iterrows():
            dist = haversine_distance(center_lat, center_lon, row['위도'], row['경도'])
            distances.append(dist)
        
        valid_coords_copy = valid_coords.copy()
        valid_coords_copy['거리'] = distances
        
        # 반경 내 데이터
        filtered_data = valid_coords_copy[valid_coords_copy['거리'] <= radius]
        
        print(f"  반경 내 데이터: {len(filtered_data)}건")
        
        if len(filtered_data) > 0:
            print(f"  평균 거래가: {filtered_data['거래금액'].mean():.0f}만원")
            print(f"  평균 전용면적: {filtered_data['전용면적(㎡)'].mean():.1f}㎡")
            
            # 주요 단지
            top_complexes = filtered_data.groupby('단지명').size().sort_values(ascending=False).head(3)
            print(f"  주요 단지:")
            for complex_name, count in top_complexes.items():
                print(f"    - {complex_name}: {count}건")

if __name__ == "__main__":
    # 인천 데이터 처리
    processed_file = process_incheon_data()
    
    # 필터링 테스트
    if processed_file:
        test_incheon_filtering(processed_file)