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

# 5. DB 기반 크롤링 통계
echo "5️⃣ 크롤링 통계 (DB)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker exec college-crawler python - <<'PY' 2>/dev/null
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

sys.path.insert(0, str(Path("/app")))
from src.database.connection import get_db
from src.database.models import School, AuditLog

with get_db() as db:
    total_schools = db.query(School).count()
    last_24h = datetime.now(timezone.utc) - timedelta(days=1)
    crawl_logs = db.query(AuditLog).filter(
        AuditLog.action == "CRAWL",
        AuditLog.created_at >= last_24h
    ).all()
    success = sum(
        1 for log in crawl_logs
        if isinstance(log.new_value, dict) and log.new_value.get("status") == "success"
    )
    failed = len(crawl_logs) - success
    print(f"🏫 DB 저장 학교 수: {total_schools}개")
    print(f"📈 최근 24시간 크롤링: 총 {len(crawl_logs)}건 / 성공 {success}건 / 실패 {failed}건")
PY
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
