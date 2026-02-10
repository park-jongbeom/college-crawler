# ⚡ 빠른 모니터링 가이드

운영 서버에서 College Crawler가 제대로 동작하는지 **3분 안에** 확인하는 방법입니다.

## 🚀 가장 빠른 확인 방법

### 1단계: 종합 모니터링 스크립트 실행

```bash
cd /media/ubuntu/data120g/college-crawler
./scripts/monitor.sh
```

이 명령 하나로 다음 항목들을 확인할 수 있습니다:
- ✅ 컨테이너 실행 상태
- ✅ 헬스체크 상태  
- ✅ CPU/메모리 사용량
- ✅ 최근 에러 로그
- ✅ 크롤링 결과 개수
- ✅ 데이터베이스 연결
- ✅ 디스크 사용량

**예상 출력:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 College Crawler 운영 상태 확인
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ 컨테이너 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAMES              STATUS              RUNNING FOR
college-crawler    Up 2 hours          2 hours ago

2️⃣ 헬스체크
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 상태: 정상

3️⃣ 리소스 사용량
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NAME               CPU %     MEM USAGE
college-crawler    2.45%     245MiB / 1GiB

4️⃣ 최근 에러 로그 (5줄)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 최근 에러 없음

5️⃣ 크롤링 결과
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📁 저장된 크롤링 결과: 25개

6️⃣ 데이터베이스 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   전체 학교 수: 60개
   유학생 담당자 정보가 있는 학교: 25개

7️⃣ 디스크 사용량
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 로그 볼륨: 124M
📊 데이터 볼륨: 3.2M

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 모니터링 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔍 상세 확인 방법

### 1. 실시간 로그 모니터링

```bash
# 실시간 로그 확인 (Ctrl+C로 종료)
docker compose logs -f college-crawler

# 최근 50줄만
docker compose logs --tail=50 college-crawler

# 최근 1시간 로그
docker compose logs --since 1h college-crawler
```

### 2. 헬스체크

```bash
./scripts/health_monitor.sh
```

**예상 출력:**
```
🏥 College Crawler 헬스체크 모니터링
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ 컨테이너 상태: running
2️⃣ 헬스체크: healthy
3️⃣ Python 실행 테스트
   ✅ Python 3.11.9
4️⃣ 데이터베이스 연결 테스트
   ✅ 데이터베이스 연결 성공
5️⃣ 크롤러 모듈 테스트
   ✅ 크롤러 모듈 로드 성공
6️⃣ 환경변수 확인
   ✅ 필수 환경변수 설정됨

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ 헬스체크 완료: 모든 항목 정상
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 3. 데이터베이스 확인

```bash
# DB 상태 체크
docker exec college-crawler python scripts/check_db.py
```

**예상 출력:**
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
   2. Santa Monica College (CA)
      📧 admission@smc.edu
   ...

4. 유학생 담당자 정보가 있는 학교: 25개

=== 확인 완료 ===
```

---

## 🚨 문제 발생 시 즉시 확인

### 컨테이너가 실행되지 않는 경우

```bash
# 1. 컨테이너 상태 확인
docker ps -a | grep college-crawler

# 2. 최근 로그 확인
docker compose logs --tail=100 college-crawler

# 3. 재시작
docker compose restart college-crawler
```

### 에러 로그 확인

```bash
# 에러만 필터링
docker compose logs college-crawler | grep -i error

# 최근 에러 5개
docker compose logs college-crawler | grep -i error | tail -5

# 특정 날짜의 에러
docker compose logs --since "2026-02-10T00:00:00" college-crawler | grep -i error
```

### 메모리 이슈

```bash
# 실시간 리소스 모니터링
docker stats college-crawler

# 컨테이너 재시작
docker compose restart college-crawler
```

---

## 📊 크롤링 진행 상황 확인

### 방법 1: 로그로 확인

```bash
# 크롤링 성공 로그
docker compose logs college-crawler | grep "✅ 성공"

# 크롤링 실패 로그
docker compose logs college-crawler | grep "❌ 실패"

# 통계
echo "성공: $(docker compose logs college-crawler | grep -c '✅')"
echo "실패: $(docker compose logs college-crawler | grep -c '❌')"
```

