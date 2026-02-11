"""
환경 변수 설정 모듈
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """환경 변수 설정 클래스"""
    
    # Database
    DATABASE_HOST: str = os.getenv('DATABASE_HOST', 'localhost')
    DATABASE_PORT: int = int(os.getenv('DATABASE_PORT', '5432'))
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'ga_db')
    DATABASE_USER: str = os.getenv('DATABASE_USER') or 'postgres'  # 빈 문자열도 기본값으로 대체
    DATABASE_PASSWORD: str = os.getenv('DATABASE_PASSWORD') or ''
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL 연결 URL"""
        return f"postgresql://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
    
    # Crawling Settings
    CRAWL_DELAY: int = int(os.getenv('CRAWL_DELAY', '2'))
    MAX_RETRY: int = int(os.getenv('MAX_RETRY', '3'))
    CRAWL_TIMEOUT: int = int(os.getenv('CRAWL_TIMEOUT', '30'))
    USER_AGENT: str = os.getenv('USER_AGENT', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE: str = os.getenv('LOG_FILE', 'logs/app.log')
    LOG_MAX_BYTES: int = int(os.getenv('LOG_MAX_BYTES', '10485760'))
    LOG_BACKUP_COUNT: int = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Application
    APP_NAME: str = os.getenv('APP_NAME', 'College Crawler')
    APP_VERSION: str = os.getenv('APP_VERSION', '1.0.0')
    ENVIRONMENT: str = os.getenv('ENVIRONMENT', 'development')


# 싱글톤 인스턴스
config = Config()
