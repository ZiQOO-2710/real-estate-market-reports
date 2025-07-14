# Supabase 데이터베이스 설정 가이드

네이버 부동산 크롤링 데이터를 Supabase에 저장하는 완전한 가이드입니다.

## 🎯 개요

크롤링된 네이버 부동산 데이터를 구조화된 PostgreSQL 데이터베이스에 저장하여:
- 체계적인 데이터 관리
- SQL을 통한 고급 분석
- API를 통한 데이터 접근
- 실시간 데이터 동기화

## 📊 데이터베이스 스키마

### 주요 테이블 구조

1. **apartment_complexes** - 아파트 단지 기본 정보
   - complex_id, complex_name, address, completion_year
   - total_households, source_url, coordinates

2. **current_listings** - 현재 매물 정보  
   - deal_type (매매/전세/월세), price_amount, area_sqm
   - floor_info, description

3. **transaction_history** - 실거래가 정보
   - transaction_type, price_amount, transaction_date
   - area_sqm, floor_info

4. **price_analysis** - 가격 분석 데이터
   - price_min, price_max, price_avg
   - deal_type_summary, total_listings

## 🚀 설정 단계

### 1. Supabase 프로젝트 생성

1. [Supabase](https://supabase.com)에 회원가입
2. 새 프로젝트 생성
3. 프로젝트 설정에서 다음 정보 확인:
   - **Project URL**: `https://[project-id].supabase.co`
   - **API Key**: `Settings > API > anon/public key`

### 2. 데이터베이스 스키마 생성

Supabase 대시보드에서:

1. **SQL Editor** 메뉴로 이동
2. `supabase_schema.sql` 파일 내용을 복사하여 붙여넣기
3. **RUN** 버튼 클릭하여 테이블 생성

```sql
-- 또는 터미널에서 실행
psql -h [db-host] -U postgres -d postgres -f supabase_schema.sql
```

### 3. 환경변수 설정

터미널에서 다음 환경변수를 설정:

```bash
# Linux/Mac
export SUPABASE_URL='https://your-project-id.supabase.co'
export SUPABASE_KEY='your-anon-key'

# Windows
set SUPABASE_URL=https://your-project-id.supabase.co
set SUPABASE_KEY=your-anon-key
```

### 4. 의존성 설치

```bash
pip install supabase==2.3.4 postgrest==0.13.2
```

### 5. 연결 테스트

```bash
python supabase_setup.py
```

## 📥 데이터 삽입

### 자동 데이터 삽입

크롤링된 모든 JSON 파일을 자동으로 처리:

```bash
python supabase_data_processor.py
```

### 수동 데이터 삽입

특정 파일만 처리:

```python
from supabase_data_processor import SupabaseDataProcessor

processor = SupabaseDataProcessor(SUPABASE_URL, SUPABASE_KEY)
success = await processor.insert_complex_data('data/output/complex_2592_comprehensive.json')
```

## 🔍 데이터 조회

### 기본 조회

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 모든 단지 조회
complexes = supabase.table('apartment_complexes').select('*').execute()

# 특정 단지의 매물 조회
listings = supabase.table('current_listings').select('*').eq('complex_id', '2592').execute()

# 가격 범위로 필터링
expensive_listings = supabase.table('current_listings').select('*').gte('price_amount', 100000).execute()
```

### 고급 쿼리

```sql
-- 단지별 평균 가격 (SQL Editor에서 실행)
SELECT 
    ac.complex_name,
    AVG(cl.price_amount) as avg_price,
    COUNT(cl.id) as listing_count
FROM apartment_complexes ac
JOIN current_listings cl ON ac.complex_id = cl.complex_id
WHERE cl.deal_type = '매매'
GROUP BY ac.complex_id, ac.complex_name
ORDER BY avg_price DESC;

-- 면적대별 가격 분석
SELECT 
    CASE 
        WHEN area_sqm < 60 THEN '소형(60㎡ 미만)'
        WHEN area_sqm < 85 THEN '중소형(60-85㎡)'
        WHEN area_sqm < 135 THEN '중형(85-135㎡)'
        ELSE '대형(135㎡ 이상)'
    END as area_type,
    AVG(price_amount) as avg_price,
    COUNT(*) as count
FROM current_listings 
WHERE area_sqm IS NOT NULL 
GROUP BY area_type
ORDER BY avg_price;
```

## 📊 데이터 분석 예시

### Python으로 분석

```python
import pandas as pd

# 데이터 가져오기
response = supabase.table('current_listings').select('*').execute()
df = pd.DataFrame(response.data)

# 거래유형별 평균 가격
avg_prices = df.groupby('deal_type')['price_amount'].mean()
print(avg_prices)

# 면적별 가격 분포
df['price_per_sqm'] = df['price_amount'] / df['area_sqm'] * 10000  # ㎡당 가격
print(df[['area_sqm', 'price_per_sqm']].describe())
```

## 🔐 보안 설정

### Row Level Security (RLS) 활성화

```sql
-- 테이블별 RLS 활성화
ALTER TABLE apartment_complexes ENABLE ROW LEVEL SECURITY;
ALTER TABLE current_listings ENABLE ROW LEVEL SECURITY;

-- 읽기 전용 정책 생성
CREATE POLICY "Enable read access for all users" ON apartment_complexes
    FOR SELECT USING (true);
```

### API 키 관리

- **anon/public key**: 클라이언트용 (읽기 전용)
- **service_role key**: 서버용 (모든 권한)
- 프로덕션에서는 service_role key 사용 권장

## 🚨 주의사항

### 데이터 품질

1. **중복 데이터**: `complex_id`를 기준으로 upsert 처리
2. **NULL 값**: 파싱 실패시 NULL로 저장
3. **데이터 타입**: 가격은 만원 단위 정수로 통일

### 성능 최적화

1. **인덱스**: 주요 검색 컬럼에 인덱스 생성됨
2. **배치 처리**: 대량 데이터는 배치로 삽입
3. **연결 풀링**: 동시 연결 수 제한

## 📈 실제 데이터 예시

### 테스트 결과 (정든한진6차)

- **단지ID**: 2592
- **매물 수**: 25개
- **실거래가**: 40개 
- **가격 범위**: 8억~22억원
- **평균 가격**: 13.8억원
- **거래유형**: 매매, 전세

### 성공적인 파싱 예시

```
가격 파싱:
'14억 5,000' -> 145,000만원
'8억' -> 80,000만원  
'3천만원' -> 3,000만원

면적 파싱:
'121.35㎡' -> 121.35㎡ (36.71평)
'37평' -> 122.31㎡ (37.00평)
```

## 🔧 트러블슈팅

### 일반적인 문제

1. **연결 오류**
   ```bash
   # URL과 키 확인
   echo $SUPABASE_URL
   echo $SUPABASE_KEY
   ```

2. **스키마 생성 실패**
   - 권한 확인: service_role 키 사용
   - SQL 문법 확인: PostgreSQL 문법 준수

3. **데이터 삽입 실패**
   - JSON 파일 형식 확인
   - 필수 필드 누락 여부 확인

### 디버깅

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 상세 로그로 문제 추적
processor = SupabaseDataProcessor(url, key)
```

## 🎯 다음 단계

1. **실시간 업데이트**: 크롤러에 Supabase 연동 추가
2. **대시보드**: Grafana/Metabase로 시각화
3. **API 서버**: FastAPI로 REST API 구축
4. **알림 시스템**: 가격 변동 알림 구현

---

💡 **도움이 필요하신가요?**
- Supabase 공식 문서: https://supabase.com/docs
- 프로젝트 이슈: GitHub Issues
- 테스트 실행: `python simple_test.py`