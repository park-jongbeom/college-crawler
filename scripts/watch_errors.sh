#!/bin/bash
# 에러 로그 실시간 모니터링 스크립트
# 30초마다 에러 로그를 확인하고 발생 시 알림

echo "🔍 에러 로그 모니터링 시작..."
echo "Ctrl+C로 중지할 수 있습니다."
echo

CHECK_INTERVAL=30  # 체크 주기 (초)
ERROR_THRESHOLD=0  # 알림을 보낼 최소 에러 개수

while true; do
    # 최근 30초 동안의 에러 로그 확인
    ERROR_COUNT=$(docker compose logs --since ${CHECK_INTERVAL}s college-crawler 2>/dev/null | grep -ci error)
    
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ "$ERROR_COUNT" -gt "$ERROR_THRESHOLD" ]; then
        echo "[$TIMESTAMP] ⚠️  에러 발생: ${ERROR_COUNT}건"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        docker compose logs --tail=10 college-crawler 2>/dev/null | grep -i error | tail -3
        echo
        
        # 여기에 알림 발송 로직 추가 가능
        # 예: Slack webhook, 이메일, Discord 등
        # curl -X POST "YOUR_WEBHOOK_URL" -d "{'text': 'Error detected: ${ERROR_COUNT}'}"
    else
        echo "[$TIMESTAMP] ✅ 정상 (에러 없음)"
    fi
    
    sleep $CHECK_INTERVAL
done
