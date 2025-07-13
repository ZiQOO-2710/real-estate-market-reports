"""
데이터 파싱 모듈
"""

import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import pandas as pd
from loguru import logger


class DataParser:
    """데이터 파싱 클래스"""
    
    def __init__(self):
        self.price_patterns = {
            '매매': r'(\d+(?:,\d+)*)\s*만원',
            '전세': r'전세\s*(\d+(?:,\d+)*)\s*만원',
            '월세': r'월세\s*(\d+(?:,\d+)*)/(\d+(?:,\d+)*)\s*만원'
        }
        
    def parse_price(self, price_text: str, trade_type: str) -> str:
        """가격 파싱"""
        try:
            price_text = price_text.strip()
            
            if trade_type == '매매':
                # 매매가 파싱: "2억 3,000만원" -> "23000"
                match = re.search(r'(\d+)억\s*(\d+(?:,\d+)*)?만원', price_text)
                if match:
                    eok = int(match.group(1))
                    man = int(match.group(2).replace(',', '')) if match.group(2) else 0
                    return str(eok * 10000 + man)
                    
                # 만원 단위만 있는 경우
                match = re.search(r'(\d+(?:,\d+)*)\s*만원', price_text)
                if match:
                    return match.group(1).replace(',', '')
                    
            elif trade_type == '전세':
                # 전세가 파싱
                match = re.search(r'(\d+)억\s*(\d+(?:,\d+)*)?', price_text)
                if match:
                    eok = int(match.group(1))
                    man = int(match.group(2).replace(',', '')) if match.group(2) else 0
                    return str(eok * 10000 + man)
                    
                match = re.search(r'(\d+(?:,\d+)*)', price_text)
                if match:
                    return match.group(1).replace(',', '')
                    
            elif trade_type == '월세':
                # 월세 파싱: "보증금/월세"
                match = re.search(r'(\d+(?:,\d+)*)/(\d+(?:,\d+)*)', price_text)
                if match:
                    deposit = match.group(1).replace(',', '')
                    monthly = match.group(2).replace(',', '')
                    return f"{deposit}/{monthly}"
                    
            return price_text
            
        except Exception as e:
            logger.error(f"가격 파싱 오류: {e}")
            return price_text
            
    def parse_area(self, area_text: str) -> Tuple[Optional[float], Optional[float]]:
        """면적 파싱 (전용면적, 공급면적)"""
        try:
            area_text = area_text.strip()
            
            # 전용면적 추출: "84.99㎡" or "84.99m²"
            exclusive_match = re.search(r'(\d+\.?\d*)\s*[㎡m²]', area_text)
            exclusive_area = float(exclusive_match.group(1)) if exclusive_match else None
            
            # 공급면적은 보통 전용면적보다 크므로 1.3배 정도로 추정
            supply_area = exclusive_area * 1.3 if exclusive_area else None
            
            return exclusive_area, supply_area
            
        except Exception as e:
            logger.error(f"면적 파싱 오류: {e}")
            return None, None
            
    def parse_floor(self, floor_text: str) -> Optional[int]:
        """층수 파싱"""
        try:
            floor_text = floor_text.strip()
            
            # 층수 추출: "5층" or "5/25층"
            match = re.search(r'(\d+)', floor_text)
            return int(match.group(1)) if match else None
            
        except Exception as e:
            logger.error(f"층수 파싱 오류: {e}")
            return None
            
    def parse_year(self, year_text: str) -> Optional[int]:
        """건축년도 파싱"""
        try:
            year_text = year_text.strip()
            
            # 년도 추출: "2018년" or "2018"
            match = re.search(r'(\d{4})', year_text)
            return int(match.group(1)) if match else None
            
        except Exception as e:
            logger.error(f"건축년도 파싱 오류: {e}")
            return None
            
    def clean_address(self, address: str) -> str:
        """주소 정제"""
        try:
            address = address.strip()
            
            # 불필요한 문자 제거
            address = re.sub(r'\s+', ' ', address)
            address = re.sub(r'[^\w\s-]', '', address)
            
            return address
            
        except Exception as e:
            logger.error(f"주소 정제 오류: {e}")
            return address
            
    def parse_single_item(self, item: Dict) -> Dict:
        """개별 아이템 파싱"""
        try:
            parsed_item = {}
            
            # 단지명
            parsed_item['단지명'] = item.get('단지명', '').strip()
            
            # 주소
            parsed_item['주소'] = self.clean_address(item.get('주소', ''))
            
            # 거래타입
            parsed_item['거래타입'] = item.get('거래타입', '매매')
            
            # 가격
            parsed_item['가격'] = self.parse_price(
                item.get('가격', ''), 
                parsed_item['거래타입']
            )
            
            # 면적
            exclusive_area, supply_area = self.parse_area(item.get('면적', ''))
            parsed_item['전용면적'] = exclusive_area
            parsed_item['공급면적'] = supply_area
            
            # 층수
            parsed_item['층수'] = self.parse_floor(item.get('층수', ''))
            
            # 건축년도
            parsed_item['건축년도'] = self.parse_year(item.get('건축년도', ''))
            
            # 거래일자
            parsed_item['거래일자'] = item.get('거래일자', datetime.now().strftime('%Y-%m-%d'))
            
            # 위도, 경도
            parsed_item['위도'] = item.get('위도')
            parsed_item['경도'] = item.get('경도')
            
            # 수집일시
            parsed_item['수집일시'] = item.get('수집일시', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            return parsed_item
            
        except Exception as e:
            logger.error(f"아이템 파싱 오류: {e}")
            return item
            
    def parse_data(self, data: List[Dict]) -> List[Dict]:
        """데이터 리스트 파싱"""
        try:
            logger.info(f"데이터 파싱 시작: {len(data)}개 항목")
            
            parsed_data = []
            
            for item in data:
                try:
                    parsed_item = self.parse_single_item(item)
                    parsed_data.append(parsed_item)
                    
                except Exception as e:
                    logger.error(f"아이템 파싱 실패: {e}")
                    continue
                    
            logger.info(f"데이터 파싱 완료: {len(parsed_data)}개 항목")
            return parsed_data
            
        except Exception as e:
            logger.error(f"데이터 파싱 오류: {e}")
            return data
            
    def validate_data(self, data: List[Dict]) -> List[Dict]:
        """데이터 유효성 검증"""
        try:
            validated_data = []
            
            for item in data:
                # 필수 필드 검증
                if not item.get('단지명') or not item.get('주소'):
                    logger.warning(f"필수 필드 누락: {item}")
                    continue
                    
                # 가격 유효성 검증
                if not item.get('가격') or item.get('가격') == '':
                    logger.warning(f"가격 정보 누락: {item.get('단지명')}")
                    continue
                    
                validated_data.append(item)
                
            logger.info(f"데이터 검증 완료: {len(validated_data)}개 유효한 항목")
            return validated_data
            
        except Exception as e:
            logger.error(f"데이터 검증 오류: {e}")
            return data
            
    def to_dataframe(self, data: List[Dict]) -> pd.DataFrame:
        """데이터프레임 변환"""
        try:
            df = pd.DataFrame(data)
            
            # 컬럼 순서 정렬
            columns = ['단지명', '주소', '거래타입', '가격', '전용면적', '공급면적', 
                      '층수', '건축년도', '거래일자', '위도', '경도', '수집일시']
            
            # 존재하는 컬럼만 선택
            available_columns = [col for col in columns if col in df.columns]
            df = df[available_columns]
            
            logger.info(f"데이터프레임 변환 완료: {len(df)}행 x {len(df.columns)}열")
            return df
            
        except Exception as e:
            logger.error(f"데이터프레임 변환 오류: {e}")
            return pd.DataFrame(data)