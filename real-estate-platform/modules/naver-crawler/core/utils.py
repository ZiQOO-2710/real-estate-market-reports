"""
유틸리티 함수들
"""

import subprocess
import asyncio
import aiohttp
from pathlib import Path
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

async def check_warp_status() -> Tuple[bool, str]:
    """
    WARP 연결 상태 확인
    
    Returns:
        Tuple[bool, str]: (연결 상태, IP 주소)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://1.1.1.1/cdn-cgi/trace', timeout=10) as response:
                if response.status == 200:
                    text = await response.text()
                    lines = text.strip().split('\n')
                    
                    warp_status = False
                    ip_address = 'unknown'
                    
                    for line in lines:
                        if line.startswith('warp='):
                            warp_status = line.split('=')[1] == 'on'
                        elif line.startswith('ip='):
                            ip_address = line.split('=')[1]
                    
                    return warp_status, ip_address
    except Exception as e:
        logger.error(f"WARP 상태 확인 실패: {e}")
        return False, 'unknown'
    
    return False, 'unknown'

def setup_warp() -> bool:
    """
    WARP CLI 설정 (이미 설치되어 있다고 가정)
    
    Returns:
        bool: 설정 성공 여부
    """
    try:
        # WARP CLI 상태 확인
        result = subprocess.run(['warp-cli', 'status'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            if 'Connected' in result.stdout:
                logger.info("WARP가 이미 연결되어 있습니다.")
                return True
            else:
                # 연결 시도
                logger.info("WARP 연결 중...")
                connect_result = subprocess.run(['warp-cli', 'connect'],
                                              capture_output=True, text=True, timeout=30)
                
                if connect_result.returncode == 0:
                    logger.info("WARP 연결 성공")
                    return True
                else:
                    logger.error(f"WARP 연결 실패: {connect_result.stderr}")
                    return False
        else:
            logger.error("WARP CLI를 찾을 수 없습니다. 설치가 필요합니다.")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("WARP 명령 타임아웃")
        return False
    except FileNotFoundError:
        logger.error("WARP CLI가 설치되어 있지 않습니다.")
        return False
    except Exception as e:
        logger.error(f"WARP 설정 중 오류: {e}")
        return False

def get_region_code(city: str, district: str) -> Optional[str]:
    """
    도시와 구/군으로부터 지역 코드 조회
    
    Args:
        city: 도시명 (예: "서울", "부산")
        district: 구/군명 (예: "강남구", "해운대구")
        
    Returns:
        Optional[str]: 지역 코드 또는 None
    """
    from .types import REGION_CODES
    
    if city in REGION_CODES and district in REGION_CODES[city]:
        return REGION_CODES[city][district]
    return None

def get_trade_type_code(trade_type: str) -> str:
    """
    거래 타입명으로부터 코드 조회
    
    Args:
        trade_type: 거래 타입 (예: "매매", "전세", "월세")
        
    Returns:
        str: 거래 타입 코드
    """
    from .types import TRADE_TYPE_CODES
    
    return TRADE_TYPE_CODES.get(trade_type, "A1")  # 기본값: 매매

def get_real_estate_type_code(estate_type: str) -> str:
    """
    부동산 타입명으로부터 코드 조회
    
    Args:
        estate_type: 부동산 타입 (예: "아파트", "오피스텔")
        
    Returns:
        str: 부동산 타입 코드
    """
    from .types import REAL_ESTATE_TYPE_CODES
    
    return REAL_ESTATE_TYPE_CODES.get(estate_type, "APT")  # 기본값: 아파트

def calculate_coordinates(region_code: str) -> Tuple[float, float, float, float]:
    """
    지역 코드로부터 대략적인 좌표 범위 계산
    
    Args:
        region_code: 지역 코드
        
    Returns:
        Tuple[float, float, float, float]: (leftLon, rightLon, topLat, bottomLat)
    """
    # 지역별 대략적인 좌표 (실제 서비스에서는 더 정확한 좌표 사용 권장)
    coordinate_mapping = {
        # 서울 강남구
        "1168010500": (127.020, 127.080, 37.530, 37.480),
        # 부산 해운대구  
        "2644010100": (129.150, 129.200, 35.180, 35.140),
        # 기본값 (서울 중심)
        "default": (126.95, 127.05, 37.58, 37.52)
    }
    
    return coordinate_mapping.get(region_code, coordinate_mapping["default"])

def setup_logging(level: str = "INFO", log_file: Optional[str] = None):
    """
    로깅 설정
    
    Args:
        level: 로그 레벨
        log_file: 로그 파일 경로 (선택사항)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            *([] if log_file is None else [logging.FileHandler(log_file)])
        ]
    )

def create_output_directory(output_dir: str) -> Path:
    """
    출력 디렉토리 생성
    
    Args:
        output_dir: 출력 디렉토리 경로
        
    Returns:
        Path: 생성된 디렉토리 Path 객체
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path

def validate_price_range(price_min: int, price_max: int) -> Tuple[int, int]:
    """
    가격 범위 유효성 검사 및 보정
    
    Args:
        price_min: 최소 가격
        price_max: 최대 가격
        
    Returns:
        Tuple[int, int]: 보정된 (최소 가격, 최대 가격)
    """
    if price_min < 0:
        price_min = 0
    if price_max < price_min:
        price_max = price_min + 1000000  # 기본 1000만원 범위
    
    return price_min, price_max

def validate_area_range(area_min: float, area_max: float) -> Tuple[float, float]:
    """
    면적 범위 유효성 검사 및 보정
    
    Args:
        area_min: 최소 면적
        area_max: 최대 면적
        
    Returns:
        Tuple[float, float]: 보정된 (최소 면적, 최대 면적)
    """
    if area_min < 0:
        area_min = 0
    if area_max < area_min:
        area_max = area_min + 100  # 기본 100㎡ 범위
    
    return area_min, area_max