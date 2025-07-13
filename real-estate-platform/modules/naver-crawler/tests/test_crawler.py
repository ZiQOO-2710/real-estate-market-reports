"""
크롤러 테스트 모듈
"""

import asyncio
import pytest
from pathlib import Path
import sys

# 프로젝트 루트 경로 설정
sys.path.append(str(Path(__file__).parent.parent))

from src.crawler import NaverRealEstateCrawler
from src.parser import DataParser
from src.storage import DataStorage
from config.settings import REGIONS


class TestNaverRealEstateCrawler:
    """네이버 부동산 크롤러 테스트"""
    
    def test_crawler_initialization(self):
        """크롤러 초기화 테스트"""
        crawler = NaverRealEstateCrawler()
        assert crawler.data_parser is not None
        assert crawler.data_storage is not None
        
    def test_regions_configuration(self):
        """지역 설정 테스트"""
        assert "서울" in REGIONS
        assert "부산" in REGIONS
        assert "인천" in REGIONS
        
        # 서울 강남구 코드 확인
        assert REGIONS["서울"]["강남구"] == "1168010500"
        
    @pytest.mark.asyncio
    async def test_browser_initialization(self):
        """브라우저 초기화 테스트"""
        crawler = NaverRealEstateCrawler()
        
        try:
            await crawler.init_browser()
            assert crawler.browser is not None
            assert crawler.page is not None
            
        finally:
            await crawler.close_browser()
            
    def test_data_parser(self):
        """데이터 파서 테스트"""
        parser = DataParser()
        
        # 가격 파싱 테스트
        assert parser.parse_price("2억 3,000만원", "매매") == "23000"
        assert parser.parse_price("1억 5,000만원", "매매") == "15000"
        assert parser.parse_price("5,000만원", "매매") == "5000"
        
        # 면적 파싱 테스트
        exclusive, supply = parser.parse_area("84.99㎡")
        assert exclusive == 84.99
        assert supply == pytest.approx(84.99 * 1.3, rel=0.1)
        
        # 층수 파싱 테스트
        assert parser.parse_floor("5층") == 5
        assert parser.parse_floor("5/25층") == 5
        
        # 건축년도 파싱 테스트
        assert parser.parse_year("2018년") == 2018
        assert parser.parse_year("2018") == 2018
        
    def test_data_storage(self):
        """데이터 저장 테스트"""
        storage = DataStorage()
        
        # 테스트 데이터
        test_data = [
            {
                "단지명": "테스트아파트",
                "주소": "서울특별시 강남구 테스트동",
                "거래타입": "매매",
                "가격": "50000",
                "전용면적": 84.99,
                "층수": 5,
                "건축년도": 2018
            }
        ]
        
        # 파일 정보 확인
        file_info = storage.get_file_info("nonexistent_file.csv")
        assert "error" in file_info
        
        # 출력 파일 목록 확인
        file_list = storage.list_output_files()
        assert isinstance(file_list, list)


async def test_sample_crawling():
    """샘플 크롤링 테스트"""
    crawler = NaverRealEstateCrawler()
    
    try:
        await crawler.init_browser()
        
        # 서울 강남구 페이지 이동 테스트
        success = await crawler.navigate_to_region("1168010500")
        assert success, "페이지 이동 실패"
        
        # 매물 링크 수집 테스트 (소수만)
        links = await crawler.get_article_links()
        print(f"수집된 매물 링크: {len(links)}개")
        
        # 첫 번째 매물만 테스트
        if links:
            article_data = await crawler.extract_article_data(links[0])
            print(f"추출된 데이터: {article_data}")
            assert article_data is not None
            
    finally:
        await crawler.close_browser()


if __name__ == "__main__":
    # 기본 테스트 실행
    test_crawler = TestNaverRealEstateCrawler()
    test_crawler.test_crawler_initialization()
    test_crawler.test_regions_configuration()
    test_crawler.test_data_parser()
    test_crawler.test_data_storage()
    
    print("✅ 모든 기본 테스트 통과")
    
    # 샘플 크롤링 테스트 (선택사항)
    run_sample_test = input("샘플 크롤링 테스트를 실행하시겠습니까? (y/n): ")
    if run_sample_test.lower() == 'y':
        asyncio.run(test_sample_crawling())
        print("✅ 샘플 크롤링 테스트 완료")