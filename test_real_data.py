#!/usr/bin/env python3
"""
실제 데이터로 시스템 테스트
"""
import pandas as pd
from data_processing import process_uploaded_csv
from map_utils import get_latlon_from_address

def test_data_processing():
    """데이터 처리 테스트"""
    print("=== 실제 데이터 처리 테스트 ===")
    
    # 실제 데이터 파일 경로
    test_file = "/home/ksj27/projects/uploads/20250704123432.csv"
    
    try:
        # 데이터 처리
        print(f"[TEST] 파일 처리 시작: {test_file}")
        temp_path, columns = process_uploaded_csv(test_file)
        print(f"[TEST] 처리 완료: {temp_path}")
        print(f"[TEST] 컬럼: {columns}")
        
        # 처리된 데이터 확인
        df = pd.read_csv(temp_path, encoding='utf-8-sig')
        print(f"[TEST] 처리된 데이터 행 수: {len(df)}")
        print(f"[TEST] 처리된 컬럼: {df.columns.tolist()}")
        
        # 샘플 데이터 출력
        print("\n[TEST] 샘플 데이터 (상위 3개):")
        print(df.head(3).to_string())
        
        return True
        
    except Exception as e:
        print(f"[TEST ERROR] 데이터 처리 실패: {e}")
        return False

def test_address_conversion():
    """주소 변환 테스트"""
    print("\n=== 주소 변환 테스트 ===")
    
    # 테스트할 주소들 (실제 데이터에서 추출)
    test_addresses = [
        "인천광역시 중구 중산동",
        "인천 중구 운서동", 
        "인천광역시 중구 답동",
        "인천광역시 중구"
    ]
    
    success_count = 0
    for address in test_addresses:
        print(f"\n[TEST] 주소 변환 테스트: {address}")
        lat, lon = get_latlon_from_address(address)
        if lat is not None and lon is not None:
            print(f"[TEST] 성공: {lat}, {lon}")
            success_count += 1
        else:
            print(f"[TEST] 실패: 좌표를 찾을 수 없음")
    
    print(f"\n[TEST] 주소 변환 성공률: {success_count}/{len(test_addresses)} ({success_count/len(test_addresses)*100:.1f}%)")
    return success_count > 0

def main():
    print("실제 데이터로 시스템 테스트를 시작합니다...\n")
    
    # 1. 데이터 처리 테스트
    data_test = test_data_processing()
    
    # 2. 주소 변환 테스트  
    address_test = test_address_conversion()
    
    # 결과 요약
    print("\n" + "="*50)
    print("테스트 결과 요약:")
    print(f"- 데이터 처리: {'✓ 성공' if data_test else '✗ 실패'}")
    print(f"- 주소 변환: {'✓ 성공' if address_test else '✗ 실패'}")
    
    if data_test and address_test:
        print("\n🎉 모든 테스트가 성공했습니다!")
        print("실제 데이터로 웹 애플리케이션을 테스트할 준비가 되었습니다.")
    else:
        print("\n⚠️ 일부 테스트가 실패했습니다. 로그를 확인해주세요.")

if __name__ == "__main__":
    main()