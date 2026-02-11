"""
College Crawler 메인 실행 파일
"""

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from src.crawlers.school_crawler import SchoolCrawler
from src.database.connection import get_db
from src.database.models import AuditLog, School
from src.database.repository import SchoolRepository
from src.services.scorecard_enrichment_service import ScorecardEnrichmentService
from src.utils.failed_sites import failed_site_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)
SYSTEM_ACTOR_ID = uuid.UUID("00000000-0000-0000-0000-000000000000")
_AUDIT_USER_ID_CACHE: Optional[uuid.UUID] = None
_SCORECARD_SERVICE = ScorecardEnrichmentService()


def load_schools_list(json_file: Path) -> list:
    """
    학교 목록 JSON 파일 로드
    
    Args:
        json_file: JSON 파일 경로
        
    Returns:
        학교 목록
    """
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('schools', [])


def _find_school_record(db, name: str, website: str) -> Optional[School]:
    """이름/웹사이트로 학교 레코드를 찾습니다."""
    school = db.query(School).filter(
        School.name == name,
        School.website == website,
    ).first()
    if school:
        return school

    return db.query(School).filter(School.name == name).first()


def _resolve_audit_user_id(db) -> Optional[uuid.UUID]:
    """
    운영 DB에서 audit_logs.user_id/created_by/updated_by가 NOT NULL(및 FK)일 수 있어
    "실존하는 users.id"를 해석합니다.

    우선순위:
    1) 환경변수 AUDIT_SYSTEM_USER_ID 또는 AUDIT_USER_ID (UUID)
    2) users 테이블에서 가장 오래된 1개(id) 선택
    """
    global _AUDIT_USER_ID_CACHE
    if _AUDIT_USER_ID_CACHE:
        return _AUDIT_USER_ID_CACHE

    env_value = os.getenv("AUDIT_SYSTEM_USER_ID") or os.getenv("AUDIT_USER_ID")
    if env_value:
        try:
            _AUDIT_USER_ID_CACHE = uuid.UUID(env_value.strip())
            return _AUDIT_USER_ID_CACHE
        except ValueError:
            logger.warning(f"AUDIT_SYSTEM_USER_ID/AUDIT_USER_ID 형식 오류(무시): {env_value!r}")

    try:
        row = db.execute(text("SELECT id FROM users ORDER BY created_at ASC LIMIT 1")).fetchone()
        if row and row[0]:
            _AUDIT_USER_ID_CACHE = uuid.UUID(str(row[0]))
            return _AUDIT_USER_ID_CACHE
    except Exception as e:
        logger.warning(f"audit user_id 자동 해석 실패(무시): {e}")

    return None


def _update_school_crawl_metadata(name: str, website: str, status: str, message: str) -> None:
    """schools 최신 크롤링 상태 컬럼을 갱신합니다(실패/스킵 포함)."""
    try:
        with get_db() as db:
            school = _find_school_record(db, name, website)
            if not school:
                return
            now = datetime.now(timezone.utc)
            school.last_crawled_at = now
            school.last_crawl_status = status
            school.last_crawl_message = message
            db.flush()
    except Exception as e:
        logger.warning(f"schools 크롤링 메타데이터 갱신 실패(무시): {name} - {e}")


def _build_school_payload(
    name: str,
    website: str,
    crawled_data: Dict[str, Any],
    seed_school: Optional[Dict[str, Any]],
    existing_school: Optional[School],
) -> Dict[str, Any]:
    """DB 저장용 학교 payload를 구성합니다."""
    payload: Dict[str, Any] = {
        "name": name,
        "website": website,
        "international_email": crawled_data.get("international_email"),
        "international_phone": crawled_data.get("international_phone"),
        "esl_program": crawled_data.get("esl_program"),
        "international_support": crawled_data.get("international_support"),
        "facilities": crawled_data.get("facilities"),
    }

    if seed_school:
        payload.update(
            {
                "type": seed_school.get("type"),
                "state": seed_school.get("state"),
                "city": seed_school.get("city"),
                "tuition": seed_school.get("tuition"),
                "description": seed_school.get("description"),
            }
        )
    elif existing_school:
        payload["type"] = existing_school.type

    # None 값은 업데이트 시 기존 유효값을 덮어쓰지 않도록 제외
    return {k: v for k, v in payload.items() if v is not None}


