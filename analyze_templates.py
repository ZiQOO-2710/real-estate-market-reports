#!/usr/bin/env python3
"""
HTML 템플릿 파일들을 직접 분석해서 이전 페이지 버튼 문제 디버깅
"""

import os
import re
from bs4 import BeautifulSoup

def analyze_template_files():
    """템플릿 파일들을 분석해서 이전 페이지 버튼 관련 코드 찾기"""
    
    template_dir = "/home/ksj27/projects/templates"
    
    if not os.path.exists(template_dir):
        print(f"❌ 템플릿 디렉토리를 찾을 수 없음: {template_dir}")
        return
    
    html_files = [f for f in os.listdir(template_dir) if f.endswith('.html')]
    
    print(f"🔍 템플릿 파일 분석 시작... ({len(html_files)}개 파일)")
    print(f"📁 템플릿 디렉토리: {template_dir}")
    
    for file_name in html_files:
        file_path = os.path.join(template_dir, file_name)
        print(f"\n📄 파일 분석: {file_name}")
        print("=" * 50)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # BeautifulSoup으로 파싱
            soup = BeautifulSoup(content, 'html.parser')
            
            # 1. 이전 페이지 관련 버튼 찾기
            prev_buttons = []
            
            # 버튼 요소 검색
            buttons = soup.find_all('button')
            for btn in buttons:
                btn_text = btn.get_text(strip=True)
                onclick = btn.get('onclick', '')
                
                if any(keyword in btn_text for keyword in ['이전', 'back', '뒤로']):
                    prev_buttons.append({
                        'type': 'button',
                        'text': btn_text,
                        'onclick': onclick,
                        'html': str(btn)
                    })
            
            # 링크 요소 검색
            links = soup.find_all('a')
            for link in links:
                link_text = link.get_text(strip=True)
                onclick = link.get('onclick', '')
                href = link.get('href', '')
                
                if any(keyword in link_text for keyword in ['이전', 'back', '뒤로']):
                    prev_buttons.append({
                        'type': 'link',
                        'text': link_text,
                        'onclick': onclick,
                        'href': href,
                        'html': str(link)
                    })
            
            print(f"🔘 이전 페이지 버튼 발견: {len(prev_buttons)}개")
            for i, btn in enumerate(prev_buttons):
                print(f"   {i+1}. [{btn['type'].upper()}] '{btn['text']}'")
                if btn.get('onclick'):
                    print(f"      onclick: {btn['onclick']}")
                if btn.get('href'):
                    print(f"      href: {btn['href']}")
                print(f"      HTML: {btn['html'][:100]}...")
                print()
            
            # 2. JavaScript 함수 검색
            scripts = soup.find_all('script')
            js_functions = []
            
            for script in scripts:
                if script.string:
                    script_content = script.string
                    
                    # goBack 함수 정의 찾기
                    if 'function goBack' in script_content or 'goBack()' in script_content:
                        js_functions.append('goBack 함수')
                        
                        # goBack 함수 내용 추출
                        go_back_match = re.search(r'function goBack\(\)[^}]*\{([^}]*)\}', script_content, re.DOTALL)
                        if go_back_match:
                            function_body = go_back_match.group(1).strip()
                            print(f"🔧 goBack 함수 내용:")
                            print(f"      {function_body}")
                    
                    # history.back 호출 찾기
                    if 'history.back' in script_content:
                        js_functions.append('history.back() 호출')
                        
                        # history.back 호출 문맥 추출
                        history_lines = [line.strip() for line in script_content.split('\n') if 'history.back' in line]
                        for line in history_lines:
                            print(f"🔧 history.back 호출: {line}")
            
            if js_functions:
                print(f"✅ JavaScript 함수 발견: {', '.join(js_functions)}")
            else:
                print("❌ 이전 페이지 관련 JavaScript 함수 없음")
            
            # 3. onclick 속성 검색
            onclick_elements = soup.find_all(attrs={"onclick": re.compile(r".*")})
            prev_onclick = []
            
            for elem in onclick_elements:
                onclick = elem.get('onclick', '')
                if any(keyword in onclick.lower() for keyword in ['history.back', 'goback']):
                    prev_onclick.append({
                        'tag': elem.name,
                        'text': elem.get_text(strip=True)[:30] + "...",
                        'onclick': onclick
                    })
            
            if prev_onclick:
                print(f"🖱️  onclick 이벤트 발견: {len(prev_onclick)}개")
                for elem in prev_onclick:
                    print(f"   <{elem['tag']}> '{elem['text']}' - onclick: {elem['onclick']}")
            
            # 4. 전체 문자열 패턴 검색
            patterns = {
                'history.back': content.count('history.back'),
                'goBack': content.count('goBack'),
                'window.history': content.count('window.history'),
                '이전': content.count('이전'),
                'back': content.count('back'),
                'button': content.count('<button')
            }
            
            print(f"📊 패턴 출현 빈도:")
            for pattern, count in patterns.items():
                if count > 0:
                    print(f"   ✅ '{pattern}': {count}회")
                else:
                    print(f"   ❌ '{pattern}': 없음")
            
        except Exception as e:
            print(f"❌ 파일 분석 오류: {e}")
    
    print(f"\n🎯 이전 페이지 버튼 문제 진단:")
    print("=" * 50)
    
    # map.html과 results.html 비교
    map_file = os.path.join(template_dir, "map.html")
    results_file = os.path.join(template_dir, "results.html")
    
    if os.path.exists(map_file) and os.path.exists(results_file):
        print("📋 두 파일의 이전 페이지 버튼 구현 비교:")
        
        for file_path, file_name in [(map_file, "map.html"), (results_file, "results.html")]:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📄 {file_name}:")
            
            # goBack 함수 존재 여부
            has_go_back = 'goBack' in content
            print(f"   goBack 함수: {'✅ 있음' if has_go_back else '❌ 없음'}")
            
            # history.back 존재 여부
            has_history_back = 'history.back' in content
            print(f"   history.back: {'✅ 있음' if has_history_back else '❌ 없음'}")
            
            # 버튼 타입 확인
            if 'type="button"' in content:
                print(f"   버튼 타입: ✅ type='button' 명시됨")
            else:
                print(f"   버튼 타입: ⚠️  type 속성 없음")

if __name__ == "__main__":
    analyze_template_files()