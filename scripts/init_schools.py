#!/usr/bin/env python
"""
초기 학교 데이터 삽입 스크립트
"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db
from src.database.repository import SchoolRepository
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def load_schools_data() -> dict:
    """
    schools_initial.json 파일에서 학교 데이터 로드
    
    Returns:
        학교 데이터 딕셔너리
    """
    data_file = Path(__file__).parent.parent / 'data' / 'schools_initial.json'
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.info(f"학교 데이터 로드 완료: {len(data['schools'])}개")
        return data
    except FileNotFoundError:
        logger.error(f"데이터 파일을 찾을 수 없음: {data_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSON 파싱 오류: {e}")
        raise


def insert_schools() -> None:
    """학교 데이터를 데이터베이스에 삽입"""
    
    logger.info("=== 초기 학교 데이터 삽입 시작 ===")
    
    # 데이터 로드
    data = load_schools_data()
    schools = data['schools']
    
    inserted_count = 0
    updated_count = 0
    skipped_count = 0
    
    with get_db() as db:
        repo = SchoolRepository(db)
        
        for school_data in schools:
            name = school_data['name']
            state = school_data.get('state')
            
            try:
                # 중복 체크
                existing_school = repo.get_by_name(name, state)
                
                if existing_school:
                    logger.info(f"⏭️  이미 존재: {name} ({state})")
                    
                    # 업데이트할 데이터가 있는지 확인
                    update_needed = False
                    for key, value in school_data.items():
                        if key == 'name' or key == 'state':
                            continue
                        if getattr(existing_school, key, None) != value:
                            update_needed = True
                            break
                    
                    if update_needed:
                        repo.update(existing_school.id, school_data)
                        updated_count += 1
                        logger.info(f"✅ 업데이트: {name}")
                    else:
                        skipped_count += 1
                else:
                    # 새로 삽입
                    repo.create(school_data)
                    inserted_count += 1
                    logger.info(f"✅ 삽입: {name} ({state})")
                    
            except Exception as e:
                logger.error(f"❌ 처리 실패: {name} - {e}")
                continue
    
    # 결과 출력
    logger.info("=" * 50)
    logger.info(f"📊 처리 결과:")
    logger.info(f"  - 신규 삽입: {inserted_count}개")
    logger.info(f"  - 업데이트: {updated_count}개")
    logger.info(f"  - 건너뜀: {skipped_count}개")
    logger.info(f"  - 총 처리: {inserted_count + updated_count + skipped_count}개")
    logger.info("=" * 50)
    logger.info("✅ 초기 학교 데이터 삽입 완료!")


if __name__ == '__main__':
    try:
        insert_schools()
    except Exception as e:
        logger.error(f"스크립트 실행 실패: {e}")
        sys.exit(1)
