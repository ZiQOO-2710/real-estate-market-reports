#!/usr/bin/env python3
"""
간단한 Flask 앱 디버깅 도구 (의존성 문제 없이 사용 가능)
"""

from playwright.sync_api import sync_playwright
import json

def test_previous_button():
    """이전 페이지 버튼 기능 테스트"""
    
    try:
        with sync_playwright() as p:
            # 헤드리스 모드로 브라우저 실행
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("🎭 Playwright 헤드리스 디버깅 시작...")
            
            # 콘솔 로그 캡처
            console_logs = []
            def capture_console(msg):
                log_entry = f"[{msg.type.upper()}] {msg.text}"
                console_logs.append(log_entry)
                print(f"📝 {log_entry}")
            
            page.on("console", capture_console)
            
            # Flask 앱 접속
            print("🌐 Flask 앱 접속 중...")
            try:
                page.goto("http://localhost:8001", timeout=10000)
                print("✅ 홈페이지 로드 성공")
                
                # 페이지 정보 수집
                title = page.title()
                url = page.url
                print(f"📄 페이지 제목: {title}")
                print(f"🔗 현재 URL: {url}")
                
                # 스크린샷 저장
                page.screenshot(path="debug_home.png")
                print("📸 홈페이지 스크린샷 저장: debug_home.png")
                
                # 이전 페이지 버튼 찾기
                button_selectors = [
                    "button:has-text('이전')",
                    "button:has-text('뒤로')", 
                    "a:has-text('이전')",
                    "[onclick*='history.back']",
                    "[onclick*='goBack']"
                ]
                
                buttons_found = []
                for selector in button_selectors:
                    try:
                        elements = page.locator(selector)
                        count = elements.count()
                        if count > 0:
                            for i in range(count):
                                text = elements.nth(i).inner_text()
                                visible = elements.nth(i).is_visible()
                                buttons_found.append({
                                    'selector': selector,
                                    'text': text,
                                    'visible': visible
                                })
                    except Exception as e:
                        pass
                
                print(f"🔍 발견된 이전 페이지 버튼: {len(buttons_found)}개")
                for btn in buttons_found:
                    print(f"   - '{btn['text']}' (보임: {btn['visible']})")
                
                # 페이지 소스에서 history.back 검색
                content = page.content()
                if "history.back" in content:
                    print("✅ history.back() 코드가 페이지에 존재함")
                else:
                    print("❌ history.back() 코드를 찾을 수 없음")
                
                # goBack 함수 검색
                if "goBack" in content:
                    print("✅ goBack() 함수가 페이지에 존재함")
                else:
                    print("❌ goBack() 함수를 찾을 수 없음")
                
                # JavaScript 실행해서 함수 존재 확인
                try:
                    has_go_back = page.evaluate("typeof goBack === 'function'")
                    print(f"🔧 goBack 함수 존재 여부: {has_go_back}")
                except:
                    print("🔧 JavaScript 함수 확인 실패")
                
            except Exception as e:
                print(f"❌ 홈페이지 접속 실패: {e}")
                print("💡 Flask 앱이 http://localhost:8001에서 실행 중인지 확인하세요")
                return
            
            # 분석 결과를 파일로 저장
            report = {
                "page_title": title,
                "page_url": url,
                "buttons_found": buttons_found,
                "console_logs": console_logs,
                "has_history_back": "history.back" in content,
                "has_go_back_function": "goBack" in content
            }
            
            with open("debug_report.json", "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print("📊 디버깅 리포트 저장: debug_report.json")
            
            browser.close()
            print("✅ 디버깅 완료")
            
    except Exception as e:
        print(f"❌ Playwright 오류: {e}")
        print("💡 시스템 의존성 설치가 필요할 수 있습니다:")
        print("   sudo playwright install-deps")

def check_page_structure():
    """페이지 구조 분석"""
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("🔍 페이지 구조 분석 시작...")
            
            try:
                page.goto("http://localhost:8001", timeout=10000)
                
                # 모든 버튼 찾기
                buttons = page.locator("button").all()
                links = page.locator("a").all()
                
                print(f"🔘 발견된 버튼: {len(buttons)}개")
                for i, btn in enumerate(buttons):
                    try:
                        text = btn.inner_text()
                        onclick = btn.get_attribute("onclick") or ""
                        print(f"   버튼 {i+1}: '{text}' (onclick: {onclick[:50]}...)")
                    except:
                        print(f"   버튼 {i+1}: 텍스트 추출 실패")
                
                print(f"🔗 발견된 링크: {len(links)}개")
                for i, link in enumerate(links):
                    try:
                        text = link.inner_text()
                        href = link.get_attribute("href") or ""
                        print(f"   링크 {i+1}: '{text}' (href: {href})")
                    except:
                        print(f"   링크 {i+1}: 텍스트 추출 실패")
                
                # 페이지 HTML 저장
                html_content = page.content()
                with open("debug_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                
                print("💾 페이지 HTML 저장: debug_page.html")
                
            except Exception as e:
                print(f"❌ 페이지 분석 실패: {e}")
            
            browser.close()
            
    except Exception as e:
        print(f"❌ 페이지 구조 분석 오류: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "structure":
            check_page_structure()
        else:
            print("사용법:")
            print("  python simple_debug.py           # 이전 페이지 버튼 테스트")
            print("  python simple_debug.py structure # 페이지 구조 분석")
    else:
        test_previous_button()