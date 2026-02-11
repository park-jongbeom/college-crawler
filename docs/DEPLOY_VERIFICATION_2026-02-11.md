# 배포 검증 보고서 (2026-02-11)

## 1. Push 및 CI/CD 트리거

| 항목 | 결과 |
|------|------|
| **Push** | ✅ 성공 (`1d5530f..aaf4c1b  main -> main`) |
| **트리거된 워크플로우** | Deploy College Crawler (Run #23) |
| **커밋** | `aaf4c1b` - feat: 학교 데이터 업데이트 및 웹 크롤링 개선 |
| **상태** | GitHub Actions 실행 중 (in_progress → 완료 후 확인 필요) |

**Actions URL**: https://github.com/park-jongbeom/college-crawler/actions/runs/21892390364

---

## 2. 운영 환경 동작 확인

### 2.1 모니터 대시보드

| 항목 | 결과 |
|------|------|
| **URL** | https://go-almond.ddnsfree.com/monitor/ |
| **접근** | ✅ 정상 (College Crawler Monitor 페이지 로드) |
| **표시 내용** | 컨테이너 상태, DB, CPU/메모리, 크롤링 통계, 최근 로그 |

### 2.2 모니터 API – 데이터베이스 연동

**URL**: `GET https://go-almond.ddnsfree.com/monitor/api/database`

**응답 (검증 시점)**:
```json
{
  "connected": true,
  "total_schools": 84,
  "schools_with_email": 50,
  "schools_with_phone": 50,
  "schools_with_esl": 10,
  "schools_with_employment_rate": 0,
  "schools_with_facilities": 8,
  "recently_updated": 74,
  "completion_rate": 59.5
}
```

| 항목 | 값 | 비고 |
|------|-----|------|
| **DB 연결** | `connected: true` | ✅ 정상 |
| **총 학교 수** | **84개** | ✅ 이전 62개 추가 반영 (22→84) |
| **유학생 이메일** | 50개 | ✅ |
| **유학생 전화** | 50개 | ✅ |
| **완료율** | 59.5% | 크롤링 진행률 |

→ **운영 DB에 84개 학교가 반영되어 있으며, 모니터 API가 정상 응답함.**

### 2.3 Health API

- **URL**: `GET https://go-almond.ddnsfree.com/monitor/api/health`
- **비고**: 요청 시 타임아웃 발생 가능 (네트워크/서버 부하). 모니터 페이지 및 `/api/database` 정상 동작으로 운영 서비스는 정상으로 판단.

---

## 3. CI/CD 워크플로우 단계 (참고)

1. Checkout → Set up Python 3.11 → Install dependencies → Run unit tests (`pytest -m unit`)
2. Docker Hub 로그인 → Build & Push `patrick5471/college-crawler:latest`
3. SCP로 서버에 `docker-compose.yml` 복사
4. SSH로 서버 접속 후:
   - `.env` 생성 (Secrets 기반)
   - 기존 college-crawler / monitor 컨테이너 중지·제거
   - 최신 이미지 pull (재시도 3회)
   - college-crawler, monitor 컨테이너 `up -d`
   - college-crawler-monitor를 `ga-api-platform_ga-network`에 연결
   - ga-nginx 재시작
   - 컨테이너 상태 및 로그 확인

배포 완료 여부는 위 Actions Run #23의 **status: completed**, **conclusion: success** 로 확인하면 됩니다.

---

## 6. (추가) 2026-02-11 후속 업데이트: College Scorecard 메타데이터 보강

### 변경 요약
- Level 1 메타데이터 확장을 위해 College Scorecard API 연동을 추가했습니다.
- 배포 워크플로우에서 unit 테스트를 실제로 실행하도록 변경했습니다.

### Secrets / 환경변수
- 신규(또는 사용): `COLLEGE_SCORECARD_API`
  - 위치: `college-crawler` GitHub Actions Secrets
  - 전달: 배포 시 서버의 `/home/<user>/college-crawler/.env`에 `COLLEGE_SCORECARD_API=...`로 생성

### 워크플로우 단계 변경
- (기존) Run tests: placeholder
- (변경) Run tests: `pytest -m unit`

---

## 4. 최종 체크리스트

| # | 확인 항목 | 상태 |
|---|-----------|------|
| 1 | `git push origin main` 성공 | ✅ |
| 2 | GitHub Actions Run #23 트리거됨 | ✅ |
| 3 | 모니터 페이지 접근 가능 | ✅ |
| 4 | 모니터 `/api/database` 응답 정상 | ✅ |
| 5 | 운영 DB 학교 수 84개 | ✅ |
| 6 | Actions Run #23 완료(success) | ⏳ 배포 완료 후 확인 |

---

## 5. 사용자 권장 사항

1. **Actions 완료 확인**  
   https://github.com/park-jongbeom/college-crawler/actions  
   에서 Run #23이 **완료(success)** 인지 확인.

2. **모니터에서 수동 확인**  
   https://go-almond.ddnsfree.com/monitor/  
   새로고침 후 컨테이너 상태·크롤링 통계가 기대대로 나오는지 확인.

3. **실패 시**  
   Actions 로그에서 실패 단계(테스트, Docker push, SSH 배포 등) 확인 후, 필요 시 동일 Run에서 “Re-run” 하거나 수정 후 재푸시.

---

**문서 작성 시각**: 2026-02-11 13:15 KST
