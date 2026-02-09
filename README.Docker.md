# 🐳 Docker 사용 가이드

College Crawler를 Docker로 실행하는 방법을 안내합니다.

## 📋 목차

- [사전 요구사항](#사전-요구사항)
- [로컬 개발 환경](#로컬-개발-환경)
- [프로덕션 배포](#프로덕션-배포)
- [CI/CD 파이프라인](#cicd-파이프라인)
- [문제 해결](#문제-해결)

---

## 사전 요구사항

- Docker Engine 20.10+
- Docker Compose V2+

### Docker 설치 확인

```bash
docker --version
docker compose version
```

---

## 🛠️ 로컬 개발 환경

로컬에서 PostgreSQL과 함께 개발 환경을 실행합니다.

### 1. 환경 변수 설정

`.env.example`을 복사하여 `.env` 파일 생성:

```bash
cp .env.example .env
```

### 2. 로컬 환경 시작

```bash
# PostgreSQL + Crawler 컨테이너 시작
docker compose -f docker-compose-local.yml up -d

# 로그 확인
docker compose -f docker-compose-local.yml logs -f
```

### 3. 데이터베이스 마이그레이션

```bash
# Crawler 컨테이너에 접속
docker compose -f docker-compose-local.yml exec crawler-local bash

# 마이그레이션 실행
python -m alembic upgrade head

# 초기 데이터 삽입
python scripts/init_schools.py
```

### 4. 크롤링 실행

```bash
# 컨테이너 내부에서
python src/main.py crawl --limit 5

# 또는 호스트에서 직접 실행
docker compose -f docker-compose-local.yml exec crawler-local python src/main.py crawl --limit 5
```

### 5. 환경 종료

```bash
# 컨테이너 중지
docker compose -f docker-compose-local.yml down

# 볼륨까지 삭제 (데이터 초기화)
docker compose -f docker-compose-local.yml down -v
```

---

## 🚀 프로덕션 배포

### 1. Docker Hub에 이미지 빌드 및 푸시

```bash
# 이미지 빌드
docker build -t patrick5471/college-crawler:latest .

# Docker Hub 로그인
docker login

# 이미지 푸시
docker push patrick5471/college-crawler:latest
```

### 2. 서버에서 실행

서버에 `.env` 파일을 준비한 후:

```bash
# 최신 이미지 가져오기
docker compose pull

# 서비스 시작
docker compose up -d

# 로그 확인
docker compose logs -f college-crawler

# 상태 확인
docker compose ps
```

### 3. 서비스 관리

```bash
# 서비스 재시작
docker compose restart college-crawler

# 서비스 중지
docker compose stop college-crawler

# 컨테이너 재생성
docker compose up -d --force-recreate college-crawler
```

---

## 🔄 CI/CD 파이프라인

### GitHub Actions 자동 배포

`main` 브랜치에 푸시하면 자동으로 빌드 및 배포됩니다.

#### 배포 프로세스

1. **코드 체크아웃**
2. **Python 3.11 설정 및 의존성 설치**
3. **테스트 실행** (선택)
4. **Docker 이미지 빌드**
5. **Docker Hub에 푸시**
6. **서버에 docker-compose.yml 복사**
7. **SSH로 서버 접속하여 배포**

#### 필요한 GitHub Secrets

GitHub 저장소 Settings → Secrets and variables → Actions에 추가:

| Secret 이름 | 설명 | 예시 |
|------------|------|------|
| `DOCKER_USERNAME` | Docker Hub 사용자명 | `patrick5471` |
| `DOCKER_PASSWORD` | Docker Hub 액세스 토큰 | `dckr_pat_...` |
| `SERVER_HOST` | 배포 서버 IP/도메인 | `123.456.789.0` |
| `SERVER_USER` | 서버 SSH 사용자명 | `ubuntu` |
| `SERVER_SSH_KEY` | 서버 SSH 개인키 | `-----BEGIN RSA...` |

#### 배포 트리거

다음 파일이 변경되면 자동 배포:
- `src/**`
- `scripts/**`
- `requirements.txt`
- `Dockerfile`
- `docker-compose.yml`
- `alembic.ini`

### 수동 배포

GitHub Actions 페이지에서 "Run workflow" 버튼으로 수동 실행 가능.

---

## 🔍 문제 해결

### 컨테이너가 시작되지 않음

```bash
# 상세 로그 확인
docker compose logs college-crawler

# 컨테이너 상태 확인
docker compose ps -a

# 이벤트 로그 확인
docker events
```

### 데이터베이스 연결 실패

1. `.env` 파일의 데이터베이스 설정 확인
2. 네트워크 연결 확인:
   ```bash
   docker compose exec college-crawler ping -c 3 <DATABASE_HOST>
   ```

### 이미지 빌드 실패

```bash
# 캐시 없이 빌드
docker build --no-cache -t patrick5471/college-crawler:latest .

# 빌드 로그 상세 출력
docker build --progress=plain -t patrick5471/college-crawler:latest .
```

### 볼륨 권한 문제

```bash
# 볼륨 소유자 확인
docker compose exec college-crawler ls -la /app/data

# 권한 수정 (필요시)
docker compose exec -u root college-crawler chown -R crawler:crawler /app/data
```

### 메모리 부족

`docker-compose.yml`에 리소스 제한 추가:

```yaml
services:
  college-crawler:
    # ... 기존 설정 ...
    deploy:
      resources:
        limits:
          memory: 1G
        reservations:
          memory: 512M
```

---

## 📚 추가 자료

- [Docker 공식 문서](https://docs.docker.com/)
- [Docker Compose 문서](https://docs.docker.com/compose/)
- [GitHub Actions 문서](https://docs.github.com/en/actions)

---

## 🆘 지원

문제가 발생하면 GitHub Issues에 등록해주세요:
https://github.com/park-jongbeom/college-crawler/issues
