import requests
from urllib.parse import quote
import os

KAKAO_REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')

def get_latlon_from_address(address):
    """
    주소 문자열을 받아 카카오 API를 통해 위도, 경도를 반환하는 함수.
    """
    print(f'[get_latlon_from_address] 주소 변환 시도: {address}')
    try:
        url = f"https://dapi.kakao.com/v2/local/search/address.json?query={quote(address)}"
        headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()  # HTTP 오류 발생 시 예외 발생
        
        result = resp.json()
        if result['documents']:
            lat = float(result['documents'][0]['y'])
            lon = float(result['documents'][0]['x'])
            print(f"[카카오맵 REST API 성공] lat: {lat}, lon: {lon}")
            return lat, lon
        else:
            print("[카카오맵 REST API] 주소에 해당하는 좌표를 찾지 못했습니다.")
            return None, None  # 변환 실패 시 None 반환
            
    except requests.exceptions.RequestException as e:
        print(f'[카카오맵 REST API 실패] 요청 오류: {e}')
    except Exception as e:
        print(f'[카카오맵 REST API 실패] 기타 오류: {e}')
        
    return None, None  # 실패 시 None 반환