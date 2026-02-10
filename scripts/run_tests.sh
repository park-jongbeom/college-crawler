#!/bin/bash
# 모니터링 API 테스트 실행 스크립트

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 College Crawler 모니터링 API 테스트"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 컨테이너 이름
CONTAINER_NAME="college-crawler-test"

# 테스트 타입 (기본: unit)
TEST_TYPE="${1:-unit}"

# 이전 테스트 컨테이너 정리
echo "🧹 이전 테스트 컨테이너 정리..."
docker rm -f $CONTAINER_NAME 2>/dev/null || true
echo

# Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드..."
docker build -t college-crawler:test . --quiet
echo "✅ 이미지 빌드 완료"
echo

# 테스트 실행
echo "🚀 테스트 실행 중..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

if [ "$TEST_TYPE" == "unit" ]; then
    echo "📝 단위 테스트 실행"
    docker run --rm \
        --name $CONTAINER_NAME \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        college-crawler:test \
        pytest tests/test_monitor_api.py -v --tb=short -m "not integration"
elif [ "$TEST_TYPE" == "integration" ]; then
    echo "🔗 통합 테스트 실행"
    echo "⚠️  통합 테스트는 실행 중인 서버가 필요합니다"
    echo
    
    # 모니터 서비스 시작
    docker compose up -d monitor
    
    # 서버 준비 대기
    echo "⏳ 서버 시작 대기 중..."
    sleep 10
    
    # 통합 테스트 실행
    docker run --rm \
        --name $CONTAINER_NAME \
        --network host \
        college-crawler:test \
        pytest tests/test_monitor_integration.py -v --tb=short -m "integration"
    
    # 정리
    docker compose stop monitor
elif [ "$TEST_TYPE" == "all" ]; then
    echo "📦 전체 테스트 실행"
    docker run --rm \
        --name $CONTAINER_NAME \
        -v /var/run/docker.sock:/var/run/docker.sock:ro \
        college-crawler:test \
        pytest tests/ -v --tb=short
else
    echo "❌ 알 수 없는 테스트 타입: $TEST_TYPE"
    echo "사용법: $0 [unit|integration|all]"
    exit 1
fi

TEST_EXIT_CODE=$?

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "✅ 테스트 성공!"
else
    echo "❌ 테스트 실패 (Exit code: $TEST_EXIT_CODE)"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $TEST_EXIT_CODE
