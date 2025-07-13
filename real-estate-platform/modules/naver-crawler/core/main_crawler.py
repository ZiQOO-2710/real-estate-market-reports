"""
네이버 부동산 크롤러 메인 모듈
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import argparse

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import pandas as pd
from loguru import logger

# 프로젝트 루트 경로 설정
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import (
    NAVER_REAL_ESTATE_BASE_URL,
    CRAWLING_CONFIG,
    DATA_CONFIG,
    LOG_CONFIG,
    REGIONS,
    DATA_FIELDS,
    USER_AGENTS
)
import os
from src.parser import DataParser
from src.storage import DataStorage
from src.utils import setup_directories, get_random_user_agent
from src.stealth import StealthCrawler
from src.rate_limiter import RateLimiter


class NaverRealEstateCrawler:
    """네이버 부동산 크롤러 클래스"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None
        self.data_parser = DataParser()
        self.data_storage = DataStorage()
        self.stealth = StealthCrawler()
        self.rate_limiter = RateLimiter(CRAWLING_CONFIG)
        self.setup_logging()
        setup_directories()
        
    def setup_logging(self):
        """로깅 설정"""
        log_dir = DATA_CONFIG["log_dir"]
        log_file = log_dir / f"crawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logger.remove()
        logger.add(
            log_file,
            level=LOG_CONFIG["level"],
            format=LOG_CONFIG["format"],
            rotation=LOG_CONFIG["rotation"],
            retention=LOG_CONFIG["retention"],
            encoding="utf-8"
        )
        logger.add(
            sys.stdout,
            level=LOG_CONFIG["level"],
            format=LOG_CONFIG["format"]
        )
        
    async def init_browser(self) -> None:
        """브라우저 초기화"""
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=CRAWLING_CONFIG["headless"],
            args=[
                '--no-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--disable-extensions',
                '--no-first-run',
                '--disable-default-apps',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-background-networking',
            ]
        )
        
        # 스텔스 브라우저 컨텍스트 설정
        self.context = await self.stealth.setup_stealth_browser(self.browser)
        self.page = await self.context.new_page()
        
        # 스텔스 페이지 설정
        await self.stealth.setup_stealth_page(self.page)
        
        # 타임아웃 설정
        self.page.set_default_timeout(CRAWLING_CONFIG["timeout"] * 1000)
        
        logger.info("스텔스 브라우저 초기화 완료")
        
    async def close_browser(self) -> None:
        """브라우저 종료"""
        if self.browser:
            await self.browser.close()
            logger.info("브라우저 종료 완료")

    async def crawl_by_api(self, url: str) -> List[Dict]:
        """주어진 URL에서 네트워크 탭을 통해 API 데이터를 크롤링"""
        logger.info(f"API 크롤링 시작: {url}")
        all_data = []
        
        try:
            # API 응답을 저장할 리스트
            api_responses = []

            # 요청 가로채기 설정
            # Playwright의 route 기능을 사용하여 특정 URL 패턴의 응답을 가로챕니다.
            # 네이버 부동산의 매물 데이터는 보통 JSON 형태로 제공됩니다.
            # 'complexes/articles' 또는 'articles/list'와 같은 패턴을 예상합니다.
            await self.page.route("**/*", lambda route: asyncio.ensure_future(self._handle_api_response(route, api_responses)))

            logger.info(f"페이지 이동 중: {url}")
            await self.page.goto(url, wait_until="networkidle")
            
            # 페이지 로딩 대기 및 API 응답 수집을 위한 충분한 시간 제공
            await asyncio.sleep(10) # API 호출이 완료될 시간을 충분히 줍니다.

            # 수집된 API 응답 처리
            for response_data in api_responses:
                if isinstance(response_data, list):
                    all_data.extend(response_data)
                elif isinstance(response_data, dict):
                    all_data.append(response_data)
            
            logger.info(f"API 크롤링 완료: 총 {len(all_data)}개 데이터 수집")

            # 캡처된 JSON 응답을 임시 파일로 저장
            temp_json_path = DATA_CONFIG["log_dir"] / f"captured_api_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(temp_json_path, 'w', encoding='utf-8') as f:
                json.dump(api_responses, f, ensure_ascii=False, indent=4)
            logger.info(f"캡처된 API 응답이 임시 파일에 저장되었습니다: {temp_json_path}")

            return all_data

        except Exception as e:
            logger.error(f"API 크롤링 중 오류 발생 ({url}): {e}")
            return []

    async def _handle_api_response(self, route, api_responses):
        """API 응답을 처리하고 데이터를 저장"""
        try:
            response = await route.fetch()
            if response.status == 200 and "application/json" in response.headers.get("content-type", ""):
                try:
                    json_data = await response.json()
                except Exception as json_e:
                    logger.warning(f"JSON 파싱 실패 ({route.request.url}): {json_e}")
                    await route.continue_()
                    return
                logger.info(f"API 응답 가로챔: {route.request.url} (데이터 크기: {len(str(json_data))} bytes)")
                api_responses.append({"url": route.request.url, "data": json_data})
            await route.continue_()
        except Exception as e:
            logger.warning(f"API 응답 처리 중 오류: {e}")
            await route.abort() # 오류 발생 시 요청 중단
            
    async def navigate_to_region(self, region_code: str) -> bool:
        """특정 지역으로 이동"""
        try:
            # 새로운 네이버 부동산 complexes 페이지로 이동
            # 지역 코드를 기반으로 검색 파라미터 구성
            url = f"{NAVER_REAL_ESTATE_BASE_URL}/complexes?cortarNo={region_code}&rletTypeCd=A01&tradTpCd=A1"
            
            logger.info(f"페이지 이동 중: {url}")
            await self.page.goto(url, wait_until="networkidle")
            
            # 페이지 로딩 대기 (SPA이므로 더 길게)
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(3)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(10)  # JavaScript 렌더링 완료 대기
            
            # 동적 콘텐츠 로딩 확인
            for i in range(5):
                content_count = await self.page.evaluate("document.querySelectorAll('div').length")
                logger.info(f"페이지 로딩 확인 {i+1}/5: div 요소 {content_count}개")
                if content_count > 500:  # 충분한 콘텐츠가 로드됨
                    break
                await asyncio.sleep(2)
            
            # 매물 목록이 로드될 때까지 대기 (예: 특정 매물 아이템의 셀렉터)
            try:
                await self.page.wait_for_selector(".item_list_search", timeout=30000) # 30초 대기
                logger.info("매물 목록 컨테이너 로드 확인")
            except Exception as e:
                logger.warning(f"매물 목록 컨테이너 로드 실패: {e}")
                # 실패 시 스크린샷 및 HTML 저장 (디버깅용)
                await self.page.screenshot(path=f"screenshots/debug_no_items_{region_code}.png")
                html_content = await self.page.content()
                with open(f"screenshots/debug_no_items_{region_code}.html", 'w', encoding='utf-8') as f:
                    f.write(html_content)
                return False
            
            # 스크린샷 저장 (디버깅용)
            screenshot_dir = Path("screenshots")
            screenshot_dir.mkdir(exist_ok=True)
            await self.page.screenshot(path=f"screenshots/debug_region_{region_code}.png")
            
            return True
            
        except Exception as e:
            logger.error(f"지역 이동 실패: {e}")
            return False
            
    async def get_article_links(self) -> List[str]:
        """매물 링크 수집"""
        try:
            # 매물 목록 컨테이너 대기
            # 디버깅을 위해 현재 페이지의 HTML 구조 확인
            await self.page.wait_for_load_state("networkidle")
            
            # 네이버 페이 부동산의 실제 구조에 맞는 셀렉터들
            selectors_to_try = [
                # React 컴포넌트 기반 셀렉터들 (CSS 모듈)
                "[class*='ComplexList']",
                "[class*='ComplexItem']", 
                "[class*='ItemList']",
                "[class*='PropertyList']",
                "[class*='RealEstateList']",
                # 네이버 특화 셀렉터들
                "[data-module]",
                "[data-react-component]",
                "[class*='_container']",
                "[class*='_wrapper']",
                "[class*='_item']",
                # 표준 부동산 관련 셀렉터들
                ".complex-item",
                ".property-item", 
                ".estate-item",
                ".apt-item",
                # 리스트 구조 셀렉터들
                ".list-container",
                ".card-list",
                ".item-card",
                "article",
                # 기존 셀렉터들
                ".item_list_search",
                ".list_contents",
                ".item",
                # 범용 셀렉터들
                "[role='listitem']",
                "[role='article']"
            ]
            
            found_selector = None
            elements_count = 0
            
            for selector in selectors_to_try:
                try:
                    await self.page.wait_for_selector(selector, timeout=3000)
                    elements = await self.page.query_selector_all(selector)
                    elements_count = len(elements)
                    
                    if elements_count > 0:
                        found_selector = selector
                        logger.info(f"발견된 셀렉터: {selector} ({elements_count}개 요소)")
                        break
                except:
                    continue
            
            if not found_selector:
                # 페이지 구조 분석을 위한 디버깅 정보 수집
                page_info = await self.page.evaluate("""
                    () => {
                        return {
                            url: window.location.href,
                            title: document.title,
                            bodyClasses: document.body.className,
                            allClasses: Array.from(document.querySelectorAll('[class]')).map(el => el.className).slice(0, 20),
                            dataTestIds: Array.from(document.querySelectorAll('[data-testid]')).map(el => el.getAttribute('data-testid')).slice(0, 10),
                            commonTags: ['div', 'article', 'section', 'ul', 'li'].map(tag => ({
                                tag: tag,
                                count: document.querySelectorAll(tag).length
                            }))
                        };
                    }
                """)
                
                logger.error(f"모든 셀렉터 실패. 페이지 정보: {page_info}")
                
                # HTML 전체 저장 (디버깅용)
                html_content = await self.page.content()
                debug_dir = Path("screenshots")
                debug_dir.mkdir(exist_ok=True)
                
                debug_filename = f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                with open(debug_dir / debug_filename, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                logger.info(f"디버깅 HTML 저장: {debug_filename}")
                
                return []
            
            # 새로운 구조에 맞는 매물 링크 수집 (강화된 필터링)
            article_links = await self.page.evaluate(f"""
                (foundSelector) => {{
                    const links = [];
                    
                    // 발견된 셀렉터를 사용하여 요소들 선택
                    const items = document.querySelectorAll(foundSelector);
                    
                    items.forEach(item => {{
                        // 각 아이템에서 링크 찾기
                        const linkElements = item.querySelectorAll('a');
                        
                        linkElements.forEach(linkEl => {{
                            if (linkEl && linkEl.href) {{
                                const href = linkEl.href;
                                
                                // 유효한 네이버 부동산 링크 수집 (완화된 조건)
                                if (!href.includes('javascript') && 
                                    !href.includes('void(0)') &&
                                    href.includes('naver.com')) {{
                                    
                                    // 복합단지 링크
                                    if (href.includes('complex') || 
                                        href.includes('articleDetail') ||
                                        href.includes('/apt/') ||
                                        href.match(/land\.naver\.com\/.*[0-9]/)) {{
                                        links.push(href);
                                    }}
                                }}
                            }}
                        }});
                        
                        // data-* 속성에서 복합단지 ID 찾기
                        const complexId = item.getAttribute('data-complex-id') || 
                                        item.getAttribute('data-apt-id') ||
                                        item.getAttribute('data-id');
                        if (complexId && /^[0-9]+$/.test(complexId)) {{
                            links.push(`https://new.land.naver.com/complex/${{complexId}}`);
                        }}
                        
                        // onclick 이벤트에서 복합단지 ID 추출
                        const onclickAttr = item.getAttribute('onclick') || '';
                        const complexMatch = onclickAttr.match(/complex[/(]([0-9]+)/);
                        if (complexMatch && complexMatch[1]) {{
                            links.push(`https://new.land.naver.com/complex/${{complexMatch[1]}}`);
                        }}
                        
                        // 실제 매물/복합단지 링크만 수집
                        const allLinks = item.querySelectorAll('a');
                        allLinks.forEach(link => {{
                            if (link.href && 
                                link.href.includes('land.naver.com') && 
                                !link.href.includes('javascript') &&
                                !link.href.includes('community') &&
                                !link.href.includes('search') &&
                                !link.href.includes('news') &&
                                !link.href.includes('landad') &&
                                (link.href.includes('/complex/') || 
                                 link.href.includes('/article/') ||
                                 link.href.includes('/apt/'))) {{
                                links.push(link.href);
                            }}
                        }});
                    }});
                    
                    // 중복 제거 및 기본 필터링만
                    const validLinks = [...new Set(links)].filter(link => {{
                        return link && 
                               link.startsWith('http') && 
                               link.includes('naver.com') &&
                               !link.includes('javascript') &&
                               !link.includes('void(0)');
                    }});
                    
                    return validLinks;
                }}
            """, found_selector)
            
            logger.info(f"매물 링크 {len(article_links)}개 수집 완료")
            return article_links
            
        except Exception as e:
            logger.error(f"매물 링크 수집 실패: {e}")
            return []
            
    async def extract_article_data(self, article_url: str) -> Optional[Dict]:
        """개별 매물 데이터 추출"""
        try:
            # Rate Limiter 확인
            if not await self.rate_limiter.wait_if_needed():
                logger.warning("일일 요청 제한 초과로 크롤링 중단")
                return None
            
            logger.info(f"매물 페이지 이동: {article_url}")
            await self.page.goto(article_url, wait_until="networkidle")
            
            # 요청 기록
            break_needed = self.rate_limiter.record_request()
            if break_needed == True:  # 긴 휴식
                await self.rate_limiter.sleep(CRAWLING_CONFIG.get('long_break_duration', 300))
            elif break_needed == "session_break":  # 세션 휴식
                await self.rate_limiter.sleep(CRAWLING_CONFIG.get('session_break_duration', 30))
            
            await asyncio.sleep(3)
            
            # 페이지 로딩 대기
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            # 새로운 네이버 부동산 구조에 맞는 데이터 추출
            article_data = await self.page.evaluate("""
                () => {
                    const data = {};
                    
                    // 다양한 셀렉터로 단지명 추출 시도
                    const titleSelectors = [
                        'h1',
                        '.complex_title',
                        '.apt_name',
                        '.complex_name', 
                        '[class*="title"]',
                        '[class*="name"]',
                        '.title',
                        'h2',
                        '.header-title'
                    ];
                    
                    for (const selector of titleSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim()) {
                            data.단지명 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 주소 정보
                    const addressSelectors = [
                        '.address',
                        '.location',
                        '[class*="address"]',
                        '[class*="location"]',
                        '.addr',
                        '.road_addr'
                    ];
                    
                    for (const selector of addressSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim()) {
                            data.주소 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 가격 정보
                    const priceSelectors = [
                        '.price',
                        '.amount',
                        '[class*="price"]',
                        '[class*="amount"]',
                        '.cost',
                        '.money'
                    ];
                    
                    for (const selector of priceSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && element.textContent.includes('억')) {
                            data.가격 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 면적 정보
                    const areaSelectors = [
                        '.area',
                        '.size',
                        '[class*="area"]',
                        '[class*="size"]',
                        '.space'
                    ];
                    
                    for (const selector of areaSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && (element.textContent.includes('㎡') || element.textContent.includes('평'))) {
                            data.면적 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 층수 정보
                    const floorSelectors = [
                        '.floor',
                        '[class*="floor"]',
                        '.level'
                    ];
                    
                    for (const selector of floorSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && element.textContent.includes('층')) {
                            data.층수 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 건축년도
                    const yearSelectors = [
                        '.year',
                        '.built',
                        '[class*="year"]',
                        '[class*="built"]',
                        '.construction'
                    ];
                    
                    for (const selector of yearSelectors) {
                        const element = document.querySelector(selector);
                        if (element && element.textContent.trim() && /[0-9]{4}/.test(element.textContent)) {
                            data.건축년도 = element.textContent.trim();
                            break;
                        }
                    }
                    
                    // 메타 정보에서 추출
                    const metaTitle = document.querySelector('title');
                    if (metaTitle && !data.단지명) {
                        const titleText = metaTitle.textContent;
                        if (titleText && !titleText.includes('네이버')) {
                            data.단지명 = titleText.split('|')[0].trim();
                        }
                    }
                    
                    // 모든 텍스트에서 패턴 매칭으로 정보 추출
                    const bodyText = document.body.textContent || '';
                    
                    // 가격 패턴 매칭
                    if (!data.가격) {
                        const priceMatch = bodyText.match(/([0-9]+억[\\s]*[0-9]*,?[0-9]*만원?)/);
                        if (priceMatch) {
                            data.가격 = priceMatch[1];
                        }
                    }
                    
                    // 면적 패턴 매칭  
                    if (!data.면적) {
                        const areaMatch = bodyText.match(/([0-9]+[.]?[0-9]*㎡|[0-9]+[.]?[0-9]*평)/);
                        if (areaMatch) {
                            data.면적 = areaMatch[1];
                        }
                    }
                    
                    return data;
                }
            """)
            
            # 거래타입 결정 (URL에서 추출)
            if 'tradTpCd=A1' in article_url:
                article_data['거래타입'] = '매매'
            elif 'tradTpCd=B1' in article_url:
                article_data['거래타입'] = '전세'
            elif 'tradTpCd=B2' in article_url:
                article_data['거래타입'] = '월세'
            else:
                article_data['거래타입'] = '매매'
                
            # 수집일시 추가
            article_data['수집일시'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 위도, 경도는 추후 주소 변환으로 설정
            article_data['위도'] = None
            article_data['경도'] = None
            article_data['거래일자'] = datetime.now().strftime('%Y-%m-%d')
            
            return article_data
            
        except Exception as e:
            logger.error(f"매물 데이터 추출 실패 ({article_url}): {e}")
            return None
            
    async def crawl_region(self, region: str, district: str = None) -> List[Dict]:
        """지역별 크롤링 실행"""
        logger.info(f"지역 크롤링 시작: {region} {district if district else '전체'}")
        
        all_data = []
        
        # 지역 코드 가져오기
        if region not in REGIONS:
            logger.error(f"지원하지 않는 지역: {region}")
            return []
            
        region_data = REGIONS[region]
        
        if district:
            if district not in region_data:
                logger.error(f"지원하지 않는 구역: {district}")
                return []
            districts = {district: region_data[district]}
        else:
            districts = region_data
            
        # 각 구역별 크롤링
        for district_name, region_code in districts.items():
            logger.info(f"구역 크롤링 시작: {district_name} ({region_code})")
            
            # 지역 페이지로 이동
            if not await self.navigate_to_region(region_code):
                continue
                
            # 매물 링크 수집
            article_links = await self.get_article_links()
            
            if not article_links:
                logger.warning(f"매물 링크를 찾을 수 없음: {district_name}")
                continue
                
            # 각 매물 데이터 추출
            for i, article_url in enumerate(article_links[:100]):  # 테스트용으로 100개만
                logger.info(f"매물 크롤링 중: {i+1}/{len(article_links[:5])}")
                
                # 세션 제한 확인
                if not await self.stealth.check_session_limits():
                    logger.info("세션 제한 도달, 세션 재시작")
                    await self.stealth.reset_session()
                    break
                
                # 레이트 리미트 감지 및 처리
                if await self.stealth.handle_rate_limit(self.page):
                    logger.info("레이트 리미트 처리 완료")
                    continue
                
                article_data = await self.extract_article_data(article_url)
                if article_data:
                    all_data.append(article_data)
                    
                # 인간 행동 시뮬레이션
                await self.stealth.simulate_human_behavior(self.page)
                
                # 랜덤 딜레이
                await self.stealth.random_delay()
                
                # 세션 통계 로깅
                if i % 3 == 0:
                    stats = self.stealth.get_session_stats()
                    logger.info(f"세션 통계: {stats}")
                
            logger.info(f"구역 크롤링 완료: {district_name} - {len(article_links)}개 매물")
            
        logger.info(f"지역 크롤링 완료: {region} - 총 {len(all_data)}개 데이터")
        return all_data
        
    async def save_screenshot(self, filename: str = None) -> str:
        """스크린샷 저장"""
        if not filename:
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
        screenshot_path = DATA_CONFIG["screenshot_dir"] / filename
        await self.page.screenshot(path=str(screenshot_path))
        
        logger.info(f"스크린샷 저장: {screenshot_path}")
        return str(screenshot_path)
        
    async def run(self, region: str, district: str = None) -> None:
        """크롤링 실행"""
        try:
            logger.info("네이버 부동산 크롤링 시작")
            
            # 브라우저 초기화
            await self.init_browser()
            
            # 크롤링 실행
            if url:
                data = await self.crawl_by_api(url)
            else:
                data = await self.crawl_region(region, district)
            
            if data:
                # 데이터 파싱
                parsed_data = self.data_parser.parse_data(data)
                
                # 데이터 저장
                filename = DATA_CONFIG["csv_filename"].format(
                    region=region,
                    timestamp=datetime.now().strftime('%Y%m%d_%H%M%S')
                )
                
                output_path = await self.data_storage.save_to_csv(parsed_data, filename)
                logger.info(f"데이터 저장 완료: {output_path}")
                
                # 데이터 저장 (Supabase)
                await self.data_storage.save_to_supabase(parsed_data) # Supabase에 저장

                # 캡처된 API 응답 파일이 있다면 읽어서 출력
                temp_json_files = list(DATA_CONFIG["log_dir"].glob("captured_api_responses_*.json"))
                if temp_json_files:
                    latest_temp_json = max(temp_json_files, key=os.path.getctime)
                    logger.info(f"임시 파일에서 캡처된 API 응답 읽기: {latest_temp_json}")
                    with open(latest_temp_json, 'r', encoding='utf-8') as f:
                        captured_responses = json.load(f)
                    
                    logger.info("--- 캡처된 JSON 응답 요약 (파일에서 읽음) ---")
                    for i, resp in enumerate(captured_responses):
                        url = resp.get("url", "N/A")
                        data_content = resp.get("data", {})
                        summary = str(data_content)[:200] + ("..." if len(str(data_content)) > 200 else "")
                        logger.info(f"[{i+1}] URL: {url}\n    Data: {summary}")
                    logger.info("------------------------------------------")
                    os.remove(latest_temp_json) # 임시 파일 삭제

                # 캡처된 API 응답 파일이 있다면 읽어서 출력
                temp_json_files = list(DATA_CONFIG["log_dir"].glob("captured_api_responses_*.json"))
                if temp_json_files:
                    latest_temp_json = max(temp_json_files, key=os.path.getctime)
                    logger.info(f"임시 파일에서 캡처된 API 응답 읽기: {latest_temp_json}")
                    with open(latest_temp_json, 'r', encoding='utf-8') as f:
                        captured_responses = json.load(f)
                    
                    logger.info("--- 캡처된 JSON 응답 요약 (파일에서 읽음) ---")
                    for i, resp in enumerate(captured_responses):
                        url = resp.get("url", "N/A")
                        data_content = resp.get("data", {})
                        summary = str(data_content)[:200] + ("..." if len(str(data_content)) > 200 else "")
                        logger.info(f"[{i+1}] URL: {url}\n    Data: {summary}")
                    logger.info("------------------------------------------")
                    os.remove(latest_temp_json) # 임시 파일 삭제

                # 캡처된 API 응답 파일이 있다면 읽어서 출력
                temp_json_files = list(DATA_CONFIG["log_dir"].glob("captured_api_responses_*.json"))
                if temp_json_files:
                    latest_temp_json = max(temp_json_files, key=os.path.getctime)
                    logger.info(f"임시 파일에서 캡처된 API 응답 읽기: {latest_temp_json}")
                    with open(latest_temp_json, 'r', encoding='utf-8') as f:
                        captured_responses = json.load(f)
                    
                    logger.info("--- 캡처된 JSON 응답 요약 (파일에서 읽음) ---")
                    for i, resp in enumerate(captured_responses):
                        url = resp.get("url", "N/A")
                        data_content = resp.get("data", {})
                        summary = str(data_content)[:200] + ("..." if len(str(data_content)) > 200 else "")
                        logger.info(f"[{i+1}] URL: {url}\n    Data: {summary}")
                    logger.info("------------------------------------------")
                    os.remove(latest_temp_json) # 임시 파일 삭제

                # 캡처된 API 응답 파일이 있다면 읽어서 출력
                temp_json_files = list(DATA_CONFIG["log_dir"].glob("captured_api_responses_*.json"))
                if temp_json_files:
                    latest_temp_json = max(temp_json_files, key=os.path.getctime)
                    logger.info(f"임시 파일에서 캡처된 API 응답 읽기: {latest_temp_json}")
                    with open(latest_temp_json, 'r', encoding='utf-8') as f:
                        captured_responses = json.load(f)
                    
                    logger.info("--- 캡처된 JSON 응답 요약 (파일에서 읽음) ---")
                    for i, resp in enumerate(captured_responses):
                        url = resp.get("url", "N/A")
                        data_content = resp.get("data", {})
                        summary = str(data_content)[:200] + ("..." if len(str(data_content)) > 200 else "")
                        logger.info(f"[{i+1}] URL: {url}\n    Data: {summary}")
                    logger.info("------------------------------------------")
                    os.remove(latest_temp_json) # 임시 파일 삭제

                # 캡처된 API 응답 파일이 있다면 읽어서 출력
                temp_json_files = list(DATA_CONFIG["log_dir"].glob("captured_api_responses_*.json"))
                if temp_json_files:
                    latest_temp_json = max(temp_json_files, key=os.path.getctime)
                    logger.info(f"임시 파일에서 캡처된 API 응답 읽기: {latest_temp_json}")
                    with open(latest_temp_json, 'r', encoding='utf-8') as f:
                        captured_responses = json.load(f)
                    
                    logger.info("--- 캡처된 JSON 응답 요약 (파일에서 읽음) ---")
                    for i, resp in enumerate(captured_responses):
                        url = resp.get("url", "N/A")
                        data_content = resp.get("data", {})
                        summary = str(data_content)[:200] + ("..." if len(str(data_content)) > 200 else "")
                        logger.info(f"[{i+1}] URL: {url}\n    Data: {summary}")
                    logger.info("------------------------------------------")
                    os.remove(latest_temp_json) # 임시 파일 삭제
                
                # 스크린샷 저장
                await self.save_screenshot()
                
            else:
                logger.warning("크롤링된 데이터가 없습니다")
                
        except Exception as e:
            logger.error(f"크롤링 실행 중 오류: {e}")
            raise
            
        finally:
            # 브라우저 종료
            await self.close_browser()
            logger.info("크롤링 완료")


async def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='네이버 부동산 크롤러')
    parser.add_argument('--region', '-r', type=str, 
                       choices=list(REGIONS.keys()),
                       help='크롤링할 지역 (서울, 부산, 인천)')
    parser.add_argument('--district', '-d', type=str, 
                       help='크롤링할 구역 (선택사항)')
    parser.add_argument('--headless', action='store_true',
                       help='헤드리스 모드로 실행')
    parser.add_argument('--url', '-u', type=str, 
                       help='크롤링할 특정 URL (API 크롤링용)')
    
    args = parser.parse_args()
    
    # 헤드리스 모드 설정
    if args.headless:
        CRAWLING_CONFIG["headless"] = True
    
    # 크롤러 실행
    crawler = NaverRealEstateCrawler()
    if args.url:
        await crawler.run(url=args.url)
    elif args.region:
        await crawler.run(region=args.region, district=args.district)
    else:
        parser.print_help()
        logger.error("지역 또는 URL을 지정해야 합니다.")


if __name__ == "__main__":
    asyncio.run(main())