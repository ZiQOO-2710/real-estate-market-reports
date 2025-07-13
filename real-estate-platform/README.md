# 부동산 시장 분석 플랫폼

🏠 **부동산 개발자를 위한 지도 기반 중앙화 분석 플랫폼**

## 📋 프로젝트 개요

부동산 개발자들이 잠재적 개발 부지를 효율적으로 조사하고 분석할 수 있도록 지원하는 **지도 기반 중앙화 플랫폼**입니다.

### 🎯 핵심 가치
- **데이터 통합**: 분산된 시장 데이터를 단일 인터페이스로 통합
- **의사결정 가속화**: 데이터 기반의 빠른 의사결정 지원  
- **효율성 향상**: 수동 작업 자동화 및 시각화를 통한 업무 효율 증대

### 👥 목표 사용자
- **주 사용자**: 부동산 개발회사의 토지 매입 및 사업성 검토팀
- **사용 시나리오**: 개발 후보지 선정, 시장 가격 동향 분석, 경쟁 단지 비교

## 🏗️ 프로젝트 구조

```
real-estate-platform/
├── frontend/                 # React.js 프론트엔드
│   ├── src/
│   │   ├── components/       # 재사용 가능한 컴포넌트
│   │   ├── pages/           # 페이지 컴포넌트
│   │   ├── services/        # API 서비스
│   │   ├── store/           # Redux 상태 관리
│   │   ├── utils/           # 유틸리티 함수
│   │   ├── types/           # TypeScript 타입 정의
│   │   └── hooks/           # 커스텀 훅
│   └── public/              # 정적 파일
├── backend/                  # Node.js 백엔드
│   ├── src/
│   │   ├── controllers/     # API 컨트롤러
│   │   ├── services/        # 비즈니스 로직
│   │   ├── models/          # 데이터 모델
│   │   ├── middleware/      # 미들웨어
│   │   ├── config/          # 설정 파일
│   │   └── utils/           # 유틸리티
│   └── tests/               # 테스트
├── database/                 # 데이터베이스 관련
│   ├── migrations/          # DB 마이그레이션
│   ├── seeds/               # 초기 데이터
│   ├── schemas/             # 스키마 정의
│   └── backups/             # 백업 파일
├── deployment/               # 배포 관련
├── docs/                     # 문서
└── scripts/                  # 유틸리티 스크립트
```

## 🚀 기술 스택

### Frontend
- **Framework**: React.js 18.x + TypeScript
- **상태관리**: Redux Toolkit
- **지도**: Kakao Maps API / Leaflet.js
- **UI**: Material-UI v5
- **차트**: Chart.js / Recharts

### Backend  
- **Runtime**: Node.js 18.x LTS
- **Framework**: Express.js + TypeScript
- **크롤링**: Puppeteer + Cheerio
- **인증**: JWT + OAuth2.0

### Database
- **주 DB**: PostgreSQL 14 + PostGIS 3.2
- **캐시**: Redis 7.0
- **스토리지**: AWS S3

### DevOps
- **컨테이너**: Docker + Docker Compose
- **CI/CD**: GitHub Actions
- **모니터링**: Prometheus + Grafana

## ✨ 핵심 기능

### 🗺️ 대화형 지도 기반 대시보드
- 카카오 맵 기반 실시간 지도 인터페이스
- 아파트 데이터 레이어 시각화
- 프로젝트 사이트 마킹 및 관리

### 🔍 반경 기반 시장 검색
- PostGIS 활용 지리 검색 엔진
- 1km/3km/5km 반경별 시장 분석
- 검색 결과 CSV 내보내기

### 📈 가격 추적 및 트렌드 분석
- 실시간 가격 데이터 크롤링
- 월간 스냅샷 아카이빙 시스템
- 가격 변동 트렌드 분석 및 예측

### 📊 데이터 통합 및 시각화
- 다양한 부동산 데이터 소스 통합
- 차트 및 그래프를 통한 시각화
- 사용자 맞춤형 대시보드

## 🔗 기존 모듈 연계

이 프로젝트는 기존에 개발된 모듈들을 활용합니다:

### 네이버 부동산 크롤러 (`naver_real_estate_module`)
- **활용**: 실시간 아파트 매물 데이터 수집
- **연계점**: 백엔드 크롤링 서비스로 통합

### 부동산 데이터 분석기 (`real_estate_analyzer_module`)  
- **활용**: CSV 데이터 처리 및 위치 기반 분석
- **연계점**: 데이터 처리 엔진으로 활용

## 📅 개발 일정

### Phase 1: 기초 개발 (8주)
- 개발 환경 구축
- 데이터베이스 설계
- 기본 API 개발
- 지도 인터페이스 구현

### Phase 2: 핵심 기능 (8주)  
- 반경 검색 기능
- 가격 트렌드 분석
- 데이터 내보내기
- 성능 최적화

### Phase 3: 배포 및 안정화 (4주)
- 테스트 및 QA
- 배포 환경 구축
- 운영 체계 수립

## 🚀 시작하기

### 환경 설정
```bash
# 프로젝트 클론
git clone <repository-url>
cd real-estate-platform

# 환경 변수 설정
cp .env.example .env

# 의존성 설치
npm run install:all

# 개발 서버 실행
npm run dev
```

## 👥 팀 구성

- **프로젝트 총괄**: 지쿠 & 클로디
- **개발**: 클로디 (Claude Code)
- **설계 및 기획**: 상세설계서 기반

## 📞 연락처

- **GitHub**: [프로젝트 저장소]
- **문서**: [프로젝트 위키]

---

**시작일**: 2025년 7월 13일  
**개발자**: 지쿠 & 클로디 (Claude Code)  
**버전**: 1.0.0-alpha