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
