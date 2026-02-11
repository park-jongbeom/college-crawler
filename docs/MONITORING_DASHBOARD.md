# 📊 모니터링 웹 대시보드 가이드

College Crawler의 실시간 모니터링 웹 대시보드 사용 가이드입니다.

## 🎯 개요

FastAPI 기반 실시간 모니터링 대시보드로, 웹 브라우저에서 크롤러의 상태를 편리하게 확인할 수 있습니다.

### 주요 기능

✅ **실시간 상태 모니터링**
- 컨테이너 실행 상태 및 헬스체크
- CPU, 메모리 사용량
- 데이터베이스 연결 상태

✅ **크롤링 통계**
- 성공/실패 통계
- 전체 완료율
- 최근 크롤링 현황

✅ **데이터 조회**
- 최근 업데이트된 학교 목록
- 수집된 연락처 정보
- 실시간 로그 확인

✅ **자동 새로고침**
- 30초마다 자동 업데이트
- 수동 새로고침 가능

---

## 🚀 빠른 시작

### 운영 환경 (프로덕션)

```bash
# 1. 서비스 시작 (모니터 포함)
docker compose up -d

# 2. 브라우저에서 접속
http://서버IP:8080
```

### 로컬 개발 환경

```bash
# 1. 서비스 시작
docker compose -f docker-compose-local.yml up -d

# 2. 브라우저에서 접속
http://localhost:8080
```

---

## 📱 대시보드 화면 구성

### 1. 상단 헤더

```
🕷️ College Crawler Monitor        [마지막 업데이트: 2026-02-10 18:45]  [🔄 새로고침]
```

- 실시간 타임스탬프 표시
- 수동 새로고침 버튼

### 2. 상태 카드 (4개)

#### 🟢 컨테이너 상태
```
컨테이너 상태
Running ✅
Health: healthy
```
- 실행 여부 (Running/Stopped)
- 헬스체크 상태

#### 💾 데이터베이스
```
데이터베이스
60 개
이메일: 25개
```
- 전체 학교 수
- 이메일이 있는 학교 수

#### ⚡ CPU 사용률
```
CPU 사용률
2.5%
[━━━━━━━━━━━━━━━━━━] 2.5%
```
- 실시간 CPU 사용률
- 프로그레스 바

#### 🧠 메모리 사용량
```
메모리 사용량
245MB
/ 1024MB (24%)
```
- 현재 메모리 사용량
- 전체 메모리 대비 비율

### 3. 크롤링 통계

```
📊 크롤링 통계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    23              2               92%
   성공            실패           성공률

[━━━━━━━━━━━━━━━━━━━━━━━━━━] 92%
전체 완료율: 92%
```

### 4. 최근 업데이트된 학교

```
🎓 최근 업데이트된 학교
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

학교명                           위치          연락처                  업데이트
────────────────────────────────────────────────────────────────────
Los Angeles Trade-Technical...   CA, LA        📧 intl@lattc.edu      2월 10 18:45
Santa Monica College             CA, SM        📞 (310) 434-4000      2월 10 18:42
...
```

### 5. 최근 로그

```
📝 최근 로그                                              [새로고침]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[터미널 스타일 로그]
2026-02-10T18:45:32 - INFO - ✅ Santa Monica College 크롤링 완료
2026-02-10T18:42:15 - INFO - 📧 이메일 수집: admission@smc.edu
2026-02-10T18:40:03 - WARNING - ⚠️  연결 재시도: UCLA
...
```

---

## 🔌 API 엔드포인트

대시보드는 다음 REST API를 제공합니다:

### 주요 엔드포인트

| 엔드포인트 | 메서드 | 설명 |
|-----------|--------|------|
| `/` | GET | 대시보드 HTML 페이지 |
| `/api/status` | GET | 전체 시스템 상태 (통합) |
| `/api/container` | GET | 컨테이너 상태 |
| `/api/database` | GET | 데이터베이스 통계 |
| `/api/crawling/stats` | GET | 크롤링 통계 |
| `/api/resources` | GET | 리소스 사용량 (CPU, 메모리) |
| `/api/logs/recent` | GET | 최근 로그 |
| `/api/schools/recent` | GET | 최근 업데이트된 학교 (페이징: page, per_page / 필터: state, school_type, q) |
| `/api/health` | GET | 헬스체크 |

### API 사용 예시

```bash
# 전체 상태 조회
curl http://localhost:8080/api/status

# 크롤링 통계
curl http://localhost:8080/api/crawling/stats

# 최근 로그 (100줄)
curl http://localhost:8080/api/logs/recent?lines=100

# 최근 학교 (페이징·필터)
curl "http://localhost:8080/api/schools/recent?page=1&per_page=20"
curl "http://localhost:8080/api/schools/recent?page=1&per_page=10&state=CA&school_type=community_college&q=College"
```

