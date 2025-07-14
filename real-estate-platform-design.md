# 부동산 시장 분석 플랫폼 상세 설계서

## 1. 프로젝트 개요

### 1.1 프로젝트 목적
부동산 개발자들이 잠재적 개발 부지를 효율적으로 조사하고 분석할 수 있도록 지원하는 지도 기반 중앙화 플랫폼 구축

### 1.2 핵심 가치
- **데이터 통합**: 분산된 시장 데이터를 단일 인터페이스로 통합
- **의사결정 가속화**: 데이터 기반의 빠른 의사결정 지원
- **효율성 향상**: 수동 작업 자동화 및 시각화를 통한 업무 효율 증대

### 1.3 목표 사용자
- **주 사용자**: 부동산 개발회사의 토지 매입 및 사업성 검토팀
- **사용 시나리오**: 개발 후보지 선정, 시장 가격 동향 분석, 경쟁 단지 비교

## 2. 시스템 아키텍처

### 2.1 전체 구조
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│         (React.js + Redux + Leaflet/Kakao Maps)         │
└────────────────────┬────────────────────────────────────┘
                     │ REST API / WebSocket
┌────────────────────┴────────────────────────────────────┐
│                    Backend Layer                         │
│              (Node.js + Express.js)                      │
├─────────────────────────────────────────────────────────┤
│   - API Gateway         - Authentication Service        │
│   - Business Logic      - Data Processing Service       │
│   - Crawling Service    - Analytics Service            │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────┴────────────────────────────────────┐
│                  Data Layer                              │
│         PostgreSQL + PostGIS + Redis Cache              │
└─────────────────────────────────────────────────────────┘
```

### 2.2 기술 스택 상세

#### Frontend
- **Framework**: React.js 18.x + TypeScript
- **상태관리**: Redux Toolkit
- **지도**: Kakao Maps API (주) / Leaflet.js (백업)
- **UI 라이브러리**: Material-UI v5
- **차트**: Chart.js / Recharts
- **HTTP Client**: Axios

#### Backend
- **Runtime**: Node.js 18.x LTS
- **Framework**: Express.js
- **언어**: TypeScript
- **크롤링**: Puppeteer + Cheerio
- **스케줄러**: node-cron
- **인증**: JWT + OAuth2.0

#### Database & Storage
- **주 데이터베이스**: PostgreSQL 14 + PostGIS 3.2
- **캐시**: Redis 7.0
- **파일 스토리지**: AWS S3 (지도 타일, 리포트)

#### DevOps & Infrastructure
- **컨테이너**: Docker + Docker Compose
- **오케스트레이션**: Kubernetes (Production)
- **CI/CD**: GitHub Actions
- **모니터링**: Prometheus + Grafana
- **로깅**: ELK Stack

## 3. 핵심 기능 상세 설계

### 3.1 대화형 지도 기반 대시보드

#### 3.1.1 지도 인터페이스
```typescript
interface MapComponent {
  // 기본 지도 설정
  center: { lat: number; lng: number };
  zoom: number;
  
  // 레이어 관리
  layers: {
    base: BaseMapLayer;
    apartments: ApartmentLayer;
    projects: ProjectSiteLayer;
    analysis: AnalysisLayer;
  };
  
  // 인터랙션
  events: {
    onClick: (e: MapClickEvent) => void;
    onZoom: (level: number) => void;
    onMove: (bounds: MapBounds) => void;
  };
}
```

#### 3.1.2 아파트 데이터 레이어
```typescript
interface ApartmentComplex {
  id: string;
  name: string;
  address: {
    road: string;
    jibun: string;
    dong: string;
    gu: string;
    city: string;
  };
  coordinates: {
    lat: number;
    lng: number;
  };
  details: {
    totalUnits: number;
    constructionYear: number;
    floors: number;
    parkingRatio: number;
  };
  marketData: {
    lastTransactionPrice: number;
    lastTransactionDate: Date;
    currentAskingPrice: number;
    pricePerPyeong: number;
  };
}
```

#### 3.1.3 실시간 시장 가격 통합
```typescript
interface PriceCrawler {
  sources: {
    actualTransaction: {
      url: string;
      parser: HTMLParser;
      schedule: CronExpression;
    };
    askingPrice: {
      url: string;
      parser: JSONParser;
      schedule: CronExpression;
    };
  };
  
