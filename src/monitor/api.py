"""
FastAPI 기반 모니터링 API
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
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
            # 최근 24시간 크롤링 로그
            yesterday = datetime.now() - timedelta(days=1)
            recent_logs = db.query(AuditLog).filter(
                AuditLog.action == 'CRAWL',
                AuditLog.created_at >= yesterday
            ).all()
            
            # 성공/실패 카운트 (new_value에 status 정보가 있다고 가정)
            total = len(recent_logs)
            success = sum(1 for log in recent_logs 
                         if log.new_value and log.new_value.get('status') == 'success')
            failed = total - success
            
            return {
                "total": total,
                "success": success,
                "failed": failed,
                "success_rate": round((success / total * 100), 1) if total > 0 else 0,
                "last_crawl": recent_logs[-1].created_at.isoformat() if recent_logs else None
            }
            
    except Exception as e:
        logger.error(f"크롤링 통계 조회 실패: {e}")
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "success_rate": 0
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
            schools = db.query(School).order_by(
                School.updated_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": str(school.id),
                    "name": school.name,
                    "state": school.state,
                    "city": school.city,
                    "international_email": school.international_email,
                    "international_phone": school.international_phone,
                    "website": school.website,
                    "updated_at": school.updated_at.isoformat() if school.updated_at else None
                }
                for school in schools
            ]
            
    except Exception as e:
        logger.error(f"학교 목록 조회 실패: {e}")
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
