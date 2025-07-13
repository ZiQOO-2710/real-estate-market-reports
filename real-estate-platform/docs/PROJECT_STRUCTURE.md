# 프로젝트 구조 상세 설명

## 📁 전체 디렉토리 구조

```
real-estate-platform/
├── 📁 frontend/                    # React.js 프론트엔드
├── 📁 backend/                     # Node.js 백엔드  
├── 📁 database/                    # 데이터베이스 관련
├── 📁 deployment/                  # 배포 설정
├── 📁 docs/                        # 프로젝트 문서
├── 📁 scripts/                     # 유틸리티 스크립트
├── 📄 package.json                 # 루트 패키지 설정
├── 📄 docker-compose.yml           # Docker 컨테이너 설정
├── 📄 .env.example                 # 환경 변수 예시
├── 📄 .gitignore                   # Git 무시 파일
└── 📄 README.md                    # 프로젝트 개요
```

## 🎨 Frontend 구조 (`/frontend`)

```
frontend/
├── src/
│   ├── components/                 # 재사용 가능한 컴포넌트
│   │   ├── Map/                    # 지도 관련 컴포넌트
│   │   │   ├── KakaoMap.tsx
│   │   │   ├── MapMarker.tsx
│   │   │   └── MapControls.tsx
│   │   ├── UI/                     # 기본 UI 컴포넌트
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── Loading.tsx
│   │   ├── Forms/                  # 폼 컴포넌트
│   │   │   ├── SearchForm.tsx
│   │   │   └── FilterForm.tsx
│   │   └── Charts/                 # 차트 컴포넌트
│   │       ├── PriceChart.tsx
│   │       └── TrendChart.tsx
│   ├── pages/                      # 페이지 컴포넌트
│   │   ├── Dashboard/              # 대시보드 페이지
│   │   │   ├── index.tsx
│   │   │   └── components/
│   │   ├── Search/                 # 검색 페이지
│   │   │   ├── index.tsx
│   │   │   └── components/
│   │   ├── Analytics/              # 분석 페이지
│   │   │   ├── index.tsx
│   │   │   └── components/
│   │   └── Settings/               # 설정 페이지
│   │       ├── index.tsx
│   │       └── components/
│   ├── services/                   # API 서비스
│   │   ├── api.ts                  # API 기본 설정
│   │   ├── apartmentService.ts     # 아파트 데이터 API
│   │   ├── searchService.ts        # 검색 API
│   │   └── analyticsService.ts     # 분석 API
│   ├── store/                      # Redux 상태 관리
│   │   ├── index.ts                # 스토어 설정
│   │   ├── slices/                 # Redux Toolkit 슬라이스
│   │   │   ├── mapSlice.ts
│   │   │   ├── searchSlice.ts
│   │   │   └── userSlice.ts
│   │   └── middleware/             # 미들웨어
│   ├── utils/                      # 유틸리티 함수
│   │   ├── formatters.ts           # 데이터 포맷팅
│   │   ├── validators.ts           # 검증 함수
│   │   └── constants.ts            # 상수 정의
│   ├── types/                      # TypeScript 타입 정의
│   │   ├── apartment.ts
│   │   ├── search.ts
│   │   └── user.ts
│   ├── hooks/                      # 커스텀 훅
│   │   ├── useMap.ts
│   │   ├── useSearch.ts
│   │   └── useDebounce.ts
│   ├── styles/                     # 스타일 파일
│   │   ├── globals.css
│   │   ├── components/
│   │   └── themes/
│   ├── assets/                     # 정적 자원
│   │   ├── images/
│   │   ├── icons/
│   │   └── fonts/
│   ├── App.tsx                     # 메인 앱 컴포넌트
│   └── index.tsx                   # 앱 진입점
├── public/                         # 정적 파일
│   ├── index.html
│   ├── favicon.ico
│   └── manifest.json
├── package.json                    # 프론트엔드 의존성
├── tsconfig.json                   # TypeScript 설정
├── Dockerfile                      # Docker 설정
└── .env.local                      # 로컬 환경 변수
```

## 🔧 Backend 구조 (`/backend`)

```
backend/
├── src/
│   ├── controllers/                # API 컨트롤러
│   │   ├── apartmentController.ts  # 아파트 API
│   │   ├── searchController.ts     # 검색 API
│   │   ├── analyticsController.ts  # 분석 API
│   │   └── userController.ts       # 사용자 API
│   ├── services/                   # 비즈니스 로직
│   │   ├── apartmentService.ts     # 아파트 비즈니스 로직
│   │   ├── crawlingService.ts      # 크롤링 서비스
│   │   ├── geolocationService.ts   # 지리 정보 서비스
│   │   ├── priceAnalysisService.ts # 가격 분석 서비스
│   │   └── cacheService.ts         # 캐시 서비스
│   ├── models/                     # 데이터 모델
│   │   ├── Apartment.ts            # 아파트 모델
│   │   ├── PriceData.ts            # 가격 데이터 모델
│   │   ├── User.ts                 # 사용자 모델
│   │   └── ProjectSite.ts          # 프로젝트 사이트 모델
│   ├── middleware/                 # 미들웨어
│   │   ├── auth.ts                 # 인증 미들웨어
│   │   ├── validation.ts           # 검증 미들웨어
│   │   ├── rateLimit.ts            # 레이트 리미팅
│   │   └── errorHandler.ts         # 에러 핸들링
│   ├── routes/                     # 라우트 정의
│   │   ├── index.ts                # 라우트 인덱스
│   │   ├── apartments.ts           # 아파트 라우트
│   │   ├── search.ts               # 검색 라우트
│   │   ├── analytics.ts            # 분석 라우트
│   │   └── auth.ts                 # 인증 라우트
│   ├── config/                     # 설정 파일
│   │   ├── database.ts             # 데이터베이스 설정
│   │   ├── redis.ts                # Redis 설정
│   │   ├── crawler.ts              # 크롤러 설정
│   │   └── app.ts                  # 앱 설정
│   ├── utils/                      # 유틸리티
│   │   ├── logger.ts               # 로깅 유틸
│   │   ├── validation.ts           # 검증 유틸
│   │   ├── encryption.ts           # 암호화 유틸
│   │   └── helpers.ts              # 헬퍼 함수
│   ├── types/                      # TypeScript 타입
│   │   ├── api.ts                  # API 타입
│   │   ├── database.ts             # DB 타입
│   │   └── crawler.ts              # 크롤러 타입
│   ├── jobs/                       # 백그라운드 작업
│   │   ├── crawlJob.ts             # 크롤링 작업
│   │   ├── analysisJob.ts          # 분석 작업
│   │   └── cleanupJob.ts           # 정리 작업
│   ├── app.ts                      # Express 앱 설정
│   └── server.ts                   # 서버 진입점
├── tests/                          # 테스트
│   ├── unit/                       # 단위 테스트
│   ├── integration/                # 통합 테스트
│   └── fixtures/                   # 테스트 데이터
├── package.json                    # 백엔드 의존성
├── tsconfig.json                   # TypeScript 설정
├── Dockerfile                      # Docker 설정
├── Dockerfile.crawler              # 크롤러 Docker 설정
└── .env                            # 환경 변수
```

