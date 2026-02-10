#!/usr/bin/env python
"""
데이터베이스 상태 확인 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db, test_connection
from src.database.repository import SchoolRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def check_database() -> None:
    """데이터베이스 연결 및 데이터 확인"""
    
    logger.info("=== 데이터베이스 상태 확인 ===")
    
    # 1. 연결 테스트
    logger.info("1. 데이터베이스 연결 테스트...")
    if not test_connection():
        logger.error("데이터베이스 연결 실패")
        return
    
    # 2. 학교 데이터 확인
    logger.info("\n2. 학교 데이터 확인...")
    with get_db() as db:
        repo = SchoolRepository(db)
        
        # 전체 개수
        total_count = repo.count()
        logger.info(f"   전체 학교 수: {total_count}개")
        
        # 주별 통계
        ca_schools = repo.get_by_state('CA')
        tx_schools = repo.get_by_state('TX')
        logger.info(f"   캘리포니아 (CA): {len(ca_schools)}개")
        logger.info(f"   텍사스 (TX): {len(tx_schools)}개")
        
        # 최근 학교 10개
        logger.info("\n3. 최근 등록 학교 (최대 10개):")
        recent_schools = repo.get_all(skip=0, limit=10)
        for i, school in enumerate(recent_schools, 1):
            logger.info(f"   {i}. {school.name} ({school.state})")
            if school.international_email:
                logger.info(f"      📧 {school.international_email}")
            if school.international_phone:
                logger.info(f"      📞 {school.international_phone}")
        
        # 국제 학생 담당자 정보 있는 학교
        schools_with_intl = [s for s in repo.get_all() if s.international_email]
        logger.info(f"\n4. 유학생 담당자 정보가 있는 학교: {len(schools_with_intl)}개")
    
    logger.info("\n=== 확인 완료 ===")


if __name__ == '__main__':
    try:
        check_database()
    except Exception as e:
        logger.error(f"스크립트 실행 실패: {e}")
        sys.exit(1)
