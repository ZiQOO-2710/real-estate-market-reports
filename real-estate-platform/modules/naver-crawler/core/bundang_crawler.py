"""
성남시 분당구 아파트 5개 단지 테스트 크롤러 v2
실제 아파트 매물 API 찾기
"""

import asyncio
import aiohttp
import json
import csv
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

class BundangApartmentCrawlerV2:
    """분당구 아파트 매물 정보 크롤러 v2"""
    
    def __init__(self):
        self.session = None
        self.browser = None
        self.page = None
        # 분당구 검색 URL
        self.target_url = "https://new.land.naver.com/complexes?ms=37.3595,127.1052,14&a=APT&b=A1:A2:B1:B2:B3"
        self.collected_apartments = []
        self.max_apartments = 5
        
    async def init_browser(self):
        """브라우저 초기화"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=False)
        context = await self.browser.new_context()
        self.page = await context.new_page()
        
        # 네트워크 요청 모니터링 - 아파트 관련 API만 필터링
        self.api_calls = []
        
        async def handle_response(response):
            url = response.url.lower()
            
            # 아파트 관련 API 호출만 감지
            apartment_api_keywords = [
                'complexes',
                'complex',
                'apartment', 
                'apt',
                'articles',
                'article',
                'real',
                'estate',
                'items',
                'list'
            ]
            
            if any(keyword in url for keyword in apartment_api_keywords) and response.status == 200:
                try:
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        data = await response.json()
                        self.api_calls.append({
                            'url': response.url,
                            'method': response.request.method,
                            'status': response.status,
                            'data': data
                        })
                        print(f"🏠 아파트 API 감지: {response.url}")
                except Exception as e:
                    print(f"API 파싱 오류: {e}")
                    
        self.page.on('response', handle_response)
        
    async def search_apartments_step_by_step(self):
        """단계적으로 아파트 검색"""
        print(f"🔍 분당구 아파트 검색 시작")
        
        # 1단계: 기본 페이지 로드
        print("1️⃣ 네이버 랜드 메인 페이지 로드")
        await self.page.goto("https://new.land.naver.com/", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # 2단계: 검색창에 '분당구' 입력
        print("2️⃣ 분당구 검색")
        try:
            # 검색창 찾기
            search_input = await self.page.wait_for_selector('input[placeholder*="검색"], input[placeholder*="지역"], input.search_input, #search_input', timeout=10000)
            await search_input.fill('성남시 분당구')
            await asyncio.sleep(1)
            
            # Enter 키 또는 검색 버튼 클릭
            await search_input.press('Enter')
            await asyncio.sleep(5)
            
        except Exception as e:
            print(f"검색 입력 오류: {e}")
            # 직접 URL로 이동
            await self.page.goto(self.target_url, wait_until="networkidle")
            await asyncio.sleep(5)
        
        # 3단계: 아파트 필터 적용
        print("3️⃣ 아파트 필터 적용")
        try:
            # 아파트 체크박스나 필터 찾기
            apt_filter = await self.page.query_selector('label[for*="APT"], input[value*="APT"], .filter_item:has-text("아파트")')
            if apt_filter:
                await apt_filter.click()
                await asyncio.sleep(3)
        except Exception as e:
            print(f"필터 적용 오류: {e}")
        
        # 4단계: 페이지에서 아파트 목록 확인
        print("4️⃣ 아파트 목록 확인")
        await asyncio.sleep(5)  # 추가 로딩 대기
        
        # 5단계: 더 구체적인 아파트 요소 찾기
        apartment_elements = await self.page.evaluate("""
            () => {
                const apartments = [];
                
                // 다양한 아파트 요소 선택자
                const selectors = [
                    '.complex_link',
                    '.item_complex',
                    '.complex_item',
                    '[data-complex-no]',
                    '.list_contents .item',
                    '.complex_info',
                    '.item_link',
                    '.complex_title',
                    'a[href*="complex"]'
                ];
                
                console.log('아파트 요소 검색 시작');
                
                for (const selector of selectors) {
                    const elements = document.querySelectorAll(selector);
                    console.log(`${selector}: ${elements.length}개 발견`);
                    
                    for (let i = 0; i < Math.min(elements.length, 10); i++) {
                        const el = elements[i];
                        const text = el.textContent.trim();
                        
                        if (text && text.length > 10 && (
                            text.includes('아파트') || 
                            text.includes('단지') ||
                            text.includes('억') ||
                            text.includes('만원') ||
                            text.includes('㎡') ||
                            text.includes('세대')
                        )) {
                            apartments.push({
                                selector: selector,
                                text: text.substring(0, 200),
                                href: el.href || el.querySelector('a')?.href,
                                complexNo: el.getAttribute('data-complex-no') || 
                                         el.querySelector('[data-complex-no]')?.getAttribute('data-complex-no')
                            });
                        }
                    }
                }
                
                console.log(`총 ${apartments.length}개 아파트 요소 발견`);
                return apartments;
            }
        """)
        
        return apartment_elements
        
    async def extract_apartment_data_from_apis(self):
        """API 호출에서 아파트 데이터 추출"""
        apartment_list = []
        
        print(f"📡 {len(self.api_calls)}개 API 응답 분석 중...")
        
        for i, api_call in enumerate(self.api_calls, 1):
            try:
                print(f"  {i}. {api_call['url']}")
                data = api_call['data']
                extracted = self.parse_apartment_data(data, api_call['url'])
                if extracted:
                    apartment_list.extend(extracted)
                    print(f"    ✅ {len(extracted)}개 아파트 추출")
                    
                    # 5개 제한
                    if len(apartment_list) >= self.max_apartments:
                        apartment_list = apartment_list[:self.max_apartments]
                        break
                else:
                    print(f"    ❌ 아파트 데이터 없음")
                        
            except Exception as e:
                print(f"    ❌ 파싱 오류: {e}")
                continue
                
        return apartment_list
        
    def parse_apartment_data(self, data, source_url):
        """API 데이터에서 아파트 정보 파싱 - 더 상세한 분석"""
        apartments = []
        
        try:
            print(f"    데이터 타입: {type(data)}")
            
            if isinstance(data, dict):
                print(f"    키 목록: {list(data.keys())}")
                
                # 모든 키-값 쌍 검사
                for key, value in data.items():
                    if isinstance(value, list) and value:
                        print(f"      '{key}': {len(value)}개 항목")
                        
                        # 첫 번째 항목 구조 확인
                        if value and isinstance(value[0], dict):
                            sample_keys = list(value[0].keys())
                            print(f"        샘플 키: {sample_keys[:10]}")
                        
                        for item in value[:10]:  # 최대 10개만 검사
                            if isinstance(item, dict):
                                apt_info = self.extract_apartment_info(item)
                                if apt_info:
                                    apt_info['source_api'] = source_url
                                    apt_info['data_key'] = key
                                    apartments.append(apt_info)
                                    
                                    if len(apartments) >= self.max_apartments:
                                        return apartments
                                        
            elif isinstance(data, list):
                print(f"    리스트 길이: {len(data)}")
                for item in data[:10]:
                    if isinstance(item, dict):
                        apt_info = self.extract_apartment_info(item)
                        if apt_info:
                            apt_info['source_api'] = source_url
                            apartments.append(apt_info)
                            
                            if len(apartments) >= self.max_apartments:
                                return apartments
                            
        except Exception as e:
            print(f"    파싱 오류: {e}")
            
        return apartments
        
    def extract_apartment_info(self, item):
        """개별 아파트 정보 추출 - 더 포괄적"""
        if not isinstance(item, dict):
            return None
            
        apartment = {}
        
        # 모든 가능한 필드명 매핑
        field_mapping = {
            'name': [
                'complexName', 'aptName', 'name', 'buildingName', 'realEstateTypeName',
                'complexNm', 'aptNm', 'buildingNm', 'title', 'complexTitle'
            ],
            'address': [
                'address', 'cortarAddress', 'roadAddress', 'jibunAddress', 'cortarName',
                'addr', 'roadAddr', 'jibunAddr', 'location', 'sido', 'sigungu', 'dong'
            ],
            'price': [
                'dealPrice', 'price', 'dealAmount', 'rentPrice', 'prc', 'avgPrice',
                'minPrice', 'maxPrice', 'pricePerSquare', 'averagePrice'
            ],
            'area': [
                'exclusiveArea', 'supplyArea', 'area', 'space', 'totalArea',
                'exclusiveAreaAvg', 'supplyAreaAvg', 'areaRange'
            ],
            'build_year': [
                'buildYear', 'useApproveYmd', 'constructionYear', 'approveDate',
                'completionDate', 'buildYmd'
            ],
            'floor': [
                'floor', 'floorInfo', 'totalFloor', 'maxFloor', 'minFloor',
                'floorRange', 'buildingFloor'
            ],
            'id': [
                'complexNo', 'itemId', 'articleNo', 'realEstateId', 'complexId',
                'id', 'no', 'code'
            ],
            'households': [
                'totalHouseholds', 'households', 'totalDong', 'totalUnit',
                'householdCount', 'unitCount'
            ]
        }
        
        # 필드 추출
        for field, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in item and item[key] is not None:
                    apartment[field] = str(item[key])
                    break
        
        # 기본 정보가 있는지 확인
        has_basic_info = apartment.get('name') or apartment.get('address') or apartment.get('id')
        
        if has_basic_info:
            apartment['collect_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            apartment['region'] = '성남시 분당구'
            
            # 원본 데이터 샘플 저장
            important_fields = {}
            for key, value in item.items():
                if any(keyword in key.lower() for keyword in ['name', 'addr', 'price', 'area', 'year', 'complex']):
                    important_fields[key] = value
            
            apartment['raw_sample'] = json.dumps(important_fields, ensure_ascii=False)[:200]
            
            return apartment
            
        return None
        
    async def save_apartment_data(self, apartments):
        """아파트 데이터 저장"""
        if not apartments:
            print("💾 저장할 아파트 데이터가 없습니다.")
            return None
            
        filename = f"bundang_apartments_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = Path("data/output") / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        all_fields = set()
        for apt in apartments:
            all_fields.update(apt.keys())
            
        all_fields = sorted(list(all_fields))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fields)
            writer.writeheader()
            writer.writerows(apartments)
            
        print(f"💾 데이터 저장: {filepath}")
        return filepath
        
    async def run_test(self):
        """테스트 실행"""
        try:
            await self.init_browser()
            
            print(f"🏠 성남시 분당구 아파트 크롤링 테스트 v2")
            
            # 단계적 검색
            page_elements = await self.search_apartments_step_by_step()
            print(f"🔍 페이지 요소: {len(page_elements)}개 발견")
            
            # API 데이터 추출
            api_apartments = await self.extract_apartment_data_from_apis()
            print(f"📡 API 아파트: {len(api_apartments)}개 추출")
            
            if api_apartments:
                filepath = await self.save_apartment_data(api_apartments)
                
                print(f"\n📋 추출된 분당구 아파트:")
                for i, apt in enumerate(api_apartments, 1):
                    print(f"\n{i}. {apt.get('name', '이름미상')}")
                    print(f"   주소: {apt.get('address', '주소미상')}")
                    print(f"   가격: {apt.get('price', '가격미상')}")
                    print(f"   면적: {apt.get('area', '면적미상')}")
                    print(f"   ID: {apt.get('id', 'ID미상')}")
                    
                print(f"\n✅ 성공! 총 {len(api_apartments)}개 수집")
                return filepath
            else:
                print(f"\n📊 결과 요약:")
                print(f"- API 호출: {len(self.api_calls)}개")
                print(f"- 페이지 요소: {len(page_elements)}개")
                
                if page_elements:
                    print(f"\n페이지 요소 샘플:")
                    for i, elem in enumerate(page_elements[:3], 1):
                        print(f"  {i}. {elem['text'][:100]}...")
                
                return None
                
        finally:
            if self.browser:
                await self.browser.close()

async def main():
    """메인 함수"""
    crawler = BundangApartmentCrawlerV2()
    result = await crawler.run_test()
    
    if result:
        print(f"\n🎉 테스트 완료! 파일: {result}")
    else:
        print(f"\n🔍 추가 분석 필요")

if __name__ == "__main__":
    asyncio.run(main())