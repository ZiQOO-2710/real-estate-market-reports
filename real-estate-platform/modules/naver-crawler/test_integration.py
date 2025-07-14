#!/usr/bin/env python3
"""
부동산 플랫폼 통합 테스트 스크립트
크롤링 → 데이터베이스 저장 → 검증
"""

import os
import sys
import asyncio
from datetime import datetime

# 프로젝트 모듈 임포트 경로 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.naver_complex_crawler import crawl_single_complex
from supabase_data_processor import SupabaseDataProcessor

async def test_end_to_end_pipeline():
    """크롤링부터 DB 저장까지 전체 파이프라인 테스트"""
    print("🚀 부동산 플랫폼 통합 테스트 시작\n")
    
    # 1. 크롤링 테스트
    print("1️⃣ 네이버 부동산 크롤링 테스트...")
    test_url = "https://new.land.naver.com/complexes/2592?ms=37.36286,127.115578,17&a=APT:ABYG:JGC:PRE&e=RETAIL"
    
    try:
        result = await crawl_single_complex(test_url, "정든한진6차_테스트", headless=True)
        
        if result['success']:
            print(f"   ✅ 크롤링 성공!")
            print(f"   📊 단지명: {result['complex_name']}")
            print(f"   🏠 매물: {result['data_summary']['listings_count']}개")
            print(f"   💰 거래: {result['data_summary']['transactions_count']}개")
            print(f"   📋 가격: {result['data_summary']['prices_count']}개")
            
            json_file = result['files']['json_file']
            print(f"   📄 데이터 파일: {json_file}")
            
        else:
            print(f"   ❌ 크롤링 실패: {result['error']}")
            return False
            
    except Exception as e:
        print(f"   ❌ 크롤링 오류: {e}")
        return False
    
    # 2. Supabase 연결 테스트
    print(f"\n2️⃣ Supabase 데이터베이스 연결 테스트...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY') 
    
    if not supabase_url or not supabase_key:
        print("   ⚠️ Supabase 환경변수가 설정되지 않음")
        print("   💡 다음 명령어로 설정하세요:")
        print("      export SUPABASE_URL='your_url'")
        print("      export SUPABASE_KEY='your_key'")
        print("   🔄 크롤링 데이터만 검증하고 종료")
        return test_data_validation(json_file)
    
    try:
        processor = SupabaseDataProcessor(supabase_url, supabase_key)
        print("   ✅ Supabase 클라이언트 생성 성공")
        
        # 3. 데이터 삽입 테스트
        print(f"\n3️⃣ 데이터베이스 삽입 테스트...")
        success = await processor.insert_complex_data(json_file)
        
        if success:
            print("   ✅ 데이터 삽입 성공!")
            
            # 4. 삽입된 데이터 검증
            print(f"\n4️⃣ 삽입 데이터 검증...")
            verification_success = verify_inserted_data(processor, result['complex_id'])
            
            if verification_success:
                print("   ✅ 데이터 검증 완료!")
                print(f"\n🎉 전체 파이프라인 테스트 성공!")
                return True
            else:
                print("   ❌ 데이터 검증 실패")
                return False
                
        else:
            print("   ❌ 데이터 삽입 실패")
            return False
            
    except Exception as e:
        print(f"   ❌ Supabase 연결 오류: {e}")
        print("   💡 URL과 키를 확인하고 테이블이 생성되었는지 확인하세요")
        return False

def test_data_validation(json_file):
    """JSON 데이터 검증만 수행"""
    print(f"\n📊 크롤링 데이터 검증...")
    
    try:
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 기본 구조 확인
        required_sections = ['complex_basic_info', 'current_listings', 'transaction_history']
        for section in required_sections:
            if section in data:
                print(f"   ✅ {section}: 존재")
            else:
                print(f"   ❌ {section}: 누락")
                return False
                
        # 데이터 품질 확인
        listings = data.get('current_listings', [])
        transactions = data.get('transaction_history', [])
        
        price_count = 0
        for listing in listings:
            if listing.get('price'):
                price_count += 1
                
        print(f"   📊 매물 {len(listings)}개 중 가격정보 {price_count}개")
        print(f"   📊 거래기록 {len(transactions)}개")
        
        if price_count > 0:
            print(f"   ✅ 크롤링 데이터 품질 양호")
            return True
        else:
            print(f"   ⚠️ 가격 정보가 부족합니다")
            return False
            
    except Exception as e:
        print(f"   ❌ 데이터 검증 오류: {e}")
        return False

def verify_inserted_data(processor, complex_id):
    """삽입된 데이터 검증"""
    try:
        # 기본 정보 확인
        result = processor.supabase.table('apartment_complexes').select('*').eq('complex_id', complex_id).execute()
        
        if len(result.data) > 0:
            complex_data = result.data[0]
            print(f"   ✅ 단지 정보: {complex_data['complex_name']}")
            
            # 매물 정보 확인
            listings_result = processor.supabase.table('current_listings').select('*').eq('complex_id', complex_id).execute()
            print(f"   ✅ 매물 정보: {len(listings_result.data)}개")
            
            # 가격 분석 확인
            analysis_result = processor.supabase.table('price_analysis').select('*').eq('complex_id', complex_id).execute()
            if len(analysis_result.data) > 0:
                analysis = analysis_result.data[0]
                print(f"   ✅ 가격 분석: {analysis['price_min']:,}~{analysis['price_max']:,}만원")
                
            return True
        else:
            print(f"   ❌ 단지 데이터를 찾을 수 없음")
            return False
            
    except Exception as e:
        print(f"   ❌ 검증 오류: {e}")
        return False

def print_project_status():
    """프로젝트 상태 출력"""
    print("📁 프로젝트 구조 확인:")
    
    base_path = "/home/ksj27/projects/real-estate-platform"
    
    key_files = [
        "modules/naver-crawler/core/naver_complex_crawler.py",
        "modules/naver-crawler/supabase_data_processor.py", 
        "database/schemas/supabase_schema.sql",
        "docs/SUPABASE_GUIDE.md"
    ]
    
    for file_path in key_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")

async def main():
    """메인 테스트 실행"""
    print("🏢 Real Estate Platform - 통합 테스트")
    print("=" * 50)
    
    # 프로젝트 구조 확인
    print_project_status()
    
    print(f"\n⏰ 테스트 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 통합 테스트 실행
    success = await test_end_to_end_pipeline()
    
    print(f"\n⏰ 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success:
        print(f"\n🎯 다음 단계:")
        print(f"1. 프론트엔드에서 API 연결")
        print(f"2. 실시간 데이터 업데이트 구현") 
        print(f"3. 분석 대시보드 구축")
        print(f"4. 사용자 알림 시스템 개발")
    else:
        print(f"\n🔧 문제 해결이 필요합니다.")
        print(f"로그를 확인하고 설정을 점검해주세요.")

if __name__ == "__main__":
    asyncio.run(main())