  methods: {
    crawl(): Promise<MarketData[]>;
    parse(html: string): MarketData;
    validate(data: MarketData): boolean;
    store(data: MarketData[]): Promise<void>;
  };
}
```

### 3.2 반경 기반 시장 검색 및 데이터 추출

#### 3.2.1 위치 기반 검색 엔진
```sql
-- PostGIS를 활용한 반경 검색 쿼리
CREATE OR REPLACE FUNCTION search_apartments_by_radius(
  center_lat DOUBLE PRECISION,
  center_lng DOUBLE PRECISION,
  radius_km INTEGER
)
RETURNS TABLE (
  apartment_id UUID,
  name VARCHAR,
  address JSONB,
  distance_km DOUBLE PRECISION,
  transaction_price NUMERIC,
  asking_price NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT 
    a.id,
    a.name,
    a.address,
    ST_Distance(
      a.location::geography,
      ST_MakePoint(center_lng, center_lat)::geography
    ) / 1000 as distance_km,
    p.transaction_price,
    p.asking_price
  FROM apartments a
  JOIN price_data p ON a.id = p.apartment_id
  WHERE ST_DWithin(
    a.location::geography,
    ST_MakePoint(center_lng, center_lat)::geography,
    radius_km * 1000
  )
  ORDER BY distance_km;
END;
$$ LANGUAGE plpgsql;
```

#### 3.2.2 검색 결과 처리 및 내보내기
```typescript
interface SearchService {
  // 검색 실행
  async searchByRadius(params: {
    center: { address?: string; coordinates?: Coordinates };
    radii: number[]; // [1, 3, 5] km
  }): Promise<SearchResult>;
  
  // 결과 포맷팅
  formatResults(results: SearchResult): {
    summary: RadiusSummary;
    details: ApartmentDetail[];
  };
  
  // CSV 내보내기
  exportToCSV(results: SearchResult): Buffer;
}
```

### 3.3 가격 추적 및 트렌드 분석

#### 3.3.1 데이터 아카이빙 시스템
```typescript
interface PriceArchiveService {
  // 월간 스냅샷 저장
  async createMonthlySnapshot(): Promise<{
    timestamp: Date;
    recordsCount: number;
    status: 'success' | 'partial' | 'failed';
  }>;
  
  // 가격 이력 조회
  async getPriceHistory(
    apartmentId: string,
    period: { from: Date; to: Date }
  ): Promise<PriceHistory[]>;
}

// 스케줄러 설정
const scheduleConfig = {
  monthlySnapshot: '0 0 1 * *', // 매월 1일 00:00
  dailyUpdate: '0 2 * * *',     // 매일 02:00
  weeklyAnalysis: '0 0 * * 0'   // 매주 일요일 00:00
};
```

#### 3.3.2 트렌드 분석 엔진
```typescript
interface TrendAnalyzer {
  // 개별 단지 분석
  analyzeComplex(apartmentId: string): {
    priceChange: {
      monthly: number;
      quarterly: number;
      yearly: number;
    };
    volatility: number;
    trendDirection: 'up' | 'down' | 'stable';
    forecast: PriceForecast;
  };
  
  // 지역 분석
  analyzeRegion(regionCode: string): {
    averagePrice: number;
    medianPrice: number;
    priceDistribution: Distribution;
    hotspots: Coordinates[];
  };
}
```

## 4. 데이터베이스 설계

### 4.1 주요 테이블 구조

```sql
-- 아파트 단지 정보
CREATE TABLE apartments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(200) NOT NULL,
  address JSONB NOT NULL,
  location GEOMETRY(Point, 4326) NOT NULL,
  details JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 가격 데이터
CREATE TABLE price_data (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  apartment_id UUID REFERENCES apartments(id),
  transaction_price NUMERIC(12, 0),
  transaction_date DATE,
  asking_price NUMERIC(12, 0),
  price_per_pyeong NUMERIC(10, 0),
  data_source VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- 가격 이력 (월간 스냅샷)
CREATE TABLE price_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  apartment_id UUID REFERENCES apartments(id),
  snapshot_date DATE NOT NULL,
  avg_transaction_price NUMERIC(12, 0),
  avg_asking_price NUMERIC(12, 0),
  transaction_count INTEGER,
  price_change_rate NUMERIC(5, 2)
);

-- 사용자 프로젝트 사이트
CREATE TABLE project_sites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id),
  name VARCHAR(200) NOT NULL,
  location GEOMETRY(Point, 4326) NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_apartments_location ON apartments USING GIST(location);
