# 데이터베이스 스키마 문서

## 개요

College Crawler는 `ga-api-platform`과 동일한 PostgreSQL 데이터베이스를 사용합니다.
이 문서는 crawler 관점에서 필요한 테이블과 컬럼만 요약합니다.

- 데이터베이스: PostgreSQL 17
- 스키마: `public`
- 문서 작성일: 2026-02-11

## 스키마 동기화 원칙

- DB 스키마 변경은 `ga-api-platform`의 Flyway와 `college-crawler`의 Alembic에 동기화 반영합니다.
- Crawler는 원문/구조화 데이터를 저장하고, 임베딩 생성은 `ga-api-platform`이 담당합니다.
- 운영 기준 상세 스키마 문서는 `ga-api-platform/docs/DATABASE_SCHEMA.md`를 Source of Truth로 사용합니다.

## 주요 테이블 (Crawler 사용)

### `schools`

학교 기본 정보 및 크롤링 확장 필드를 저장합니다.

핵심 컬럼:
- `id` (UUID, PK)
- `name`, `type`, `state`, `city`
- `tuition`, `living_cost`, `website`
- `international_email`, `international_phone`
- `employment_rate`
- `facilities` (JSONB)
- `staff_info` (JSONB)
- `esl_program` (JSONB)
- `international_support` (JSONB)
- `created_at`, `updated_at`

### `programs`

학교별 프로그램 정보를 저장합니다.

핵심 컬럼:
- `id` (UUID, PK)
- `school_id` (UUID, FK -> `schools.id`)
- `name`, `type`, `degree`, `duration`
- `tuition`
- `created_at`, `updated_at`

### `school_documents`

학교 문서 원문(RAG 입력)을 저장합니다.

핵심 컬럼:
- `id` (UUID, PK)
- `school_id` (UUID, FK -> `schools.id`)
- `document_type`, `title`, `content`
- `metadata` (JSONB)
- `created_at`, `updated_at`

참고:
- crawler는 문서 원문을 저장합니다.
- 임베딩 생성/업데이트는 `ga-api-platform`에서 수행합니다.

### `program_documents`

프로그램 문서 원문(RAG 입력)을 저장합니다.

핵심 컬럼:
- `id` (UUID, PK)
- `program_id` (UUID, FK -> `programs.id`)
- `document_type`, `title`, `content`
- `metadata` (JSONB)
- `created_at`, `updated_at`

### `audit_logs`

크롤링 실행 결과 및 변경 이력을 저장합니다.

핵심 컬럼:
- `id` (UUID, PK)
- `table_name`, `record_id`, `action`
- `old_value`, `new_value`
- `created_at`, `updated_at`

## 최근 스키마 반영 이력

### 2026-02-09 (V7 동기화)

`schools`에 아래 컬럼 추가:
- `international_email`
- `international_phone`
- `employment_rate`
- `facilities`
- `staff_info`
- `esl_program`
- `international_support`

인덱스 추가:
- `idx_schools_international_email`

## 운영 검증 체크 포인트

- `monitor/api/database` 응답에서 이메일/전화/ESL 집계 값이 조회되는지 확인
- `monitor/api/schools/{id}` 응답에서 `facilities`, `international_support`, `employment_rate`, `staff_info` 필드가 조회되는지 확인
- `ga-api-platform` 배포 시 Flyway `V7__add_international_fields.sql` 적용 여부를 확인
