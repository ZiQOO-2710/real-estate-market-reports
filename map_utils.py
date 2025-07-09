import requests
from urllib.parse import quote
import os
import time
from functools import lru_cache
from typing import Dict, List, Tuple, Optional
import threading

KAKAO_REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')

# 캐시 및 레이트 제한을 위한 글로벌 변수
_cache: Dict[str, Tuple[Optional[float], Optional[float]]] = {}
_last_request_time = 0
_rate_limit_lock = threading.Lock()

def _rate_limit_wait():
    """레이트 제한을 위한 대기 함수 (초당 최대 10회 요청)"""
    global _last_request_time
    with _rate_limit_lock:
        current_time = time.time()
        time_since_last = current_time - _last_request_time
        min_interval = 0.1  # 100ms 간격
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        _last_request_time = time.time()

@lru_cache(maxsize=1000)
def get_latlon_from_address(address: str) -> Tuple[Optional[float], Optional[float]]:
    """
    주소 문자열을 받아 카카오 API를 통해 위도, 경도를 반환하는 함수.
    캐싱과 레이트 제한이 적용됨.
    """
    if not address or not address.strip():
        print(f'[get_latlon_from_address] 빈 주소 입력')
        return None, None
    
    original_address = address.strip()
    
    # 여러 주소 형식 시도
    address_variants = [
        original_address,
        # "서울 강남구 삼성동" 형식
        original_address.replace('시 ', ' ').replace('구 ', ' ').replace('동 ', ' '),
        # "서울특별시 강남구 삼성동" 형식
        original_address + "동" if not original_address.endswith(('동', '읍', '면', '리')) else original_address,
    ]
    
    for i, address in enumerate(address_variants):
        print(f'[get_latlon_from_address] 주소 변환 시도 #{i+1}: {address}')
        
        # 캐시 확인
        if address in _cache:
            result = _cache[address]
            print(f'[get_latlon_from_address] 캐시에서 발견: {result}')
            return result
        
        # 레이트 제한 적용
        _rate_limit_wait()
        
        try:
            url = f"https://dapi.kakao.com/v2/local/search/address.json?query={quote(address)}"
            headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
            print(f'[get_latlon_from_address] API 요청 URL: {url}')
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            
            result = resp.json()
            print(f'[get_latlon_from_address] API 응답: {result}')
            
            if result['documents']:
                lat = float(result['documents'][0]['y'])
                lon = float(result['documents'][0]['x'])
                print(f"[카카오맵 REST API 성공] {address} -> lat: {lat}, lon: {lon}")
                _cache[original_address] = (lat, lon)  # 원래 주소로 캐시
                return lat, lon
            else:
                print(f"[카카오맵 REST API] 주소 '{address}'에 해당하는 좌표를 찾지 못했습니다.")
                
        except requests.exceptions.RequestException as e:
            print(f'[카카오맵 REST API 실패] 요청 오류 for {address}: {e}')
        except Exception as e:
            print(f'[카카오맵 REST API 실패] 기타 오류 for {address}: {e}')
    
    # 모든 시도 실패
    print(f'[get_latlon_from_address] 모든 주소 형식 시도 실패: {original_address}')
    _cache[original_address] = (None, None)
    return None, None

def batch_get_latlon_from_addresses(addresses: List[str]) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
    """
    여러 주소를 배치로 처리하여 위도/경도를 반환하는 함수.
    """
    results = {}
    unique_addresses = list(set(addr.strip() for addr in addresses if addr and addr.strip()))
    
    print(f'[batch_get_latlon_from_addresses] {len(unique_addresses)}개의 고유 주소 배치 처리 시작')
    
    for i, address in enumerate(unique_addresses):
        if i % 10 == 0:
            print(f'[batch_get_latlon_from_addresses] 진행상황: {i}/{len(unique_addresses)}')
        
        lat, lon = get_latlon_from_address(address)
        results[address] = (lat, lon)
    
    print(f'[batch_get_latlon_from_addresses] 배치 처리 완료: {len(results)}개 주소')
    return results

def clear_cache():
    """캐시를 초기화하는 함수"""
    global _cache
    cache_size = len(_cache)
    _cache.clear()
    get_latlon_from_address.cache_clear()
    print(f'[캐시] 주소 변환 캐시를 초기화했습니다. (삭제된 항목: {cache_size}개)')

def get_cache_info():
    """캐시 정보 반환"""
    return {
        'size': len(_cache),
        'items': dict(_cache)
    }