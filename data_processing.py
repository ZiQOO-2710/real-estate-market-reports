import pandas as pd
import numpy as np
import re
import os
from supabase import Client
import tempfile
from datetime import datetime
import shutil
import chardet
import gc
import atexit
from typing import Optional, Tuple, List

# 임시 파일 추적을 위한 글로벌 변수
_temp_files: List[str] = []

def _cleanup_temp_files():
    """프로그램 종료 시 임시 파일들을 정리하는 함수"""
    global _temp_files
    for file_path in _temp_files:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"[CLEANUP] 임시 파일 삭제: {file_path}")
        except Exception as e:
            print(f"[CLEANUP] 임시 파일 삭제 실패: {file_path}, 오류: {e}")
    _temp_files.clear()

# 프로그램 종료 시 임시 파일 정리 등록
atexit.register(_cleanup_temp_files)

# 컬럼명 정규화 함수
COL_RENAME = {
    '거래금액(만원)': '거래금액',
    '거래금액만원': '거래금액',
    '전용평당(만원)': '전용평당',
    '공급평당(만원)': '공급평당',
    '건축 년도': '건축년도',
    ' 도로명': '도로명',
}
def normalize_columns(df):
    def clean_col(x):
        x = x.strip()
        x = re.sub(r'[\s\(\)\u33A1,\-]', '', x)
        # '전용면적'이 포함된 모든 컬럼명을 '전용면적(\u33A1)'로 통일
        if '전용면적' in x:
            return '전용면적(\u33A1)'
        if '건축년도' in x:
            return '건축년도'
        return x
    df = df.rename(columns=clean_col)
    df = df.rename(columns=COL_RENAME)
    print('==== [DEBUG] 정규화된 컬럼명:', list(df.columns))
    return df

def process_uploaded_csv(file_path, center_lat=None, center_lon=None):
    global _temp_files
    
    # 메모리 효율적인 인코딩 감지
    with open(file_path, 'rb') as f:
        raw = f.read(10000)
        encoding = chardet.detect(raw)['encoding'] or 'utf-8'
    
    # 청크 단위로 읽기 (메모리 효율성)
    try:
        df = pd.read_csv(file_path, encoding=encoding, skiprows=15, low_memory=False)
        print(f"[DEBUG] Original DataFrame shape: {df.shape}")
        print(f"[DEBUG] Original DataFrame columns: {df.columns.tolist()}")
        
        # 메모리 사용량 최적화: 필요한 컬럼만 미리 필터링
        df = normalize_columns(df)
        print(f"[DEBUG] Normalized DataFrame shape: {df.shape}")

        # --- 로깅 및 필터링 로직 추가 ---
        log_lines = []
        original_filename = os.path.basename(file_path)
        log_filename = f"{os.path.splitext(original_filename)[0]}_filter_log.txt"
        # 로그 파일은 원본과 같은 디렉터리에 저장
        log_path = os.path.join(os.path.dirname(file_path), log_filename)

        # 1. '거래유형'이 '직거래'인 행 삭제 및 로깅
        if '거래유형' in df.columns:
            direct_deals = df[df['거래유형'] == '직거래']
            if not direct_deals.empty:
                log_lines.append(f"=== '거래유형'이 '직거래'여서 삭제된 데이터 ({len(direct_deals)}건) ===")
                log_lines.append(direct_deals.to_string())
                log_lines.append("\n")
                df = df[df['거래유형'] != '직거래'].copy()
                print(f"[FILTER] '직거래' 데이터 {len(direct_deals)}건 필터링 완료")

        # 2. '해제사유발생일'에 날짜값이 있는 행 삭제 및 로깅 (수정된 로직)
        if '해제사유발생일' in df.columns:
            # 실제 날짜/숫자 데이터가 있는 행을 식별 (NaT/NaN이 아닌 값)
            # pd.to_numeric은 숫자/날짜 형식의 문자열을 숫자로 변환하고, '-' 같은 문자는 NaN으로 만듭니다.
            numeric_dates = pd.to_numeric(df['해제사유발생일'], errors='coerce')
            cancelled_deals = df[numeric_dates.notna()]

            if not cancelled_deals.empty:
                log_lines.append(f"=== '해제사유발생일'이 존재하여 삭제된 데이터 ({len(cancelled_deals)}건) ===")
                log_lines.append(cancelled_deals.to_string())
                log_lines.append("\n")
                # 숫자/날짜 형식의 값이 없는 행만 유지합니다.
                df = df[numeric_dates.isna()].copy()
                print(f"[FILTER] '해제사유발생일' 데이터 {len(cancelled_deals)}건 필터링 완료")

        # 로그 파일이 생성될 경우에만 저장
        if log_lines:
            try:
                with open(log_path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(log_lines))
                print(f"[FILTER] 필터링 로그 파일이 생성되었습니다: {log_path}")
            except Exception as e:
                print(f"[ERROR] 필터링 로그 파일 저장 실패: {e}")
        # --- 필터링 로직 종료 ---
        
        # 필요한 컬럼만 추출하여 메모리 사용량 감소
        col_map = {
            '시군구': '시군구',
            '번지': '번지',
            '단지명': '단지명',
            '전용면적(㎡)': '전용면적(㎡)',
            '계약년월': '계약년월',
            '거래금액': '거래금액',
            '층': '층',
            '건축년도': '건축년도',
            '도로명': '도로명',
        }
        
        # 메모리 효율적인 컬럼 선택
        available_cols = {k: v for k, v in col_map.items() if v in df.columns}
        result_df = df[list(available_cols.values())].copy()
        result_df = result_df.rename(columns={v: k for k, v in available_cols.items()})
        
        # 원본 DataFrame 메모리 해제
        del df
        gc.collect()
        
        print(f"[DEBUG] Result DataFrame shape: {result_df.shape}")
        
        # 데이터 타입 최적화
        if '거래금액' in result_df.columns:
            result_df['거래금액'] = result_df['거래금액'].astype(str).str.replace(',', '', regex=False)
            result_df['거래금액'] = pd.to_numeric(result_df['거래금액'], errors='coerce').astype('float32')
        
        # 숫자형 변환 (메모리 효율적인 타입 사용)
        for col in ['전용면적(㎡)', '계약년월', '층', '건축년도']:
            if col in result_df.columns:
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce').astype('float32')
        
        # 파생 컬럼 생성 (벡터화 연산 사용)
        if '전용면적(㎡)' in result_df.columns:
            result_df['전용평'] = (result_df['전용면적(㎡)'] * 0.3025).round(2).astype('float32')
        
        if '거래금액' in result_df.columns and '전용평' in result_df.columns:
            mask = (result_df['거래금액'].notna()) & (result_df['전용평'].notna()) & (result_df['전용평'] > 0)
            result_df['전용평당'] = np.where(mask, 
                                        (result_df['거래금액'] / result_df['전용평']).round(2), 
                                        np.nan).astype('float32')
        
        if '전용평당' in result_df.columns:
            result_df['공급평당'] = (result_df['전용평당'] * 0.75).round(2).astype('float32')
        
        # 인덱스 초기화
        result_df = result_df.reset_index(drop=True)
        columns = result_df.columns.tolist()
        
        # 임시 파일로 저장
        temp_dir = tempfile.gettempdir()
        temp_filename = f"realestate_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.csv"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # 임시 파일 추적 목록에 추가
        _temp_files.append(temp_path)
        
        result_df.to_csv(temp_path, index=False, encoding='utf-8-sig')
        print(f"[DEBUG] Processed CSV saved to: {temp_path}")
        
        return temp_path, columns
        
    except Exception as e:
        print(f"[ERROR] CSV 처리 중 오류 발생: {e}")
        raise

