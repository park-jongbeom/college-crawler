#!/bin/bash
# College Crawler 운영 상태 종합 모니터링 스크립트

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 College Crawler 운영 상태 확인"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 1. 컨테이너 상태
echo "1️⃣ 컨테이너 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker ps --filter "name=college-crawler" --format "table {{.Names}}\t{{.Status}}\t{{.RunningFor}}"
echo

# 2. 헬스체크
echo "2️⃣ 헬스체크"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
HEALTH=$(docker inspect --format='{{.State.Health.Status}}' college-crawler 2>/dev/null)
if [ "$HEALTH" == "healthy" ]; then
    echo "✅ 상태: 정상"
else
    echo "⚠️  상태: $HEALTH"
fi
echo

# 3. 리소스 사용량
echo "3️⃣ 리소스 사용량"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" college-crawler
echo

# 4. 최근 로그 (에러만)
echo "4️⃣ 최근 에러 로그 (5줄)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=100 college-crawler 2>/dev/null | grep -i error | tail -5
if [ $? -ne 0 ]; then
    echo "✅ 최근 에러 없음"
fi
echo

# 5. 크롤링 결과 통계
echo "5️⃣ 크롤링 결과"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
CRAWLED_COUNT=$(docker exec college-crawler find /app/data/crawled -name "*.json" 2>/dev/null | wc -l)
echo "📁 저장된 크롤링 결과: ${CRAWLED_COUNT}개"
echo

# 6. 데이터베이스 상태
echo "6️⃣ 데이터베이스 상태"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec college-crawler python scripts/check_db.py 2>/dev/null | grep -E "전체 학교|유학생 담당자"
echo

# 7. 디스크 사용량
echo "7️⃣ 디스크 사용량"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LOG_SIZE=$(sudo du -sh /var/lib/docker/volumes/crawler_logs/_data/ 2>/dev/null | cut -f1)
DATA_SIZE=$(sudo du -sh /var/lib/docker/volumes/crawler_data/_data/ 2>/dev/null | cut -f1)
if [ -n "$LOG_SIZE" ]; then
    echo "📊 로그 볼륨: $LOG_SIZE"
else
    echo "📊 로그 볼륨: 확인 불가 (권한 필요)"
fi
if [ -n "$DATA_SIZE" ]; then
    echo "📊 데이터 볼륨: $DATA_SIZE"
else
    echo "📊 데이터 볼륨: 확인 불가 (권한 필요)"
fi
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모니터링 완료 ($(date '+%Y-%m-%d %H:%M:%S'))"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
