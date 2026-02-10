# 🕷️ College Crawler

미국 대학 정보 수집을 위한 웹 크롤링 프로젝트

## 📋 프로젝트 개요

다수의 대학 웹사이트에서 학교 정보, 프로그램, 입학 요건 등을 자동으로 수집하는 크롤러입니다.

## 🛠️ 기술 스택

- **Python**: 3.10+
- **크롤링**: BeautifulSoup4, Selenium, Playwright
- **데이터 처리**: pandas, numpy
- **데이터베이스**: PostgreSQL (SQLAlchemy)
- **비동기**: asyncio, aiohttp
- **스케줄링**: APScheduler

## 📁 프로젝트 구조

```
college-crawler/
├── crawlers/              # 크롤러 모듈
│   ├── base.py           # 베이스 크롤러
│   └── schools/          # 학교별 크롤러
├── processors/            # 데이터 처리
│   ├── normalizer.py     # 데이터 정규화
│   └── validator.py      # 데이터 검증
├── models/                # 데이터 모델
│   └── school.py
├── utils/                 # 유틸리티
│   ├── logger.py
│   └── db.py
├── config/                # 설정
│   └── settings.py
├── tests/                 # 테스트
├── docs/                  # 문서
├── requirements.txt       # 의존성
└── main.py               # 진입점
```

## 🚀 시작하기

### 1. 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env` 파일 생성:

```env
# Database
DB_HOST=ls-584229d62cccd625a5fa723267dbdbc614b3b0e5.c9wi0gwweu9n.ap-northeast-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ga_db
DB_USER=dbmasteruser
DB_PASSWORD=your_password

# Crawler Settings
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
REQUEST_DELAY=2
MAX_RETRIES=3
TIMEOUT=30
```

### 4. 실행

```bash
python main.py
```

## 📝 개발 가이드

### 새로운 크롤러 추가

```python
from crawlers.base import BaseCrawler

class NewSchoolCrawler(BaseCrawler):
    def __init__(self):
        super().__init__(base_url="https://example.edu")
    
    def parse(self, html: str) -> dict:
        # 파싱 로직 구현
        pass
```

### 테스트 실행

```bash
pytest tests/
pytest tests/ -v  # 상세 출력
pytest tests/ --cov=crawlers  # 커버리지
```

## 🔒 윤리 및 법적 준수

- ✅ robots.txt 확인
- ✅ 이용약관 검토
- ✅ Rate Limiting 적용
- ✅ User-Agent 명시
- ✅ 서버 부하 최소화

## 📊 데이터베이스 스키마

연결: `ga_db` PostgreSQL 데이터베이스
- `schools`: 학교 마스터 데이터
- `programs`: 프로그램 정보
- `school_documents`: 학교 문서 (RAG)
- `program_documents`: 프로그램 문서 (RAG)

## 🐛 문제 해결

### Selenium 드라이버 설치

```bash
# Chrome
pip install webdriver-manager
```

### Playwright 설치

```bash
playwright install
```

## 📚 참고 문서

- [BeautifulSoup4 문서](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Selenium 문서](https://www.selenium.dev/documentation/)
- [Playwright 문서](https://playwright.dev/python/)

## 👥 기여

1. Fork the Project
2. Create your Feature Branch
3. Commit your Changes
4. Push to the Branch
5. Open a Pull Request

## 📄 라이선스

Private Project
