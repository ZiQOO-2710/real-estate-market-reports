"""
네이버 부동산 단지별 모듈화 크롤러
Playwright MCP를 활용한 범용 단지 크롤링 모듈

사용법:
    crawler = NaverComplexCrawler()
    result = await crawler.crawl_complex(complex_url)
"""

import asyncio
import json
import csv
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
import re

class NaverComplexCrawler:
    """네이버 부동산 단지 크롤러 모듈"""
    
    def __init__(self, headless=False, screenshot=True):
        """
        Args:
            headless (bool): 헤드리스 모드 여부
            screenshot (bool): 스크린샷 저장 여부
        """
        self.browser = None
        self.page = None
        self.headless = headless
        self.screenshot = screenshot
        
    async def init_browser(self):
        """브라우저 초기화 (F12 차단 우회)"""
        playwright = await async_playwright().start()
        
        # 안티 디텍션 브라우저 설정
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-features=VizDisplayCompositor',
                '--disable-ipc-flooding-protection',
                '--disable-renderer-backgrounding',
                '--disable-backgrounding-occluded-windows',
                '--disable-client-side-phishing-detection',
                '--disable-component-extensions-with-background-pages',
                '--disable-default-apps',
                '--disable-extensions',
                '--disable-features=TranslateUI',
                '--disable-hang-monitor',
                '--disable-web-security',
                '--no-first-run',
                '--no-default-browser-check',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        self.page = await context.new_page()
        
        # 개발자도구 탐지 우회
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            delete window.console.debug;
            delete window.console.clear;
            
            Object.defineProperty(navigator, 'languages', {
                get: () => ['ko-KR', 'ko', 'en-US', 'en'],
            });
            
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
        """)
        
    async def extract_complex_basic_info(self, url):
        """단지 기본 정보 추출"""
        print(f"🔍 단지 기본 정보 추출: {url}")
        
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(5)
            
            # 단지명 추출 (URL에서도 추출)
            complex_id = self.extract_complex_id_from_url(url)
            
            basic_info = await self.page.evaluate("""
                () => {
                    const info = {};
                    
                    // 페이지 제목에서 단지명 추출
                    const title = document.title;
                    if (title && !title.includes('네이버페이')) {
                        info.complexName = title.split('|')[0].trim();
                    }
                    
                    // 다양한 셀렉터로 단지명 찾기
                    const nameSelectors = [
                        'h1.complex_title',
                        '.complex_name', 
                        '.title',
                        'h1',
                        '[class*="title"]',
                        '[class*="name"]'
                    ];
                    
                    for (const selector of nameSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && 
                            !element.textContent.includes('거래방식') &&
                            !element.textContent.includes('@naver')) {
                            info.complexName = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 주소 정보
                    const addressSelectors = [
                        '.complex_address',
                        '.address',
                        '[class*="address"]',
                        '[class*="location"]'
                    ];
                    
                    for (const selector of addressSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && 
                            !element.textContent.includes('@naver')) {
                            info.address = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 전체 텍스트에서 정보 추출
                    const allText = document.body.textContent;
                    
                    // 준공년도
                    const yearPatterns = [
                        /(19|20)\\d{2}년?\\s*준?공?/,
                        /(19|20)\\d{2}[\\./]\\d{1,2}/,
                        /준공\\s*(19|20)\\d{2}/
                    ];
                    
                    for (const pattern of yearPatterns) {
                        const match = allText.match(pattern);
                        if (match) {
                            info.completionYear = match[0];
                            break;
                        }
                    }
                    
                    // 세대수
                    const householdMatches = allText.match(/(\\d+)\\s*세대/);
                    if (householdMatches) {
                        info.totalHouseholds = householdMatches[1];
                    }
                    
                    // 면적 정보
                    const areaMatches = allText.match(/(\\d+\\.?\\d*)㎡/g);
                    if (areaMatches && areaMatches.length > 0) {
                        info.areas = [...new Set(areaMatches)].slice(0, 10);
                    }
                    
                    return info;
                }
            """)
            
            # URL에서 추출한 ID 추가
            basic_info['complex_id'] = complex_id
            basic_info['source_url'] = url
            
            return basic_info
            
        except Exception as e:
            print(f"❌ 기본 정보 추출 오류: {e}")
            return {'complex_id': self.extract_complex_id_from_url(url), 'source_url': url}
            
    def extract_complex_id_from_url(self, url):
        """URL에서 단지 ID 추출"""
        match = re.search(r'/complexes/(\d+)', url)
        return match.group(1) if match else 'unknown'
        
    async def extract_current_listings(self):
        """현재 매물 정보 추출"""
        print("🏠 현재 매물 정보 추출 중...")
        
        try:
            await self.page.wait_for_timeout(3000)
            
            listings = await self.page.evaluate("""
                () => {
                    const listings = [];
                    
                    // 매물 관련 셀렉터들
                    const listingSelectors = [
                        '.item_link',
                        '.article_item',
                        '.property_item',
                        '[class*="item"]',
                        '[class*="article"]',
                        '[class*="property"]',
                        '.list_item'
                    ];
                    
                    for (const selector of listingSelectors) {
                        const elements = document.querySelectorAll(selector);
                        
                        elements.forEach((element, index) => {
                            const text = element.textContent.trim();
                            
                            // 부동산 관련 키워드 필터링
                            if (text && (
                                text.includes('억') || 
                                text.includes('만원') ||
                                text.includes('전세') ||
                                text.includes('월세') ||
                                text.includes('매매') ||
                                text.includes('㎡') ||
                                text.includes('평') ||
                                text.includes('층')
                            ) && text.length > 20) {  // 최소 길이 조건
                                
                                // 상세 정보 추출
                                const priceMatch = text.match(/(\\d+)억\\s*(\\d+)?/);
                                const monthlyMatch = text.match(/월세\\s*(\\d+)/);
                                const areaMatch = text.match(/(\\d+\\.?\\d*)㎡/);
                                const floorMatch = text.match(/(\\d+)층/);
                                const typeMatch = text.match(/(매매|전세|월세)/);
                                
                                listings.push({
                                    index: index,
                                    selector: selector,
                                    text: text.substring(0, 300),  // 길이 제한
                                    price: priceMatch ? priceMatch[0] : null,
                                    monthly_rent: monthlyMatch ? monthlyMatch[0] : null,
                                    area: areaMatch ? areaMatch[0] : null,
                                    floor: floorMatch ? floorMatch[0] : null,
                                    deal_type: typeMatch ? typeMatch[0] : null,
                                    raw_text: text
                                });
                            }
                        });
                        
                        if (listings.length >= 30) break; // 최대 30개
                    }
                    
                    // 중복 제거 (텍스트 기준)
                    const unique_listings = [];
                    const seen_texts = new Set();
                    
                    for (const listing of listings) {
                        const short_text = listing.text.substring(0, 100);
                        if (!seen_texts.has(short_text)) {
                            seen_texts.add(short_text);
                            unique_listings.push(listing);
                        }
                    }
                    
                    return unique_listings.slice(0, 25); // 최대 25개 반환
                }
            """)
            
            print(f"📝 매물 정보 {len(listings)}개 추출")
            return listings
            
        except Exception as e:
            print(f"❌ 매물 추출 오류: {e}")
            return []
            
    async def extract_transaction_history(self):
        """실거래가 정보 추출"""
        print("💰 실거래가 정보 추출 중...")
        
        try:
            # 실거래가 탭 클릭 시도
            await self.page.wait_for_timeout(2000)
            
            tab_selectors = [
                'text="실거래가"',
                'text="거래"', 
                'text="실거래"',
                '[class*="deal"]',
                '[class*="transaction"]'
            ]
            
            for selector in tab_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        print(f"✅ 실거래가 탭 클릭 성공")
                        await self.page.wait_for_timeout(3000)
                        break
                except:
                    continue
                    
            # 실거래가 데이터 추출
            transactions = await self.page.evaluate("""
                () => {
                    const transactions = [];
                    const text = document.body.textContent;
                    
                    // 실거래가 패턴들
                    const patterns = [
                        // 날짜 + 가격 패턴
                        /\\d{4}[\\.\\/]\\d{1,2}[\\.\\/]\\d{1,2}.*?(\\d+)억\\s*(\\d+)?/g,
                        // 가격 + 면적 패턴  
                        /(\\d+)억\\s*(\\d+)?.*?(\\d+\\.?\\d*)㎡/g,
                        // 거래유형 + 가격
                        /(매매|전세).*?(\\d+)억/g,
                        // 층수 + 가격
                        /(\\d+)층.*?(\\d+)억/g
                    ];
                    
                    patterns.forEach((pattern, patternIndex) => {
                        let match;
                        let count = 0;
                        while ((match = pattern.exec(text)) !== null && count < 15) {
                            transactions.push({
                                pattern_type: patternIndex,
                                match_text: match[0],
                                context: text.substring(
                                    Math.max(0, match.index - 100), 
                                    Math.min(text.length, match.index + 200)
                                )
                            });
                            count++;
                        }
                    });
                    
                    // 테이블 데이터 추출
                    const tables = document.querySelectorAll('table, .table, [class*="table"]');
                    tables.forEach((table, tableIndex) => {
                        const tableText = table.textContent;
                        if ((tableText.includes('억') || tableText.includes('만원')) && 
                            tableText.length > 50) {
                            transactions.push({
                                type: 'table',
                                table_index: tableIndex,
                                content: tableText.substring(0, 800)
                            });
                        }
                    });
                    
                    return transactions.slice(0, 40); // 최대 40개
                }
            """)
            
            print(f"💸 실거래가 정보 {len(transactions)}개 추출")
            return transactions
            
        except Exception as e:
            print(f"❌ 실거래가 추출 오류: {e}")
            return []
            
    async def extract_comprehensive_data(self, url):
        """종합 데이터 추출"""
        print("📊 종합 데이터 추출 중...")
        
        try:
            # 스크린샷 저장
            if self.screenshot:
                complex_id = self.extract_complex_id_from_url(url)
                screenshot_path = f"data/output/screenshot_{complex_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                Path("data/output").mkdir(parents=True, exist_ok=True)
                await self.page.screenshot(path=screenshot_path, full_page=True)
                print(f"📸 스크린샷 저장: {screenshot_path}")
            else:
                screenshot_path = None
                
            # 상세 정보 추출
            detailed_info = await self.page.evaluate("""
                () => {
                    const info = {
                        page_title: document.title,
                        url: window.location.href,
                        extracted_at: new Date().toISOString()
                    };
                    
                    const fullText = document.body.textContent;
                    
                    // 모든 가격 정보 추출
                    const pricePatterns = [
                        /\\d+억\\s*\\d*천?만?원?/g,
                        /\\d+천만원/g,
                        /\\d+만원/g,
                        /월세\\s*\\d+만?원?/g,
                        /전세\\s*\\d+억?\\d*천?만?원?/g,
                        /매매\\s*\\d+억?\\d*천?만?원?/g
                    ];
                    
                    info.all_prices = [];
                    pricePatterns.forEach(pattern => {
                        const matches = fullText.match(pattern) || [];
                        info.all_prices.push(...matches);
                    });
                    
                    // 중복 제거
                    info.all_prices = [...new Set(info.all_prices)];
                    
                    // 면적 정보
                    const areaMatches = fullText.match(/\\d+\\.?\\d*㎡/g) || [];
                    info.areas = [...new Set(areaMatches)];
                    
                    // 층수 정보
                    const floorMatches = fullText.match(/\\d+층/g) || [];
                    info.floors = [...new Set(floorMatches)].slice(0, 15);
                    
                    // 거래유형
                    const dealMatches = fullText.match(/(매매|전세|월세)/g) || [];
                    info.deal_types = [...new Set(dealMatches)];
                    
                    return info;
                }
            """)
            
            detailed_info['screenshot_path'] = screenshot_path
            return detailed_info
            
        except Exception as e:
            print(f"❌ 종합 데이터 추출 오류: {e}")
            return {'screenshot_path': None}
            
    def analyze_price_data(self, listings, transactions, detailed_info):
        """가격 데이터 분석"""
        analysis = {
            'listing_prices': [],
            'transaction_prices': [],
            'price_range': {'min': 0, 'max': 0},
            'avg_price': 0,
            'deal_type_count': {},
            'area_price_ratio': []
        }
        
        try:
            # 매물 가격 분석
            for listing in listings:
                if listing.get('price'):
                    price_text = listing['price']
                    # 억 단위로 변환
                    match = re.search(r'(\d+)억\s*(\d+)?', price_text)
                    if match:
                        price = int(match.group(1)) * 10000  # 만원 단위
                        if match.group(2):
                            price += int(match.group(2)) * 1000
                        analysis['listing_prices'].append(price)
                        
                # 거래유형 카운트
                deal_type = listing.get('deal_type')
                if deal_type:
                    analysis['deal_type_count'][deal_type] = analysis['deal_type_count'].get(deal_type, 0) + 1
                    
            # 가격 범위 계산
            if analysis['listing_prices']:
                analysis['price_range']['min'] = min(analysis['listing_prices'])
                analysis['price_range']['max'] = max(analysis['listing_prices'])
                analysis['avg_price'] = sum(analysis['listing_prices']) / len(analysis['listing_prices'])
                
        except Exception as e:
            print(f"⚠️ 가격 분석 오류: {e}")
            
        return analysis
        
    async def save_complex_data(self, complex_id, basic_info, listings, transactions, detailed_info, analysis):
        """단지 데이터 저장"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        Path("data/output").mkdir(parents=True, exist_ok=True)
        
        # 종합 데이터 구성
        comprehensive_data = {
            'complex_basic_info': basic_info,
            'current_listings': listings,
            'transaction_history': transactions,
            'detailed_analysis': detailed_info,
            'price_analysis': analysis,
            'crawl_metadata': {
                'complex_id': complex_id,
                'crawled_at': datetime.now().isoformat(),
                'method': 'playwright_mcp_modular',
                'total_listings': len(listings),
                'total_transactions': len(transactions),
                'total_prices': len(detailed_info.get('all_prices', []))
            }
        }
        
        # JSON 파일 저장
        json_file = f"data/output/complex_{complex_id}_comprehensive_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(comprehensive_data, f, ensure_ascii=False, indent=2)
            
        # CSV 요약 저장
        csv_file = f"data/output/complex_{complex_id}_summary_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'complex_id', 'complex_name', 'address', 'completion_year', 'households',
                'total_listings', 'total_transactions', 'price_min', 'price_max', 'price_avg',
                'deal_types', 'areas_count', 'floors_count', 'source_url', 'screenshot_path'
            ])
            
            deal_types_str = ', '.join(analysis['deal_type_count'].keys()) if analysis['deal_type_count'] else '정보없음'
            
            writer.writerow([
                complex_id,
                basic_info.get('complexName', '정보없음'),
                basic_info.get('address', '정보없음'),
                basic_info.get('completionYear', '정보없음'),
                basic_info.get('totalHouseholds', '정보없음'),
                len(listings),
                len(transactions),
                analysis['price_range']['min'] if analysis['listing_prices'] else 0,
                analysis['price_range']['max'] if analysis['listing_prices'] else 0,
                round(analysis['avg_price']) if analysis['avg_price'] > 0 else 0,
                deal_types_str,
                len(detailed_info.get('areas', [])),
                len(detailed_info.get('floors', [])),
                basic_info.get('source_url', ''),
                detailed_info.get('screenshot_path', '')
            ])
            
        return {
            'json_file': json_file,
            'csv_file': csv_file,
            'screenshot': detailed_info.get('screenshot_path')
        }
        
    async def crawl_complex(self, complex_url, complex_name=None):
        """
        단지 크롤링 메인 함수
        
        Args:
            complex_url (str): 네이버 부동산 단지 URL
            complex_name (str): 단지명 (선택사항)
            
        Returns:
            dict: 크롤링 결과 및 파일 경로
        """
        try:
            await self.init_browser()
            
            complex_id = self.extract_complex_id_from_url(complex_url)
            display_name = complex_name or f"단지_{complex_id}"
            
            print(f"\n🏠 {display_name} 크롤링 시작!")
            print(f"🎯 URL: {complex_url}")
            
            # 1. 기본 정보 추출
            basic_info = await self.extract_complex_basic_info(complex_url)
            
            # 2. 현재 매물 추출
            listings = await self.extract_current_listings()
            
            # 3. 실거래가 추출
            transactions = await self.extract_transaction_history()
            
            # 4. 종합 데이터 추출
            detailed_info = await self.extract_comprehensive_data(complex_url)
            
            # 5. 가격 분석
            analysis = self.analyze_price_data(listings, transactions, detailed_info)
            
            # 6. 데이터 저장
            file_paths = await self.save_complex_data(
                complex_id, basic_info, listings, transactions, detailed_info, analysis
            )
            
            # 7. 결과 요약
            print(f"\n🎉 {display_name} 크롤링 완료!")
            print(f"📊 수집 결과:")
            print(f"  🏢 단지ID: {complex_id}")
            print(f"  🏠 매물: {len(listings)}개")
            print(f"  💰 거래기록: {len(transactions)}개")
            print(f"  📋 가격정보: {len(detailed_info.get('all_prices', []))}개")
            
            if analysis['listing_prices']:
                print(f"  💵 가격범위: {analysis['price_range']['min']:,}~{analysis['price_range']['max']:,}만원")
                print(f"  📈 평균가격: {analysis['avg_price']:,.0f}만원")
                
            if analysis['deal_type_count']:
                print(f"  🏷️ 거래유형: {', '.join(analysis['deal_type_count'].keys())}")
                
            return {
                'success': True,
                'complex_id': complex_id,
                'complex_name': basic_info.get('complexName', display_name),
                'data_summary': {
                    'listings_count': len(listings),
                    'transactions_count': len(transactions),
                    'prices_count': len(detailed_info.get('all_prices', [])),
                    'price_range': analysis['price_range'],
                    'avg_price': analysis['avg_price']
                },
                'files': file_paths
            }
            
        except Exception as e:
            print(f"❌ {display_name} 크롤링 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'complex_id': self.extract_complex_id_from_url(complex_url)
            }
            
        finally:
            if self.browser:
                await self.browser.close()