CREATE INDEX idx_price_data_apartment_date ON price_data(apartment_id, transaction_date DESC);
CREATE INDEX idx_price_history_date ON price_history(snapshot_date DESC);
```

## 5. API 설계

### 5.1 주요 엔드포인트

```typescript
// 지도 데이터 API
GET /api/v1/map/apartments
  Query: { bounds: MapBounds, zoom: number }
  Response: ApartmentMarker[]

// 아파트 상세 정보
GET /api/v1/apartments/:id
  Response: ApartmentDetail

// 반경 검색
POST /api/v1/search/radius
  Body: { center: Coordinates, radii: number[] }
  Response: RadiusSearchResult

// 가격 트렌드
GET /api/v1/analytics/trends/:apartmentId
  Query: { period: string }
  Response: TrendData

// 프로젝트 사이트 관리
POST /api/v1/projects/sites
GET /api/v1/projects/sites
PUT /api/v1/projects/sites/:id
DELETE /api/v1/projects/sites/:id

// 데이터 내보내기
POST /api/v1/export/csv
  Body: { data: SearchResult }
  Response: { downloadUrl: string }
```

## 6. 보안 및 성능 최적화

### 6.1 보안 고려사항
- JWT 기반 인증 시스템
- API Rate Limiting (사용자별 시간당 요청 제한)
- SQL Injection 방지 (Parameterized Queries)
- XSS 방지 (입력값 검증 및 이스케이프)
- HTTPS 강제 적용

### 6.2 성능 최적화
- Redis 캐싱 전략
  - 자주 조회되는 아파트 정보 캐싱
  - 검색 결과 캐싱 (TTL: 1시간)
- 데이터베이스 최적화
  - 적절한 인덱싱
  - 파티셔닝 (날짜별 가격 데이터)
- 프론트엔드 최적화
  - 지도 마커 클러스터링
  - 가상 스크롤링
  - 이미지 레이지 로딩

## 7. 배포 및 운영

### 7.1 배포 파이프라인
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://backend:4000
  
  backend:
    build: ./backend
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/realestate
      - REDIS_URL=redis://redis:6379
    depends_on:
      - postgres
      - redis
  
  postgres:
    image: postgis/postgis:14-3.2
    environment:
      - POSTGRES_DB=realestate
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 7.2 모니터링 및 로깅
- 애플리케이션 메트릭스 (Prometheus)
  - API 응답 시간
  - 데이터베이스 쿼리 성능
  - 크롤링 성공률
- 로그 수집 및 분석 (ELK Stack)
  - 에러 로그 실시간 모니터링
  - 사용자 행동 분석
- 알림 시스템
  - 크롤링 실패 알림
  - 시스템 리소스 임계치 알림

## 8. 향후 확장 계획

### 8.1 단기 (3-6개월)
- 모바일 반응형 UI 개선
- 추가 데이터 소스 통합 (KB부동산, 한국감정원)
- 사용자 맞춤형 알림 기능

### 8.2 중장기 (6-12개월)
- AI 기반 가격 예측 모델 도입
- 3D 지도 시각화
- 협업 기능 (팀 내 정보 공유)
- RESTful API 공개 (외부 연동)

## 9. 프로젝트 일정

### Phase 1: 기초 개발 (8주)
- 1-2주: 개발 환경 구축 및 아키텍처 설계
- 3-4주: 데이터베이스 설계 및 기본 API 개발
- 5-6주: 지도 인터페이스 및 기본 기능 구현
- 7-8주: 크롤링 모듈 개발 및 데이터 수집

### Phase 2: 핵심 기능 구현 (8주)
- 9-10주: 반경 검색 기능 구현
- 11-12주: 가격 트렌드 분석 기능
- 13-14주: 데이터 내보내기 및 리포트 기능
- 15-16주: 성능 최적화 및 버그 수정

### Phase 3: 배포 및 안정화 (4주)
- 17-18주: 테스트 및 QA
- 19-20주: 배포 준비 및 운영 환경 구축

## 10. 예상 리소스

### 10.1 개발팀 구성
- 프로젝트 매니저: 1명
- 백엔드 개발자: 2명
- 프론트엔드 개발자: 2명
- 데이터 엔지니어: 1명
- UI/UX 디자이너: 1명
- QA 엔지니어: 1명

### 10.2 인프라 비용 (월간)
- 클라우드 서버 (AWS): $500-800
- 데이터베이스 (RDS): $200-300
- 캐시 서버 (ElastiCache): $100-150
- 지도 API: $300-500
- 모니터링 도구: $100-200
- 총계: 약 $1,200-1,950/월