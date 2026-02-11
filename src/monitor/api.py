"""
FastAPI 기반 모니터링 API
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import uuid
import docker
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import base64
import decimal
from sqlalchemy import and_, func, or_

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.connection import get_db, test_connection
from src.database.repository import SchoolRepository
from src.database.models import School, AuditLog
from src.utils.failed_sites import failed_site_manager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="College Crawler Monitor",
    description="실시간 크롤러 모니터링 대시보드",
    version="1.0.0"
)


def _extract_crawl_status(new_value: Optional[Dict[str, Any]]) -> tuple[str, str]:
    """AuditLog new_value에서 상태/메시지를 표준화합니다."""
    if not isinstance(new_value, dict):
        return "unknown", "크롤링 상태 정보 없음"

    status = str(new_value.get("status", "unknown")).lower()
    message = (
        new_value.get("message")
        or new_value.get("error_message")
        or new_value.get("note")
        or ""
    )

    if status in ("success", "failed", "skipped"):
        return status, str(message)

    error_type = str(new_value.get("error_type", "")).lower()
    if "skip" in error_type:
        return "skipped", str(message) or "실패 이력으로 건너뜀"
    if error_type:
        return "failed", str(message) or "크롤링 실패"

    return "unknown", str(message) or "상태 해석 불가"


def _json_safe(value: Any) -> Any:
    """
    운영 데이터가 예상과 다를 때(JSON 직렬화 불가 타입 포함) 상세 API가 500으로 깨지는 것을 방지합니다.
    - Decimal/UUID/datetime/bytes 등은 안전한 기본 타입으로 변환
    """
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        try:
            return float(value)
        except Exception:
            return str(value)
    if isinstance(value, (bytes, bytearray)):
        # 바이너리가 섞여 들어온 경우 base64로 전달
        return base64.b64encode(bytes(value)).decode("ascii")
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def _failed_sites_by_website() -> Dict[str, Dict[str, Any]]:
    """SSL 실패 사이트 목록을 website 키 맵으로 반환합니다."""
    failed_sites = failed_site_manager.get_failed_sites("ssl_verification_failed")
    return {
        str(item.get("website")): item
        for item in failed_sites
        if item.get("website")
    }


def _crawl_auditlog_filter():
    """
    운영 DB 제약/히스토리 차이로 인해 크롤링 이력이 action=CRAWL 또는 action=UPDATE로 기록될 수 있습니다.

    - 신규 포맷: action=UPDATE + new_value.event_type='crawl'
    - 구 포맷: action=CRAWL
    """
    return or_(
        AuditLog.action == "CRAWL",
        and_(
            AuditLog.action == "UPDATE",
            AuditLog.new_value["event_type"].astext == "crawl",
        ),
    )


def _school_crawl_columns_available(db) -> bool:
    """배포 직후 마이그레이션 누락 시에도 API가 죽지 않도록 가드합니다."""
    try:
        # 컬럼이 없으면 DB에서 UndefinedColumn 계열 예외가 발생합니다.
        db.query(School.last_crawled_at).limit(1).all()
        return True
    except Exception:
        return False

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker 클라이언트
try:
    docker_client = docker.from_env()
except Exception as e:
    logger.warning(f"Docker 클라이언트 초기화 실패: {e}")
    docker_client = None


@app.get("/")
async def root():
    """대시보드 HTML 페이지"""
    html_file = Path(__file__).parent / "static" / "dashboard.html"
    if html_file.exists():
        return HTMLResponse(content=html_file.read_text())
    return {"message": "College Crawler Monitor API"}


@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """
    전체 시스템 상태 조회
    
    Returns:
        시스템 상태 정보
    """
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "container": await get_container_status(),
            "database": await get_database_status(),
            "crawling": await get_crawling_stats(),
            "resources": await get_resource_usage(),
        }
        return status
    except Exception as e:
        logger.error(f"상태 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/container")
async def get_container_status() -> Dict[str, Any]:
    """
    컨테이너 상태 조회
    
    Returns:
        컨테이너 상태 정보
    """
    if not docker_client:
        return {
            "status": "unknown",
            "message": "Docker 클라이언트 사용 불가"
        }
    
    try:
        container = docker_client.containers.get("college-crawler")
        
        return {
            "name": container.name,
            "status": container.status,
            "state": container.attrs['State']['Status'],
            "health": container.attrs['State'].get('Health', {}).get('Status', 'none'),
            "started_at": container.attrs['State']['StartedAt'],
            "running": container.status == "running",
            "restart_count": container.attrs['RestartCount'],
        }
    except docker.errors.NotFound:
        return {
            "status": "not_found",
            "message": "컨테이너를 찾을 수 없습니다"
        }
    except Exception as e:
        logger.error(f"컨테이너 상태 조회 실패: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/api/database")
async def get_database_status() -> Dict[str, Any]:
    """
    데이터베이스 상태 조회
    
    Returns:
        데이터베이스 통계 정보
    """
    try:
        # DB 연결 테스트
        connected = test_connection()
        
        if not connected:
            return {
                "connected": False,
                "message": "데이터베이스 연결 실패"
            }
        
        with get_db() as db:
            repo = SchoolRepository(db)
            
            # 전체 통계
            total_schools = repo.count()
            
            # 이메일이 있는 학교
            schools_with_email = db.query(School).filter(
                School.international_email != None
            ).count()
            
            # 전화가 있는 학교
            schools_with_phone = db.query(School).filter(
                School.international_phone != None
            ).count()
            
            # ESL 프로그램이 있는 학교
            schools_with_esl = db.query(School).filter(
                School.esl_program != None
            ).count()

            # 취업률 데이터가 있는 학교
            schools_with_employment_rate = db.query(School).filter(
                School.employment_rate != None
            ).count()

            # 시설 정보가 있는 학교
            schools_with_facilities = db.query(School).filter(
                School.facilities != None
            ).count()

            # Scorecard Level 1 필드
            schools_with_graduation_rate = db.query(School).filter(
                School.graduation_rate != None
            ).count()

            schools_with_average_salary = db.query(School).filter(
                School.average_salary != None
            ).count()

            # Scorecard 데이터 커버리지 (하나라도 있는 경우)
            schools_with_any_scorecard = db.query(School).filter(
                or_(
                    School.graduation_rate != None,
                    School.average_salary != None
                )
            ).count()
            
            # 최근 업데이트된 학교 (24시간 이내)
            yesterday = datetime.now() - timedelta(days=1)
            if _school_crawl_columns_available(db):
                # 하이브리드 설계: schools.last_crawled_at을 "최근 업데이트"의 1차 소스로 사용
                recently_updated = (
                    db.query(School.id)
                    .filter(School.last_crawled_at != None)  # noqa: E711
                    .filter(School.last_crawled_at >= yesterday)
                    .count()
                )
            else:
                # 폴백: 마이그레이션 적용 전에는 audit_logs 기반으로 계산
                recently_updated = (
                    db.query(School.id)
                    .join(AuditLog, AuditLog.record_id == School.id)
                    .filter(
                        AuditLog.table_name == "schools",
                        _crawl_auditlog_filter(),
                        AuditLog.created_at >= yesterday,
                    )
                    .distinct()
                    .count()
                )
            
            return {
                "connected": True,
                "total_schools": total_schools,
                "schools_with_email": schools_with_email,
                "schools_with_phone": schools_with_phone,
                "schools_with_esl": schools_with_esl,
                "schools_with_employment_rate": schools_with_employment_rate,
                "schools_with_facilities": schools_with_facilities,
                "schools_with_graduation_rate": schools_with_graduation_rate,
                "schools_with_average_salary": schools_with_average_salary,
                "schools_with_any_scorecard": schools_with_any_scorecard,
                "recently_updated": recently_updated,
                # NOTE: 이 값은 "크롤링 성공률"이 아니라 "연락처(이메일) 채움률"입니다.
                "completion_rate": round((schools_with_email / total_schools * 100), 1) if total_schools > 0 else 0,
                "contact_completion_rate": round((schools_with_email / total_schools * 100), 1) if total_schools > 0 else 0,
                "scorecard_coverage_rate": round((schools_with_any_scorecard / total_schools * 100), 1) if total_schools > 0 else 0,
            }
            
    except Exception as e:
        logger.error(f"데이터베이스 상태 조회 실패: {e}")
        return {
            "connected": False,
            "message": str(e)
        }


@app.get("/api/crawling/stats")
async def get_crawling_stats() -> Dict[str, Any]:
    """
    크롤링 통계 조회
    
    Returns:
        크롤링 성공/실패 통계
    """
    try:
        with get_db() as db:
            ssl_failures = failed_site_manager.get_failed_sites("ssl_verification_failed")
            ssl_websites = {
                str(item.get("website"))
                for item in ssl_failures
                if item.get("website") and bool(item.get("skip", True))
            }
            total_schools = db.query(School).count()
            if _school_crawl_columns_available(db):
                # 하이브리드 설계: schools.last_crawl_* 컬럼을 통계의 1차 소스로 사용
                attempted = db.query(School).filter(School.last_crawled_at != None).count()  # noqa: E711
                success = (
                    db.query(School)
                    .filter(School.last_crawl_status == "success")
                    .count()
                )
                failed_total = (
                    db.query(School)
                    .filter(School.last_crawl_status == "failed")
                    .count()
                )
                skipped_total = (
                    db.query(School)
                    .filter(School.last_crawl_status == "skipped")
                    .count()
                )

                # SSL 검증 오류는 다음 크롤링에서 자동 스킵되므로, 통계/배지에서도 "건너뜀"으로 분류합니다.
                failed_ssl_overlap = 0
                ssl_school_count = 0
                if ssl_websites:
                    ssl_list = list(ssl_websites)
                    ssl_school_count = (
                        db.query(School.id)
                        .filter(School.website.in_(ssl_list))
                        .count()
                    )
                    failed_ssl_overlap = (
                        db.query(School.id)
                        .filter(School.last_crawl_status == "failed")
                        .filter(School.website.in_(ssl_list))
                        .count()
                    )

                ssl_only_count = max(len(ssl_websites) - ssl_school_count, 0)
                failed = max(failed_total - failed_ssl_overlap, 0)
                skipped = skipped_total + failed_ssl_overlap + ssl_only_count
                attempted = attempted + ssl_only_count

                yesterday = datetime.now() - timedelta(days=1)
                recently_updated = (
                    db.query(School.id)
                    .filter(School.last_crawled_at != None)  # noqa: E711
                    .filter(School.last_crawled_at >= yesterday)
                    .count()
                )

                last_crawl_at = db.query(func.max(School.last_crawled_at)).scalar()
            else:
                # 폴백: 마이그레이션 적용 전에는 audit_logs 기반으로 계산
                success = 0
                failed = 0
                skipped = 0

                latest_per_school = (
                    db.query(
                        AuditLog.record_id.label("school_id"),
                        func.max(AuditLog.created_at).label("last_crawl_at"),
                    )
                    .filter(
                        AuditLog.table_name == "schools",
                        _crawl_auditlog_filter(),
                    )
                    .group_by(AuditLog.record_id)
                    .subquery()
                )

                latest_logs = (
                    db.query(AuditLog.record_id, AuditLog.new_value)
                    .join(
                        latest_per_school,
                        (AuditLog.record_id == latest_per_school.c.school_id)
                        & (AuditLog.created_at == latest_per_school.c.last_crawl_at),
                    )
                    .all()
                )
                attempted = len(latest_logs)

                for _school_id, new_value in latest_logs:
                    # SSL 검증 오류 목록(failed_sites.json)에 포함된 website는 '실패'보다 '자동 건너뜀' 성격이므로
                    # 통계에서는 skipped로 재분류합니다.
                    website = ""
                    if isinstance(new_value, dict):
                        website = str(new_value.get("website") or "")
                    if website and website in ssl_websites:
                        skipped += 1
                        continue

                    status, _message = _extract_crawl_status(new_value)
                    if status == "success":
                        success += 1
                    elif status == "failed":
                        failed += 1
                    elif status == "skipped":
                        skipped += 1

                yesterday = datetime.now() - timedelta(days=1)
                recently_updated = (
                    db.query(School.id)
                    .join(AuditLog, AuditLog.record_id == School.id)
                    .filter(
                        AuditLog.table_name == "schools",
                        _crawl_auditlog_filter(),
                        AuditLog.created_at >= yesterday,
                    )
                    .distinct()
                    .count()
                )

                latest_crawl_log = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.table_name == "schools",
                        _crawl_auditlog_filter(),
                    )
                    .order_by(AuditLog.created_at.desc())
                    .first()
                )
                last_crawl_at = latest_crawl_log.created_at if latest_crawl_log else None

            return {
                "total": total_schools,
                "attempted": attempted,
                "success": success,
                "failed": failed,
                "skipped": skipped,
                # NOTE: success_rate는 "시도(attempted)" 기준이 더 직관적입니다.
                "success_rate": round((success / attempted * 100), 1) if attempted > 0 else 0,
                "coverage_rate": round((attempted / total_schools * 100), 1) if total_schools > 0 else 0,
                "recently_updated": recently_updated,
                "last_crawl": last_crawl_at.isoformat() if last_crawl_at else None,
            }
            
    except Exception as e:
        logger.error(f"크롤링 통계 조회 실패: {e}")
        return {
            "total": 0,
            "attempted": 0,
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "success_rate": 0,
            "coverage_rate": 0,
            "recently_updated": 0,
            "last_crawl": None,
        }


@app.get("/api/scorecard/stats")
async def get_scorecard_stats() -> Dict[str, Any]:
    """
    College Scorecard Level 1 데이터 수집 현황 조회
    
    Returns:
        Scorecard 메타데이터 커버리지 통계
    """
    try:
        with get_db() as db:
            total_schools = db.query(School).count()
            
            # Level 1 필드별 커버리지
            with_graduation_rate = db.query(School).filter(
                School.graduation_rate != None
            ).count()
            
            with_average_salary = db.query(School).filter(
                School.average_salary != None
            ).count()
            
            # 하나라도 Scorecard 데이터가 있는 학교
            with_any_scorecard_data = db.query(School).filter(
                or_(
                    School.graduation_rate != None,
                    School.average_salary != None
                )
            ).count()
            
            return {
                "total_schools": total_schools,
                "scorecard_enriched": {
                    "with_graduation_rate": with_graduation_rate,
                    "with_average_salary": with_average_salary,
                    "with_any_data": with_any_scorecard_data,
                },
                "coverage_rates": {
                    "graduation_rate": round((with_graduation_rate / total_schools * 100), 1) if total_schools > 0 else 0,
                    "average_salary": round((with_average_salary / total_schools * 100), 1) if total_schools > 0 else 0,
                    "overall": round((with_any_scorecard_data / total_schools * 100), 1) if total_schools > 0 else 0,
                },
                "timestamp": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Scorecard 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/resources")
async def get_resource_usage() -> Dict[str, Any]:
    """
    리소스 사용량 조회
    
    Returns:
        CPU, 메모리 사용량
    """
    if not docker_client:
        return {
            "available": False,
            "message": "Docker 클라이언트 사용 불가"
        }
    
    try:
        container = docker_client.containers.get("college-crawler")
        
        # 컨테이너 통계 (stats는 스트리밍이므로 한 번만 가져오기)
        stats = container.stats(stream=False)
        
        # CPU 사용률 계산
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                   stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                      stats['precpu_stats']['system_cpu_usage']
        cpu_count = stats['cpu_stats']['online_cpus']
        cpu_percent = (cpu_delta / system_delta) * cpu_count * 100.0 if system_delta > 0 else 0
        
        # 메모리 사용량
        memory_usage = stats['memory_stats']['usage']
        memory_limit = stats['memory_stats']['limit']
        memory_percent = (memory_usage / memory_limit) * 100.0 if memory_limit > 0 else 0
        
        return {
            "available": True,
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_mb": round(memory_usage / 1024 / 1024, 2),
            "memory_limit_mb": round(memory_limit / 1024 / 1024, 2),
            "memory_percent": round(memory_percent, 2)
        }
        
    except Exception as e:
        logger.error(f"리소스 사용량 조회 실패: {e}")
        return {
            "available": False,
            "message": str(e)
        }


@app.get("/api/logs/recent")
async def get_recent_logs(lines: int = 50) -> Dict[str, Any]:
    """
    최근 로그 조회
    
    Args:
        lines: 조회할 로그 라인 수 (기본: 50)
        
    Returns:
        최근 로그 목록
    """
    if not docker_client:
        return {
            "logs": [],
            "message": "Docker 클라이언트 사용 불가"
        }
    
    try:
        container = docker_client.containers.get("college-crawler")
        logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
        
        # 로그를 라인별로 분리
        log_lines = []
        for line in logs.strip().split('\n'):
            if line:
                # 타임스탬프와 메시지 분리
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    log_lines.append({
                        "timestamp": parts[0],
                        "message": parts[1]
                    })
        
        return {
            "logs": log_lines,
            "count": len(log_lines)
        }
        
    except Exception as e:
        logger.error(f"로그 조회 실패: {e}")
        return {
            "logs": [],
            "message": str(e)
        }


@app.get("/api/schools/recent")
async def get_recent_schools(
    page: int = Query(1, ge=1, description="페이지 번호 (1-based)"),
    per_page: int = Query(20, description="페이지당 개수"),
    state: Optional[str] = Query(None, description="주 필터 (예: CA, TX)"),
    school_type: Optional[str] = Query(None, description="학교 타입 (예: community_college)"),
    q: Optional[str] = Query(None, description="학교 이름 검색 (부분 일치)"),
) -> Dict[str, Any]:
    """
    최근 업데이트된 학교 목록 (페이징 및 필터 지원)

    Returns:
        items: 현재 페이지 학교 목록
        total: 필터 적용 후 전체 개수
        page, per_page, total_pages
    """
    if per_page not in (10, 20):
        per_page = 20

    try:
        with get_db() as db:
            use_school_cols = _school_crawl_columns_available(db)
            if use_school_cols:
                # 하이브리드 설계: 최근 업데이트(정렬)는 schools.last_crawled_at을 우선 사용
                base = db.query(School)
                latest_crawl_at_subq = None
            else:
                # 폴백: 마이그레이션 적용 전에는 audit_logs 기반 정렬/상태를 사용
                latest_crawl_at_subq = (
                    db.query(
                        AuditLog.record_id.label("school_id"),
                        func.max(AuditLog.created_at).label("last_crawl_at"),
                    )
                    .filter(
                        AuditLog.table_name == "schools",
                        _crawl_auditlog_filter(),
                    )
                    .group_by(AuditLog.record_id)
                    .subquery()
                )
                base = (
                    db.query(School)
                    .outerjoin(
                        latest_crawl_at_subq,
                        latest_crawl_at_subq.c.school_id == School.id,
                    )
                )
            if state and state.strip():
                base = base.filter(School.state == state.strip())
            if school_type and school_type.strip():
                base = base.filter(School.type == school_type.strip())
            if q and q.strip():
                base = base.filter(School.name.ilike(f"%{q.strip()}%"))

            total = base.count()
            total_pages = (total + per_page - 1) // per_page if total > 0 else 0
            offset = (page - 1) * per_page

            if use_school_cols:
                schools = (
                    base.order_by(
                        School.last_crawled_at.desc().nullslast(),
                        School.updated_at.desc().nullslast(),
                    )
                    .offset(offset)
                    .limit(per_page)
                    .all()
                )
                items = [
                    _build_recent_school_item(
                        school,
                        None,
                        None,
                    )
                    for school in schools
                ]
            else:
                schools = (
                    base.order_by(
                        latest_crawl_at_subq.c.last_crawl_at.desc().nullslast(),
                        School.updated_at.desc().nullslast(),
                    )
                    .offset(offset)
                    .limit(per_page)
                    .all()
                )
                school_ids = [school.id for school in schools]
                latest_logs_by_school: Dict[uuid.UUID, AuditLog] = {}
                if school_ids:
                    crawl_logs = (
                        db.query(AuditLog)
                        .filter(
                            _crawl_auditlog_filter(),
                            AuditLog.record_id.in_(school_ids),
                        )
                        .order_by(AuditLog.created_at.desc())
                        .all()
                    )
                    for log in crawl_logs:
                        if log.record_id not in latest_logs_by_school:
                            latest_logs_by_school[log.record_id] = log

                items = [
                    _build_recent_school_item(
                        school,
                        latest_logs_by_school.get(school.id),
                        None,
                    )
                    for school in schools
                ]

            return {
                "items": items,
                "total": total,
                "page": page,
                "per_page": per_page,
                "total_pages": total_pages,
            }

    except Exception as e:
        logger.error(f"학교 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_recent_school_item(
    school: School,
    latest_log: Optional[AuditLog] = None,
    failed_site: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if latest_log is not None:
        crawl_status, crawl_message = _extract_crawl_status(latest_log.new_value)
        crawl_updated_at = (
            latest_log.created_at.isoformat() if latest_log.created_at else None
        )
    else:
        crawl_status = (school.last_crawl_status or "unknown").lower()
        crawl_message = school.last_crawl_message or ""
        crawl_updated_at = school.last_crawled_at.isoformat() if school.last_crawled_at else None
    if failed_site:
        # SSL 검증 오류는 다음 크롤링에서 자동으로 건너뜀 처리되므로, UI에서도 skipped로 노출합니다.
        crawl_status = "skipped"
        crawl_message = str(failed_site.get("error_message") or "SSL 검증 실패(자동 건너뜀)")
        crawl_updated_at = str(
            failed_site.get("last_checked_at") or failed_site.get("first_failed_at")
        )
    elif crawl_status == "unknown":
        # 크롤링 이력이 없는 학교. 최근 업데이트 기준이 "크롤링 시각"이므로 unknown 유지.
        crawl_message = "크롤링 이력 없음"

    return {
                    "id": str(school.id),
                    "name": school.name,
                    "state": school.state,
                    "city": school.city,
                    "international_email": school.international_email,
                    "international_phone": school.international_phone,
                    "website": school.website,
                    "updated_at": school.updated_at.isoformat() if school.updated_at else None,
                    "has_contact_info": bool(
                        school.international_email or school.international_phone
                    ),
                    "crawl_status": crawl_status,
                    "crawl_message": crawl_message,
                    "crawl_updated_at": crawl_updated_at,
                }


@app.get("/api/schools/{school_id}")
async def get_school_detail(school_id: str) -> Dict[str, Any]:
    """학교 상세 정보 및 최근 크롤링 이력을 조회합니다."""
    try:
        school_uuid = uuid.UUID(school_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="유효하지 않은 school_id 입니다") from e

    try:
        with get_db() as db:
            school = db.query(School).filter(School.id == school_uuid).first()
            if not school:
                raise HTTPException(status_code=404, detail="학교를 찾을 수 없습니다")

            crawl_logs = (
                db.query(AuditLog)
                .filter(
                    AuditLog.table_name == "schools",
                    AuditLog.record_id == school_uuid,
                    _crawl_auditlog_filter(),
                )
                .order_by(AuditLog.created_at.desc())
                .limit(10)
                .all()
            )

            crawl_history: List[Dict[str, Any]] = [
                {
                    "id": str(log.id),
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "status": _extract_crawl_status(log.new_value)[0],
                    "message": _extract_crawl_status(log.new_value)[1],
                    "raw": _json_safe(log.new_value) if isinstance(log.new_value, dict) else {},
                }
                for log in crawl_logs
            ]

            # schools에 저장된 "최신 상태"를 최상단에 표시(하이브리드 설계)
            if school.last_crawled_at or school.last_crawl_status or school.last_crawl_message:
                crawl_history.insert(
                    0,
                    {
                        "id": "latest",
                        "timestamp": school.last_crawled_at.isoformat() if school.last_crawled_at else None,
                        "status": (school.last_crawl_status or "unknown").lower(),
                        "message": school.last_crawl_message or "크롤링 이력 없음",
                        "raw": {
                            "last_crawl_data_updated_at": school.last_crawl_data_updated_at.isoformat()
                            if school.last_crawl_data_updated_at
                            else None,
                        },
                    },
                )
            if not crawl_history:
                crawl_history.append(
                    {
                        "id": "db-updated",
                        "timestamp": school.updated_at.isoformat()
                        if school.updated_at
                        else None,
                        "status": "unknown",
                        "message": "크롤링 이력 없음(최근 DB 업데이트만 존재)",
                        "raw": {},
                    }
                )

            return {
                "school": {
                    "id": str(school.id),
                    "name": school.name,
                    "type": school.type,
                    "state": school.state,
                    "city": school.city,
                    "website": school.website,
                    "description": school.description,
                    "international_email": school.international_email,
                    "international_phone": school.international_phone,
                    "employment_rate": float(school.employment_rate) if school.employment_rate is not None else None,
                    "esl_program": _json_safe(school.esl_program),
                    "international_support": _json_safe(school.international_support),
                    "facilities": _json_safe(school.facilities),
                    "staff_info": _json_safe(school.staff_info),
                    "tuition": school.tuition,
                    "living_cost": school.living_cost,
                    "acceptance_rate": school.acceptance_rate,
                    "transfer_rate": school.transfer_rate,
                    "graduation_rate": school.graduation_rate,
                    "updated_at": school.updated_at.isoformat() if school.updated_at else None,
                    "last_crawled_at": school.last_crawled_at.isoformat() if school.last_crawled_at else None,
                    "last_crawl_status": (school.last_crawl_status or "unknown").lower(),
                    "last_crawl_message": school.last_crawl_message,
                    "last_crawl_data_updated_at": school.last_crawl_data_updated_at.isoformat()
                    if school.last_crawl_data_updated_at
                    else None,
                },
                "crawl_history": crawl_history,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"학교 상세 조회 실패: {school_id} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """
    헬스체크 엔드포인트
    
    Returns:
        상태 정보
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/failed-sites")
async def get_failed_sites() -> Dict[str, Any]:
    """
    실패 사이트 목록 조회

    Returns:
        SSL 검증 실패 사이트 목록 및 집계 정보
    """
    try:
        # 동기화 원칙: 하단 목록도 상단 통계/최근 업데이트와 동일하게 "DB 기준"으로 계산합니다.
        # (운영에서 failed_sites.json과 DB가 어긋날 수 있으므로 UI는 DB를 신뢰)
        with get_db() as db:
            if _school_crawl_columns_available(db):
                rows = (
                    db.query(
                        School.name,
                        School.website,
                        School.last_crawled_at,
                        School.last_crawl_message,
                    )
                    .filter(School.last_crawl_status == "skipped")
                    .filter(School.last_crawl_message.ilike("%SSL%"))
                    .order_by(School.last_crawled_at.desc().nullslast())
                    .limit(100)
                    .all()
                )
                ssl_failures = [
                    {
                        "name": name,
                        "website": website,
                        "error_message": last_crawl_message or "SSL 검증 실패(자동 건너뜀)",
                        "first_failed_at": last_crawled_at.isoformat() if last_crawled_at else None,
                        "last_checked_at": last_crawled_at.isoformat() if last_crawled_at else None,
                        "retry_count": 1,
                        "skip": True,
                    }
                    for name, website, last_crawled_at, last_crawl_message in rows
                ]
            else:
                # 폴백: 스키마 미적용 환경에서는 기존 파일 기반을 유지
                ssl_failures = failed_site_manager.get_failed_sites("ssl_verification_failed")
        return {
            "ssl_failures": ssl_failures,
            "total_ssl_failures": len(ssl_failures),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"실패 사이트 조회 실패: {e}")
        return {
            "ssl_failures": [],
            "total_ssl_failures": 0,
            "error": str(e),
        }


