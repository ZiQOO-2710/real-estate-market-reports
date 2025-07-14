#!/usr/bin/env python3
"""
Supabase 설정 및 초기 테이블 생성 스크립트
"""

import os
import sys
from supabase import create_client, Client
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseSetup:
    """Supabase 초기 설정 클래스"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Args:
            supabase_url: Supabase 프로젝트 URL
            supabase_key: Supabase 서비스 역할 키 (또는 anon 키)
        """
        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("✅ Supabase 클라이언트 연결 성공")
        except Exception as e:
            logger.error(f"❌ Supabase 연결 실패: {e}")
            sys.exit(1)
            
    def read_sql_file(self, file_path: str) -> str:
        """SQL 파일 읽기"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"SQL 파일 읽기 실패: {e}")
            return ""
            
    def execute_sql_commands(self, sql_content: str) -> bool:
        """SQL 명령어들 실행"""
        try:
            # SQL을 개별 명령어로 분리 (;으로 구분)
            commands = [cmd.strip() for cmd in sql_content.split(';') if cmd.strip()]
            
            for i, command in enumerate(commands, 1):
                if command.upper().startswith(('CREATE', 'ALTER', 'INSERT', 'DROP')):
                    try:
                        # Supabase에서는 rpc를 통해 SQL 실행
                        result = self.supabase.rpc('exec_sql', {'query': command}).execute()
                        logger.info(f"✅ SQL 명령 {i}/{len(commands)} 실행 완료")
                    except Exception as e:
                        logger.warning(f"⚠️ SQL 명령 {i} 실행 오류: {e}")
                        # 테이블이 이미 존재하는 경우 등은 무시
                        continue
                        
            return True
            
        except Exception as e:
            logger.error(f"❌ SQL 실행 실패: {e}")
            return False
            
    def create_exec_sql_function(self) -> bool:
        """SQL 실행용 함수 생성 (Supabase에서 필요)"""
        try:
            sql_function = """
            CREATE OR REPLACE FUNCTION exec_sql(query text)
            RETURNS text AS $$
            BEGIN
                EXECUTE query;
                RETURN 'Success';
            EXCEPTION WHEN OTHERS THEN
                RETURN 'Error: ' || SQLERRM;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # 직접 실행 시도 (관리자 권한 필요)
            result = self.supabase.rpc('exec_sql', {'query': sql_function}).execute()
            logger.info("✅ SQL 실행 함수 생성 완료")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ SQL 실행 함수 생성 실패: {e}")
            logger.info("💡 Supabase 대시보드에서 직접 스키마를 생성해주세요.")
            return False
            
    def test_connection(self) -> bool:
        """연결 테스트"""
        try:
            # 간단한 쿼리로 연결 테스트
            result = self.supabase.table('apartment_complexes').select('*').limit(1).execute()
            logger.info("✅ 데이터베이스 연결 테스트 성공")
            return True
        except Exception as e:
            logger.info(f"ℹ️ 테이블이 아직 생성되지 않음: {e}")
            return False
            
    def create_sample_data(self) -> bool:
        """샘플 데이터 생성"""
        try:
            sample_complex = {
                'complex_id': 'test_001',
                'complex_name': '테스트 아파트',
                'address': '서울시 테스트구 테스트동',
                'completion_year': 2020,
                'total_households': 500,
                'source_url': 'https://test.com'
            }
            
            result = self.supabase.table('apartment_complexes').insert(sample_complex).execute()
            logger.info("✅ 샘플 데이터 생성 완료")
            
            # 샘플 데이터 삭제
            self.supabase.table('apartment_complexes').delete().eq('complex_id', 'test_001').execute()
            logger.info("✅ 샘플 데이터 정리 완료")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 샘플 데이터 테스트 실패: {e}")
            return False

def main():
    """메인 설정 함수"""
    print("🚀 Supabase 데이터베이스 설정을 시작합니다!")
    
    # 환경변수에서 Supabase 정보 가져오기
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("\n❌ Supabase 설정이 필요합니다!")
        print("다음 명령어로 환경변수를 설정해주세요:")
        print("export SUPABASE_URL='https://your-project.supabase.co'")
        print("export SUPABASE_KEY='your-anon-or-service-key'")
        print("\n📝 Supabase 프로젝트에서 다음 정보를 확인하세요:")
        print("1. Project URL: Settings > API > Project URL")
        print("2. API Key: Settings > API > Project API keys > anon/public")
        return
        
    # Supabase 설정 실행
    setup = SupabaseSetup(supabase_url, supabase_key)
    
    print("\n📋 설정 단계:")
    print("1. 연결 테스트")
    print("2. 스키마 파일 읽기")
    print("3. 테이블 생성")
    print("4. 기능 테스트")
    
    # 1. 연결 테스트
    print("\n🔍 1. Supabase 연결 테스트...")
    setup.test_connection()
    
    # 2. 스키마 파일 읽기
    print("\n📂 2. 스키마 파일 읽기...")
    schema_file = "supabase_schema.sql"
    if os.path.exists(schema_file):
        sql_content = setup.read_sql_file(schema_file)
        if sql_content:
            logger.info(f"✅ 스키마 파일 읽기 완료 ({len(sql_content.split(';'))}개 명령어)")
        else:
            logger.error("❌ 스키마 파일이 비어있습니다")
            return
    else:
        logger.error(f"❌ 스키마 파일을 찾을 수 없습니다: {schema_file}")
        return
        
    # 3. 테이블 생성 안내
    print("\n🏗️ 3. 테이블 생성...")
    print("⚠️ Supabase에서는 보안상 SQL 실행이 제한될 수 있습니다.")
    print("📋 다음 방법 중 하나를 선택해주세요:")
    print("   A. Supabase 대시보드 > SQL Editor에서 supabase_schema.sql 내용 실행")
    print("   B. 이 스크립트로 자동 생성 시도")
    
    choice = input("\n선택 (A/B): ").strip().upper()
    
    if choice == 'B':
        print("🔄 자동 테이블 생성 시도...")
        success = setup.execute_sql_commands(sql_content)
        if success:
            print("✅ 테이블 생성 완료!")
        else:
            print("❌ 자동 생성 실패. 수동으로 생성해주세요.")
            
    # 4. 최종 테스트
    print("\n🧪 4. 최종 연결 및 기능 테스트...")
    if setup.test_connection():
        print("🎉 모든 설정이 완료되었습니다!")
        print("\n📁 다음 파일들을 사용할 수 있습니다:")
        print("- supabase_data_processor.py: 크롤링 데이터를 DB로 변환")
        print("- supabase_schema.sql: 테이블 스키마 정의")
        
        print("\n🚀 데이터 삽입 실행:")
        print("python supabase_data_processor.py")
        
    else:
        print("⚠️ 테이블이 생성되지 않았을 수 있습니다.")
        print("Supabase 대시보드에서 수동으로 스키마를 생성해주세요.")

if __name__ == "__main__":
    main()