def get_stats(df):
    return {
        'total_count': len(df),
        'area_avg': df['전용면적(\u33A1)'].mean(),
        'price_avg': df['거래금액'].mean(),
        'regions': df['시군구'].value_counts().to_dict(),
        'complexes': df['단지명'].value_counts().to_dict()
    }

def clean_for_json(obj):
    if isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    elif isinstance(obj, set):
        return [clean_for_json(v) for v in list(obj)]
    elif obj is None or (isinstance(obj, float) and np.isnan(obj)):
        return ""
    else:
        return obj

def _decode_supabase_strings(df, columns_to_decode):
    """
    Supabase에서 가져온 DataFrame의 특정 컬럼에 대해 인코딩을 교정합니다.
    """
    for col in columns_to_decode:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.encode('latin1').decode('utf-8') if isinstance(x, str) else x)
    return df

def match_with_supabase(df, supabase: Client):
    """
    임시로 Supabase 연결 비활성화 - character varying(4) 오류 해결을 위해
    """
    print("[DEBUG] Supabase 매칭 임시 비활성화 - 로컬 분석 모드")
    print("[DEBUG] character varying(4) 오류 해결을 위해 Supabase 연결 스킵")
    
    # 위도/경도 컬럼 추가 (빈 값으로)
    df['위도'] = np.nan
    df['경도'] = np.nan
    
    # 중복 제거 로직은 유지
    print("[DEBUG] 중복 제거 시작...")
    original_count = len(df)
    
    # 실거래 핵심 정보 컬럼들을 기준으로 중복 제거
    key_columns = ['시군구', '번지', '단지명', '전용면적(㎡)', '계약년월', '거래금액', '층', '건축년도']
    available_key_columns = [col for col in key_columns if col in df.columns]
    
    if available_key_columns:
        # 중복 제거: 첫 번째 매칭 결과만 유지
        df = df.drop_duplicates(subset=available_key_columns, keep='first')
        final_count = len(df)
        removed_count = original_count - final_count
        
        print(f"[DEBUG] 중복 제거 결과: {original_count}건 → {final_count}건 (제거: {removed_count}건)")
        
        if removed_count > 0:
            print(f"[INFO] 중복 데이터 {removed_count}건이 제거되었습니다.")
    else:
        print("[DEBUG] 중복 제거용 키 컬럼을 찾을 수 없습니다.")
    
    print(f"[DEBUG] 최종 DataFrame shape: {df.shape}")
    return df