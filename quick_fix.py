#!/usr/bin/env python3
"""
빠른 수정 - 세션 없이도 필터링 가능하도록 함
"""

from flask import Flask, render_template, request, session
import pandas as pd
import glob
import os
from map_utils import get_latlon_from_address
from geopy.distance import geodesic
import numpy as np

app = Flask(__name__)
app.secret_key = 'your-secret-key'

@app.route('/quick_filter')
def quick_filter():
    """세션 없이 직접 필터링"""
    # 파라미터 받기
    address = request.args.get('address', '서초동 1326-17')
    radius_km = float(request.args.get('radius', 5))
    
    print(f"빠른 필터링 요청: {address}, 반경 {radius_km}km")
    
    # 최신 분석 파일 찾기
    analysis_files = glob.glob('uploads/*_분석완료.csv')
    if not analysis_files:
        return "분석 파일을 찾을 수 없습니다. 먼저 CSV 파일을 업로드해주세요."
    
    latest_file = max(analysis_files, key=os.path.getmtime)
    print(f"사용할 파일: {latest_file}")
    
    try:
        # 데이터 로드
        df = pd.read_csv(latest_file, encoding='utf-8-sig')
        columns = df.columns.tolist()
        
        # 좌표 변환
        center_lat, center_lon = get_latlon_from_address(address)
        if center_lat is None or center_lon is None:
            return f"주소 '{address}'의 좌표를 찾을 수 없습니다."
        
        # 거리 계산
        df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
        df['경도'] = pd.to_numeric(df['경도'], errors='coerce')
        df = df.dropna(subset=['위도', '경도'])
        
        if not df.empty:
            df['중심점과의거리'] = df.apply(
                lambda row: geodesic((center_lat, center_lon), (row['위도'], row['경도'])).meters / 1000, 
                axis=1
            )
            
            # 필터링
            filtered_df = df[df['중심점과의거리'] <= radius_km].copy()
            
            # 결과 준비
            data_records = filtered_df.to_dict('records')
            
            # 안전한 데이터 준비
            safe_data = {
                'data': data_records,
                'columns': columns,
                'count': len(data_records),
                'center_lat': center_lat,
                'center_lon': center_lon,
                'radius': radius_km * 1000,  # 미터 단위
                'pagination': {
                    'page': 1,
                    'per_page': len(data_records),
                    'total_count': len(data_records),
                    'total_pages': 1,
                    'has_prev': False,
                    'has_next': False
                }
            }
            
            return render_template('results.html', **safe_data)
            
        else:
            return "유효한 좌표 데이터가 없습니다."
            
    except Exception as e:
        return f"오류 발생: {e}"

if __name__ == "__main__":
    app.run(debug=True, port=8005, host='0.0.0.0')