## 🗃️ Database 구조 (`/database`)

```
database/
├── migrations/                     # DB 마이그레이션
│   ├── 001_create_apartments.sql
│   ├── 002_create_price_data.sql
│   ├── 003_create_users.sql
│   └── 004_create_project_sites.sql
├── seeds/                          # 초기 데이터
│   ├── apartments.sql
│   ├── sample_price_data.sql
│   └── admin_user.sql
├── schemas/                        # 스키마 정의
│   ├── init.sql                    # 초기 스키마
│   ├── indexes.sql                 # 인덱스 생성
│   └── functions.sql               # 저장 함수
├── backups/                        # 백업 파일
│   └── .gitkeep
└── redis.conf                      # Redis 설정
```

## 🚀 Deployment 구조 (`/deployment`)

```
deployment/
├── docker/                        # Docker 설정
│   ├── production.dockerfile
│   └── staging.dockerfile
├── nginx/                          # Nginx 설정
│   ├── nginx.conf
│   ├── ssl/
│   └── sites-enabled/
├── kubernetes/                     # K8s 매니페스트
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── ingress.yaml
├── terraform/                      # 인프라 코드
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── scripts/                        # 배포 스크립트
│   ├── deploy-staging.sh
│   ├── deploy-production.sh
│   └── rollback.sh
└── environments/                   # 환경별 설정
    ├── staging.env
    └── production.env
```

## 📚 Documentation 구조 (`/docs`)

```
docs/
├── API.md                          # API 문서
├── DEPLOYMENT.md                   # 배포 가이드
├── DEVELOPMENT.md                  # 개발 가이드
├── DATABASE.md                     # 데이터베이스 설계
├── ARCHITECTURE.md                 # 아키텍처 문서
├── CONTRIBUTING.md                 # 기여 가이드
├── CHANGELOG.md                    # 변경 로그
└── images/                         # 문서 이미지
    ├── architecture-diagram.png
    └── database-schema.png
```

## 🛠️ Scripts 구조 (`/scripts`)

```
scripts/
├── setup/                          # 초기 설정 스크립트
│   ├── install-dependencies.sh
│   ├── setup-database.sh
│   └── setup-environment.sh
├── maintenance/                     # 유지보수 스크립트
│   ├── backup-database.sh
│   ├── cleanup-logs.sh
│   └── update-dependencies.sh
├── data/                           # 데이터 처리 스크립트
│   ├── import-apartments.py
│   ├── process-price-data.py
│   └── generate-sample-data.js
└── monitoring/                     # 모니터링 스크립트
    ├── health-check.sh
    ├── performance-test.js
    └── log-analyzer.py
```

## 🔗 주요 설정 파일

### 루트 레벨
- **package.json**: 프로젝트 메타데이터 및 스크립트
- **docker-compose.yml**: 개발 환경 컨테이너 설정
- **.env.example**: 환경 변수 템플릿
- **.gitignore**: Git 무시 파일 설정

### Frontend
- **package.json**: React 앱 의존성
- **tsconfig.json**: TypeScript 컴파일러 설정
- **craco.config.js**: Create React App 설정 오버라이드

### Backend
- **package.json**: Node.js 서버 의존성
- **tsconfig.json**: TypeScript 서버 설정
- **nodemon.json**: 개발 서버 자동 재시작 설정

## 📝 파일 명명 규칙

### 컴포넌트
- **React 컴포넌트**: PascalCase (예: `KakaoMap.tsx`)
- **페이지 컴포넌트**: PascalCase (예: `Dashboard/index.tsx`)

### 서비스 및 유틸리티
- **서비스 파일**: camelCase + Service (예: `apartmentService.ts`)
- **유틸리티 파일**: camelCase (예: `formatters.ts`)

### 데이터베이스
- **마이그레이션**: 숫자_설명 (예: `001_create_apartments.sql`)
- **시드 파일**: 테이블명 (예: `apartments.sql`)

### 설정 파일
- **환경별 설정**: 환경명.env (예: `production.env`)
- **Docker 파일**: 목적.dockerfile (예: `production.dockerfile`)

이 구조는 확장 가능하고 유지보수가 용이하도록 설계되었으며, 각 모듈의 책임을 명확히 분리하여 개발 효율성을 높입니다.