#!/bin/bash
# 로컬에서 간단한 API 테스트 (curl 사용)

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 모니터링 API 간단 테스트 (curl)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 테스트할 URL
BASE_URL="${1:-http://localhost:8080}"

# 색상 코드
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 테스트 카운터
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 테스트 함수
test_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_code=${3:-200}
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing $name... "
    
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" --connect-timeout 5)
    
    if [ "$HTTP_CODE" == "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $HTTP_CODE)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
}

# 서버 연결 확인
echo "🔍 서버 연결 확인: $BASE_URL"
if ! curl -s -f "$BASE_URL/api/health" --connect-timeout 5 > /dev/null; then
    echo -e "${RED}❌ 서버에 연결할 수 없습니다!${NC}"
    echo "서버가 실행 중인지 확인하세요:"
    echo "  docker compose up -d monitor"
    exit 1
fi
echo -e "${GREEN}✅ 서버 연결 성공${NC}"
echo

# 테스트 시작
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 API 엔드포인트 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 헬스체크
test_endpoint "Health Check" "/api/health"

# 상태 API
test_endpoint "Status API" "/api/status"
test_endpoint "Container Status" "/api/container"
test_endpoint "Database Status" "/api/database"
test_endpoint "Resource Usage" "/api/resources"
test_endpoint "Crawling Stats" "/api/crawling/stats"

# 데이터 조회
test_endpoint "Recent Logs" "/api/logs/recent"
test_endpoint "Recent Schools" "/api/schools/recent"
test_endpoint "Recent Logs (20)" "/api/logs/recent?lines=20"
test_endpoint "Recent Schools (page=1, per_page=5)" "/api/schools/recent?page=1&per_page=5"

# 대시보드 페이지
test_endpoint "Dashboard Page" "/"

# OpenAPI 문서
test_endpoint "API Docs" "/docs"
test_endpoint "OpenAPI JSON" "/openapi.json"

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 테스트 결과"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total:  $TOTAL_TESTS tests"
echo -e "Passed: ${GREEN}$PASSED_TESTS tests${NC}"
echo -e "Failed: ${RED}$FAILED_TESTS tests${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo
    echo -e "${GREEN}🎉 모든 테스트 통과!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo
    echo -e "${RED}❌ 일부 테스트 실패${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
