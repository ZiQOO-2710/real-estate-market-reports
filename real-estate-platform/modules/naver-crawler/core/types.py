"""
데이터 타입 정의
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class ApartmentData:
    """아파트 매물 정보 데이터 클래스"""
    
    # 기본 정보
    complex_name: Optional[str] = None
    complex_no: Optional[str] = None
    address: Optional[str] = None
    
    # 가격 정보 (만원 단위)
    min_deal_price: Optional[int] = None
    max_deal_price: Optional[int] = None
    min_jeonse_price: Optional[int] = None
    max_jeonse_price: Optional[int] = None
    min_monthly_rent: Optional[int] = None
    max_monthly_rent: Optional[int] = None
    
    # 면적 정보 (㎡)
    min_area: Optional[float] = None
    max_area: Optional[float] = None
    representative_area: Optional[float] = None
    
    # 건물 정보
    total_household_count: Optional[int] = None
    total_dong_count: Optional[int] = None
    completion_year_month: Optional[str] = None
    floor_area_ratio: Optional[float] = None
    
    # 위치 정보
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # 거래 정보
    deal_count: Optional[int] = None
    lease_count: Optional[int] = None
    rent_count: Optional[int] = None
    
    # 메타 정보
    photo_count: Optional[int] = None
    real_estate_type: Optional[str] = None
    collect_time: Optional[datetime] = None
    source_region: Optional[str] = None
    
    # 원본 데이터
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {}
        for key, value in self.__dict__.items():
            if value is not None:
                if isinstance(value, datetime):
                    result[key] = value.isoformat()
                else:
                    result[key] = value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApartmentData':
        """딕셔너리에서 생성"""
        if 'collect_time' in data and isinstance(data['collect_time'], str):
            data['collect_time'] = datetime.fromisoformat(data['collect_time'])
        return cls(**data)

@dataclass
class CrawlerConfig:
    """크롤러 설정 클래스"""
    
    # 요청 설정
    request_delay: float = 2.0  # 요청 간 딜레이 (초)
    timeout: int = 30  # 타임아웃 (초)
    max_retries: int = 3  # 최대 재시도 횟수
    
    # 지역 설정
    zoom_level: int = 16  # 지도 줌 레벨
    
    # 필터 설정
    price_min: int = 0  # 최소 가격 (만원)
    price_max: int = 900000000  # 최대 가격 (만원)
    area_min: float = 0  # 최소 면적 (㎡)
    area_max: float = 900000000  # 최대 면적 (㎡)
    build_years_old: int = 50  # 최대 건축 년수
    build_years_new: int = 0  # 최소 건축 년수
    
    # 출력 설정
    save_to_file: bool = True  # 파일 저장 여부
    output_format: str = "csv"  # 출력 형식 (csv, json, excel)
    output_dir: str = "output"  # 출력 디렉토리
    
    # 로깅 설정
    log_level: str = "INFO"  # 로그 레벨
    verbose: bool = False  # 상세 로그 출력 여부

# 지역 코드 매핑
REGION_CODES = {
    "서울": {
        "강남구": "1168010500",
        "강동구": "1168010600", 
        "강북구": "1168010700",
        "강서구": "1168010800",
        "관악구": "1168010900",
        "광진구": "1168011000",
        "구로구": "1168011100",
        "금천구": "1168011200",
        "노원구": "1168011300",
        "도봉구": "1168011400",
        "동대문구": "1168011500",
        "동작구": "1168011600",
        "마포구": "1168011700",
        "서대문구": "1168011800",
        "서초구": "1168011900",
        "성동구": "1168012000",
        "성북구": "1168012100",
        "송파구": "1168012200",
        "양천구": "1168012300",
        "영등포구": "1168012400",
        "용산구": "1168012500",
        "은평구": "1168012600",
        "종로구": "1168012700",
        "중구": "1168012800",
        "중랑구": "1168012900",
    },
    "부산": {
        "해운대구": "2644010100",
        "수영구": "2644010200",
        "남구": "2644010300",
        "동구": "2644010400",
        "서구": "2644010500",
        "중구": "2644010600",
        "영도구": "2644010700",
        "부산진구": "2644010800",
        "동래구": "2644010900",
        "북구": "2644011000",
        "금정구": "2644011100",
        "강서구": "2644011200",
        "연제구": "2644011300",
        "사상구": "2644011400",
        "사하구": "2644011500",
        "기장군": "2644011600",
    },
    "인천": {
        "중구": "2811010100",
        "동구": "2811010200",
        "미추홀구": "2811010300",
        "연수구": "2811010400",
        "남동구": "2811010500",
        "부평구": "2811010600",
        "계양구": "2811010700",
        "서구": "2811010800",
        "강화군": "2811010900",
        "옹진군": "2811011000",
    }
}

# 거래 타입 코드
TRADE_TYPE_CODES = {
    "매매": "A1",
    "전세": "B1", 
    "월세": "B2",
    "단기임대": "B3"
}

# 부동산 타입 코드  
REAL_ESTATE_TYPE_CODES = {
    "아파트": "APT",
    "오피스텔": "OPST",
    "빌라": "VL",
    "아파트분양권": "ABYG",
    "주택": "JGC",
    "토지": "LAND",
    "상가": "SG",
    "사무실": "SMC",
    "공장": "FAC",
    "창고": "WH"
}