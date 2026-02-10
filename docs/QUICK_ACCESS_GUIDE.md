# ⚡ 빠른 접근 가이드

College Crawler 모니터링 대시보드 접근 방법 (1분 가이드)

---

## 🎯 포트 충돌 여부

### ✅ 문제 없습니다!

```
현재 포트 사용 현황:
─────────────────────────────────────
ga-matching-api      → 포트 8080 ✅
crawler-monitor      → 포트 8081 ✅
─────────────────────────────────────

결론: 각 서비스가 다른 포트를 사용하므로 
      충돌 없이 독립적으로 운영 가능!
```

---

## 🌐 현재 접근 방법

### 1. 로컬 서버에서
```bash
http://localhost:8081
```

### 2. 같은 네트워크 내에서
```bash
http://192.168.0.94:8081
```

### 3. 외부 인터넷에서
```bash
# 서버의 외부 IP 확인 (서버에서 실행)
curl ifconfig.me

# 브라우저에서 접근
http://확인한_외부_IP:8081

# 예시
http://13.125.123.45:8081
```

---

## 🚀 실제 운영 서버 배포 시

### 방법 1: 직접 포트 노출 (가장 빠름)

**장점**: 설정 없이 바로 사용  
**단점**: 비표준 포트, SSL 없음

```bash
# 1. 방화벽 포트 열기
sudo ufw allow 8081/tcp
sudo ufw reload

# 2. 외부 IP 확인
curl ifconfig.me

# 3. 브라우저에서 접근
http://외부_IP:8081
```

**보안 강화 (선택)**:
```bash
# 특정 IP만 허용
sudo ufw allow from 회사_IP to any port 8081
```

---

### 방법 2: nginx 리버스 프록시 (권장)

**장점**: 표준 포트(80/443), SSL 적용, 보안 강화  
**단점**: 초기 설정 필요

#### 빠른 설정 (5분)

```bash
# 1. nginx 설치
sudo apt update && sudo apt install nginx -y

# 2. 설정 파일 생성
sudo tee /etc/nginx/sites-available/monitor <<EOF
server {
    listen 80;
    server_name _;  # 모든 도메인/IP 허용
    
    location / {
        proxy_pass http://localhost:8081;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

# 3. 활성화
sudo ln -s /etc/nginx/sites-available/monitor /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 4. 방화벽
sudo ufw allow 'Nginx Full'

# 5. 접근
http://외부_IP  (포트 번호 없이!)
```

#### SSL 추가 (권장)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx -y

# 도메인이 있는 경우
sudo certbot --nginx -d monitor.yourdomain.com

# 자동 갱신 확인
sudo certbot renew --dry-run

# 접근
https://monitor.yourdomain.com
```

---

## 🔒 보안 옵션

### 옵션 1: 기본 인증 (nginx)

```bash
# 비밀번호 설정
sudo apt install apache2-utils -y
sudo htpasswd -c /etc/nginx/.htpasswd admin

# nginx 설정에 추가
sudo nano /etc/nginx/sites-available/monitor

# location / 블록 안에 추가:
#     auth_basic "Monitoring";
#     auth_basic_user_file /etc/nginx/.htpasswd;

sudo systemctl restart nginx
```

### 옵션 2: IP 제한

```bash
# nginx 설정
sudo nano /etc/nginx/sites-available/monitor

# location / 블록 안에 추가:
#     allow 회사_IP;
#     allow VPN_IP;
#     deny all;

sudo systemctl restart nginx
```

### 옵션 3: VPN 전용

- VPN을 통해서만 접근
- 가장 안전하지만 VPN 설정 필요

---

## 📋 접근 방법 비교

| 방법 | 설정 시간 | 보안 | URL | 권장도 |
|------|-----------|------|-----|--------|
| 직접 포트 | 1분 | ⚠️ 낮음 | `http://IP:8081` | 개발/테스트 |
| nginx (HTTP) | 5분 | ⭐⭐ 중간 | `http://IP` | 내부망 |
| nginx + SSL | 10분 | ⭐⭐⭐ 높음 | `https://domain` | **운영 환경** |
| + 기본 인증 | +2분 | ⭐⭐⭐⭐ 매우 높음 | 위와 동일 | 민감한 데이터 |

