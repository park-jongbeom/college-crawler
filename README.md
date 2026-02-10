# College Crawler

미국 대학 정보 자동 수집 및 이메일 발송 시스템

## 프로젝트 개요

미국 Community College 60개교의 상세 정보를 자동으로 수집하고, 유학사업에 필요한 정보를 관리하는 시스템입니다.

### 주요 기능

- **학교 정보 크롤링**: 웹사이트에서 자동으로 학교 정보 수집
- **데이터 관리**: PostgreSQL 데이터베이스에 구조화된 데이터 저장
- **이메일 자동화**: 학교 담당자에게 자동 이메일 발송 (Phase 3)

### 수집 정보

- 유학생 담당자 연락처 (이메일, 전화)
- 학교 시설 (기숙사, 식당, 체육관, 엔터테인먼트)
- 스텝 현황 (교수진, 직원 수)
- 유학생 지원 방법
- ESL 프로그램 정보
- 취업률
- 학교 환경 및 역사

## 기술 스택

- **언어**: Python 3.11+
- **데이터베이스**: PostgreSQL 17 (기존 ga-api-platform DB 활용)
- **웹 크롤링**: BeautifulSoup4, Requests, Selenium, Scrapy
- **ORM**: SQLAlchemy + Alembic
- **스케줄링**: APScheduler
- **템플릿**: Jinja2

## 설치 및 설정

### 1. 가상환경 생성 및 활성화

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일 생성 후 실제 값 입력:

```bash
cp .env.example .env
```

### 4. 데이터베이스 마이그레이션

```bash
# Alembic 초기화 (이미 완료됨)
# alembic init src/database/migrations

# 마이그레이션 실행
alembic upgrade head
```

### 5. 초기 데이터 삽입

```bash
python scripts/init_schools.py
```

## 사용법

### 학교 정보 크롤링

```bash
python src/main.py crawl
```

### 특정 학교만 크롤링

```bash
python src/main.py crawl --school "Los Angeles Trade-Technical College"
```

### 데이터베이스 확인

```bash
python scripts/check_db.py
```

## 🐳 Docker로 실행하기

Docker를 사용하면 환경 설정 없이 바로 실행할 수 있습니다.

### 로컬 개발 환경 (소스 빌드, 핫 리로드)

로컬에서 개발할 때는 `docker-compose.local.yml`을 사용합니다:

```bash
# 환경 시작 (소스 코드가 마운트되어 핫 리로드 지원)
docker-compose -f docker-compose.local.yml up -d

# 로그 확인
docker-compose -f docker-compose.local.yml logs -f

# 크롤링 실행
docker-compose -f docker-compose.local.yml exec college-crawler-local python src/main.py crawl --limit 5

# 환경 종료
docker-compose -f docker-compose.local.yml down
```

### 프로덕션 배포 (자동화)

**운영 서버 배포는 GitHub Actions가 자동으로 처리합니다:**

1. `main` 브랜치에 푸시
2. GitHub Actions가 자동으로:
   - Docker 이미지 빌드 (`patrick5471/college-crawler:latest`)
   - Docker Hub에 푸시
   - 서버에 `.env` 파일 생성 (GitHub Secrets 사용)
   - `college-crawler`와 `monitor` 서비스 배포
   - `ga-api-platform` 네트워크에 연결
   - `ga-nginx` 재시작

**필요한 GitHub Secrets:**
- `DOCKER_USERNAME`, `DOCKER_PASSWORD` - Docker Hub 인증
- `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY` - 서버 접근
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` - DB 연결
- `DATABASE_USER`, `DATABASE_PASSWORD` - DB 인증

**수동 배포 (필요 시):**

```bash
# 서버에서 실행 (.env는 GitHub Actions가 생성)
cd ~/college-crawler
docker-compose up -d
```

**상세 가이드**: [README.Docker.md](README.Docker.md)

## 🔄 CI/CD

GitHub Actions를 통한 자동 배포가 구성되어 있습니다.

`main` 브랜치에 푸시하면:
1. ✅ Python 의존성 설치 및 테스트
2. 🐳 Docker 이미지 빌드
3. 📤 Docker Hub에 푸시 (`patrick5471/college-crawler:latest`)
4. 📝 서버에 `.env` 파일 자동 생성 (GitHub Secrets에서)
5. 🚀 `college-crawler`와 `monitor` 서비스 배포
6. 🔗 `college-crawler-monitor`를 `ga-api-platform_ga-network`에 연결
7. ♻️ `ga-nginx` 재시작하여 `/monitor/` 경로 활성화

**필요한 GitHub Secrets**:
- `DOCKER_USERNAME`, `DOCKER_PASSWORD` - Docker Hub 인증
- `SERVER_HOST`, `SERVER_USER`, `SERVER_SSH_KEY` - 서버 SSH 접근
- `DATABASE_HOST`, `DATABASE_PORT`, `DATABASE_NAME` - PostgreSQL 연결 정보
- `DATABASE_USER`, `DATABASE_PASSWORD` - PostgreSQL 인증

## 📊 운영 모니터링

### 🌐 웹 대시보드 (NEW!)

실시간 모니터링 웹 대시보드를 제공합니다:

```bash
# 서비스 시작
docker compose up -d

