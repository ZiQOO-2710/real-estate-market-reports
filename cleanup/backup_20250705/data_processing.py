import pandas as pd
import numpy as np
import re
import os
from supabase import Client
import tempfile
from datetime import datetime
import shutil
import chardet

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
    with open(file_path, 'rb') as f:
        raw = f.read(10000)
        encoding = chardet.detect(raw)['encoding'] or 'utf-8'
    # 1~15줄 건너뛰고 16번째 줄을 컬럼명으로 사용
    df = pd.read_csv(file_path, encoding=encoding, skiprows=15)
    print(f"[DEBUG] Original DataFrame head:\n{df.head()}")
    print(f"[DEBUG] Original DataFrame columns: {df.columns.tolist()}")

    df = normalize_columns(df)
    print(f"[DEBUG] Normalized DataFrame head:\n{df.head()}")
    print(f"[DEBUG] Normalized DataFrame columns: {df.columns.tolist()}")

    # 2. 필요한 컬럼만 추출 (B, C, F, G, H, J, L, O, P)
    # 컬럼명: 시군구, 번지, 단지명, 전용면적(㎡), 계약년월, 거래금액(만원), 층, 건축년도, 도로명
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
    # 실제 컬럼명과 매칭하여 DataFrame 생성
    result_df = pd.DataFrame({k: df[v] if v in df.columns else [np.nan]*len(df) for k, v in col_map.items()})
    print(f"[DEBUG] Result DataFrame (after col_map) head:\n{result_df.head()}")
    print(f"[DEBUG] Result DataFrame (after col_map) columns: {result_df.columns.tolist()}")

    # 거래금액 쉼표 제거 후 숫자 변환
    if '거래금액' in result_df.columns:
        result_df['거래금액'] = result_df['거래금액'].replace({',': ''}, regex=True)
        result_df['거래금액'] = pd.to_numeric(result_df['거래금액'], errors='coerce')
    print(f"[DEBUG] Result DataFrame (after 거래금액 numeric) head:\n{result_df.head()}")

    # 3. 숫자형 변환 및 파생 컬럼 생성
    for col in ['전용면적(㎡)', '계약년월', '층', '건축년도']:
        if col in result_df.columns:
            result_df[col] = pd.to_numeric(result_df[col], errors='coerce')
    print(f"[DEBUG] Result DataFrame (after numeric conversion) head:\n{result_df.head()}")

    result_df['전용평'] = result_df['전용면적(㎡)'].apply(lambda x: round(x * 0.3025, 2) if pd.notnull(x) and x > 0 else np.nan)
    result_df['전용평당'] = result_df.apply(
        lambda row: round(row['거래금액'] / row['전용평'], 2) if pd.notnull(row['거래금액']) and pd.notnull(row['전용평']) and row['전용평'] > 0 else np.nan, axis=1)
    result_df['공급평당'] = result_df['전용평당'].apply(lambda x: round(x * 0.75, 2) if pd.notnull(x) and x > 0 else np.nan)
    print(f"[DEBUG] Result DataFrame (after derived columns) head:\n{result_df.head()}")

    # 인덱스 초기화, 불필요 컬럼 제거
    result_df = result_df.reset_index(drop=True)
    columns = [col for col in result_df.columns]
    # 임시 파일로 저장
    temp_dir = tempfile.gettempdir()
    temp_filename = f"realestate_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.csv"
    temp_path = os.path.join(temp_dir, temp_filename)
    result_df.to_csv(temp_path, index=False, encoding='utf-8-sig')
    print(f"[DEBUG] Processed CSV saved to: {temp_path}")
    return temp_path, columns

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
                    df = pd.merge(df, supabase_df[['full_address', '위도', '경도']], on='full_address', how='left', suffixes= ('_old', ''))
                    df['위도'] = df['위도'].fillna(df['위도_old'])
                    df['경도'] = df['경도'].fillna(df['경도_old'])
                    df = df.drop(columns=['위도_old', '경도_old'])
                    print(f"[DEBUG] 3단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
            except Exception as e:
                print(f"[ERROR] Supabase 3단계 매칭 중 오류 발생: {e}")
    df = df.drop(columns=['full_address'], errors='ignore') # 임시 컬럼 삭제

    # 4단계: 시군구 (CSV) vs ltno_adres (DB) (부분 매칭 - '동'까지만)
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
                # CSV의 각 미매칭 행에 대해 부분 매칭 시도
                for idx, row in unmatched_df.iterrows():
                    if pd.isna(row['위도']):
                        csv_sigungu = row['시군구']
                        if pd.notna(csv_sigungu):
                            # DB 주소에서 시군구동 부분을 추출하여 비교
                            matched_db_row = None
                            for _, db_row in db_addresses.iterrows():
                                db_lnno_adres = str(db_row['lnno_adres'])
                                print(f"[DEBUG] 4단계 비교: CSV='{csv_sigungu}' vs DB='{db_lnno_adres}'")
                                db_sigungu_parts = db_lnno_adres.split(' ')
                                csv_sigungu_parts = csv_sigungu.split(' ')
                                if len(db_sigungu_parts) >= 2 and len(csv_sigungu_parts) >= 2 and \
                                   db_sigungu_parts[0] == csv_sigungu_parts[0] and \
                                   db_sigungu_parts[1] == csv_sigungu_parts[1]:
                                    if len(db_sigungu_parts) >= 3 and len(csv_sigungu_parts) >= 3:
                                        if db_sigungu_parts[2] == csv_sigungu_parts[2]:
                                            matched_db_row = db_row
                                            break
                                    elif len(db_sigungu_parts) < 3 and len(csv_sigungu_parts) < 3:
                                        matched_db_row = db_row
                                        break
                            if matched_db_row is not None:
                                df.loc[idx, '위도'] = matched_db_row['위도_db']
                                df.loc[idx, '경도'] = matched_db_row['경도_db']
                print(f"[DEBUG] 4단계 매칭 후 남은 미매칭 건수: {df['위도'].isna().sum()}")
        except Exception as e:
            print(f"[ERROR] Supabase 4단계 매칭 중 오류 발생: {e}")

    # 최종적으로 위도/경도가 없는 경우 NaN 유지
    df['위도'] = pd.to_numeric(df['위도'], errors='coerce')
    df['경도'] = pd.to_numeric(df['경도'], errors='coerce')

    return df