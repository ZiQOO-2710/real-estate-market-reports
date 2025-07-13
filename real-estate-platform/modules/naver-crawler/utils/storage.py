"""
데이터 저장 모듈
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import pandas as pd
from loguru import logger

from config.settings import DATA_CONFIG


class DataStorage:
    """데이터 저장 클래스"""
    
    def __init__(self):
        self.output_dir = DATA_CONFIG["output_dir"]
        self.ensure_directories()
        
    def ensure_directories(self):
        """필요한 디렉토리 생성"""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    async def save_to_csv(self, data: List[Dict], filename: str) -> str:
        """CSV 파일로 저장"""
        try:
            if not data:
                logger.warning("저장할 데이터가 없습니다")
                return ""
                
            filepath = self.output_dir / filename
            
            # 데이터프레임 변환
            df = pd.DataFrame(data)
            
            # CSV 저장
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
            
            logger.info(f"CSV 파일 저장 완료: {filepath}")
            logger.info(f"저장된 데이터: {len(df)}행 x {len(df.columns)}열")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"CSV 저장 오류: {e}")
            return ""
            
    async def save_to_json(self, data: List[Dict], filename: str) -> str:
        """JSON 파일로 저장"""
        try:
            if not data:
                logger.warning("저장할 데이터가 없습니다")
                return ""
                
            filepath = self.output_dir / filename
            
            # JSON 저장
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"JSON 파일 저장 완료: {filepath}")
            logger.info(f"저장된 데이터: {len(data)}개 항목")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"JSON 저장 오류: {e}")
            return ""
            
    async def save_to_excel(self, data: List[Dict], filename: str) -> str:
        """Excel 파일로 저장"""
        try:
            if not data:
                logger.warning("저장할 데이터가 없습니다")
                return ""
                
            filepath = self.output_dir / filename.replace('.csv', '.xlsx')
            
            # 데이터프레임 변환
            df = pd.DataFrame(data)
            
            # Excel 저장
            df.to_excel(filepath, index=False, engine='openpyxl')
            
            logger.info(f"Excel 파일 저장 완료: {filepath}")
            logger.info(f"저장된 데이터: {len(df)}행 x {len(df.columns)}열")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Excel 저장 오류: {e}")
            return ""
            
    def get_file_info(self, filepath: str) -> Dict:
        """파일 정보 조회"""
        try:
            path = Path(filepath)
            
            if not path.exists():
                return {"error": "파일이 존재하지 않습니다"}
                
            stat = path.stat()
            
            return {
                "filename": path.name,
                "size": stat.st_size,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                "extension": path.suffix
            }
            
        except Exception as e:
            logger.error(f"파일 정보 조회 오류: {e}")
            return {"error": str(e)}
            
    def list_output_files(self) -> List[Dict]:
        """출력 파일 목록 조회"""
        try:
            files = []
            
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file():
                    file_info = self.get_file_info(str(file_path))
                    files.append(file_info)
                    
            # 수정 날짜 기준으로 정렬
            files.sort(key=lambda x: x.get("modified", ""), reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"파일 목록 조회 오류: {e}")
            return []
            
    def backup_existing_file(self, filepath: str) -> bool:
        """기존 파일 백업"""
        try:
            path = Path(filepath)
            
            if not path.exists():
                return True
                
            # 백업 파일명 생성
            backup_name = f"{path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{path.suffix}"
            backup_path = path.parent / backup_name
            
            # 파일 복사
            path.rename(backup_path)
            
            logger.info(f"기존 파일 백업 완료: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"파일 백업 오류: {e}")
            return False
            
    def merge_csv_files(self, file_paths: List[str], output_filename: str) -> str:
        """여러 CSV 파일 병합"""
        try:
            if not file_paths:
                logger.warning("병합할 파일이 없습니다")
                return ""
                
            all_data = []
            
            for file_path in file_paths:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                    all_data.append(df)
                    logger.info(f"파일 로드 완료: {file_path} ({len(df)}행)")
                    
                except Exception as e:
                    logger.error(f"파일 로드 실패: {file_path} - {e}")
                    continue
                    
            if not all_data:
                logger.error("병합할 데이터가 없습니다")
                return ""
                
            # 데이터프레임 병합
            merged_df = pd.concat(all_data, ignore_index=True)
            
            # 중복 제거
            original_count = len(merged_df)
            merged_df = merged_df.drop_duplicates()
            deduplicated_count = len(merged_df)
            
            # 결과 저장
            output_path = self.output_dir / output_filename
            merged_df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"파일 병합 완료: {output_path}")
            logger.info(f"총 {original_count}행 -> {deduplicated_count}행 (중복 {original_count - deduplicated_count}행 제거)")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"파일 병합 오류: {e}")
            return ""
            
    async def save_to_supabase(self, data: List[Dict], table_name: str = "naver_apt_data") -> Optional[int]:
        """
        Supabase에 데이터를 저장합니다.
        테이블 이름은 'real_estate_data'로 가정합니다.
        """
        if not self.supabase:
            logger.error("Supabase 클라이언트가 초기화되지 않았습니다. 데이터를 저장할 수 없습니다.")
            return None
        
        if not data:
            logger.warning("Supabase에 저장할 데이터가 없습니다.")
            return 0
            
        try:
            # Supabase에 삽입할 데이터 준비
            # Python dict의 None 값은 Supabase의 NULL로 자동 매핑됩니다.
            # 날짜/시간 형식은 Supabase의 timestamp with time zone에 맞게 조정될 수 있습니다.
            # 여기서는 크롤러에서 이미 문자열로 처리하고 있으므로 그대로 전달합니다.
            
            # 데이터 정제: Supabase에 맞지 않는 필드 제거 또는 변환
            cleaned_data = []
            for item in data:
                cleaned_item = item.copy()
                # 예시: '가격' 필드가 문자열 '10억 5,000만원' 형태일 경우 숫자형으로 변환
                # 이 부분은 Supabase 스키마에 따라 조정 필요
                if '가격' in cleaned_item and isinstance(cleaned_item['가격'], str):
                    try:
                        price_str = cleaned_item['가격'].replace('억', '00000000').replace(',', '').replace('만원', '0000')
                        cleaned_item['가격'] = int(price_str)
                    except ValueError:
                        cleaned_item['가격'] = None # 변환 실패 시 None
                
                # 위도, 경도 필드명 조정 (Supabase 스키마에 맞게)
                if '위도' in cleaned_item:
                    cleaned_item['latitude'] = cleaned_item.pop('위도')
                if '경도' in cleaned_item:
                    cleaned_item['longitude'] = cleaned_item.pop('경도')
                
                # 거래일자 필드명 조정 및 형식 변환 (Supabase date 타입에 맞게)
                if '거래일자' in cleaned_item and isinstance(cleaned_item['거래일자'], str):
                    try:
                        cleaned_item['transaction_date'] = datetime.strptime(cleaned_item['거래일자'], '%Y-%m-%d').date().isoformat()
                    except ValueError:
                        cleaned_item['transaction_date'] = None
                    cleaned_item.pop('거래일자') # 원본 필드 제거
                
                # 수집일시 필드명 조정 및 형식 변환 (Supabase timestamp with time zone 타입에 맞게)
                if '수집일시' in cleaned_item and isinstance(cleaned_item['수집일시'], str):
                    try:
                        cleaned_item['collected_at'] = datetime.strptime(cleaned_item['수집일시'], '%Y-%m-%d %H:%M:%S').isoformat() + '+09:00' # 한국 시간대
                    except ValueError:
                        cleaned_item['collected_at'] = None
                    cleaned_item.pop('수집일시') # 원본 필드 제거
                
                cleaned_data.append(cleaned_item)

            response = await self.supabase.table(table_name).insert(cleaned_data).execute()
            
            if response.data:
                logger.info(f"Supabase에 {len(response.data)}개 데이터 저장 완료 (테이블: {table_name})")
                return len(response.data)
            elif response.error:
                logger.error(f"Supabase 저장 오류 (테이블: {table_name}): {response.error.message}")
                return None
            
        except Exception as e:
            logger.error(f"Supabase 저장 중 예외 발생: {e}")
            return None
            
    def cleanup_old_files(self, days: int = 30) -> int:
        """오래된 파일 정리"""
        try:
            import time
            
            current_time = time.time()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            deleted_count = 0
            
            for file_path in self.output_dir.glob("*"):
                if file_path.is_file():
                    if file_path.stat().st_mtime < cutoff_time:
                        file_path.unlink()
                        deleted_count += 1
                        logger.info(f"오래된 파일 삭제: {file_path.name}")
                        
            logger.info(f"파일 정리 완료: {deleted_count}개 파일 삭제")
            return deleted_count
            
        except Exception as e:
            logger.error(f"파일 정리 오류: {e}")
            return 0