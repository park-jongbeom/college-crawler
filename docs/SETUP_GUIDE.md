# 🚀 College Crawler SSH 원격 구성 가이드

Windows PC(C:\Users\qk54r\college-crawler)에서 Cursor로 원격 서버에 SSH 연결하는 방법

## ✅ 완료된 작업

원격 서버(`3.37.222.156`)에 다음이 준비되었습니다:

```
/media/ubuntu/data120g/college-crawler/
├── .cursorrules              # Cursor AI 규칙 (Python 크롤링 전문)
├── .vscode/
│   ├── settings.json        # Python 환경 + SSH 설정
│   └── extensions.json      # 추천 확장 프로그램
├── .gitignore               # Python 프로젝트용
├── .env.example             # 환경변수 템플릿
├── README.md                # 프로젝트 문서
├── requirements.txt         # Python 의존성
├── main.py                  # 진입점
├── crawlers/                # 크롤러 모듈
│   ├── base.py             # 베이스 클래스
│   └── schools/            # 사이트별 크롤러
├── config/                  # 설정
│   └── settings.py
├── processors/              # 데이터 처리
├── models/                  # 데이터 모델
├── utils/                   # 유틸리티
├── tests/                   # 테스트
└── logs/                    # 로그
```

## 📋 Windows PC에서 수행할 작업

### 1️⃣ 로컬 코드를 Git에 푸시 (선택사항)

로컬에 이미 작업 중인 코드가 있다면:

```bash
# Windows PowerShell 또는 CMD에서
cd C:\Users\qk54r\college-crawler

# Git 저장소가 없다면 초기화
git init
git branch -m main

# 원격 저장소 연결 (GitHub, GitLab 등)
git remote add origin https://github.com/your-username/college-crawler.git

# 커밋 및 푸시
git add .
git commit -m "feat: 기존 작업 내용 커밋"
git push -u origin main
```

### 2️⃣ 원격 서버에서 코드 가져오기

SSH로 원격 서버 접속:

```bash
ssh ubuntu@3.37.222.156 -i C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem
```

원격 서버에서:

```bash
cd /media/ubuntu/data120g/college-crawler

# Git 저장소에서 코드 가져오기
git remote add origin https://github.com/your-username/college-crawler.git
git pull origin main

# 또는 기존 파일 유지하고 병합
git fetch origin
git merge origin/main --allow-unrelated-histories
```

### 3️⃣ Cursor에서 SSH 연결

#### 방법 A: Cursor의 Remote SSH 기능 사용

1. **Cursor 실행**
2. **F1** 또는 **Ctrl+Shift+P** → `Remote-SSH: Connect to Host...`
3. **SSH 호스트 추가**:
   ```
   Host ga-api-crawler
       HostName 3.37.222.156
       User ubuntu
       IdentityFile C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem
   ```
4. **연결 후 폴더 열기**: `/media/ubuntu/data120g/college-crawler`

#### 방법 B: SSH Config 파일 직접 편집

`C:\Users\qk54r\.ssh\config` 파일 생성/편집:

```ssh-config
# GA API Platform
Host ga-api-platform
    HostName 3.37.222.156
    User ubuntu
    IdentityFile C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3

# College Crawler
Host college-crawler
    HostName 3.37.222.156
    User ubuntu
    IdentityFile C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem
    ServerAliveInterval 60
    ServerAliveCountMax 3
```

Cursor에서:
- **F1** → `Remote-SSH: Connect to Host...`
- **college-crawler** 선택
- 폴더 열기: `/media/ubuntu/data120g/college-crawler`

### 4️⃣ Python 가상환경 설정

원격 서버의 college-crawler 폴더에서:

```bash
# Python 가상환경 생성
python3 -m venv .venv

# 활성화
source .venv/bin/activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# Playwright 설치 (필요 시)
playwright install
```

### 5️⃣ 환경변수 설정

`.env` 파일 생성:

```bash
cp .env.example .env
nano .env  # 또는 vim .env
```

`.env` 내용:

