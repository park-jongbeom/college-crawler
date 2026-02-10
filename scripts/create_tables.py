#!/usr/bin/env python
"""
데이터베이스 테이블 생성 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import engine, Base
from src.database.models import School, Program, AuditLog
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def create_all_tables():
    """필수 테이블 생성 (SchoolDocument 제외 - pgvector 필요)"""
    try:
        logger.info("=== 데이터베이스 테이블 생성 시작 ===")
        
        # 필수 테이블만 생성 (SchoolDocument는 pgvector 필요로 제외)
        School.__table__.create(bind=engine, checkfirst=True)
        Program.__table__.create(bind=engine, checkfirst=True)
        AuditLog.__table__.create(bind=engine, checkfirst=True)
        
        logger.info("✅ 필수 테이블 생성 완료")
        logger.info("생성된 테이블:")
        logger.info("  - schools")
        logger.info("  - programs")
        logger.info("  - audit_logs")
        logger.info("")
        logger.info("ℹ️  school_documents 테이블은 pgvector 확장이 필요하여 제외됨")
            
    except Exception as e:
        logger.error(f"❌ 테이블 생성 실패: {e}")
        raise


if __name__ == '__main__':
    try:
        create_all_tables()
    except Exception as e:
        logger.error(f"스크립트 실행 실패: {e}")
        sys.exit(1)