@app.get("/api/failed-sites/detail")
async def get_failed_site_detail(website: str) -> Dict[str, Any]:
    """실패 사이트 1건의 상세 로그를 조회합니다."""
    if not website:
        raise HTTPException(status_code=400, detail="website 쿼리 파라미터가 필요합니다")

    try:
        with get_db() as db:
            school = db.query(School).filter(School.website == website).first()
            logs: List[Dict[str, Any]] = []

            if not school:
                raise HTTPException(status_code=404, detail="학교를 찾을 수 없습니다")

            crawl_logs = (
                db.query(AuditLog)
                .filter(
                    _crawl_auditlog_filter(),
                    AuditLog.record_id == school.id,
                )
                .order_by(AuditLog.created_at.desc())
                .limit(50)
                .all()
            )

            for log in crawl_logs:
                status, message = _extract_crawl_status(log.new_value)
                if status not in ("failed", "skipped"):
                    continue
                logs.append(
                    {
                        "id": str(log.id),
                        "timestamp": log.created_at.isoformat() if log.created_at else None,
                        "status": status,
                        "message": message,
                        "raw": _json_safe(log.new_value) if isinstance(log.new_value, dict) else {},
                    }
                )

            site = {
                "name": school.name,
                "website": school.website,
                "error_message": school.last_crawl_message or "SSL 검증 실패(자동 건너뜀)",
                "first_failed_at": school.last_crawled_at.isoformat() if school.last_crawled_at else None,
                "last_checked_at": school.last_crawled_at.isoformat() if school.last_crawled_at else None,
                "retry_count": 1,
                "skip": True,
            }

            return {
                "site": site,
                "school_id": str(school.id),
                "logs": logs,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"실패 사이트 상세 조회 실패: {website} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def generate_events():
    """
    Server-Sent Events (SSE)를 위한 이벤트 생성
    실시간 상태 업데이트
    """
    while True:
        try:
            status = await get_status()
            yield f"data: {json.dumps(status)}\n\n"
            await asyncio.sleep(5)  # 5초마다 업데이트
        except Exception as e:
            logger.error(f"SSE 이벤트 생성 실패: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(10)


@app.get("/api/stream")
async def stream_status():
    """
    실시간 상태 스트리밍 (SSE)
    
    Returns:
        Server-Sent Events 스트림
    """
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
