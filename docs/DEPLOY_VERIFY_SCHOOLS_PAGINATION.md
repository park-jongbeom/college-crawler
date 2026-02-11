# 배포 검증: 최근 업데이트 학교 페이징/필터 (2026-02-11)

## 배포 내용

- **커밋**: `8e6be7c` — feat: 최근 업데이트 학교 목록 페이징 및 필터(주/타입/이름 검색) 추가
- **GitHub Actions**: Deploy College Crawler Run #24  
  https://github.com/park-jongbeom/college-crawler/actions/runs/21892607968

## 배포 완료 후 확인 방법

### 1. GitHub Actions

- 위 Run #24에서 **status: completed**, **conclusion: success** 인지 확인.

### 2. 운영 API (새 응답 형식)

배포가 반영되면 다음처럼 **객체**가 반환되어야 합니다 (배열이 아님).

```bash
# 페이징 (5개만)
curl -s "https://go-almond.ddnsfree.com/monitor/api/schools/recent?page=1&per_page=5" | jq 'keys'
# 기대: ["items", "total", "page", "per_page", "total_pages"]

# 필터: CA만
curl -s "https://go-almond.ddnsfree.com/monitor/api/schools/recent?page=1&per_page=10&state=CA" | jq '.total, (.items | length)'
# total = CA 학교 수, items 길이 <= 10

# 이름 검색
curl -s "https://go-almond.ddnsfree.com/monitor/api/schools/recent?page=1&per_page=20&q=College" | jq '.total, .total_pages'
```

### 3. 대시보드 UI

- https://go-almond.ddnsfree.com/monitor/ 접속
- "최근 업데이트된 학교" 섹션에 **주**, **학교 타입**, **이름 검색**, **페이지당 10개/20개** 필터 및 **이전/다음, 페이지 번호**가 보이는지 확인.
- 주를 CA로 바꾸면 CA 학교만, 20개 선택 시 20개씩 표시되는지 확인.

## 현재 상태 (검증 시점)

- **Push**: 완료 (`aaf4c1b..8e6be7c  main -> main`)
- **Actions Run #24**: in_progress (배포 중)
- **운영 API**: 아직 이전 버전(배열 응답) — 배포 완료 후 위 항목으로 재확인
