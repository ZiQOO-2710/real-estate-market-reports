#!/usr/bin/env python3
"""
requests 라이브러리를 사용한 간단한 웹 디버깅
"""

import requests
from bs4 import BeautifulSoup
import re

def debug_flask_app():
    """Flask 앱의 HTML 소스를 분석해서 이전 페이지 버튼 디버깅"""
    
    try:
        print("🌐 Flask 앱 접속 중...")
        response = requests.get("http://localhost:8001", timeout=10)
        
        if response.status_code == 200:
            print("✅ 홈페이지 접속 성공")
            html_content = response.text
            
            # BeautifulSoup으로 HTML 파싱
            soup = BeautifulSoup(html_content, 'html.parser')
            
            print(f"📄 페이지 제목: {soup.title.string if soup.title else 'No title'}")
            
            # 이전 페이지 관련 요소 찾기
            print("\n🔍 이전 페이지 관련 요소 검색:")
            
            # 1. 버튼 요소 검색
            buttons = soup.find_all('button')
            prev_buttons = []
            
            for btn in buttons:
                btn_text = btn.get_text(strip=True)
                onclick = btn.get('onclick', '')
                
                if any(keyword in btn_text.lower() for keyword in ['이전', 'back', '뒤로']):
                    prev_buttons.append({
                        'text': btn_text,
                        'onclick': onclick,
                        'html': str(btn)
                    })
            
            print(f"🔘 이전 페이지 버튼 발견: {len(prev_buttons)}개")
            for i, btn in enumerate(prev_buttons):
                print(f"   버튼 {i+1}: '{btn['text']}'")
                print(f"   onclick: {btn['onclick']}")
                print(f"   HTML: {btn['html'][:100]}...")
                print()
            
            # 2. JavaScript 함수 검색
            scripts = soup.find_all('script')
            js_functions = []
            
            for script in scripts:
                if script.string:
                    # goBack 함수 찾기
                    if 'goBack' in script.string:
                        js_functions.append('goBack 함수 발견')
                    
                    # history.back 호출 찾기
                    if 'history.back' in script.string:
                        js_functions.append('history.back() 호출 발견')
            
            print(f"🔧 JavaScript 함수 검색 결과:")
            for func in js_functions:
                print(f"   ✅ {func}")
            
            if not js_functions:
                print("   ❌ 이전 페이지 관련 JavaScript 함수를 찾을 수 없음")
            
            # 3. HTML에서 onclick 속성 검색
            onclick_elements = soup.find_all(attrs={"onclick": re.compile(r".*")})
            prev_onclick = []
            
            for elem in onclick_elements:
                onclick = elem.get('onclick', '')
                if any(keyword in onclick.lower() for keyword in ['history.back', 'goback']):
                    prev_onclick.append({
                        'tag': elem.name,
                        'text': elem.get_text(strip=True),
                        'onclick': onclick
                    })
            
            print(f"\n🖱️  onclick 이벤트 검색 결과:")
            for elem in prev_onclick:
                print(f"   <{elem['tag']}> '{elem['text']}' - onclick: {elem['onclick']}")
            
            # 4. 전체 HTML에서 패턴 검색
            print(f"\n📝 전체 소스 코드 패턴 검색:")
            patterns = [
                ('history.back', html_content.count('history.back')),
                ('goBack', html_content.count('goBack')),
                ('이전', html_content.count('이전')),
                ('window.history', html_content.count('window.history'))
            ]
            
            for pattern, count in patterns:
                if count > 0:
                    print(f"   ✅ '{pattern}': {count}회 발견")
                else:
                    print(f"   ❌ '{pattern}': 발견되지 않음")
            
            # 5. HTML 파일로 저장
            with open('debug_page_source.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"\n💾 페이지 소스 저장: debug_page_source.html")
            
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 연결 거부: Flask 앱이 실행 중인지 확인하세요")
        print("   python app.py")
    except requests.exceptions.Timeout:
        print("❌ 연결 시간 초과")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    debug_flask_app()