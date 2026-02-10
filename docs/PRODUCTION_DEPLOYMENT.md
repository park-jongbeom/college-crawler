# 🚀 운영 서버 배포 가이드

College Crawler 모니터링 대시보드를 운영 서버에 배포하는 방법입니다.

---

## 📊 현재 포트 사용 현황

### 분석 결과
```
ga-matching-api:        포트 8080 ✅
college-crawler-monitor: 포트 8081 ✅
```

**결론**: ✅ **포트 충돌 없음 - 문제 없습니다!**

### 상세 현황
```bash
# ga-matching-api (기존)
0.0.0.0:8080 -> 컨테이너 내부 8080
서비스: Spring Boot API
상태: Up 11 days (healthy)

# college-crawler-monitor (신규)
0.0.0.0:8081 -> 컨테이너 내부 8080
서비스: FastAPI Monitor
상태: Up (healthy)
```

**포트 전략**:
- 각 서비스가 다른 외부 포트 사용 (8080 vs 8081)
- 컨테이너 내부는 각각 표준 포트 사용
- 충돌 없이 독립 운영 가능 ✅

---

## 🌐 운영 서버 접근 방법

### 현재 서버 정보
```
내부 IP: 192.168.0.94
방화벽: 비활성 (UFW inactive)
```

### 1. 직접 접근 (빠른 방법)

#### 옵션 A: 포트 직접 노출
```bash
# 브라우저에서 직접 접근
http://서버_외부_IP:8081

# 예시 (외부 IP가 13.125.123.45인 경우)
http://13.125.123.45:8081
```

**장점**:
- 설정 간단
- 즉시 사용 가능

**단점**:
- 비표준 포트 노출
- SSL/HTTPS 없음
- 보안 취약

#### 옵션 B: SSH 터널링 (보안 강화)
```bash
# 로컬 PC에서 실행
ssh -L 8081:localhost:8081 user@서버_IP

# 브라우저에서 접근
http://localhost:8081
```

**장점**:
- 보안 강화
- 포트 노출 불필요

**단점**:
- 매번 SSH 연결 필요

---

### 2. 프로덕션 권장 방법: nginx 리버스 프록시

#### 장점
- ✅ 표준 포트 (80/443) 사용
- ✅ SSL/HTTPS 적용 가능
- ✅ 도메인 기반 접근
- ✅ 보안 강화
- ✅ 로드 밸런싱 가능

#### 설정 방법

##### Step 1: nginx 설치
```bash
sudo apt update
sudo apt install nginx -y
```

##### Step 2: 설정 파일 생성
```bash
sudo nano /etc/nginx/sites-available/crawler-monitor
```

