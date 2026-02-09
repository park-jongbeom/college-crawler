"""
데이터베이스 연결 관리 모듈
"""

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from typing import Generator

from ..utils.config import config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# Engine 생성 (싱글톤)
engine = create_engine(
    config.DATABASE_URL,
    echo=False,  # SQL 로깅 (개발 시에는 True)
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_size=5,
    max_overflow=10
)

# SessionLocal 클래스
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션을 제공하는 컨텍스트 매니저
    
    Yields:
        데이터베이스 세션
        
    Example:
        with get_db() as db:
            schools = db.query(School).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"데이터베이스 트랜잭션 오류: {e}")
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    데이터베이스 초기화 (테이블 생성)
    
    Note:
        프로덕션에서는 Alembic 마이그레이션 사용 권장
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블 생성 완료")
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise


def test_connection() -> bool:
    """
    데이터베이스 연결 테스트
    
    Returns:
        연결 성공 여부
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("데이터베이스 연결 성공")
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        return False
