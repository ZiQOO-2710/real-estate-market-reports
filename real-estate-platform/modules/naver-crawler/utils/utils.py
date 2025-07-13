"""
유틸리티 함수 모듈
"""

import random
import time
from pathlib import Path
from typing import Optional, Dict, Any
import hashlib
import json
from datetime import datetime
from loguru import logger

from config.settings import DATA_CONFIG, USER_AGENTS


def setup_directories() -> None:
    """필요한 디렉토리 생성"""
    directories = [
        DATA_CONFIG["output_dir"],
        DATA_CONFIG["screenshot_dir"],
        DATA_CONFIG["log_dir"]
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.debug(f"디렉토리 생성/확인: {directory}")


def get_random_user_agent() -> str:
    """랜덤 User-Agent 반환"""
    return random.choice(USER_AGENTS)


def generate_hash(data: str) -> str:
    """데이터 해시 생성"""
    return hashlib.md5(data.encode('utf-8')).hexdigest()


def safe_filename(filename: str) -> str:
    """안전한 파일명 생성"""
    # 사용할 수 없는 문자 제거
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # 길이 제한
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def retry_async(max_attempts: int = 3, delay: float = 1.0):
    """비동기 함수 재시도 데코레이터"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"함수 {func.__name__} 실행 실패 (시도 {attempt + 1}/{max_attempts}): {e}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
                    
            logger.error(f"함수 {func.__name__} 최대 재시도 횟수 초과")
            raise last_exception
            
        return wrapper
    return decorator


def validate_region_code(region_code: str) -> bool:
    """지역 코드 유효성 검사"""
    # 지역 코드는 10자리 숫자
    if not region_code.isdigit() or len(region_code) != 10:
        return False
    return True


def format_price(price: str, trade_type: str = "매매") -> str:
    """가격 포맷팅"""
    try:
        if not price or price == "":
            return ""
            
        # 숫자만 추출
        price_num = int(price.replace(',', '').replace('/', ''))
        
        if trade_type == "매매":
            if price_num >= 10000:
                eok = price_num // 10000
                man = price_num % 10000
                if man == 0:
                    return f"{eok}억"
                else:
                    return f"{eok}억 {man:,}만"
            else:
                return f"{price_num:,}만"
        else:
            return f"{price_num:,}만"
            
    except Exception as e:
        logger.error(f"가격 포맷팅 오류: {e}")
        return price


def calculate_area_pyeong(area_m2: float) -> float:
    """제곱미터를 평으로 변환"""
    return round(area_m2 / 3.3058, 2)


def calculate_price_per_pyeong(price: int, area_pyeong: float) -> int:
    """평당 가격 계산"""
    try:
        return round(price / area_pyeong)
    except (ZeroDivisionError, TypeError):
        return 0


def get_timestamp() -> str:
    """현재 시각 타임스탬프 반환"""
    return datetime.now().strftime('%Y%m%d_%H%M%S')


def save_debug_info(data: Dict[str, Any], filename: str = None) -> str:
    """디버그 정보 저장"""
    try:
        if not filename:
            filename = f"debug_{get_timestamp()}.json"
            
        debug_path = DATA_CONFIG["log_dir"] / filename
        
        with open(debug_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
        logger.debug(f"디버그 정보 저장: {debug_path}")
        return str(debug_path)
        
    except Exception as e:
        logger.error(f"디버그 정보 저장 오류: {e}")
        return ""


def load_debug_info(filename: str) -> Optional[Dict[str, Any]]:
    """디버그 정보 로드"""
    try:
        debug_path = DATA_CONFIG["log_dir"] / filename
        
        if not debug_path.exists():
            return None
            
        with open(debug_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        logger.debug(f"디버그 정보 로드: {debug_path}")
        return data
        
    except Exception as e:
        logger.error(f"디버그 정보 로드 오류: {e}")
        return None


def clean_text(text: str) -> str:
    """텍스트 정제"""
    if not text:
        return ""
        
    # 공백 정규화
    text = ' '.join(text.split())
    
    # 특수 문자 정리
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    
    return text.strip()


def is_valid_coordinate(lat: float, lon: float) -> bool:
    """좌표 유효성 검사"""
    try:
        # 한국 좌표 범위 확인
        if not (33.0 <= lat <= 39.0):
            return False
        if not (124.0 <= lon <= 132.0):
            return False
        return True
    except (TypeError, ValueError):
        return False


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 간 거리 계산 (km)"""
    try:
        import math
        
        # 위도, 경도를 라디안으로 변환
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        # 하버사인 공식
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 지구 반지름 (km)
        earth_radius = 6371
        
        distance = earth_radius * c
        return round(distance, 2)
        
    except Exception as e:
        logger.error(f"거리 계산 오류: {e}")
        return 0.0


def create_summary_stats(data: list) -> Dict[str, Any]:
    """데이터 요약 통계 생성"""
    try:
        if not data:
            return {}
            
        import pandas as pd
        
        df = pd.DataFrame(data)
        
        stats = {
            "총_건수": len(df),
            "수집_시간": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "지역별_분포": df.get('주소', pd.Series()).value_counts().to_dict() if '주소' in df.columns else {},
            "거래타입별_분포": df.get('거래타입', pd.Series()).value_counts().to_dict() if '거래타입' in df.columns else {},
        }
        
        # 가격 통계 (매매만)
        if '가격' in df.columns and '거래타입' in df.columns:
            매매_data = df[df['거래타입'] == '매매']
            if not 매매_data.empty:
                try:
                    prices = pd.to_numeric(매매_data['가격'], errors='coerce').dropna()
                    if not prices.empty:
                        stats["매매가격_통계"] = {
                            "평균": round(prices.mean()),
                            "최소": int(prices.min()),
                            "최대": int(prices.max()),
                            "중간값": round(prices.median())
                        }
                except Exception:
                    pass
        
        return stats
        
    except Exception as e:
        logger.error(f"요약 통계 생성 오류: {e}")
        return {}


# 비동기 함수용 import
try:
    import asyncio
except ImportError:
    logger.warning("asyncio를 사용할 수 없습니다")