**설정 내용 (HTTP)**:
```nginx
# /etc/nginx/sites-available/crawler-monitor
server {
    listen 80;
    server_name monitor.yourcompany.com;  # 또는 IP 주소
    
    # 모니터링 대시보드
    location / {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 타임아웃 설정
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 기존 API (선택 사항)
    location /api/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**설정 내용 (HTTPS - 권장)**:
```nginx
# HTTP를 HTTPS로 리다이렉트
server {
    listen 80;
    server_name monitor.yourcompany.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 설정
server {
    listen 443 ssl http2;
    server_name monitor.yourcompany.com;
    
    # SSL 인증서 (Let's Encrypt 권장)
    ssl_certificate /etc/letsencrypt/live/monitor.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/monitor.yourcompany.com/privkey.pem;
    
    # SSL 보안 설정
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 보안 헤더
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 모니터링 대시보드
    location / {
        proxy_pass http://localhost:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

##### Step 3: 설정 활성화
```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/crawler-monitor /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# nginx 재시작
sudo systemctl restart nginx
```

##### Step 4: SSL 인증서 설정 (Let's Encrypt)
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# SSL 인증서 발급
sudo certbot --nginx -d monitor.yourcompany.com

# 자동 갱신 설정 확인
sudo certbot renew --dry-run
```

##### Step 5: 접근
```bash
# HTTP (자동으로 HTTPS로 리다이렉트)
http://monitor.yourcompany.com

# HTTPS (권장)
https://monitor.yourcompany.com
```

---

### 3. 방화벽 설정

#### UFW 사용 시
```bash
# 방화벽 활성화
sudo ufw enable

# HTTP/HTTPS 허용 (nginx 사용 시)
sudo ufw allow 'Nginx Full'

# 또는 직접 포트 허용
sudo ufw allow 8081/tcp  # 직접 접근 시
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# SSH 포트 보안 설정
sudo ufw allow 22/tcp

# 상태 확인
sudo ufw status
```

#### iptables 사용 시
```bash
# 포트 8081 허용
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT

# HTTP/HTTPS 허용
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 설정 저장
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

---

## 🔒 보안 권장 사항

### 1. 기본 인증 추가 (nginx)

**nginx 설정에 추가**:
```nginx
location / {
    # 기본 인증
    auth_basic "Monitoring Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    
    proxy_pass http://localhost:8081;
    # ... 나머지 설정
}
```

**비밀번호 파일 생성**:
```bash
# htpasswd 설치
sudo apt install apache2-utils -y

# 사용자 추가
sudo htpasswd -c /etc/nginx/.htpasswd admin

# 추가 사용자 (기존 파일에 추가)
sudo htpasswd /etc/nginx/.htpasswd user2

# nginx 재시작
sudo systemctl restart nginx
```

### 2. IP 화이트리스트

**특정 IP만 허용**:
```nginx
location / {
    # 허용할 IP
    allow 1.2.3.4;      # 회사 IP
    allow 5.6.7.8;      # VPN IP
    deny all;           # 나머지 차단
    
    proxy_pass http://localhost:8081;
}
```

### 3. Rate Limiting

**과도한 요청 방지**:
```nginx
# nginx.conf에 추가
http {
    limit_req_zone $binary_remote_addr zone=monitor:10m rate=10r/s;
}

# 서버 블록에 추가
location / {
    limit_req zone=monitor burst=20;
    proxy_pass http://localhost:8081;
}
```

---

## 📋 배포 체크리스트

### 배포 전
- [ ] 포트 충돌 확인 (8080 vs 8081) ✅
- [ ] Docker 이미지 빌드 완료
- [ ] .env 파일 설정 완료
- [ ] 데이터베이스 연결 테스트

### 배포 중
- [ ] `docker compose up -d` 실행
- [ ] 컨테이너 상태 확인 (`docker ps`)
- [ ] 로그 확인 (`docker compose logs`)
- [ ] API 테스트 (`curl localhost:8081/api/health`)

### 배포 후
- [ ] 외부 접근 테스트
- [ ] nginx 설정 (선택)
- [ ] SSL 인증서 설정 (선택)
- [ ] 방화벽 설정
- [ ] 모니터링 설정
- [ ] 백업 설정

---

## 🌐 접근 방법 요약

### 개발/테스트 환경
```bash
# 로컬
http://localhost:8081

# 내부 네트워크
http://192.168.0.94:8081
```

### 운영 환경

#### 방법 1: 직접 접근 (빠르지만 비권장)
```bash
http://외부_IP:8081
```

#### 방법 2: nginx + 도메인 (권장)
```bash
# HTTP
http://monitor.yourcompany.com

# HTTPS (강력 권장)
https://monitor.yourcompany.com
```

#### 방법 3: 서브도메인
```bash
# 메인 도메인의 서브도메인
https://monitor.goalmond.com
https://crawler.goalmond.com
```

---

## 🎯 권장 아키텍처

### 현재 구조
```
인터넷
  │
  ├─ :8080 → ga-matching-api (Spring Boot)
  └─ :8081 → crawler-monitor (FastAPI)
```

### 권장 구조 (nginx 적용)
```
인터넷
  │
  └─ :443 (HTTPS)
      │
      └─ nginx
          │
          ├─ api.goalmond.com → :8080 (ga-matching-api)
          └─ monitor.goalmond.com → :8081 (crawler-monitor)
```

### 이점
- ✅ 표준 포트 (443) 사용
- ✅ SSL/HTTPS 암호화
- ✅ 도메인 기반 라우팅
- ✅ 보안 강화
- ✅ 로드 밸런싱 가능

---

## 🔧 트러블슈팅

### 포트 접근 안 됨
```bash
# 1. 컨테이너 확인
docker ps | grep monitor

# 2. 방화벽 확인
sudo ufw status

# 3. 포트 리스닝 확인
netstat -tuln | grep 8081

# 4. 로그 확인
docker compose logs monitor
```

### nginx 502 Bad Gateway
```bash
# 1. 백엔드 서비스 확인
curl http://localhost:8081/api/health

# 2. nginx 에러 로그
sudo tail -f /var/log/nginx/error.log

# 3. SELinux 확인 (CentOS/RHEL)
sudo setsebool -P httpd_can_network_connect 1
```

---

## 📞 실제 운영 서버 접근 URL

### 현재 설정 (포트 8081 직접 노출)
```bash
# 개발 서버 (내부)
http://192.168.0.94:8081

# 운영 서버 (외부 IP 필요)
http://YOUR_PUBLIC_IP:8081
```

### 외부 IP 확인 방법
```bash
# 서버에서 실행
curl ifconfig.me
# 또는
curl icanhazip.com
```

### 추천 최종 URL (nginx 설정 후)
```bash
# 도메인이 있는 경우
https://monitor.goalmond.com

# 도메인이 없는 경우
https://YOUR_PUBLIC_IP  # nginx 기본 서버로 설정
```

---

## 🚀 빠른 배포 (5분 완성)

```bash
# 1. 서비스 시작
cd /media/ubuntu/data120g/college-crawler
docker compose up -d

# 2. 상태 확인
docker ps | grep monitor
curl http://localhost:8081/api/health

# 3. 방화벽 열기 (직접 접근 시)
sudo ufw allow 8081/tcp

# 4. 외부 IP 확인
curl ifconfig.me

# 5. 브라우저에서 접근
# http://확인한_IP:8081
```

---

**작성일**: 2026-02-10  
**현재 포트 상태**: ✅ 충돌 없음 (8080 vs 8081)  
**권장 방식**: nginx + SSL/HTTPS + 도메인
