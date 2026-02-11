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
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio

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


def _failed_sites_by_website() -> Dict[str, Dict[str, Any]]:
    """SSL 실패 사이트 목록을 website 키 맵으로 반환합니다."""
    failed_sites = failed_site_manager.get_failed_sites("ssl_verification_failed")
    return {
        str(item.get("website")): item
        for item in failed_sites
        if item.get("website")
    }

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
            
            # 최근 업데이트된 학교 (24시간 이내)
            yesterday = datetime.now() - timedelta(days=1)
            recently_updated = db.query(School).filter(
                School.updated_at >= yesterday
            ).count()
            
            return {
                "connected": True,
                "total_schools": total_schools,
                "schools_with_email": schools_with_email,
                "schools_with_phone": schools_with_phone,
                "schools_with_esl": schools_with_esl,
                "schools_with_employment_rate": schools_with_employment_rate,
                "schools_with_facilities": schools_with_facilities,
                "recently_updated": recently_updated,
                "completion_rate": round((schools_with_email / total_schools * 100), 1) if total_schools > 0 else 0
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
            total_schools = db.query(School).count()
            failed_sites_map = _failed_sites_by_website()
            failed = len(failed_sites_map)
            success = max(total_schools - failed, 0)

            # 최근 업데이트된 학교 수 (24시간)
            yesterday = datetime.now() - timedelta(days=1)
            recently_updated = db.query(School).filter(
                School.updated_at >= yesterday
            ).count()

            latest_crawl_log = (
                db.query(AuditLog)
                .filter(AuditLog.action == "CRAWL")
                .order_by(AuditLog.created_at.desc())
                .first()
            )

            return {
                "total": total_schools,
                "success": success,
                "failed": failed,
                "success_rate": round((success / total_schools * 100), 1) if total_schools > 0 else 0,
                "recently_updated": recently_updated,
                "last_crawl": latest_crawl_log.created_at.isoformat()
                if latest_crawl_log and latest_crawl_log.created_at
                else None,
            }
            
    except Exception as e:
        logger.error(f"크롤링 통계 조회 실패: {e}")
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "success_rate": 0,
            "recently_updated": 0,
            "last_crawl": None,
        }


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
async def get_recent_schools(limit: int = 10) -> List[Dict[str, Any]]:
    """
    최근 업데이트된 학교 목록
    
    Args:
        limit: 조회할 학교 수 (기본: 10)
        
    Returns:
        학교 목록
    """
    try:
        with get_db() as db:
            failed_sites_map = _failed_sites_by_website()
            schools = db.query(School).order_by(
                School.updated_at.desc()
            ).limit(limit).all()
            school_ids = [school.id for school in schools]
            latest_logs_by_school: Dict[uuid.UUID, AuditLog] = {}
            if school_ids:
                crawl_logs = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.action == "CRAWL",
                        AuditLog.record_id.in_(school_ids),
                    )
                    .order_by(AuditLog.created_at.desc())
                    .all()
                )
                for log in crawl_logs:
                    if log.record_id not in latest_logs_by_school:
                        latest_logs_by_school[log.record_id] = log

            return [
                _build_recent_school_item(
                    school,
                    latest_logs_by_school.get(school.id),
                    failed_sites_map.get(school.website or ""),
                )
                for school in schools
            ]

    except Exception as e:
        logger.error(f"학교 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _build_recent_school_item(
    school: School,
    latest_log: Optional[AuditLog],
    failed_site: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    crawl_status, crawl_message = _extract_crawl_status(
        latest_log.new_value if latest_log else None
    )
    crawl_updated_at = (
        latest_log.created_at.isoformat() if latest_log and latest_log.created_at else None
    )
    if failed_site:
        crawl_status = "failed"
        crawl_message = str(failed_site.get("error_message") or "SSL 검증 실패")
        crawl_updated_at = str(
            failed_site.get("last_checked_at") or failed_site.get("first_failed_at")
        )
    elif crawl_status == "unknown":
        crawl_status = "success"
        crawl_message = "최근 DB 업데이트 기준"

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
            failed_site = _failed_sites_by_website().get(school.website or "")

            crawl_logs = (
                db.query(AuditLog)
                .filter(
                    AuditLog.table_name == "schools",
                    AuditLog.record_id == school_uuid,
                    AuditLog.action == "CRAWL",
                )
                .order_by(AuditLog.created_at.desc())
                .limit(10)
                .all()
            )

            crawl_history = [
                {
                    "id": str(log.id),
                    "timestamp": log.created_at.isoformat() if log.created_at else None,
                    "status": _extract_crawl_status(log.new_value)[0],
                    "message": _extract_crawl_status(log.new_value)[1],
                    "raw": log.new_value if isinstance(log.new_value, dict) else {},
                }
                for log in crawl_logs
            ]
            if failed_site:
                crawl_history.insert(
                    0,
                    {
                        "id": "failed-site",
                        "timestamp": failed_site.get("last_checked_at")
                        or failed_site.get("first_failed_at"),
                        "status": "failed",
                        "message": failed_site.get("error_message")
                        or "SSL 검증 실패",
                        "raw": failed_site,
                    },
                )
            if not crawl_history:
                crawl_history.append(
                    {
                        "id": "db-updated",
                        "timestamp": school.updated_at.isoformat()
                        if school.updated_at
                        else None,
                        "status": "success",
                        "message": "최근 DB 업데이트 기준",
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
                    "esl_program": school.esl_program,
                    "international_support": school.international_support,
                    "facilities": school.facilities,
                    "staff_info": school.staff_info,
                    "tuition": school.tuition,
                    "living_cost": school.living_cost,
                    "acceptance_rate": school.acceptance_rate,
                    "transfer_rate": school.transfer_rate,
                    "graduation_rate": school.graduation_rate,
                    "updated_at": school.updated_at.isoformat() if school.updated_at else None,
                },
                "crawl_history": crawl_history,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"학교 상세 조회 실패: {school_id} - {e}")
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

    failed_site = _failed_sites_by_website().get(website)
    if not failed_site:
        raise HTTPException(status_code=404, detail="실패 사이트를 찾을 수 없습니다")

    try:
        with get_db() as db:
            school = db.query(School).filter(School.website == website).first()
            logs: List[Dict[str, Any]] = []

            if school:
                crawl_logs = (
                    db.query(AuditLog)
                    .filter(
                        AuditLog.action == "CRAWL",
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
                            "raw": log.new_value if isinstance(log.new_value, dict) else {},
                        }
                    )

            if not logs:
                logs.append(
                    {
                        "id": "failed-site",
                        "timestamp": failed_site.get("last_checked_at")
                        or failed_site.get("first_failed_at"),
                        "status": "failed",
                        "message": failed_site.get("error_message") or "SSL 검증 실패",
                        "raw": failed_site,
                    }
                )

            return {
                "site": failed_site,
                "school_id": str(school.id) if school else None,
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
