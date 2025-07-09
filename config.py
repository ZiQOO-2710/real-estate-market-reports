"""
애플리케이션 설정 관리 모듈
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """기본 설정 클래스"""
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'a_default_secret_key')
    UPLOAD_FOLDER = 'uploads'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    
    # Supabase 설정
    SUPABASE_URL = os.environ.get('SUPABASE_URL')
    SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
    
    # 카카오 API 설정
    KAKAO_REST_API_KEY = os.environ.get('KAKAO_REST_API_KEY')
    
    # 성능 튜닝 설정
    PANDAS_LOW_MEMORY = False
    CACHE_SIZE = 1000
    API_RATE_LIMIT = 0.1  # 100ms 간격
    
    @staticmethod
    def validate_config():
        """필수 설정 값들을 검증"""
        required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'KAKAO_REST_API_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            raise ValueError(f"필수 환경 변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        
        return True

class DevelopmentConfig(Config):
    """개발환경 설정"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """프로덕션 환경 설정"""
    DEBUG = False
    TESTING = False
    
    # 프로덕션 환경에서는 더 엄격한 설정
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB
    CACHE_SIZE = 2000

class TestingConfig(Config):
    """테스트 환경 설정"""
    DEBUG = True
    TESTING = True
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024  # 1MB

# 환경별 설정 매핑
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(env_name='default'):
    """환경에 따른 설정 객체를 반환"""
    return config_map.get(env_name, DevelopmentConfig)