# 브라우저에서 접속
http://서버IP:8080
```

**주요 기능:**
- ✅ 실시간 상태 모니터링 (컨테이너, DB, 리소스)
- 📊 크롤링 통계 및 성공률
- 📝 실시간 로그 확인
- 🎓 최근 업데이트된 학교 목록
- 🔄 자동 새로고침 (30초)

**상세 가이드**: [📊 모니터링 대시보드](docs/MONITORING_DASHBOARD.md)

### 🖥️ CLI 모니터링

```bash
# 종합 모니터링 (한 번에 모든 상태 확인)
./scripts/monitor.sh

# 헬스체크
./scripts/health_monitor.sh

# 실시간 로그
docker compose logs -f college-crawler
```

### 주요 확인 항목

- **컨테이너 상태**: `docker ps | grep college-crawler`
- **데이터베이스**: `docker exec college-crawler python scripts/check_db.py`
- **크롤링 결과**: `docker exec college-crawler ls /app/data/crawled/`
- **에러 로그**: `docker compose logs college-crawler | grep -i error`

**상세 가이드**:
- [📊 모니터링 웹 대시보드](docs/MONITORING_DASHBOARD.md) - 웹 기반 실시간 모니터링
- [⚡ 빠른 모니터링 가이드](docs/QUICK_MONITORING.md) - 3분 안에 전체 상태 확인
- [🔍 운영 서버 모니터링](docs/PRODUCTION_MONITORING.md) - 상세 모니터링 방법

## 프로젝트 구조

```
college-crawler/
├── src/
│   ├── collectors/          # 학교 리스트 수집
│   ├── crawlers/           # 웹 크롤링
│   │   └── parsers/        # 데이터 파싱
│   ├── database/           # DB 연동
│   │   ├── models.py       # SQLAlchemy 모델
│   │   ├── repository.py   # CRUD 작업
│   │   └── migrations/     # Alembic 마이그레이션
│   ├── email/              # 이메일 발송 (Phase 3)
│   └── utils/              # 유틸리티
├── scripts/                # 유틸리티 스크립트
├── data/                   # 데이터 파일
├── tests/                  # 테스트
└── docs/                   # 문서
```

## 개발 가이드

### Cursor 규칙

이 프로젝트는 `.cursorrules` 파일에 정의된 개발 정책을 따릅니다:

- 모든 코드, 주석, 문서는 한국어로 작성
- 보안 체크리스트 준수
- 테스트 코드 필수 작성
- 철저한 로깅 및 에러 처리

### 테스트 실행

```bash
pytest tests/
```

## 로드맵

### Phase 1: 프로젝트 기반 구축 (완료)
- [x] 프로젝트 구조 생성
- [x] DB 마이그레이션
- [x] 초기 학교 데이터 삽입

### Phase 2: 웹 크롤링 시스템 (진행 중)
- [ ] Base Crawler 구현
- [ ] 학교 정보 파서 구현
- [ ] 크롤링 스케줄러

### Phase 3: 이메일 시스템 (예정)
- [ ] 이메일 템플릿
- [ ] SMTP 발송 시스템
- [ ] 캠페인 관리

## 라이선스

Copyright (c) 2026 Go Almond

## 참고 문서

- [개발 정책](docs/00_DEVELOPMENT_POLICY.md)
- [데이터베이스 스키마](docs/DATABASE_SCHEMA.md)