---

## 🎯 상황별 권장 방법

### 개발/테스트
```bash
http://localhost:8081
```
- 빠르고 간단
- 로컬에서만 접근

### 사내 네트워크
```bash
http://192.168.0.94:8081
```
- 방화벽 필요 없음
- 내부 IP로 접근

### 외부 접근 (임시)
```bash
http://외부_IP:8081
```
- sudo ufw allow 8081/tcp
- 빠른 테스트용

### 운영 환경 (권장)
```bash
https://monitor.yourdomain.com
```
- nginx + SSL 필수
- 기본 인증 추가 권장

---

## 🚦 현재 상태 확인

```bash
# 1. 서비스 실행 확인
docker ps | grep monitor

# 2. 포트 확인
netstat -tuln | grep 8081

# 3. 로컬 접근 테스트
curl http://localhost:8081/api/health

# 4. 외부 IP 확인
curl ifconfig.me

# 5. 방화벽 상태
sudo ufw status
```

**모두 정상이면**: ✅ 배포 준비 완료!

---

## 🔧 빠른 트러블슈팅

### 접근이 안 돼요!

```bash
# 1. 컨테이너 실행 확인
docker ps | grep monitor
# → 없으면: docker compose up -d

# 2. 방화벽 확인
sudo ufw status
# → inactive면: sudo ufw allow 8081/tcp

# 3. 로컬 테스트
curl localhost:8081/api/health
# → 안 되면: docker compose logs monitor

# 4. 포트 확인
sudo lsof -i :8081
# → 없으면: 서비스 시작 필요
```

### nginx 502 에러

```bash
# 백엔드 확인
curl http://localhost:8081/api/health

# nginx 로그
sudo tail -f /var/log/nginx/error.log

# nginx 재시작
sudo systemctl restart nginx
```

---

## 📱 실제 사용 예시

### 예시 1: AWS EC2
```bash
# 외부 IP: 13.125.123.45

# 직접 접근
http://13.125.123.45:8081

# nginx 설정 후
http://13.125.123.45
https://13.125.123.45  (SSL 인증서 적용 시)
```

### 예시 2: 도메인 연결
```bash
# 도메인: monitor.goalmond.com
# DNS A 레코드: monitor.goalmond.com → 13.125.123.45

# 접근
https://monitor.goalmond.com
```

### 예시 3: 서브패스
```nginx
# nginx 설정
location /monitor/ {
    proxy_pass http://localhost:8081/;
}

# 접근
https://goalmond.com/monitor/
```

---

## ✅ 최종 체크리스트

배포 전 확인:
- [ ] Docker 컨테이너 실행 중 (`docker ps`)
- [ ] 로컬 접근 가능 (`curl localhost:8081`)
- [ ] 외부 IP 확인 완료
- [ ] 방화벽 설정 (포트 8081 또는 80/443)
- [ ] (선택) nginx 설정
- [ ] (선택) SSL 인증서
- [ ] (선택) 기본 인증 또는 IP 제한

---

## 📞 접근 URL (요약)

### 지금 바로 사용 (1분)
```bash
# 서버에서
curl ifconfig.me  # → 외부 IP 확인

# 브라우저에서
http://외부_IP:8081
```

### 프로덕션 (10분 설정)
```bash
# nginx + SSL 설정 후
https://monitor.yourdomain.com
```

---

**포트 충돌**: ✅ 없음 (8080 vs 8081)  
**즉시 사용 가능**: ✅ 가능  
**권장 방식**: nginx + SSL/HTTPS
