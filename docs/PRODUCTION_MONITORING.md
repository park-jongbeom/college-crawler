# 🔍 운영 서버 모니터링 가이드

College Crawler 운영 서버의 동작 상태를 확인하는 방법을 안내합니다.

## 📋 목차

1. [컨테이너 상태 확인](#1-컨테이너-상태-확인)
2. [로그 모니터링](#2-로그-모니터링)
3. [크롤링 결과 확인](#3-크롤링-결과-확인)
4. [데이터베이스 상태 확인](#4-데이터베이스-상태-확인)
5. [시스템 리소스 확인](#5-시스템-리소스-확인)
6. [헬스체크 확인](#6-헬스체크-확인)
7. [트러블슈팅](#7-트러블슈팅)

---

## 1. 컨테이너 상태 확인

### 1.1 컨테이너 실행 상태

```bash
# 컨테이너 목록 및 상태 확인
docker ps -a | grep college-crawler

# 상세 정보 확인
docker inspect college-crawler
```

**확인 사항:**
- `STATUS`: `Up` 상태인지 확인 (재시작 횟수도 체크)
- `PORTS`: 필요한 포트가 열려있는지
- `NAMES`: `college-crawler` 컨테이너가 존재하는지

### 1.2 Docker Compose 상태

```bash
# Compose 서비스 상태 확인
docker compose ps

# 상세 정보
docker compose config
```

---

## 2. 로그 모니터링

### 2.1 실시간 로그 확인

```bash
# 실시간 로그 스트리밍 (모든 로그)
docker compose logs -f college-crawler

# 최근 100줄만 보기
docker compose logs --tail=100 college-crawler

# 특정 시간 이후 로그
docker compose logs --since 1h college-crawler
```

### 2.2 로그 파일 직접 확인

```bash
# 컨테이너 내부 로그 파일 확인
docker exec college-crawler ls -lh /app/logs/

# 로그 파일 읽기
docker exec college-crawler cat /app/logs/app.log

# 최근 로그 확인 (tail)
docker exec college-crawler tail -n 100 /app/logs/app.log

# 실시간 로그 모니터링
docker exec college-crawler tail -f /app/logs/app.log
```

### 2.3 볼륨에서 직접 확인

```bash
# 볼륨 위치 확인
docker volume inspect crawler_logs

# 볼륨 마운트 포인트에서 로그 확인
sudo ls -lh /var/lib/docker/volumes/crawler_logs/_data/
sudo tail -f /var/lib/docker/volumes/crawler_logs/_data/app.log
```

### 2.4 로그 분석

```bash
# 에러 로그만 필터링
docker compose logs college-crawler | grep -i error

# 특정 학교 크롤링 로그
docker compose logs college-crawler | grep "Los Angeles"

# 크롤링 성공/실패 통계
docker compose logs college-crawler | grep -c "✅ 성공"
docker compose logs college-crawler | grep -c "❌ 실패"
```

---

## 3. 크롤링 결과 확인

### 3.1 크롤링 데이터 확인

```bash
# 저장된 크롤링 결과 목록
docker exec college-crawler ls -lh /app/data/crawled/

# 특정 학교 결과 확인
docker exec college-crawler cat /app/data/crawled/school_name.json

# 결과 파일 개수 (크롤링 완료된 학교 수)
docker exec college-crawler find /app/data/crawled -name "*.json" | wc -l
```

### 3.2 볼륨에서 직접 확인

```bash
# 볼륨 위치 확인
docker volume inspect crawler_data

# 크롤링 결과 확인
sudo ls -lh /var/lib/docker/volumes/crawler_data/_data/
sudo cat /var/lib/docker/volumes/crawler_data/_data/school_name.json
```

---

## 4. 데이터베이스 상태 확인

### 4.1 스크립트로 확인

```bash
# DB 상태 체크 스크립트 실행
docker exec college-crawler python scripts/check_db.py
```

**출력 예시:**
```
=== 데이터베이스 상태 확인 ===
1. 데이터베이스 연결 테스트...
   ✅ 연결 성공

2. 학교 데이터 확인...
   전체 학교 수: 60개
   캘리포니아 (CA): 45개
   텍사스 (TX): 5개

3. 최근 등록 학교 (최대 10개):
   1. Los Angeles Trade-Technical College (CA)
      📧 international@lattc.edu
      📞 (213) 763-7000

4. 유학생 담당자 정보가 있는 학교: 25개

=== 확인 완료 ===
```

### 4.2 직접 SQL 쿼리

```bash
# psql 접속 (환경변수 설정 필요)
docker exec -it college-crawler psql -h <DB_HOST> -U <DB_USER> -d ga_db
```

```sql
-- 전체 학교 수
SELECT COUNT(*) FROM schools;

-- 최근 크롤링된 학교 (updated_at 기준)
SELECT name, international_email, updated_at 
FROM schools 
ORDER BY updated_at DESC 
LIMIT 10;

-- 유학생 담당자 정보가 있는 학교
SELECT COUNT(*) 
FROM schools 
WHERE international_email IS NOT NULL;

-- 크롤링 로그 확인 (audit_logs)
SELECT * 
FROM audit_logs 
WHERE action = 'CRAWL' 
ORDER BY created_at DESC 
LIMIT 10;

-- ESL 프로그램이 있는 학교
SELECT name, esl_program->>'available' as has_esl
FROM schools 
WHERE esl_program->>'available' = 'true';

-- 시설 정보가 업데이트된 학교
SELECT name, facilities
FROM schools 
WHERE facilities IS NOT NULL;
```

---

## 5. 시스템 리소스 확인

### 5.1 컨테이너 리소스 사용량

```bash
# 실시간 리소스 모니터링
docker stats college-crawler

# 한 번만 출력
docker stats --no-stream college-crawler
```

**확인 사항:**
- CPU 사용률
- 메모리 사용량
- 네트워크 I/O
- 디스크 I/O

### 5.2 디스크 사용량

```bash
# Docker 볼륨 사이즈
docker system df -v | grep crawler

# 로그 볼륨 크기
sudo du -sh /var/lib/docker/volumes/crawler_logs/_data/

# 데이터 볼륨 크기
sudo du -sh /var/lib/docker/volumes/crawler_data/_data/
```

---

## 6. 헬스체크 확인

### 6.1 Docker 헬스체크

```bash
# 헬스체크 상태 확인
docker inspect --format='{{json .State.Health}}' college-crawler | jq

# 헬스체크 로그
docker inspect college-crawler | jq '.[0].State.Health.Log'
```

### 6.2 수동 헬스체크

```bash
# Python 실행 가능 여부
docker exec college-crawler python --version

# 필요한 모듈 import 테스트
docker exec college-crawler python -c "
from src.database.connection import test_connection
print('✅ 데이터베이스 연결:', test_connection())
"

# 크롤러 모듈 import 테스트
docker exec college-crawler python -c "
from src.crawlers.school_crawler import SchoolCrawler
print('✅ 크롤러 모듈 로드 성공')
"
```

---

## 7. 트러블슈팅

### 7.1 컨테이너가 재시작을 반복하는 경우

```bash
# 최근 로그 확인
docker compose logs --tail=200 college-crawler

# 컨테이너 이벤트 확인
docker events --filter 'container=college-crawler' --since 1h

# 재시작 정책 확인
docker inspect college-crawler | jq '.[0].HostConfig.RestartPolicy'
```

### 7.2 크롤링이 실행되지 않는 경우

```bash
# 환경변수 확인
docker exec college-crawler env | grep -E "DATABASE|CRAWL"

# DB 연결 테스트
docker exec college-crawler python scripts/check_db.py

# 수동으로 크롤링 실행 (테스트)
docker exec college-crawler python src/main.py test
```

### 7.3 로그가 쌓이지 않는 경우

```bash
# 로그 디렉토리 권한 확인
docker exec college-crawler ls -la /app/logs/

# 로그 설정 확인
docker exec college-crawler python -c "
from src.utils.config import config
print('LOG_LEVEL:', config.LOG_LEVEL)
print('LOG_FILE:', config.LOG_FILE)
"
```

### 7.4 메모리 부족 문제

```bash
# 메모리 사용량 확인
docker stats --no-stream college-crawler

# 컨테이너 재시작
docker compose restart college-crawler

# 리소스 제한 추가 (docker-compose.yml)
# deploy:
#   resources:
#     limits:
#       cpus: '1.0'
#       memory: 1G
#     reservations:
#       memory: 512M
```

---

## 📊 종합 모니터링 스크립트

아래 스크립트를 사용하면 한 번에 전체 상태를 확인할 수 있습니다.

### monitor.sh

```bash
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
docker compose logs --tail=100 college-crawler | grep -i error | tail -5
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
echo "📊 로그 볼륨: $(sudo du -sh /var/lib/docker/volumes/crawler_logs/_data/ 2>/dev/null | cut -f1)"
echo "📊 데이터 볼륨: $(sudo du -sh /var/lib/docker/volumes/crawler_data/_data/ 2>/dev/null | cut -f1)"
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 모니터링 완료"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
```

**사용 방법:**

```bash
# 실행 권한 부여
chmod +x scripts/monitor.sh

# 실행
./scripts/monitor.sh
```

---

## 🔔 알림 설정 (선택 사항)

### 8.1 로그 모니터링 알림

로그에 에러가 발생하면 알림을 받도록 설정할 수 있습니다.

```bash
# watch_errors.sh
#!/bin/bash
# 30초마다 에러 로그 확인

while true; do
    ERROR_COUNT=$(docker compose logs --since 30s college-crawler | grep -ci error)
    
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "[$(date)] ⚠️  에러 발생: ${ERROR_COUNT}건"
        # 여기에 Slack/Discord webhook이나 이메일 발송 로직 추가
    fi
    
    sleep 30
done
```

### 8.2 헬스체크 알림

```bash
# health_monitor.sh
#!/bin/bash

HEALTH=$(docker inspect --format='{{.State.Health.Status}}' college-crawler 2>/dev/null)

if [ "$HEALTH" != "healthy" ]; then
    echo "[$(date)] ⚠️  컨테이너 비정상: $HEALTH"
    # 알림 발송 로직
fi
```

---

## 📝 권장 모니터링 주기

| 항목 | 주기 | 방법 |
|------|------|------|
| 컨테이너 상태 | 5분 | `docker ps` |
| 헬스체크 | 5분 | `docker inspect` |
| 로그 에러 | 1분 | `docker logs` |
| 리소스 사용량 | 10분 | `docker stats` |
| DB 데이터 확인 | 1일 | `scripts/check_db.py` |
| 디스크 사용량 | 1주 | `du -sh` |

---

## 🚨 긴급 대응

### 컨테이너 비정상 종료 시

```bash
# 1. 로그 확인 (원인 파악)
docker compose logs --tail=200 college-crawler > /tmp/crash_log.txt

# 2. 컨테이너 재시작
docker compose restart college-crawler

# 3. 재시작 후 로그 모니터링
docker compose logs -f college-crawler
```

### 디스크 풀 (Disk Full) 시

```bash
# 1. 오래된 로그 삭제
docker exec college-crawler find /app/logs -name "*.log.*" -mtime +7 -delete

# 2. 불필요한 크롤링 결과 삭제
docker exec college-crawler find /app/data/crawled -name "*.json" -mtime +30 -delete

# 3. Docker 시스템 정리
docker system prune -f
```

---

## 📚 추가 참고 자료

- [Docker Compose 문서](https://docs.docker.com/compose/)
- [Docker 로그 드라이버](https://docs.docker.com/config/containers/logging/)
- [PostgreSQL 모니터링](https://www.postgresql.org/docs/current/monitoring.html)

---

**작성일**: 2026-02-10  
**버전**: 1.0.0
