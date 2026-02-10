# College Crawler – 데이터베이스 참조

크롤러가 사용하는 PostgreSQL 스키마 요약 및 ga-api-platform과의 역할 분담을 정리합니다.

## 개요

- **데이터베이스**: ga-api-platform과 **동일한 PostgreSQL** 인스턴스 사용 (`ga_db`).
- **역할 분담**
  - **college-crawler**: 학교·프로그램·문서의 **텍스트/메타데이터 수집 및 저장**.
  - **ga-api-platform**: 저장된 문서에 대해 **임베딩(embedding) 생성** 및 RAG/매칭 API 제공.

## 주요 테이블

| 테이블 | 설명 |
|--------|------|
| `schools` | 학교 마스터 (이름, 유형, 지역, 학비, 국제화 필드 등) |
| `programs` | 학교별 프로그램 (이름, 유형, 학위, 기간, OPT 여부 등) |
| `school_documents` | RAG용 학교 문서 (리뷰, 입학 가이드, 통계, 장단점) |
| `program_documents` | RAG용 프로그램 문서 (커리큘럼, 진로 통계, 학생 후기) |

## 크롤러 작업 범위

### schools 테이블에 저장할 컬럼

- **기본**: `name`, `type`, `state`, `city`, `tuition`, `living_cost`, `ranking`, `description`, `acceptance_rate`, `transfer_rate`, `graduation_rate`, `website`
- **V6 (매칭 리포트)**: `global_ranking`, `ranking_field`, `average_salary`, `alumni_network_count`, `feature_badges`
- **V7 (국제화)**: `international_email`, `international_phone`, `employment_rate`, `facilities`, `staff_info`, `esl_program`, `international_support` (JSONB는 객체/배열로 저장)

### programs 테이블에 저장할 컬럼

- `school_id`, `name`, `type`, `degree`, `duration`, `tuition`, `opt_available`

### school_documents / program_documents

- **저장**: `school_id` 또는 `program_id`, `document_type`, `title`, `content`, `metadata` (선택)
- **저장하지 않음**: **`embedding` 컬럼은 반드시 NULL로 두기.**  
  ga-api-platform이 별도 배치/API로 임베딩을 생성해 채웁니다 (V8에서 embedding nullable 처리됨).

## 상세 스키마 참조

전체 컬럼 정의, 타입, 제약조건, 인덱스는 **ga-api-platform** 저장소의 스키마 문서를 참조하세요.

- **[DATABASE_SCHEMA.md](../../ga-api-platform/docs/DATABASE_SCHEMA.md)** (같은 워크스페이스에서 상대 경로)

같은 서버/워크스페이스에 `ga-api-platform`이 없다면, 해당 레포의 `docs/DATABASE_SCHEMA.md` 파일을 열람하면 됩니다.

## 요약

1. 크롤러는 **텍스트와 메타데이터만** 넣고, `school_documents`/`program_documents`의 **embedding은 NULL**로 유지.
2. **schools**의 V7 국제화 필드(`international_email`, `facilities`, `esl_program` 등)를 수집해 저장하면 API/매칭에서 활용 가능.
3. 스키마 변경 시 ga-api-platform의 Flyway 마이그레이션(V3, V5, V6, V7, V8)과 **DATABASE_SCHEMA.md**를 함께 확인할 것.
