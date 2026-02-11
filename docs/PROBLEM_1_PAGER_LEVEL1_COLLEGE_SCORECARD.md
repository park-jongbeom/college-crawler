# Problem 1-Pager: Level 1 메타데이터 보강 (College Scorecard API)

## 배경(Background)
- 현재 `college-crawler`는 각 학교 웹사이트를 크롤링하여 유학생 연락처/ESL/지원/시설 등의 정보를 수집하고, 이를 운영 DB의 `schools` 테이블에 저장한다.
- 하지만 매칭 품질 향상을 위해서는 학교의 “정량 지표”(합격률, 졸업률, 초봉/수입 등)도 안정적으로 확보되어야 한다.
- 미국 교육부 College Scorecard API는 공공 데이터 기반의 정량 지표를 제공하며, Level 1 메타데이터 보강 소스로 적합하다.

참고(공식 문서):
- https://collegescorecard.ed.gov/data/api-documentation/

## 문제(Problem)
- 웹사이트 크롤링만으로는 합격률/졸업률/수입 등 정량 지표를 일관되게 수집하기 어렵다.
- 외부 API 연동 시 보안(키 노출), 레이트리밋(429), 응답 스키마 변경, 학교명 매칭 오류로 인해 크롤링 파이프라인이 실패/중단될 위험이 있다.

## 목표(Goal)
- TDD로 College Scorecard API 연동 모듈을 추가한다.
- `COLLEGE_SCORECARD_API` 환경변수(로컬은 `.env`, 운영은 GitHub Secrets)를 통해 키를 주입하고, 코드/로그/테스트에서 키가 노출되지 않게 한다.
- Scorecard에서 확보한 지표를 `schools`에 안전하게 업데이트한다(값 범위 검증, None 덮어쓰기 방지).
- API 장애/매칭 실패가 있어도 크롤링 자체는 계속 진행되도록 “스킵 + 감사로그”로 처리한다.

## 비목표(Non-goals)
- Level 2(프로그램 상세) / Level 3(리뷰/가이드) 수집은 이번 변경에 포함하지 않는다.
- Scorecard 데이터 전체 수집/적재(대용량 ETL) 파이프라인은 구축하지 않는다.
- 매칭 API(ga-api-platform)의 프롬프트/임베딩 로직 개편은 이번 단계의 직접 목표가 아니다(단, 이후 품질 검증 테스트로 연결).

## 제약(Constraints)
- 보안
  - API 키는 Git에 커밋하지 않는다.
  - 운영 배포 시 `college-crawler` GitHub Actions Secrets에 `COLLEGE_SCORECARD_API`로 저장하고 서버 `.env`로만 생성한다.
  - 로그에 키/요청 URL(키 포함) 전체를 출력하지 않는다.
- 안정성
  - 429(Too Many Requests) 등 레이트리밋을 고려하여 재시도/백오프를 포함한다.
  - 응답 스키마가 일부 변경되어도 필요한 필드만 방어적으로 파싱한다.
- 품질
  - unit 테스트로 API 클라이언트/매칭/정규화를 모킹하여 검증한다.
  - 실패 시 예외로 전체 작업이 중단되지 않도록 예외를 캡처하고 스킵한다.