# 사용 예시 함수들
async def crawl_single_complex(url, name=None, headless=False):
    """단일 단지 크롤링"""
    crawler = NaverComplexCrawler(headless=headless, screenshot=True)
    return await crawler.crawl_complex(url, name)

async def crawl_multiple_complexes(complex_list, headless=False):
    """
    여러 단지 순차 크롤링
    
    Args:
        complex_list (list): [{'url': 'URL', 'name': '단지명'}, ...] 형식의 리스트
        headless (bool): 헤드리스 모드 여부
        
    Returns:
        list: 각 단지별 크롤링 결과
    """
    results = []
    
    for i, complex_info in enumerate(complex_list, 1):
        print(f"\n🔄 [{i}/{len(complex_list)}] 크롤링 진행 중...")
        
        crawler = NaverComplexCrawler(headless=headless, screenshot=True)
        result = await crawler.crawl_complex(
            complex_info['url'], 
            complex_info.get('name')
        )
        results.append(result)
        
        # 요청 간격 (너무 빠른 연속 요청 방지)
        if i < len(complex_list):
            print("⏱️ 잠시 대기 중...")
            await asyncio.sleep(5)
            
    return results

# 메인 실행 함수
async def main():
    """테스트 실행"""
    # 정든한진6차 테스트
    test_url = "https://new.land.naver.com/complexes/2592?ms=37.36286,127.115578,17&a=APT:ABYG:JGC:PRE&e=RETAIL"
    
    print("🚀 네이버 부동산 모듈화 크롤러 테스트")
    result = await crawl_single_complex(test_url, "정든한진6차", headless=False)
    
    if result['success']:
        print(f"\n✅ 테스트 성공!")
        print(f"📄 생성된 파일:")
        for key, path in result['files'].items():
            if path:
                print(f"  {key}: {path}")
    else:
        print(f"❌ 테스트 실패: {result['error']}")

if __name__ == "__main__":
    asyncio.run(main())