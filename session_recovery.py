#!/usr/bin/env python3
"""
세션 복구 및 직접 필터링 테스트
"""

import os
import sys
import glob
from flask import Flask, session

# Flask 앱 초기화
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

def find_latest_analysis_file():
    """가장 최근 분석 파일 찾기"""
    analysis_files = glob.glob('uploads/*_분석완료.csv')
    if analysis_files:
        latest_file = max(analysis_files, key=os.path.getmtime)
        return os.path.basename(latest_file)
    return None

def test_direct_filtering():
    """직접 필터링 테스트"""
    with app.test_request_context():
        # 세션 설정
        latest_file = find_latest_analysis_file()
        if latest_file:
            session['datafile'] = latest_file
            print(f"✅ 세션 설정 완료: {latest_file}")
            
            # 필터링 테스트
            from app import show_filtered_results
            
            # 필터 파라미터 설정
            session['filter_params'] = {
                'address': '서초동 1326-17',
                'radius': 5,
                'area_range': 'all',
                'sort_col': None,
                'sort_order': 'desc'
            }
            
            print("📍 필터링 테스트 실행 중...")
            try:
                # 실제 필터링 함수 호출
                result = show_filtered_results()
                print("✅ 필터링 성공!")
                return True
            except Exception as e:
                print(f"❌ 필터링 실패: {e}")
                return False
        else:
            print("❌ 분석 파일을 찾을 수 없습니다.")
            return False

if __name__ == "__main__":
    success = test_direct_filtering()
    if success:
        print("\n🎉 세션 복구 및 필터링 테스트 성공!")
        print("브라우저에서 http://localhost:8004/results 접속 시 결과를 볼 수 있습니다.")
    else:
        print("\n❌ 테스트 실패. 먼저 CSV 파일을 업로드해주세요.")