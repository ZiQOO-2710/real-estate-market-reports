#!/usr/bin/env python3
"""
네이버 부동산 크롤링 데이터를 Supabase 데이터베이스로 변환하는 스크립트
"""

import json
import re
import os
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseDataProcessor:
    """크롤링 데이터를 Supabase DB로 처리하는 클래스"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase API 키
        """
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
    def parse_price_to_amount(self, price_text: str) -> Optional[int]:
        """가격 텍스트를 만원 단위 숫자로 변환"""
        if not price_text or price_text == "정보없음":
            return None
            
        try:
            # "14억 5,000" -> 145000 (만원)
            # "8억" -> 80000 (만원) 
            # "3천만원" -> 3000 (만원)
            
            # 억 단위 처리
            billion_match = re.search(r'(\d+)억\s*(\d+)?', price_text)
            if billion_match:
                billion = int(billion_match.group(1)) * 10000  # 억 -> 만원
                thousand = int(billion_match.group(2) or 0) * 1000 if billion_match.group(2) else 0
                return billion + thousand
                
            # 천만원 단위 처리
            thousand_match = re.search(r'(\d+)천만원?', price_text)
            if thousand_match:
                return int(thousand_match.group(1)) * 1000
                
            # 만원 단위 처리
            man_match = re.search(r'(\d+)만원?', price_text)
            if man_match:
                return int(man_match.group(1))
                
            # 숫자만 있는 경우 (만원 단위로 가정)
            number_match = re.search(r'(\d+)', price_text)
            if number_match:
                return int(number_match.group(1))
                
        except Exception as e:
            logger.warning(f"가격 파싱 오류: {price_text} -> {e}")
            
        return None
        
    def parse_area_to_sqm(self, area_text: str) -> Optional[float]:
        """면적 텍스트를 ㎡ 단위로 변환"""
        if not area_text:
            return None
            
        try:
            # "121.35㎡" -> 121.35
            sqm_match = re.search(r'(\d+\.?\d*)㎡', area_text)
            if sqm_match:
                return float(sqm_match.group(1))
                
            # "37평" -> 122.31 (평 -> ㎡ 변환: 1평 = 3.3058㎡)
            pyeong_match = re.search(r'(\d+\.?\d*)평', area_text)
            if pyeong_match:
                return float(pyeong_match.group(1)) * 3.3058
                
        except Exception as e:
            logger.warning(f"면적 파싱 오류: {area_text} -> {e}")
            
        return None
        
    def extract_floor_number(self, floor_text: str) -> Optional[int]:
        """층수 텍스트에서 숫자 추출"""
        if not floor_text:
            return None
            
        try:
            floor_match = re.search(r'(\d+)층', floor_text)
            if floor_match:
                return int(floor_match.group(1))
        except Exception as e:
            logger.warning(f"층수 파싱 오류: {floor_text} -> {e}")
            
        return None
        
    def process_complex_basic_info(self, data: Dict) -> Dict:
        """단지 기본 정보 처리"""
        basic_info = data.get('complex_basic_info', {})
        
        return {
            'complex_id': basic_info.get('complex_id', 'unknown'),
            'complex_name': basic_info.get('complexName', '정보없음'),
            'address': basic_info.get('address', '정보없음'),
            'completion_year': self.parse_completion_year(basic_info.get('completionYear')),
            'total_households': self.parse_int_safe(basic_info.get('totalHouseholds')),
            'source_url': basic_info.get('source_url', ''),
            'screenshot_path': data.get('detailed_analysis', {}).get('screenshot_path', '')
        }
        
    def parse_completion_year(self, year_text: str) -> Optional[int]:
        """준공년도 파싱"""
        if not year_text or year_text == "정보없음":
            return None
            
        try:
            # "2030년", "2030" 등에서 년도 추출
            year_match = re.search(r'(19|20)\d{2}', str(year_text))
            if year_match:
                year = int(year_match.group(0))
                # 합리적인 범위 체크
                if 1900 <= year <= 2050:
                    return year
        except Exception as e:
            logger.warning(f"준공년도 파싱 오류: {year_text} -> {e}")
            
        return None
        
    def parse_int_safe(self, value) -> Optional[int]:
        """안전한 정수 변환"""
        if not value:
            return None
            
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                # 문자열에서 숫자만 추출
                number_match = re.search(r'\d+', value)
                if number_match:
                    return int(number_match.group(0))
        except Exception as e:
            logger.warning(f"정수 변환 오류: {value} -> {e}")
            
        return None
        
    def process_current_listings(self, data: Dict, complex_id: str) -> List[Dict]:
        """현재 매물 정보 처리"""
        listings = data.get('current_listings', [])
        processed_listings = []
        
        for listing in listings:
            try:
                processed_listing = {
                    'complex_id': complex_id,
                    'listing_index': listing.get('index', 0),
                    'deal_type': listing.get('deal_type', '정보없음'),
                    'price_display': listing.get('price', ''),
                    'price_amount': self.parse_price_to_amount(listing.get('price', '')),
                    'monthly_rent': self.parse_price_to_amount(listing.get('monthly_rent', '')),
                    'area_sqm': self.parse_area_to_sqm(listing.get('area', '')),
                    'floor_info': listing.get('floor', ''),
                    'description': listing.get('text', '')[:500],  # 길이 제한
                    'raw_text': listing.get('raw_text', '')[:1000]  # 길이 제한
                }
                processed_listings.append(processed_listing)
                
            except Exception as e:
                logger.error(f"매물 처리 오류: {e}")
                continue
                
        return processed_listings
        
    def process_transaction_history(self, data: Dict, complex_id: str) -> List[Dict]:
        """실거래가 정보 처리"""
        transactions = data.get('transaction_history', [])
        processed_transactions = []
        
        for transaction in transactions:
            try:
                processed_transaction = {
                    'complex_id': complex_id,
                    'pattern_type': transaction.get('pattern_type', 0),
                    'match_text': transaction.get('match_text', '')[:200],
                    'context_text': transaction.get('context', '')[:500],
                    'price_amount': self.extract_price_from_transaction(transaction.get('match_text', '')),
                    'area_sqm': self.extract_area_from_transaction(transaction.get('match_text', '')),
                    'transaction_type': self.extract_deal_type_from_transaction(transaction.get('match_text', ''))
                }
                processed_transactions.append(processed_transaction)
                
            except Exception as e:
                logger.error(f"거래내역 처리 오류: {e}")
                continue
                
        return processed_transactions
        
    def extract_price_from_transaction(self, text: str) -> Optional[int]:
        """거래내역 텍스트에서 가격 추출"""
        return self.parse_price_to_amount(text)
        
    def extract_area_from_transaction(self, text: str) -> Optional[float]:
        """거래내역 텍스트에서 면적 추출"""
        return self.parse_area_to_sqm(text)
        
    def extract_deal_type_from_transaction(self, text: str) -> str:
        """거래내역 텍스트에서 거래유형 추출"""
        if '매매' in text:
            return '매매'
        elif '전세' in text:
            return '전세'
        elif '월세' in text:
            return '월세'
        return '기타'
        
    def process_detailed_prices(self, data: Dict, complex_id: str) -> List[Dict]:
        """상세 가격 정보 처리"""
        detailed_analysis = data.get('detailed_analysis', {})
        all_prices = detailed_analysis.get('all_prices', [])
        processed_prices = []
        
        for price_text in all_prices:
            try:
                processed_price = {
                    'complex_id': complex_id,
                    'price_text': price_text,
                    'price_amount': self.parse_price_to_amount(price_text),
                    'price_type': self.extract_deal_type_from_transaction(price_text),
                    'source_section': '상세분석'
                }
                processed_prices.append(processed_price)
                
            except Exception as e:
                logger.error(f"상세가격 처리 오류: {e}")
                continue
                
        return processed_prices
        
    def process_complex_areas(self, data: Dict, complex_id: str) -> List[Dict]:
        """단지 면적 정보 처리"""
        basic_info = data.get('complex_basic_info', {})
        areas = basic_info.get('areas', [])
        processed_areas = []
        
        seen_areas = set()  # 중복 제거용
        
        for area_text in areas:
            try:
                area_sqm = self.parse_area_to_sqm(area_text)
                if area_sqm and area_sqm not in seen_areas:
                    processed_area = {
                        'complex_id': complex_id,
                        'area_sqm': area_sqm,
                        'area_pyeong': round(area_sqm / 3.3058, 2)  # ㎡ -> 평 변환
                    }
                    processed_areas.append(processed_area)
                    seen_areas.add(area_sqm)
                    
            except Exception as e:
                logger.error(f"면적 처리 오류: {e}")
                continue
                
        return processed_areas
        
    def process_price_analysis(self, data: Dict, complex_id: str) -> Dict:
        """가격 분석 데이터 처리"""
        price_analysis = data.get('price_analysis', {})
        
        return {
            'complex_id': complex_id,
            'analysis_date': datetime.now().date(),
            'total_listings': len(data.get('current_listings', [])),
            'total_transactions': len(data.get('transaction_history', [])),
            'price_min': price_analysis.get('price_range', {}).get('min', 0),
            'price_max': price_analysis.get('price_range', {}).get('max', 0),
            'price_avg': int(price_analysis.get('avg_price', 0)),
            'deal_type_summary': price_analysis.get('deal_type_count', {}),
            'areas_count': len(data.get('complex_basic_info', {}).get('areas', [])),
            'floors_count': len(data.get('detailed_analysis', {}).get('floors', []))
        }
        
    def process_crawl_metadata(self, data: Dict, complex_id: str) -> Dict:
        """크롤링 메타데이터 처리"""
        metadata = data.get('crawl_metadata', {})
        
        return {
            'complex_id': complex_id,
            'crawl_method': metadata.get('method', 'unknown'),
            'crawl_timestamp': datetime.fromisoformat(metadata.get('crawled_at', datetime.now().isoformat())),
            'total_prices_extracted': metadata.get('total_prices', 0),
            'success': True,
            'error_message': None,
            'raw_data': data  # 전체 JSON 데이터 저장
        }
        
    async def insert_complex_data(self, json_file_path: str) -> bool:
        """크롤링 JSON 파일을 Supabase에 삽입"""
        try:
            # JSON 파일 읽기
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            complex_id = data.get('complex_basic_info', {}).get('complex_id', 'unknown')
            logger.info(f"단지 {complex_id} 데이터 처리 시작...")
            
            # 1. 기본 정보 삽입
            complex_info = self.process_complex_basic_info(data)
            result = self.supabase.table('apartment_complexes').upsert(complex_info).execute()
            logger.info(f"✅ 단지 기본정보 삽입: {complex_info['complex_name']}")
            
            # 2. 면적 정보 삽입
            areas_data = self.process_complex_areas(data, complex_id)
            if areas_data:
                self.supabase.table('complex_areas').upsert(areas_data).execute()
                logger.info(f"✅ 면적 정보 {len(areas_data)}개 삽입")
                
            # 3. 현재 매물 삽입
            listings_data = self.process_current_listings(data, complex_id)
            if listings_data:
                self.supabase.table('current_listings').upsert(listings_data).execute()
                logger.info(f"✅ 매물 정보 {len(listings_data)}개 삽입")
                
            # 4. 거래내역 삽입
            transactions_data = self.process_transaction_history(data, complex_id)
            if transactions_data:
                self.supabase.table('transaction_history').upsert(transactions_data).execute()
                logger.info(f"✅ 거래내역 {len(transactions_data)}개 삽입")
                
            # 5. 상세 가격 삽입
            prices_data = self.process_detailed_prices(data, complex_id)
            if prices_data:
                self.supabase.table('detailed_prices').upsert(prices_data).execute()
                logger.info(f"✅ 상세가격 {len(prices_data)}개 삽입")
                
            # 6. 가격 분석 삽입
            analysis_data = self.process_price_analysis(data, complex_id)
            self.supabase.table('price_analysis').upsert(analysis_data).execute()
            logger.info(f"✅ 가격 분석 삽입")
            
            # 7. 메타데이터 삽입
            metadata = self.process_crawl_metadata(data, complex_id)
            self.supabase.table('crawl_metadata').upsert(metadata).execute()
            logger.info(f"✅ 메타데이터 삽입")
            
            logger.info(f"🎉 단지 {complex_id} 데이터 삽입 완료!")
            return True
            
        except Exception as e:
            logger.error(f"❌ 데이터 삽입 오류: {e}")
            return False

# 사용 예시
async def main():
    """메인 실행 함수"""
    
    # Supabase 설정 (환경변수 또는 직접 입력)
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'YOUR_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'YOUR_SUPABASE_KEY')
    
    if SUPABASE_URL == 'YOUR_SUPABASE_URL':
        print("⚠️ Supabase URL과 키를 설정해주세요!")
        print("export SUPABASE_URL='your_url'")
        print("export SUPABASE_KEY='your_key'")
        return
        
    processor = SupabaseDataProcessor(SUPABASE_URL, SUPABASE_KEY)
    
    # 크롤링 데이터 파일들 처리
    data_dir = "data/output"
    json_files = [f for f in os.listdir(data_dir) if f.endswith('_comprehensive_.json')]
    
    print(f"📁 {len(json_files)}개 JSON 파일 발견")
    
    for json_file in json_files:
        file_path = os.path.join(data_dir, json_file)
        print(f"\n🔄 처리 중: {json_file}")
        
        success = await processor.insert_complex_data(file_path)
        if success:
            print(f"✅ {json_file} 처리 완료")
        else:
            print(f"❌ {json_file} 처리 실패")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())