### 방법 2: 파일로 확인

```bash
# 크롤링 완료된 학교 수
docker exec college-crawler find /app/data/crawled -name "*.json" | wc -l

# 파일 목록
docker exec college-crawler ls -lh /app/data/crawled/

# 특정 학교 결과 보기
docker exec college-crawler cat /app/data/crawled/school_name.json | jq '.'
```

### 방법 3: 데이터베이스로 확인

```bash
# 데이터베이스에 저장된 데이터 확인
docker exec college-crawler python scripts/check_db.py

# 또는 직접 SQL 실행
docker exec college-crawler python -c "
from src.database.connection import get_db
from src.database.models import School

with get_db() as db:
    total = db.query(School).count()
    with_email = db.query(School).filter(School.international_email != None).count()
    print(f'전체 학교: {total}')
    print(f'이메일 있는 학교: {with_email}')
"
```

---

## 🔔 실시간 모니터링 (백그라운드)

에러를 실시간으로 감시하고 싶다면:

```bash
# 에러 감시 스크립트 실행 (30초마다 체크)
./scripts/watch_errors.sh

# 백그라운드로 실행
nohup ./scripts/watch_errors.sh > /tmp/error_watch.log 2>&1 &

# 프로세스 확인
ps aux | grep watch_errors

# 종료
pkill -f watch_errors.sh
```

---

## 📱 주요 명령어 치트시트

| 목적 | 명령어 |
|------|--------|
| 종합 모니터링 | `./scripts/monitor.sh` |
| 헬스체크 | `./scripts/health_monitor.sh` |
| 실시간 로그 | `docker compose logs -f college-crawler` |
| 컨테이너 상태 | `docker ps \| grep college-crawler` |
| 리소스 사용량 | `docker stats college-crawler` |
| DB 확인 | `docker exec college-crawler python scripts/check_db.py` |
| 컨테이너 재시작 | `docker compose restart college-crawler` |
| 에러 로그 | `docker compose logs college-crawler \| grep -i error` |

---

## 💡 자동화 팁

### Cron으로 정기 모니터링

```bash
# crontab 편집
crontab -e

# 매 5분마다 헬스체크 (로그 저장)
*/5 * * * * cd /media/ubuntu/data120g/college-crawler && ./scripts/health_monitor.sh >> /tmp/health_check.log 2>&1

# 매일 오전 9시 종합 모니터링
0 9 * * * cd /media/ubuntu/data120g/college-crawler && ./scripts/monitor.sh | mail -s "College Crawler 일일 리포트" your@email.com
```

### Systemd 서비스로 실시간 모니터링

```bash
# /etc/systemd/system/crawler-monitor.service
[Unit]
Description=College Crawler Error Monitor
After=docker.service

[Service]
Type=simple
ExecStart=/media/ubuntu/data120g/college-crawler/scripts/watch_errors.sh
Restart=always
User=patrick

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 등록 및 시작
sudo systemctl daemon-reload
sudo systemctl enable crawler-monitor
sudo systemctl start crawler-monitor

# 상태 확인
sudo systemctl status crawler-monitor
```

---

## 🎯 일일 체크리스트

매일 다음 항목들을 확인하세요:

- [ ] 컨테이너 실행 상태 (`docker ps`)
- [ ] 헬스체크 정상 여부 (`./scripts/health_monitor.sh`)
- [ ] 에러 로그 없음 (`docker compose logs | grep -i error`)
- [ ] 크롤링 진행 상황 (로그 또는 DB)
- [ ] 디스크 사용량 (`df -h`)
- [ ] 메모리 사용량 (`docker stats`)

**소요 시간**: 약 2-3분

---

## 📚 더 알아보기

상세한 모니터링 가이드는 [PRODUCTION_MONITORING.md](./PRODUCTION_MONITORING.md)를 참고하세요.

---

**최종 업데이트**: 2026-02-10