### 응답 예시

```json
// GET /api/status
{
  "timestamp": "2026-02-10T18:45:32",
  "container": {
    "name": "college-crawler",
    "status": "running",
    "health": "healthy",
    "running": true
  },
  "database": {
    "connected": true,
    "total_schools": 60,
    "schools_with_email": 25,
    "completion_rate": 41.7
  },
  "crawling": {
    "total": 25,
    "success": 23,
    "failed": 2,
    "success_rate": 92.0
  },
  "resources": {
    "cpu_percent": 2.45,
    "memory_usage_mb": 245.0,
    "memory_limit_mb": 1024.0,
    "memory_percent": 23.9
  }
}
```

---

## ⚙️ 설정

### 포트 변경

기본 포트는 **8080**입니다. 변경하려면:

```yaml
# docker-compose.yml
services:
  monitor:
    ports:
      - "9090:8080"  # 9090으로 변경
```

### 환경변수

```bash
# .env 파일
MONITOR_PORT=8080
LOG_LEVEL=INFO
```

### 보안 설정 (선택 사항)

기본 인증을 추가하려면:

```python
# src/monitor/api.py에 추가
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

@app.get("/")
async def root(credentials: HTTPBasicCredentials = Depends(security)):
    # 인증 로직
    ...
```

---

## 🔧 트러블슈팅

### 대시보드에 접속이 안 되는 경우

```bash
# 1. 컨테이너 상태 확인
docker ps | grep monitor

# 2. 로그 확인
docker compose logs monitor

# 3. 포트 확인
netstat -tuln | grep 8080

# 4. 컨테이너 재시작
docker compose restart monitor
```

### 데이터가 표시되지 않는 경우

```bash
# 1. API 직접 호출 테스트
curl http://localhost:8080/api/status

# 2. DB 연결 확인
docker exec college-crawler-monitor python -c "
from src.database.connection import test_connection
print('DB:', test_connection())
"

# 3. Docker 소켓 권한 확인
docker exec college-crawler-monitor python -c "
import docker
client = docker.from_env()
print('Docker:', client.ping())
"
```

### CPU/메모리 데이터가 없는 경우

Docker 소켓 마운트가 제대로 되었는지 확인:

```bash
# docker-compose.yml 확인
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro  # 이 줄이 있어야 함
```

---

## 🚀 고급 기능

### 1. 외부 접근 허용

방화벽 설정:

```bash
# UFW 사용 시
sudo ufw allow 8080/tcp

# iptables 사용 시
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
```

### 2. HTTPS 설정 (nginx 리버스 프록시)

```nginx
# /etc/nginx/sites-available/crawler-monitor
server {
    listen 443 ssl;
    server_name monitor.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. Systemd 서비스로 등록

```bash
# /etc/systemd/system/crawler-monitor.service
[Unit]
Description=College Crawler Monitor
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/media/ubuntu/data120g/college-crawler
ExecStart=/usr/bin/docker compose up -d monitor
ExecStop=/usr/bin/docker compose stop monitor

[Install]
WantedBy=multi-user.target
```

---

## 📊 모니터링 베스트 프랙티스

### 일일 체크리스트

- [ ] 대시보드 접속하여 전체 상태 확인
- [ ] 컨테이너 상태가 "Running" 및 "Healthy"인지 확인
- [ ] CPU/메모리 사용량이 정상 범위인지 확인
- [ ] 크롤링 성공률 확인
- [ ] 에러 로그 확인

### 알림 설정 권장

특정 조건에서 알림을 받도록 스크립트 작성:

```bash
#!/bin/bash
# alert.sh - 크롤링 실패율이 높을 때 알림

STATUS=$(curl -s http://localhost:8080/api/crawling/stats)
FAILED=$(echo $STATUS | jq '.failed')
TOTAL=$(echo $STATUS | jq '.total')

if [ $TOTAL -gt 0 ]; then
    FAIL_RATE=$((FAILED * 100 / TOTAL))
    
    if [ $FAIL_RATE -gt 20 ]; then
        # Slack/Discord/Email 알림
        echo "⚠️ 크롤링 실패율 높음: ${FAIL_RATE}%"
    fi
fi
```

---

## 📚 추가 자료

- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [Docker API](https://docker-py.readthedocs.io/)
- [Alpine.js 가이드](https://alpinejs.dev/)

---

**작성일**: 2026-02-10  
**버전**: 1.0.0  
**문의**: patrick@goalmond.com
