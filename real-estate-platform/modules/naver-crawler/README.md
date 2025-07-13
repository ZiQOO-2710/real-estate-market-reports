# 네이버 부동산 크롤링 모듈

## 📋 개요
네이버 부동산 플랫폼에서 아파트 매물 정보를 자동으로 수집하는 모듈입니다.

## 📁 폴더 구조
```
naver-crawler/
├── core/                    # 핵심 크롤링 로직
│   ├── bundang_crawler.py   # 분당구 특화 크롤러
│   ├── main_crawler.py      # 메인 크롤러
│   ├── crawler.py           # 모듈형 크롤러
│   └── __init__.py
├── utils/                   # 유틸리티 함수들
│   ├── parser.py            # 데이터 파싱
│   ├── stealth.py           # 안티 디텍션
│   ├── rate_limiter.py      # 속도 제한
│   ├── storage.py           # 데이터 저장
│   └── utils.py             # 기타 유틸리티
├── config/                  # 설정 파일
│   └── settings.py
├── tests/                   # 테스트 파일
│   └── test_crawler.py
├── data/                    # 데이터 저장소
│   ├── input/               # 입력 데이터
│   └── output/              # 출력 데이터
├── logs/                    # 로그 파일
├── requirements.txt         # 의존성
└── README.md               # 이 파일
```

## 🚀 사용법

### 기본 사용
```python
from modules.naver_crawler import BundangApartmentCrawlerV2

# 분당구 아파트 크롤링
crawler = BundangApartmentCrawlerV2()
result = await crawler.run_test()
```

### 설치
```bash
pip install -r requirements.txt
playwright install chromium
```

## ✨ 주요 기능
- 🏠 아파트 매물 정보 수집
- 📍 지역별 필터링 (분당구 특화)
- 💰 가격 정보 추출 (매매/전세)
- 📊 면적 정보 수집
- 🗓️ 건축년도 정보
- 📄 CSV 파일 자동 저장

## 🔧 기술 스택
- Python 3.12+
- Playwright (브라우저 자동화)
- AsyncIO (비동기 처리)
- Pandas (데이터 처리)
- aiohttp (HTTP 요청)

## 📊 수집 데이터
- 아파트명
- 주소 정보
- 가격 정보 (매매/전세 단가)
- 면적 정보 (최소/최대)
- 건축년도
- 세대수 정보
- 원본 API 데이터

## ⚠️ 주의사항
- 네이버 부동산 이용약관을 준수하세요
- 과도한 요청은 IP 차단을 일으킬 수 있습니다
- 데이터 사용 시 개인정보보호법을 준수하세요

## 📝 업데이트 로그
- v1.0.0: 초기 모듈 생성 및 분당구 크롤러 구현
- 백업 생성일: 2025-07-14