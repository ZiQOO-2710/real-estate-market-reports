-- 네이버 부동산 크롤링 데이터를 위한 Supabase 데이터베이스 스키마
-- 생성일: 2025-07-14

-- 1. 아파트 단지 기본 정보 테이블
CREATE TABLE IF NOT EXISTS apartment_complexes (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) UNIQUE NOT NULL, -- 네이버 단지 ID
    complex_name VARCHAR(200) NOT NULL,
    address VARCHAR(500),
    completion_year INTEGER,
    total_households INTEGER,
    source_url TEXT,
    screenshot_path TEXT,
    latitude DECIMAL(10, 8), -- 위도 (추후 추가)
    longitude DECIMAL(11, 8), -- 경도 (추후 추가)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 단지별 면적 정보 테이블
CREATE TABLE IF NOT EXISTS complex_areas (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    area_sqm DECIMAL(10, 2) NOT NULL, -- 면적 (㎡)
    area_pyeong DECIMAL(10, 2), -- 면적 (평)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 현재 매물 정보 테이블
CREATE TABLE IF NOT EXISTS current_listings (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    listing_index INTEGER,
    deal_type VARCHAR(20) NOT NULL, -- 매매, 전세, 월세
    price_display VARCHAR(100), -- 원본 가격 표시 (예: "14억 5,000")
    price_amount BIGINT, -- 가격 (만원 단위)
    monthly_rent BIGINT, -- 월세 (만원 단위)
    area_sqm DECIMAL(10, 2), -- 면적 (㎡)
    floor_info VARCHAR(50), -- 층수 정보
    description TEXT, -- 매물 설명
    raw_text TEXT, -- 원본 텍스트
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. 실거래가 정보 테이블
CREATE TABLE IF NOT EXISTS transaction_history (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    transaction_type VARCHAR(20), -- 매매, 전세
    price_amount BIGINT, -- 거래가 (만원 단위)
    area_sqm DECIMAL(10, 2), -- 면적 (㎡)
    floor_info VARCHAR(50), -- 층수 정보
    transaction_date DATE, -- 거래 일자 (추후 파싱)
    pattern_type INTEGER, -- 패턴 분류
    match_text TEXT, -- 매칭된 텍스트
    context_text TEXT, -- 전후 문맥
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 가격 분석 데이터 테이블
CREATE TABLE IF NOT EXISTS price_analysis (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    analysis_date DATE DEFAULT CURRENT_DATE,
    total_listings INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    price_min BIGINT, -- 최저가 (만원)
    price_max BIGINT, -- 최고가 (만원)
    price_avg BIGINT, -- 평균가 (만원)
    deal_type_summary JSONB, -- 거래유형별 통계
    areas_count INTEGER, -- 면적 유형 수
    floors_count INTEGER, -- 층수 정보 수
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. 크롤링 메타데이터 테이블
CREATE TABLE IF NOT EXISTS crawl_metadata (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    crawl_method VARCHAR(50) NOT NULL, -- playwright_mcp_modular 등
    crawl_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    total_prices_extracted INTEGER DEFAULT 0,
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    raw_data JSONB, -- 전체 JSON 데이터 저장
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 상세 가격 정보 테이블 (all_prices에서 추출)
CREATE TABLE IF NOT EXISTS detailed_prices (
    id BIGSERIAL PRIMARY KEY,
    complex_id VARCHAR(50) REFERENCES apartment_complexes(complex_id) ON DELETE CASCADE,
    price_text VARCHAR(100) NOT NULL, -- 원본 가격 텍스트
    price_amount BIGINT, -- 파싱된 가격 (만원)
    price_type VARCHAR(20), -- 매매, 전세, 월세, 기타
    source_section VARCHAR(50), -- 매물, 거래, 상세 등
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_complex_id ON apartment_complexes(complex_id);
CREATE INDEX IF NOT EXISTS idx_listings_complex_id ON current_listings(complex_id);
CREATE INDEX IF NOT EXISTS idx_listings_deal_type ON current_listings(deal_type);
CREATE INDEX IF NOT EXISTS idx_transactions_complex_id ON transaction_history(complex_id);
CREATE INDEX IF NOT EXISTS idx_prices_complex_id ON detailed_prices(complex_id);
CREATE INDEX IF NOT EXISTS idx_crawl_timestamp ON crawl_metadata(crawl_timestamp);

-- RLS (Row Level Security) 정책 설정 (선택사항)
-- ALTER TABLE apartment_complexes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE current_listings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE transaction_history ENABLE ROW LEVEL SECURITY;

-- 뷰 생성: 단지별 종합 정보
CREATE OR REPLACE VIEW complex_summary AS
SELECT 
    ac.complex_id,
    ac.complex_name,
    ac.address,
    ac.completion_year,
    ac.total_households,
    pa.total_listings,
    pa.total_transactions,
    pa.price_min,
    pa.price_max,
    pa.price_avg,
    pa.deal_type_summary,
    COUNT(DISTINCT ca.area_sqm) as unique_areas_count,
    ac.created_at,
    ac.updated_at
FROM apartment_complexes ac
LEFT JOIN price_analysis pa ON ac.complex_id = pa.complex_id
LEFT JOIN complex_areas ca ON ac.complex_id = ca.complex_id
GROUP BY ac.complex_id, ac.complex_name, ac.address, ac.completion_year, 
         ac.total_households, pa.total_listings, pa.total_transactions,
         pa.price_min, pa.price_max, pa.price_avg, pa.deal_type_summary,
         ac.created_at, ac.updated_at;

-- 데이터 조회용 함수들
CREATE OR REPLACE FUNCTION get_complex_latest_analysis(input_complex_id VARCHAR)
RETURNS TABLE (
    complex_name VARCHAR,
    latest_price_min BIGINT,
    latest_price_max BIGINT,
    latest_price_avg BIGINT,
    latest_listings_count INTEGER,
    last_crawl_date TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ac.complex_name,
        pa.price_min,
        pa.price_max,
        pa.price_avg,
        pa.total_listings,
        cm.crawl_timestamp
    FROM apartment_complexes ac
    LEFT JOIN price_analysis pa ON ac.complex_id = pa.complex_id
    LEFT JOIN crawl_metadata cm ON ac.complex_id = cm.complex_id
    WHERE ac.complex_id = input_complex_id
    ORDER BY cm.crawl_timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;