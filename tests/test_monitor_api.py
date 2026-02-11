"""
모니터링 API 테스트
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.monitor.api import app


@pytest.fixture
def client():
    """FastAPI 테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_docker_client():
    """Docker 클라이언트 Mock"""
    mock = MagicMock()
    mock.ping.return_value = True
    return mock


@pytest.fixture
def mock_container():
    """Docker 컨테이너 Mock"""
    mock = MagicMock()
    mock.name = "college-crawler"
    mock.status = "running"
    mock.attrs = {
        'State': {
            'Status': 'running',
            'StartedAt': '2026-02-10T09:00:00Z',
            'Health': {
                'Status': 'healthy'
            }
        },
        'RestartCount': 0
    }
    
    # Stats mock
    mock.stats.return_value = {
        'cpu_stats': {
            'cpu_usage': {'total_usage': 100000000},
            'system_cpu_usage': 1000000000,
            'online_cpus': 2
        },
        'precpu_stats': {
            'cpu_usage': {'total_usage': 50000000},
            'system_cpu_usage': 900000000
        },
        'memory_stats': {
            'usage': 256 * 1024 * 1024,  # 256MB
            'limit': 1024 * 1024 * 1024   # 1GB
        }
    }
    
    # Logs mock
    mock.logs.return_value = b"2026-02-10T10:00:00 INFO Test log message\n"
    
    return mock


class TestHealthCheck:
    """헬스체크 엔드포인트 테스트"""
    
    def test_health_endpoint_returns_200(self, client):
        """헬스체크 엔드포인트가 200을 반환하는지 테스트"""
        response = client.get("/api/health")
        assert response.status_code == 200
    
    def test_health_response_structure(self, client):
        """헬스체크 응답 구조 테스트"""
        response = client.get("/api/health")
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
    
    def test_health_timestamp_format(self, client):
        """헬스체크 타임스탬프 형식 테스트"""
        response = client.get("/api/health")
        data = response.json()
        
        # ISO 8601 형식 확인
        timestamp = data["timestamp"]
        datetime.fromisoformat(timestamp)  # 파싱 가능해야 함


class TestRootEndpoint:
    """루트 엔드포인트 테스트"""
    
    def test_root_returns_200(self, client):
        """루트 엔드포인트가 200을 반환하는지 테스트"""
        response = client.get("/")
        assert response.status_code == 200
    
    def test_root_returns_html_or_json(self, client):
        """루트 엔드포인트가 HTML 또는 JSON을 반환하는지 테스트"""
        response = client.get("/")
        content_type = response.headers.get("content-type", "")
        
        assert "text/html" in content_type or "application/json" in content_type


class TestContainerStatus:
    """컨테이너 상태 엔드포인트 테스트"""
    
    @patch('src.monitor.api.docker_client')
    def test_container_status_endpoint(self, mock_docker, client, mock_container):
        """컨테이너 상태 조회 테스트"""
        mock_docker.containers.get.return_value = mock_container
        
        response = client.get("/api/container")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "status" in data
        assert "running" in data
    
    @patch('src.monitor.api.docker_client')
    def test_container_not_found(self, mock_docker, client):
        """컨테이너를 찾을 수 없을 때 테스트"""
        import docker.errors
        mock_docker.containers.get.side_effect = docker.errors.NotFound("Container not found")
        
        response = client.get("/api/container")
        assert response.status_code == 200  # 에러를 JSON으로 반환
        
        data = response.json()
        assert data["status"] == "not_found"
    
    @patch('src.monitor.api.docker_client', None)
    def test_container_without_docker_client(self, client):
        """Docker 클라이언트 없이 호출 시 테스트"""
        response = client.get("/api/container")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "unknown"


