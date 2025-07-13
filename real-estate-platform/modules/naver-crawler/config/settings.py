"""
네이버 부동산 크롤링 설정 파일
"""
import os
from pathlib import Path

# 프로젝트 루트 경로
BASE_DIR = Path(__file__).parent.parent

# 네이버 부동산 URL (업데이트됨)
NAVER_REAL_ESTATE_BASE_URL = "https://new.land.naver.com"
NAVER_COMPLEXES_URL = "https://new.land.naver.com/complexes"

# 크롤링 설정 (WARP 사용 - 최적화된 설정)
CRAWLING_CONFIG = {
    "delay_between_requests": 3,   # 요청 간 딜레이 (초) - WARP로 IP 변경되므로 단축
    "random_delay_range": (1, 5),  # 랜덤 딜레이 범위 (초) - 더 빠르게
    "max_retry_attempts": 3,       # 최대 재시도 횟수
    "timeout": 30,                 # 타임아웃 (초)
    "headless": True,              # 브라우저 헤드리스 모드
    "viewport_width": 1920,        # 뷰포트 너비
    "viewport_height": 1080,       # 뷰포트 높이
    "session_break_interval": 50,  # 세션 휴식 간격 (요청 수) - 더 많이
    "session_break_duration": 10,  # 세션 휴식 시간 (초) - 더 짧게
    "max_requests_per_session": 200, # 세션당 최대 요청 수 - 더 많이
    "long_break_interval": 500,    # 긴 휴식 간격 (요청 수) - 더 적게
    "long_break_duration": 60,     # 긴 휴식 시간 (초) - 1분으로 단축
    "daily_request_limit": 10000,  # 일일 요청 제한 - 대폭 증가
    "hourly_request_limit": 1000,  # 시간당 요청 제한 - 대폭 증가
}

# 데이터 저장 설정
DATA_CONFIG = {
    "output_dir": BASE_DIR / "data" / "output",
    "csv_filename": "naver_real_estate_{region}_{timestamp}.csv",
    "screenshot_dir": BASE_DIR / "screenshots",
    "log_dir": BASE_DIR / "logs",
}

# Supabase 설정
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

# 로그 설정
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    "rotation": "10 MB",
    "retention": "7 days",
}

# 크롤링 대상 지역 설정
REGIONS = {
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

# 수집할 데이터 필드
DATA_FIELDS = [
    "단지명",
    "주소",
    "거래타입",  # 매매, 전세, 월세
    "가격",
    "면적",
    "층수",
    "건축년도",
    "거래일자",
    "위도",
    "경도",
    "수집일시",
]

# 사용자 에이전트 (더 다양한 브라우저와 OS)
USER_AGENTS = [
    # 크롬 (Windows)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    # 크롬 (Mac)
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    # 파이어폭스
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
    # 사파리
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    # 엣지
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # 리눅스
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
    # 모바일 (가끔 사용)
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Android 13; Mobile; rv:109.0) Gecko/20100101 Firefox/121.0",
]

# 프록시 설정 (IP 차단 방지용)
PROXY_CONFIG = {
    "enabled": True,  # True로 설정하여 프록시 사용
    "proxy_list": [
        "socks5://127.0.0.1:40000",
        # 예시: 실제 프록시 서버로 변경하세요
        # "http://username:password@proxy1.example.com:8080",
        # "http://proxy2.example.com:3128",
        # "socks5://proxy3.example.com:1080",
        # 무료 프록시 예시 (품질 보장 안됨)
        # "http://103.156.249.66:8080",
        # "http://47.74.152.29:8888",
    ],
    "rotation_enabled": True,    # 프록시 로테이션 사용
    "rotation_interval": 50,     # N개 요청마다 프록시 변경
    "test_url": "https://httpbin.org/ip",
    "timeout": 10,               # 프록시 연결 타임아웃
    "max_retries": 3,           # 프록시 실패시 재시도
}

# 세션 관리 설정
SESSION_CONFIG = {
    "cookie_persistence": True,
    "session_rotation_interval": 100,  # 요청 수 기준
    "clear_cache_interval": 50,        # 캐시 초기화 간격
    "simulate_human_behavior": True,   # 인간 행동 시뮬레이션
}