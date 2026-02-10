# ✅ 모니터링 대시보드 설치 완료

College Crawler 프로젝트에 실시간 웹 모니터링 대시보드가 성공적으로 추가되었습니다! 🎉

## 📦 설치된 구성요소

### 1. 백엔드 API (FastAPI)
- **위치**: `src/monitor/`
- **파일**:
  - `api.py` - REST API 엔드포인트
  - `run.py` - 서버 실행 스크립트
  - `__init__.py` - 모듈 초기화

### 2. 프론트엔드 대시보드
- **위치**: `src/monitor/static/`
- **파일**:
  - `dashboard.html` - 반응형 웹 대시보드 (Tailwind CSS + Alpine.js)

### 3. Docker 설정
- **수정된 파일**:
  - `docker-compose.yml` - 운영 환경 모니터 서비스 추가
  - `docker-compose-local.yml` - 로컬 개발 환경 모니터 서비스 추가

### 4. Python 패키지
- **수정된 파일**:
  - `requirements.txt` - FastAPI, Uvicorn, Docker SDK 추가

### 5. 문서
- **새로 생성된 문서**:
  - `docs/MONITORING_DASHBOARD.md` - 상세 사용 가이드
  - `docs/MONITOR_QUICK_START.md` - 1분 빠른 시작 가이드
  - `docs/PRODUCTION_MONITORING.md` - CLI 모니터링 가이드
  - `docs/QUICK_MONITORING.md` - 빠른 CLI 모니터링

### 6. 모니터링 스크립트
- **생성된 스크립트**:
  - `scripts/monitor.sh` - 종합 상태 체크
  - `scripts/health_monitor.sh` - 헬스체크
  - `scripts/watch_errors.sh` - 에러 실시간 감시

---

## 🚀 바로 시작하기

### 운영 서버에서 시작

```bash
# 1. 의존성 설치 (필요 시)
pip install -r requirements.txt

# 2. Docker 이미지 재빌드
docker compose build

# 3. 서비스 시작
docker compose up -d

# 4. 브라우저에서 접속
# http://서버IP:8080
```

### 상태 확인

```bash
# 컨테이너 확인
docker ps | grep monitor

# 로그 확인
docker compose logs monitor

# API 테스트
curl http://localhost:8080/api/health
```

---

## 🌟 주요 기능

### 실시간 모니터링
- ✅ 컨테이너 상태 및 헬스체크
- ✅ CPU, 메모리 사용률
- ✅ 데이터베이스 연결 및 통계
- ✅ 크롤링 성공/실패 통계

### 데이터 조회
- 📊 크롤링 완료율
- 🎓 최근 업데이트된 학교 목록
- 📝 실시간 로그 (50줄)
- 📧 수집된 연락처 정보

### 자동화
- 🔄 30초 자동 새로고침
- 🚨 에러 감지 (선택)
- 📱 API를 통한 외부 연동 가능

---

## 📊 API 엔드포인트

| 엔드포인트 | 설명 |
|-----------|------|
| `GET /` | 웹 대시보드 |
| `GET /api/status` | 전체 상태 (통합) |
| `GET /api/container` | 컨테이너 상태 |
| `GET /api/database` | DB 통계 |
| `GET /api/crawling/stats` | 크롤링 통계 |
| `GET /api/resources` | CPU/메모리 |
| `GET /api/logs/recent` | 최근 로그 |
| `GET /api/schools/recent` | 최근 학교 |
| `GET /api/health` | 헬스체크 |

---

## 🎨 대시보드 화면 구성

