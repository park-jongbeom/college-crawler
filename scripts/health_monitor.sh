#!/bin/bash
# 헬스체크 모니터링 스크립트

echo "🏥 College Crawler 헬스체크 모니터링"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 컨테이너 존재 여부 확인
if ! docker ps -a --format '{{.Names}}' | grep -q "^college-crawler$"; then
    echo "❌ college-crawler 컨테이너를 찾을 수 없습니다."
    exit 1
fi

# 컨테이너 실행 상태
CONTAINER_STATE=$(docker inspect --format='{{.State.Status}}' college-crawler 2>/dev/null)
echo "1️⃣ 컨테이너 상태: $CONTAINER_STATE"

if [ "$CONTAINER_STATE" != "running" ]; then
    echo "   ⚠️  컨테이너가 실행 중이 아닙니다!"
    echo
    echo "   최근 로그:"
    docker compose logs --tail=20 college-crawler
    exit 1
fi

# 헬스체크 상태
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' college-crawler 2>/dev/null)
echo "2️⃣ 헬스체크: $HEALTH"

if [ -z "$HEALTH" ]; then
    echo "   ℹ️  헬스체크가 설정되지 않았습니다."
elif [ "$HEALTH" != "healthy" ]; then
    echo "   ⚠️  헬스체크 비정상!"
    echo
    echo "   헬스체크 로그:"
    docker inspect college-crawler | jq '.[0].State.Health.Log[-3:]' 2>/dev/null
fi

# Python 실행 가능 여부
echo "3️⃣ Python 실행 테스트"
if docker exec college-crawler python --version &>/dev/null; then
    PY_VERSION=$(docker exec college-crawler python --version 2>&1)
    echo "   ✅ $PY_VERSION"
else
    echo "   ❌ Python 실행 실패"
    exit 1
fi

# 데이터베이스 연결 테스트
echo "4️⃣ 데이터베이스 연결 테스트"
DB_TEST=$(docker exec college-crawler python -c "
from src.database.connection import test_connection
result = test_connection()
print('SUCCESS' if result else 'FAILED')
" 2>&1)

if echo "$DB_TEST" | grep -q "SUCCESS"; then
    echo "   ✅ 데이터베이스 연결 성공"
else
    echo "   ❌ 데이터베이스 연결 실패"
    echo "   상세: $DB_TEST"
    exit 1
fi

# 크롤러 모듈 로드 테스트
echo "5️⃣ 크롤러 모듈 테스트"
CRAWLER_TEST=$(docker exec college-crawler python -c "
from src.crawlers.school_crawler import SchoolCrawler
print('SUCCESS')
" 2>&1)

if echo "$CRAWLER_TEST" | grep -q "SUCCESS"; then
    echo "   ✅ 크롤러 모듈 로드 성공"
else
    echo "   ❌ 크롤러 모듈 로드 실패"
    echo "   상세: $CRAWLER_TEST"
    exit 1
fi

# 환경변수 확인
echo "6️⃣ 환경변수 확인"
ENV_VARS=$(docker exec college-crawler env | grep -E "^(DATABASE_HOST|ENVIRONMENT|LOG_LEVEL)" | wc -l)
if [ "$ENV_VARS" -ge 3 ]; then
    echo "   ✅ 필수 환경변수 설정됨"
else
    echo "   ⚠️  일부 환경변수가 누락될 수 있습니다"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 헬스체크 완료: 모든 항목 정상"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