def _record_crawl_audit(
    status: str,
    name: str,
    website: str,
    school_id: Optional[uuid.UUID] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """크롤링 감사 로그를 기록합니다."""
    try:
        with get_db() as db:
            audit_user_id = _resolve_audit_user_id(db)
            if audit_user_id is None:
                # 운영 DB 제약 때문에 audit 저장이 실패해도 크롤링 자체가 계속 돌아가야 합니다.
                logger.error("AuditLog user_id 해석 실패로 audit 기록을 건너뜁니다.")
                return

            resolved_school_id = school_id
            if resolved_school_id is None:
                school = _find_school_record(db, name, website)
                resolved_school_id = school.id if school else uuid.uuid4()

            new_value: Dict[str, Any] = {
                # 운영 DB의 audit_logs.action 체크 제약이 CRAWL을 허용하지 않는 경우가 있어,
                # 크롤링 이벤트를 new_value로 식별 가능하게 태깅합니다.
                "event_type": "crawl",
                "status": status,
                "school_name": name,
                "website": website,
                "message": "크롤링 완료" if status == "success" else "크롤링 실패",
            }
            if extra:
                new_value.update(extra)
            # 과거 포맷 호환: error_message만 있는 경우 message로 보정
            if not new_value.get("message") and new_value.get("error_message"):
                new_value["message"] = new_value["error_message"]

            db.add(
                AuditLog(
                    table_name="schools",
                    record_id=resolved_school_id,
                    # NOTE: 운영 DB 제약 호환을 위해 UPDATE로 저장합니다.
                    # 모니터는 (action=UPDATE && new_value.event_type=crawl) 또는 (action=CRAWL)을 모두 인식합니다.
                    action="UPDATE",
                    new_value=new_value,
                    ip_address="crawler-system",
                    # 운영 DB 제약 대응: NOT NULL 및 FK를 만족하는 users.id를 기록합니다.
                    user_id=audit_user_id,
                    created_by=audit_user_id,
                    updated_by=audit_user_id,
                )
            )
    except Exception as e:
        logger.error(f"AuditLog 기록 실패: {name} - {e}")


def crawl_single_school(
    name: str,
    website: str,
    seed_school: Optional[Dict[str, Any]] = None,
) -> dict:
    """
    단일 학교 크롤링
    
    Args:
        name: 학교 이름
        website: 웹사이트 URL
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"크롤링 시작: {name}")
    logger.info(f"{'='*60}\n")
    
    result = {
        "success": False,
        "ssl_error_detected": False,
        "ssl_error_message": "",
        "ssl_error_url": "",
        "school_id": None,
    }

    try:
        with SchoolCrawler(name, website) as crawler:
            data = crawler.crawl_all()
            result["ssl_error_detected"] = crawler.ssl_error_detected
            result["ssl_error_message"] = crawler.ssl_error_message
            result["ssl_error_url"] = crawler.ssl_error_url

            if crawler.ssl_error_detected:
                logger.warning(f"SSL 검증 실패로 저장을 건너뜀: {name}")
                return result

            crawled = data.get("crawled_data", {})
            try:
                with get_db() as db:
                    repo = SchoolRepository(db)
                    existing_school = _find_school_record(db, name, website)

                    # Level 1 메타데이터 보강: College Scorecard API (실패해도 크롤링은 계속)
                    state_hint = None
                    city_hint = None
                    if seed_school:
                        state_hint = seed_school.get("state") or None
                        city_hint = seed_school.get("city") or None
                    if existing_school:
                        state_hint = state_hint or getattr(existing_school, "state", None)
                        city_hint = city_hint or getattr(existing_school, "city", None)

                    scorecard_update, scorecard_audit = _SCORECARD_SERVICE.enrich_school(
                        school_name=name,
                        state=state_hint,
                        city=city_hint,
                    )
                    school_payload = _build_school_payload(
                        name=name,
                        website=website,
                        crawled_data=crawled,
                        seed_school=seed_school,
                        existing_school=existing_school,
                    )
                    # None 덮어쓰기 방지: scorecard_update는 값이 있는 필드만 포함합니다.
                    school_payload.update(scorecard_update)

                    saved_school: Optional[School] = None
                    data_changed = False
                    if existing_school:
                        for key, value in school_payload.items():
                            if getattr(existing_school, key, None) != value:
                                data_changed = True
                                break
                        repo.update(existing_school.id, school_payload)
                        saved_school = existing_school
                        logger.info(f"DB 업데이트 완료: {name}")
                    else:
                        if not school_payload.get("type"):
                            logger.warning(
                                f"DB 저장 건너뜀(필수 필드 type 없음): {name}"
                            )
                        else:
                            saved_school = repo.create(school_payload)
                            data_changed = True
                            logger.info(f"DB 생성 완료: {name}")

                    if saved_school:
                        now = datetime.now(timezone.utc)
                        saved_school.last_crawled_at = now
                        saved_school.last_crawl_status = "success"
                        saved_school.last_crawl_message = "크롤링 완료"
                        if data_changed:
                            saved_school.last_crawl_data_updated_at = now
                        db.flush()

                        result["school_id"] = str(saved_school.id)
                        _record_crawl_audit(
                            status="success",
                            name=name,
                            website=website,
                            school_id=saved_school.id,
                            extra={
                                "data_summary": {
                                    "email": crawled.get("international_email", "N/A"),
                                    "phone": crawled.get("international_phone", "N/A"),
                                    "esl": crawled.get("esl_program", {}).get(
                                        "available", False
                                    ),
                                    "majors_count": len(crawled.get("majors", [])),
                                },
                                "enrichment": scorecard_audit,
                            },
                        )
                    else:
                        _record_crawl_audit(
                            status="success",
                            name=name,
                            website=website,
                            extra={
                                "data_summary": {
                                    "email": crawled.get("international_email", "N/A"),
                                    "phone": crawled.get("international_phone", "N/A"),
                                    "esl": crawled.get("esl_program", {}).get(
                                        "available", False
                                    ),
                                    "majors_count": len(crawled.get("majors", [])),
                                },
                                "enrichment": scorecard_audit,
                                "note": "DB row 없이 크롤링 성공 로그만 기록",
                            },
                        )
            except Exception as e:
                logger.error(f"DB 저장 실패: {name} - {e}")

            result["success"] = True
            
            # 요약 출력
            logger.info(f"\n📊 크롤링 결과 요약:")
            logger.info(f"  - 이메일: {crawled.get('international_email', 'N/A')}")
            logger.info(f"  - 전화: {crawled.get('international_phone', 'N/A')}")
            logger.info(f"  - ESL: {crawled.get('esl_program', {}).get('available', False)}")
            logger.info(f"  - 전공 수: {len(crawled.get('majors', []))}")
            
    except Exception as e:
        logger.error(f"❌ 크롤링 실패: {e}")
    return result


def crawl_all_schools(json_file: Path, limit: int = None) -> None:
    """
    모든 학교 크롤링
    
    Args:
        json_file: 학교 목록 JSON 파일
        limit: 크롤링할 최대 학교 수 (None이면 전체)
    """
    schools = load_schools_list(json_file)
    
    if limit:
        schools = schools[:limit]
    
    logger.info(f"📚 총 {len(schools)}개 학교 크롤링 시작\n")
    
    success_count = 0
    fail_count = 0
    
    for i, school in enumerate(schools, 1):
        name = school.get('name')
        website = school.get('website')
        
        if not name or not website:
            logger.warning(f"⏭️  건너뜀: 정보 부족 - {school}")
            fail_count += 1
            continue

        should_skip, skip_reason = failed_site_manager.should_skip(website)
        if should_skip:
            logger.warning(f"⏭️  건너뜀: {name} - {skip_reason}")
            _record_crawl_audit(
                status="failed",
                name=name,
                website=website,
                extra={
                    "message": f"건너뜀: {skip_reason}",
                    "error_type": "skip_failed_site",
                    "error_message": skip_reason,
                },
            )
            _update_school_crawl_metadata(
                name=name,
                website=website,
                status="skipped",
                message=f"건너뜀: {skip_reason}",
            )
            fail_count += 1
            continue
        
        logger.info(f"\n[{i}/{len(schools)}] {name}")
        
        try:
            result = crawl_single_school(name, website, seed_school=school)
            if result.get("ssl_error_detected", False):
                failed_site_manager.add_ssl_failure(
                    name=name,
                    website=website,
                    error_message=result.get("ssl_error_message", "SSL verification failed"),
                    note=f"마지막 실패 URL: {result.get('ssl_error_url', website)}",
                )
                logger.warning(f"⏭️  SSL 실패 사이트로 기록: {name}")
                school_id = result.get("school_id")
                _record_crawl_audit(
                    status="failed",
                    name=name,
                    website=website,
                    school_id=uuid.UUID(school_id) if school_id else None,
                    extra={
                        "message": "SSL 검증 실패로 크롤링 중단",
                        "error_type": "ssl_verification",
                        "error_message": result.get("ssl_error_message", ""),
                    },
                )
                _update_school_crawl_metadata(
                    name=name,
                    website=website,
                    status="failed",
                    message="SSL 검증 실패로 크롤링 중단",
                )
                fail_count += 1
            elif result.get("success", False):
                success_count += 1
            else:
                school_id = result.get("school_id")
                _record_crawl_audit(
                    status="failed",
                    name=name,
                    website=website,
                    school_id=uuid.UUID(school_id) if school_id else None,
                    extra={
                        "message": "크롤링 처리 실패",
                        "error_type": "crawl_failed",
                        "error_message": "크롤링 처리 실패",
                    },
                )
                _update_school_crawl_metadata(
                    name=name,
                    website=website,
                    status="failed",
                    message="크롤링 처리 실패",
                )
                fail_count += 1
        except Exception as e:
            logger.error(f"❌ 실패: {e}")
            _record_crawl_audit(
                status="failed",
                name=name,
                website=website,
                extra={
                    "message": "예외 발생으로 크롤링 실패",
                    "error_type": "exception",
                    "error_message": str(e),
                },
            )
            _update_school_crawl_metadata(
                name=name,
                website=website,
                status="failed",
                message="예외 발생으로 크롤링 실패",
            )
            fail_count += 1
    
    # 최종 결과
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 최종 결과")
    logger.info(f"{'='*60}")
    logger.info(f"✅ 성공: {success_count}개")
    logger.info(f"❌ 실패: {fail_count}개")
    logger.info("💾 저장 방식: DB 단일 저장")


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='College Crawler - 미국 대학 정보 수집')
    
    parser.add_argument('command', choices=['crawl', 'test'], 
                       help='실행할 명령 (crawl: 크롤링 실행, test: 테스트 크롤링)')
    parser.add_argument('--school', type=str, 
                       help='크롤링할 특정 학교 이름')
    parser.add_argument('--website', type=str, 
                       help='학교 웹사이트 URL (--school과 함께 사용)')
    parser.add_argument('--limit', type=int, 
                       help='크롤링할 최대 학교 수')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    
    if args.command == 'test':
        # 테스트: 첫 번째 학교만 크롤링
        logger.info("🧪 테스트 모드: 첫 번째 학교만 크롤링")
        json_file = project_root / 'data' / 'schools_initial.json'
        crawl_all_schools(json_file, limit=1)
        
    elif args.command == 'crawl':
        if args.school and args.website:
            # 특정 학교 크롤링
            crawl_single_school(args.school, args.website)
        else:
            # 전체 학교 크롤링
            json_file = project_root / 'data' / 'schools_initial.json'
            crawl_all_schools(json_file, limit=args.limit)


if __name__ == '__main__':
    main()