```env
# Database Configuration
DB_HOST=ls-584229d62cccd625a5fa723267dbdbc614b3b0e5.c9wi0gwweu9n.ap-northeast-2.rds.amazonaws.com
DB_PORT=5432
DB_NAME=ga_db
DB_USER=dbmasteruser
DB_PASSWORD=w,*i.uAk7f^Gj;Gk`3O`oqZx3`0fj9Vm

# Crawler Settings
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
REQUEST_DELAY=2
MAX_RETRIES=3
TIMEOUT=30
CONCURRENT_REQUESTS=5

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/crawler.log

# Development
DEBUG=False
```

### 6️⃣ 테스트 실행

```bash
# 가상환경 활성화 확인
source .venv/bin/activate

# 메인 스크립트 실행
python main.py

# 기대 출력:
# 🕷️ College Crawler 시작
# 크롤러 준비 완료. 구현 대기 중...
# ✅ College Crawler 종료
```

## 🎯 Cursor에서 작업 시작

1. **Cursor로 SSH 연결된 college-crawler 폴더 열기**
2. **Cursor AI가 자동으로 `.cursorrules` 인식**
3. **Python 인터프리터 선택**: `.venv/bin/python`
4. **작업 시작**:
   ```
   "GS샵 홈페이지에서 상품 정보를 크롤링하는 크롤러를 만들어줘"
   ```

## 🔧 유용한 Cursor 설정

이미 `.vscode/settings.json`에 포함된 설정:

- ✅ Python 자동 포맷팅 (Black)
- ✅ Import 자동 정렬 (isort)
- ✅ 타입 체크 (Pylance)
- ✅ Pytest 통합
- ✅ PostgreSQL 연결 설정

## 📚 추천 Cursor 확장 프로그램

자동으로 추천되는 확장 (`.vscode/extensions.json`):

- **Python**: ms-python.python
- **Pylance**: ms-python.vscode-pylance
- **Black Formatter**: ms-python.black-formatter
- **SQL Tools**: mtxr.sqltools
- **GitLens**: eamodio.gitlens

## 🐛 문제 해결

### SSH 연결 실패

```bash
# PEM 파일 권한 확인 (Windows에서)
icacls C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem /inheritance:r
icacls C:\Users\qk54r\IdeaProjects\ssh\LightsailDefaultKey-ap-northeast-2.pem /grant:r "%USERNAME%:R"
```

### Python 인터프리터 인식 안 됨

Cursor에서:
- **Ctrl+Shift+P** → `Python: Select Interpreter`
- `.venv/bin/python` 선택

### 의존성 설치 오류

```bash
# 시스템 패키지 업데이트 (Ubuntu)
sudo apt update
sudo apt install python3-dev build-essential libpq-dev
```

## 📊 두 프로젝트 비교

| 항목 | ga-api-platform | college-crawler |
|------|-----------------|-----------------|
| 언어 | Kotlin + Spring Boot | Python |
| 목적 | API 서버 | 웹 크롤링 |
| 경로 | /media/ubuntu/data120g/ga-api-platform | /media/ubuntu/data120g/college-crawler |
| DB | PostgreSQL (같은 DB) | PostgreSQL (같은 DB) |
| Cursor 규칙 | Spring Boot/Kotlin | Python 크롤링 |

## ✅ 완료 체크리스트

- [ ] Windows에서 로컬 코드를 Git에 푸시 (선택)
- [ ] 원격 서버에서 코드 가져오기
- [ ] Cursor SSH 연결 설정
- [ ] Python 가상환경 생성 및 의존성 설치
- [ ] `.env` 파일 생성
- [ ] `python main.py` 실행 성공
- [ ] Cursor에서 college-crawler 폴더 열기
- [ ] Cursor AI 작동 확인

## 🎉 다음 단계

이제 Cursor에서 다음과 같이 작업할 수 있습니다:

```
"12개 홈쇼핑 사이트를 크롤링하는 시스템을 설계해줘"
"GS샵 크롤러를 구현해줘"
"수집한 데이터를 PostgreSQL에 저장하는 로직 만들어줘"
```

Cursor가 `.cursorrules`를 인식하고 Python 크롤링 전문가로 동작합니다! 🚀