class TestDatabaseStatus:
    """데이터베이스 상태 엔드포인트 테스트"""
    
    @patch('src.monitor.api.test_connection')
    @patch('src.monitor.api.get_db')
    def test_database_status_connected(self, mock_get_db, mock_test_conn, client):
        """데이터베이스 연결 성공 테스트"""
        mock_test_conn.return_value = True
        
        # DB 세션 Mock
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Query Mock
        mock_query = MagicMock()
        mock_query.count.return_value = 60
        mock_db.query.return_value = mock_query
        
        # Filter Mock
        mock_query.filter.return_value.count.return_value = 25
        
        response = client.get("/api/database")
        assert response.status_code == 200
        
        data = response.json()
        assert data["connected"] is True
        assert "total_schools" in data
        assert "schools_with_email" in data
        assert "schools_with_employment_rate" in data
        assert "schools_with_facilities" in data
        assert "completion_rate" in data
    
    @patch('src.monitor.api.test_connection')
    def test_database_connection_failed(self, mock_test_conn, client):
        """데이터베이스 연결 실패 테스트"""
        mock_test_conn.return_value = False
        
        response = client.get("/api/database")
        assert response.status_code == 200
        
        data = response.json()
        assert data["connected"] is False


class TestResourceUsage:
    """리소스 사용량 엔드포인트 테스트"""
    
    @patch('src.monitor.api.docker_client')
    def test_resources_endpoint(self, mock_docker, client, mock_container):
        """리소스 사용량 조회 테스트"""
        mock_docker.containers.get.return_value = mock_container
        
        response = client.get("/api/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_percent" in data
        assert "memory_usage_mb" in data
        assert "memory_limit_mb" in data
        assert "memory_percent" in data
        assert data["available"] is True
    
    @patch('src.monitor.api.docker_client', None)
    def test_resources_without_docker(self, client):
        """Docker 없이 리소스 조회 테스트"""
        response = client.get("/api/resources")
        assert response.status_code == 200
        
        data = response.json()
        assert data["available"] is False


class TestLogsEndpoint:
    """로그 엔드포인트 테스트"""
    
    @patch('src.monitor.api.docker_client')
    def test_logs_endpoint(self, mock_docker, client, mock_container):
        """로그 조회 테스트"""
        mock_docker.containers.get.return_value = mock_container
        
        response = client.get("/api/logs/recent?lines=50")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
    
    @patch('src.monitor.api.docker_client')
    def test_logs_with_custom_lines(self, mock_docker, client, mock_container):
        """커스텀 라인 수로 로그 조회 테스트"""
        mock_docker.containers.get.return_value = mock_container
        
        response = client.get("/api/logs/recent?lines=100")
        assert response.status_code == 200
        
        # lines 파라미터가 전달되었는지 확인
        mock_container.logs.assert_called()


class TestSchoolsEndpoint:
    """학교 목록 엔드포인트 테스트"""
    
    @patch('src.monitor.api.get_db')
    def test_recent_schools_endpoint(self, mock_get_db, client):
        """최근 학교 목록 조회 테스트"""
        # Mock 학교 데이터
        mock_school = MagicMock()
        mock_school.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_school.name = "Test College"
        mock_school.state = "CA"
        mock_school.city = "Los Angeles"
        mock_school.international_email = "test@college.edu"
        mock_school.international_phone = "(123) 456-7890"
        mock_school.website = "https://test.edu"
        mock_school.updated_at = datetime.now()
        
        # DB 세션 Mock
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Query Mock
        mock_query = MagicMock()
        mock_query.order_by.return_value.limit.return_value.all.return_value = [mock_school]
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/schools/recent?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            school = data[0]
            assert "id" in school
            assert "name" in school
            assert "state" in school
            assert "international_email" in school

    @patch('src.monitor.api.get_db')
    @patch('src.monitor.api._failed_sites_by_website')
    def test_school_detail_includes_extended_fields(self, mock_failed_sites, mock_get_db, client):
        """학교 상세 응답에 확장 컬럼이 포함되는지 테스트"""
        mock_failed_sites.return_value = {}

        mock_school = MagicMock()
        mock_school.id = "123e4567-e89b-12d3-a456-426614174000"
        mock_school.name = "Test College"
        mock_school.type = "community_college"
        mock_school.state = "CA"
        mock_school.city = "Los Angeles"
        mock_school.website = "https://test.edu"
        mock_school.description = "설명"
        mock_school.international_email = "test@college.edu"
        mock_school.international_phone = "(123) 456-7890"
        mock_school.employment_rate = 87.5
        mock_school.esl_program = {"available": True}
        mock_school.international_support = {"available": True}
        mock_school.facilities = {"library": True}
        mock_school.staff_info = {"international_staff_count": 2}
        mock_school.tuition = 10000
        mock_school.living_cost = 1200
        mock_school.acceptance_rate = 70
        mock_school.transfer_rate = 45
        mock_school.graduation_rate = 55
        mock_school.updated_at = datetime.now()

        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = mock_school
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

        response = client.get("/api/schools/123e4567-e89b-12d3-a456-426614174000")
        assert response.status_code == 200

        data = response.json()
        assert "school" in data
        assert data["school"]["employment_rate"] == 87.5
        assert data["school"]["facilities"] == {"library": True}
        assert data["school"]["staff_info"] == {"international_staff_count": 2}


class TestStatusEndpoint:
    """통합 상태 엔드포인트 테스트"""
    
    @patch('src.monitor.api.get_resource_usage')
    @patch('src.monitor.api.get_crawling_stats')
    @patch('src.monitor.api.get_database_status')
    @patch('src.monitor.api.get_container_status')
    def test_status_endpoint_structure(
        self, 
        mock_container, 
        mock_db, 
        mock_crawl, 
        mock_resources, 
        client
    ):
        """통합 상태 엔드포인트 구조 테스트"""
        # Mock 반환값 설정
        mock_container.return_value = {"status": "running"}
        mock_db.return_value = {"connected": True, "total_schools": 60}
        mock_crawl.return_value = {"total": 25, "success": 23}
        mock_resources.return_value = {"cpu_percent": 2.5}
        
        response = client.get("/api/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "timestamp" in data
        assert "container" in data
        assert "database" in data
        assert "crawling" in data
        assert "resources" in data


class TestCrawlingStats:
    """크롤링 통계 엔드포인트 테스트"""
    
    @patch('src.monitor.api.get_db')
    def test_crawling_stats_endpoint(self, mock_get_db, client):
        """크롤링 통계 조회 테스트"""
        # Mock DB
        mock_db = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_db
        
        # Mock Query
        mock_log = MagicMock()
        mock_log.new_value = {"status": "success"}
        mock_log.created_at = datetime.now()
        
        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_log] * 10
        mock_db.query.return_value = mock_query
        
        response = client.get("/api/crawling/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "success" in data
        assert "failed" in data
        assert "success_rate" in data


class TestAPIDocumentation:
    """API 문서 테스트"""
    
    def test_openapi_docs_available(self, client):
        """OpenAPI 문서가 제공되는지 테스트"""
        response = client.get("/docs")
        assert response.status_code == 200
    
    def test_openapi_json_available(self, client):
        """OpenAPI JSON이 제공되는지 테스트"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data


class TestErrorHandling:
    """에러 처리 테스트"""
    
    @patch('src.monitor.api.get_container_status')
    def test_status_endpoint_error_handling(self, mock_container, client):
        """상태 엔드포인트 에러 처리 테스트"""
        mock_container.side_effect = Exception("Test error")
        
        response = client.get("/api/status")
        # 에러가 발생해도 500 에러를 반환해야 함
        assert response.status_code == 500


class TestCORSConfiguration:
    """CORS 설정 테스트"""
    
    def test_cors_headers_present(self, client):
        """CORS 헤더가 존재하는지 테스트"""
        response = client.options("/api/health")
        
        # CORS 헤더 확인
        assert "access-control-allow-origin" in response.headers


# 통합 테스트
class TestIntegration:
    """통합 테스트"""
    
    def test_full_dashboard_flow(self, client):
        """전체 대시보드 플로우 테스트"""
        # 1. 헬스체크
        health = client.get("/api/health")
        assert health.status_code == 200
        
        # 2. 루트 페이지
        root = client.get("/")
        assert root.status_code == 200
        
        # 3. 각 API 엔드포인트 호출
        endpoints = [
            "/api/container",
            "/api/database",
            "/api/resources",
            "/api/logs/recent",
            "/api/schools/recent",
            "/api/crawling/stats"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # 모든 엔드포인트가 200 또는 에러를 JSON으로 반환해야 함
            assert response.status_code in [200, 500]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
