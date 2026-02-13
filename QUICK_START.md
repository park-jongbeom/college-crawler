# 🚀 Quick Start Guide

## 프로젝트 열기

Cursor에서 이 프로젝트를 열었다면, 다음 단계를 따라주세요.

## ✅ 현재 상태

- ✅ 프로젝트 구조 완성
- ✅ 웹 크롤러 구현 완료
- ✅ 데이터베이스 모델 및 마이그레이션 준비
- ✅ 20개 학교 초기 데이터 준비
- ⏳ Python 패키지 설치 필요

---

## 📦 Step 1: 패키지 설치

**PowerShell에서 실행:**

```powershell
cd C:\Users\qk54r\college-crawler
pip install sqlalchemy alembic python-dotenv beautifulsoup4 requests lxml
```

**또는 한 번에:**

```powershell
pip install -r requirements.txt
```

---

## 🗄️ Step 2: 데이터베이스 설정

### 2-1. 마이그레이션 실행

```powershell
alembic upgrade head
```

이 명령은 기존 `schools` 테이블에 다음 컬럼을 추가합니다:
- `international_email` - 유학생 담당자 이메일
- `international_phone` - 유학생 담당자 전화
- `employment_rate` - 취업률
- `facilities` - 시설 정보 (JSONB)
- `staff_info` - 스텝 현황 (JSONB)
- `esl_program` - ESL 프로그램 (JSONB)
- `international_support` - 유학생 지원 (JSONB)

### 2-2. 초기 학교 데이터 삽입

```powershell
python scripts\init_schools.py
```

20개 학교 데이터가 DB에 삽입됩니다.

### 2-3. 데이터베이스 확인

```powershell
python scripts\check_db.py
```

---

## 🕷️ Step 3: 웹 크롤링 테스트

### 3-1. 단일 학교 테스트

```powershell
python scripts\test_crawler.py
```

Los Angeles Trade-Technical College와 Santa Monica College를 크롤링합니다.

### 3-2. 처음 5개 학교 크롤링

```powershell
python src\main.py crawl --limit 5
```

### 3-3. 전체 크롤링

```powershell
python src\main.py crawl
```

### 3-4. 특정 학교만

```powershell
python src\main.py crawl --school "Santa Monica College" --website "https://smc.edu"
```

---

## 📁 크롤링 결과

크롤링 결과는 `data/crawled/` 폴더에 JSON 파일로 저장됩니다.

**예시:** `data/crawled/Los_Angeles_Trade-Technical_College.json`

```json
{
  "name": "Los Angeles Trade-Technical College",
  "website": "https://lattc.edu",
  "crawled_data": {
    "international_email": "iso@lattc.edu",
    "international_phone": "+1-213-763-7170",
    "esl_program": {
      "available": true,
      "description": "..."
    },
    "facilities": {
      "dormitory": true,
      "dining": true,
      "gym": true
    }
  }
}
```

---

## 🔍 로그 확인

로그 파일: `logs/app.log`

```powershell
Get-Content logs\app.log -Tail 50
```

---

## 📚 다음 단계 (Phase 3 - 보류)

> **참고**: 현재 GraphRAG 기능 개발에 집중하기 위해 아래 기능 구현은 잠정 보류합니다.

1. **이메일 자동 발송 시스템**
   - SMTP 설정
   - 이메일 템플릿 작성
   - 대량 발송 시스템

2. **스케줄링**
   - APScheduler 설정
   - 주기적 크롤링 자동화

---

## ⚠️ 문제 해결

### 패키지 설치 오류

```powershell
pip install --upgrade pip
pip install -r requirements.txt --user
```

### DB 연결 오류

`.env` 파일의 데이터베이스 연결 정보를 확인하세요.

```env
DATABASE_HOST=ls-584229d62cccd625a5fa723267dbdbc614b3b0e5.c9wi0gwweu9n.ap-northeast-2.rds.amazonaws.com
DATABASE_PORT=5432
DATABASE_NAME=ga_db
DATABASE_USER=dbmasteruser
DATABASE_PASSWORD=...
```

### 크롤링 타임아웃

`.env`에서 타임아웃 설정 조정:

```env
CRAWL_TIMEOUT=60
CRAWL_DELAY=3
```

---

## 📞 도움말

- README.md - 전체 프로젝트 문서
- docs/00_DEVELOPMENT_POLICY.md - 개발 정책
- docs/DATABASE_SCHEMA.md - DB 스키마

---

## ✨ 현재 구현된 기능

✅ 웹 크롤러 (robots.txt 준수, Rate limiting, 재시도)
✅ 연락처 파서 (이메일, 전화)
✅ 시설 정보 파서
✅ ESL/프로그램 파서
✅ 유학생 지원 정보 파서
✅ JSON 결과 저장
✅ 데이터베이스 연동
✅ 로깅 시스템

⏳ 이메일 발송 (Phase 3)
⏳ 스케줄링 (Phase 3)