```
┌───────────────────────────────────────────────────────────┐
│  🕷️ College Crawler Monitor              [🔄 새로고침]    │
├───────────────────────────────────────────────────────────┤
│                                                            │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────┐ │
│  │ 컨테이너   │ │ 데이터베이스│ │  CPU 사용률│ │ 메모리 │ │
│  │ Running ✅ │ │   60 개    │ │   2.5%     │ │ 245MB  │ │
│  └────────────┘ └────────────┘ └────────────┘ └────────┘ │
│                                                            │
│  📊 크롤링 통계                                            │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│     성공: 23     실패: 2      성공률: 92%                 │
│  [████████████████████████████████████████░░░░] 92%       │
│                                                            │
│  🎓 최근 업데이트된 학교                                   │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  📍 Los Angeles Trade-Tech   📧 intl@lattc.edu           │
│  📍 Santa Monica College     📞 (310) 434-4000           │
│                                                            │
│  📝 최근 로그                                              │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │
│  [터미널 스타일 로그 출력]                                 │
└───────────────────────────────────────────────────────────┘
```

---

## 🔧 설정

### 포트 변경
기본 포트는 8080입니다. 변경하려면:

```yaml
# docker-compose.yml
services:
  monitor:
    ports:
      - "9090:8080"  # 원하는 포트로 변경
```

### 방화벽 설정
```bash
# 포트 8080 열기
sudo ufw allow 8080/tcp
```

### 보안 (선택)
기본 인증 추가 가능 (상세 가이드 참조)

---

## 📚 문서 가이드

### 시작하기
1. [⚡ 1분 빠른 시작](./MONITOR_QUICK_START.md) ← **여기서 시작!**
2. [📊 대시보드 상세 가이드](./MONITORING_DASHBOARD.md)

### CLI 모니터링
3. [⚡ CLI 빠른 모니터링](./QUICK_MONITORING.md)
4. [🔍 운영 서버 모니터링](./PRODUCTION_MONITORING.md)

---

## 🧪 테스트

### 로컬에서 테스트하기

```bash
# 1. 로컬 개발 환경 시작
docker compose -f docker-compose-local.yml up -d

# 2. 대시보드 접속
open http://localhost:8080

# 3. API 테스트
curl http://localhost:8080/api/status | jq '.'
```

### 운영 환경 배포 전 체크리스트

- [ ] `requirements.txt`에 패키지 추가 확인
- [ ] Docker 이미지 빌드 성공
- [ ] 로컬에서 대시보드 접속 확인
- [ ] API 엔드포인트 동작 확인
- [ ] 방화벽 포트 8080 개방
- [ ] GitHub에 코드 커밋 및 푸시

---

## 🚀 다음 단계

### 1. 즉시 실행
```bash
# 운영 서버 배포
docker compose up -d --build
```

### 2. 확인
```bash
# 대시보드 접속
http://서버IP:8080
```

### 3. 모니터링 자동화 (선택)
```bash
# Cron으로 정기 체크
crontab -e

# 매 5분마다 헬스체크
*/5 * * * * cd /media/ubuntu/data120g/college-crawler && ./scripts/health_monitor.sh >> /tmp/health.log 2>&1
```

---

## 💡 팁

### 외부에서 접속하기
```bash
# SSH 터널링 (로컬에서 테스트 시)
ssh -L 8080:localhost:8080 user@서버IP

# 브라우저에서
http://localhost:8080
```

### 모바일에서 확인
대시보드는 반응형이므로 모바일에서도 잘 보입니다!

### Slack 알림 연동
`scripts/watch_errors.sh`를 수정하여 Slack webhook 추가 가능

---

## ❓ 문제 해결

### 대시보드가 안 열려요
```bash
docker compose logs monitor
docker compose restart monitor
```

### 데이터가 안 나와요
```bash
# Docker 소켓 권한 확인
docker compose config | grep docker.sock
```

### 포트 충돌
다른 포트로 변경 후 재시작:
```bash
# docker-compose.yml에서 포트 변경
docker compose up -d --force-recreate monitor
```

---

## 📞 지원

- **문서**: `docs/` 폴더 참조
- **이슈**: GitHub Issues
- **이메일**: patrick@goalmond.com

---

## 🎉 완료!

모니터링 대시보드가 성공적으로 설치되었습니다!

**바로 시작하기**: [⚡ 1분 빠른 시작 가이드](./MONITOR_QUICK_START.md)

---

**설치 완료일**: 2026-02-10  
**버전**: 1.0.0  
**개발자**: Patrick
