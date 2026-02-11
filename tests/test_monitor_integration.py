"""
모니터링 시스템 통합 테스트
실제 환경에 가까운 조건에서 테스트
"""

import pytest
import requests
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def base_url():
    """테스트 서버 URL"""
    return "http://localhost:8080"


@pytest.fixture
def wait_for_server(base_url):
    """서버가 준비될 때까지 대기"""
    max_retries = 10
    retry_delay = 2
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/api/health", timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            if i < max_retries - 1:
                time.sleep(retry_delay)
            else:
                pytest.skip("테스트 서버에 연결할 수 없습니다")
    
    return False


@pytest.mark.integration
class TestLiveServer:
    """실제 서버 테스트 (서버가 실행 중일 때만)"""
    
    def test_health_check(self, base_url, wait_for_server):
        """헬스체크 엔드포인트 테스트"""
        response = requests.get(f"{base_url}/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_dashboard_loads(self, base_url, wait_for_server):
        """대시보드 페이지 로딩 테스트"""
        response = requests.get(f"{base_url}/")
        assert response.status_code == 200
        
        # HTML 페이지인지 확인
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type or "application/json" in content_type
    
    def test_status_api_response_time(self, base_url, wait_for_server):
        """상태 API 응답 시간 테스트"""
        start_time = time.time()
        response = requests.get(f"{base_url}/api/status")
        elapsed_time = time.time() - start_time
        
        # 응답 시간이 5초 이내여야 함
        assert elapsed_time < 5.0
        assert response.status_code == 200
    
    def test_all_endpoints_accessible(self, base_url, wait_for_server):
        """모든 엔드포인트 접근 가능 테스트"""
        endpoints = [
            "/api/health",
            "/api/status",
            "/api/container",
            "/api/database",
            "/api/resources",
            "/api/logs/recent",
            "/api/schools/recent",
            "/api/crawling/stats"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            assert response.status_code in [200, 500], f"{endpoint} failed"
    
    def test_api_returns_valid_json(self, base_url, wait_for_server):
        """API가 유효한 JSON을 반환하는지 테스트"""
        endpoints = [
            "/api/health",
            "/api/status",
            "/api/container",
            "/api/database"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            # JSON 파싱 가능해야 함
            try:
                data = response.json()
                assert isinstance(data, (dict, list))
            except ValueError:
                pytest.fail(f"{endpoint} does not return valid JSON")
    
    def test_logs_endpoint_with_parameters(self, base_url, wait_for_server):
        """로그 엔드포인트 파라미터 테스트"""
        response = requests.get(f"{base_url}/api/logs/recent?lines=20")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)
    
    def test_schools_endpoint_with_limit(self, base_url, wait_for_server):
        """학교 엔드포인트 페이징 파라미터 테스트"""
        response = requests.get(f"{base_url}/api/schools/recent?page=1&per_page=5")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        assert data["per_page"] == 5
        assert len(data["items"]) <= 5


@pytest.mark.integration
class TestDataConsistency:
    """데이터 일관성 테스트"""
    
    def test_status_data_consistency(self, base_url, wait_for_server):
        """상태 데이터의 일관성 테스트"""
        response = requests.get(f"{base_url}/api/status")
        data = response.json()
        
        # 필수 필드 존재 확인
        assert "timestamp" in data
        assert "container" in data
        assert "database" in data
        assert "crawling" in data
        assert "resources" in data
    
    def test_multiple_requests_consistency(self, base_url, wait_for_server):
        """여러 요청 간 데이터 일관성 테스트"""
        # 첫 번째 요청
        response1 = requests.get(f"{base_url}/api/database")
        data1 = response1.json()
        
        time.sleep(1)
        
        # 두 번째 요청
        response2 = requests.get(f"{base_url}/api/database")
        data2 = response2.json()
        
        # 짧은 시간 내에 큰 변화가 없어야 함
        if data1.get("connected") and data2.get("connected"):
            # 학교 수는 동일해야 함 (크롤링 중이 아니라면)
            total1 = data1.get("total_schools", 0)
            total2 = data2.get("total_schools", 0)
            
            # 차이가 크지 않아야 함 (활발한 크롤링 중이 아니라면)
            assert abs(total1 - total2) < 10


@pytest.mark.integration
class TestPerformance:
    """성능 테스트"""
    
    def test_concurrent_requests(self, base_url, wait_for_server):
        """동시 요청 처리 테스트"""
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(f"{base_url}/api/health", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # 10개의 동시 요청
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # 대부분의 요청이 성공해야 함
        success_rate = sum(results) / len(results)
        assert success_rate > 0.8  # 80% 이상 성공
    
    def test_repeated_requests_performance(self, base_url, wait_for_server):
        """반복 요청 성능 테스트"""
        response_times = []
        
        for _ in range(5):
            start = time.time()
            response = requests.get(f"{base_url}/api/status")
            elapsed = time.time() - start
            
            if response.status_code == 200:
                response_times.append(elapsed)
        
        # 평균 응답 시간이 3초 이내여야 함
        avg_time = sum(response_times) / len(response_times) if response_times else 0
        assert avg_time < 3.0, f"Average response time: {avg_time}s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
