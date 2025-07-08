#!/usr/bin/env python3
"""
Flask 앱 Playwright 디버깅 스크립트
사용법: python debug_app.py
"""

from playwright.sync_api import sync_playwright
import time
import os

def debug_app():
    """Flask 앱을 Playwright로 디버깅"""
    
    with sync_playwright() as p:
        # 브라우저 실행 (헤드리스 모드 - 의존성 문제 회피)
        browser = p.chromium.launch(
            headless=True,  # 헤드리스 모드로 변경
            slow_mo=500     # 동작을 천천히 (500ms 지연)
        )
        
        # 새 페이지 생성
        page = browser.new_page()
        
        # 콘솔 로그 캡처
        page.on("console", lambda msg: print(f"[CONSOLE] {msg.type}: {msg.text}"))
        
        # 네트워크 요청 모니터링
        page.on("request", lambda req: print(f"[REQUEST] {req.method} {req.url}"))
        page.on("response", lambda res: print(f"[RESPONSE] {res.status} {res.url}"))
        
        print("🎭 Playwright 디버깅 시작...")
        print("📝 Flask 앱이 http://localhost:8001에서 실행 중인지 확인하세요")
        
        try:
            # Flask 앱 접속
            print("🌐 Flask 앱 접속 중...")
            page.goto("http://localhost:8001", timeout=10000)
            
            # 페이지 로드 대기
            page.wait_for_load_state("networkidle")
            
            print("✅ 페이지 로드 완료")
            print("🔍 이제 브라우저에서 수동으로 테스트할 수 있습니다")
            print("📋 자동 테스트 시나리오:")
            
            # 자동 테스트 시나리오들
            scenarios = [
                "1. 파일 업로드 테스트",
                "2. 이전 페이지 버튼 테스트", 
                "3. 필터링 기능 테스트",
                "4. 지도 표시 테스트"
            ]
            
            for scenario in scenarios:
                print(f"   - {scenario}")
            
            print("\n⏸️  수동 테스트를 위해 일시정지...")
            print("   브라우저에서 테스트 후 이 스크립트를 종료하세요 (Ctrl+C)")
            
            # 수동 디버깅을 위해 무한 대기
            page.pause()
            
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
            print("💡 Flask 앱이 실행 중인지 확인하세요:")
            print("   python app.py")
            
        finally:
            browser.close()
            print("🔚 디버깅 세션 종료")

def test_previous_button():
    """이전 페이지 버튼 특정 테스트"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, devtools=True)
        page = browser.new_page()
        
        # 콘솔 로그 캡처
        def handle_console(msg):
            if "이전 페이지" in msg.text:
                print(f"🔍 [CONSOLE] {msg.text}")
        
        page.on("console", handle_console)
        
        try:
            print("🎯 이전 페이지 버튼 테스트 시작...")
            
            # 홈페이지 접속
            page.goto("http://localhost:8001")
            page.screenshot(path="debug_home.png")
            
            # CSV 파일이 있다면 업로드 테스트
            if page.locator('input[type="file"]').is_visible():
                print("📁 파일 업로드 영역 발견")
                
            # 이전 페이지 버튼 찾기
            prev_buttons = page.locator("text=이전").or_(page.locator("text=뒤로")).or_(page.locator("button:has-text('이전')"))
            
            if prev_buttons.count() > 0:
                print(f"🔙 이전 페이지 버튼 {prev_buttons.count()}개 발견")
                
                for i in range(prev_buttons.count()):
                    button = prev_buttons.nth(i)
                    print(f"   버튼 {i+1}: {button.inner_text()}")
                    
                    # 버튼 클릭 테스트
                    print("🖱️  버튼 클릭 테스트...")
                    button.click()
                    
                    # 잠시 대기
                    page.wait_for_timeout(2000)
                    
                    # 스크린샷
                    page.screenshot(path=f"debug_after_click_{i}.png")
                    
            else:
                print("❌ 이전 페이지 버튼을 찾을 수 없습니다")
                
            page.pause()
            
        except Exception as e:
            print(f"❌ 테스트 중 오류: {e}")
            page.screenshot(path="debug_error.png")
            
        finally:
            browser.close()

def run_trace_analysis():
    """트레이스 기록 및 분석"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        
        # 트레이스 시작
        context.tracing.start(
            screenshots=True,
            snapshots=True,
            sources=True
        )
        
        page = context.new_page()
        
        try:
            print("📹 트레이스 기록 시작...")
            
            # 테스트 시나리오 실행
            page.goto("http://localhost:8001")
            page.screenshot(path="trace_home.png")
            
            # 이전 페이지 버튼 클릭
            if page.locator("text=이전").is_visible():
                page.click("text=이전")
                
            page.screenshot(path="trace_after_click.png")
            
        except Exception as e:
            print(f"❌ 트레이스 중 오류: {e}")
            
        finally:
            # 트레이스 저장
            context.tracing.stop(path="app_trace.zip")
            browser.close()
            
            print("✅ 트레이스 저장 완료: app_trace.zip")
            print("🔍 트레이스 분석: playwright show-trace app_trace.zip")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "button":
            test_previous_button()
        elif sys.argv[1] == "trace":
            run_trace_analysis()
        else:
            print("사용법:")
            print("  python debug_app.py          # 일반 디버깅")
            print("  python debug_app.py button   # 이전 페이지 버튼 테스트")
            print("  python debug_app.py trace    # 트레이스 기록")
    else:
        debug_app()