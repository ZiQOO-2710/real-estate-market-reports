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
    Pandas DataFrame의 데이터를 Supabase와 다단계로 매칭하여 위도/경도 정보를 추가합니다.
    """
    # 문자열 길이 제한 (Supabase 스키마에 맞춤)
    if '시군구' in df.columns:
        df['시군구'] = df['시군구'].astype(str).str[:50]  # 시군구는 50자로 제한
    if '단지명' in df.columns:
        df['단지명'] = df['단지명'].astype(str).str[:100]  # 단지명은 100자로 제한
    if '도로명' in df.columns:
        df['도로명'] = df['도로명'].astype(str).str[:100]  # 도로명은 100자로 제한
    print("[DEBUG] 문자열 길이 제한 적용 완료")
    
    df['위도'] = np.nan
    df['경도'] = np.nan

    # 1단계: 단지명 (CSV) vs apt_nm (DB)
    print("[DEBUG] Supabase 매칭 1단계: 단지명 매칭 시도...")
    unmatched_df = df[df['위도'].isna()].copy()
    if not unmatched_df.empty:
        unique_complex_names = unmatched_df['단지명'].dropna().unique().tolist()
        if unique_complex_names:
            try:
                response = supabase.table('apt_master_info') \
                                 .select('apt_nm', 'la', 'lo') \
                                 .in_('apt_nm', unique_complex_names) \
                                 .execute()
                if response.data:
                    supabase_df = pd.DataFrame(response.data)
                    supabase_df = supabase_df.rename(columns={'la': '위도', 'lo': '경도', 'apt_nm': '단지명'})
                    # 중복 매칭 방지: 단지명 기준으로 중복 제거 후 첫번째 값만 사용
                    supabase_df = supabase_df.drop_duplicates(subset=['단지명'], keep='first')
                    df = pd.merge(df, supabase_df[['단지명', '위도', '경도']], on='단지명', how='left', suffixes= ('_old', ''))
                    df['위도'] = df['위도'].fillna(df['위도_old'])
                    df['경도'] = df['경도'].fillna(df['경도_old'])
                    df = df.drop(columns=['위도_old', '경도_old'])
                    print(f"[DEBUG] 1단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
            except Exception as e:
                print(f"[ERROR] Supabase 1단계 매칭 중 오류 발생: {e}")

    # 2단계: 도로명 (CSV) vs rdnmadr (DB)
    print("[DEBUG] Supabase 매칭 2단계: 도로명 매칭 시도...")
    unmatched_df = df[df['위도'].isna()].copy()
    if not unmatched_df.empty:
        unique_road_names = unmatched_df['도로명'].dropna().unique().tolist()
        if unique_road_names:
            try:
                response = supabase.table('apt_master_info') \
                                 .select('rdnmadr', 'la', 'lo') \
                                 .in_('rdnmadr', unique_road_names) \
                                 .execute()
                if response.data:
                    supabase_df = pd.DataFrame(response.data)
                    supabase_df = supabase_df.rename(columns={'la': '위도', 'lo': '경도', 'rdnmadr': '도로명'})
                    # 중복 매칭 방지: 도로명 기준으로 중복 제거 후 첫번째 값만 사용
                    supabase_df = supabase_df.drop_duplicates(subset=['도로명'], keep='first')
                    df = pd.merge(df, supabase_df[['도로명', '위도', '경도']], on='도로명', how='left', suffixes= ('_old', ''))
                    df['위도'] = df['위도'].fillna(df['위도_old'])
                    df['경도'] = df['경도'].fillna(df['경도_old'])
                    df = df.drop(columns=['위도_old', '경도_old'])
                    print(f"[DEBUG] 2단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
            except Exception as e:
                print(f"[ERROR] Supabase 2단계 매칭 중 오류 발생: {e}")

    # 3단계: 시군구 + 번지 (CSV) vs ltno_adres (DB)
    print("[DEBUG] Supabase 매칭 3단계: 시군구+번지 매칭 시도...")
    unmatched_df = df[df['위도'].isna()].copy()
    if not unmatched_df.empty:
        unmatched_df['full_address'] = unmatched_df['시군구'].fillna('') + ' ' + unmatched_df['번지'].fillna('').astype(str)
        unique_full_addresses = unmatched_df['full_address'].dropna().unique().tolist()
        if unique_full_addresses:
            try:
                response = supabase.table('apt_master_info') \
                                 .select('lnno_adres', 'la', 'lo') \
                                 .in_('lnno_adres', unique_full_addresses) \
                                 .execute()
                if response.data:
                    supabase_df = pd.DataFrame(response.data)
                    supabase_df = supabase_df.rename(columns={'la': '위도', 'lo': '경도', 'lnno_adres': 'full_address'})
                    # 중복 매칭 방지: full_address 기준으로 중복 제거 후 첫번째 값만 사용
                    supabase_df = supabase_df.drop_duplicates(subset=['full_address'], keep='first')
                    df = pd.merge(df, supabase_df[['full_address', '위도', '경도']], on='full_address', how='left', suffixes= ('_old', ''))
                    df['위도'] = df['위도'].fillna(df['위도_old'])
                    df['경도'] = df['경도'].fillna(df['경도_old'])
                    df = df.drop(columns=['위도_old', '경도_old'])
                    print(f"[DEBUG] 3단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
            except Exception as e:
                print(f"[ERROR] Supabase 3단계 매칭 중 오류 발생: {e}")
    df = df.drop(columns=['full_address'], errors='ignore') # 임시 컬럼 삭제

    # 4단계: 시군구 (CSV) vs ltno_adres (DB) (부분 매칭 - '동'까지만) - 최적화된 버전
    print("[DEBUG] Supabase 매칭 4단계: 시군구 부분 매칭 시도...")
    unmatched_df = df[df['위도'].isna()].copy()
    if not unmatched_df.empty:
        try:
            # 모든 ltno_adres 데이터를 미리 가져옵니다.
            response = supabase.table('apt_master_info') \
                             .select('lnno_adres', 'la', 'lo') \
                             .execute()
            print(f"[DEBUG] Supabase 4단계 전체 데이터 쿼리 결과 (response.data): {response.data[:5] if response.data else 'No data'}")
            if response.data:
                db_addresses = pd.DataFrame(response.data)
                db_addresses = db_addresses.rename(columns={'la': '위도_db', 'lo': '경도_db'})
                
                # 최적화: DB 주소를 전처리하여 매칭 키 생성
                db_addresses['match_key'] = db_addresses['lnno_adres'].apply(
                    lambda x: ' '.join(str(x).split(' ')[:3]) if pd.notna(x) else ''
                )
                
                # 최적화: CSV 데이터에 매칭 키 생성
                unmatched_df['match_key'] = unmatched_df['시군구'].fillna('')
                
                # 최적화: 벡터화된 매칭 수행
                matched_data = unmatched_df.merge(
                    db_addresses[['match_key', '위도_db', '경도_db']].drop_duplicates('match_key'),
                    on='match_key', 
                    how='left'
                )
                
                # 매칭된 결과를 원본 DataFrame에 반영
                for idx, row in matched_data.iterrows():
                    if pd.notna(row['위도_db']) and pd.notna(row['경도_db']):
                        df.loc[unmatched_df.index[idx], '위도'] = row['위도_db']
                        df.loc[unmatched_df.index[idx], '경도'] = row['경도_db']
                        
                print(f"[DEBUG] 4단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
        except Exception as e:
            print(f"[ERROR] Supabase 4단계 매칭 중 오류 발생: {e}")

    # 최종적으로 위도/경도가 없는 경우 NaN 유지
    df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
    df['경도'] = pd.to_numeric(df['경도'], errors='coerce')

    # 매칭 후 중복 제거: 실거래 핵심 정보 기준으로 중복 제거
    print("[DEBUG] 매칭 후 중복 제거 시작...")
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
            print(f"[INFO] Supabase 매칭 과정에서 발생한 중복 데이터 {removed_count}건이 제거되었습니다.")
    else:
        print("[DEBUG] 중복 제거용 키 컬럼을 찾을 수 없습니다.")

    return df