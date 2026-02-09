# 데이터베이스 스키마 문서

## 개요

이 문서는 PostgreSQL 17 데이터베이스의 실제 스키마 구조를 문서화합니다.
JPA 엔티티와의 매핑 관계도 함께 명시합니다.

**데이터베이스:** PostgreSQL 17  
**스키마:** public  
**문서 작성일:** 2026-01-26

---

## 테이블 목록

### User Service 관련 테이블

- `users` - 사용자 정보
- `academic_profiles` - 학력 프로필
- `financial_profiles` - 재정 프로필
- `user_preferences` - 사용자 선호도
- `contact_infos` - 연락처 정보
- `user_sessions` - 사용자 세션

### Audit Service 관련 테이블

- `audit_logs` - 감사 로그

### AI Consultant Service 관련 테이블

- `conversations` - 대화 세션
- `messages` - 메시지
- `documents` - 문서 (RAG)

### 시스템 테이블

- `flyway_schema_history` - Flyway 마이그레이션 히스토리

---

## users 테이블

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | uuid_generate_v4() | Primary Key |
| email | VARCHAR(255) | NO | - | 이메일 (Unique) |
| full_name | VARCHAR(100) | NO | - | 전체 이름 |
| role | VARCHAR(20) | YES | 'STUDENT' | 역할 (USER, ADMIN, STUDENT) |
| is_active | BOOLEAN | YES | true | 활성화 여부 |
| password_hash | VARCHAR(255) | YES | - | 비밀번호 해시 |
| password_reset_token | VARCHAR(255) | YES | - | 비밀번호 재설정 토큰 |
| password_reset_expires_at | TIMESTAMPTZ | YES | - | 비밀번호 재설정 만료 시간 |
| email_verified | BOOLEAN | YES | false | 이메일 인증 여부 |
| email_verification_token | VARCHAR(255) | YES | - | 이메일 인증 토큰 |
| created_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | UUID | YES | - | 생성자 ID |
| updated_by | UUID | YES | - | 수정자 ID |

### 제약조건

- **Primary Key:** `id`
- **Unique:** `email`
- **Foreign Key:**
  - `created_by` → `users.id`
  - `updated_by` → `users.id`

### 인덱스

- `users_pkey` (Primary Key)
- `users_email_key` (Unique)
- `idx_users_email`
- `idx_users_role`
- `idx_users_is_active`
- `idx_users_email_verified`
- `idx_users_created_at`

### JPA Entity 매핑

**엔티티:** `com.goalmond.user.entity.User`

**주요 불일치:**
- Entity: `name` → DB: `full_name`
- Entity: `passwordHash` (NOT NULL) → DB: `password_hash` (nullable)
- Entity: `role` 기본값 "USER" → DB: 기본값 "STUDENT"
- DB에만 있는 컬럼: `is_active`, `email_verified`, `email_verification_token`, `password_reset_token`, `password_reset_expires_at`, `created_by`, `updated_by`

---

## academic_profiles 테이블

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | uuid_generate_v4() | Primary Key |
| user_id | UUID | NO | - | 사용자 ID (Foreign Key) |
| school_name | VARCHAR(255) | NO | - | 학교명 |
| degree_type | VARCHAR(50) | YES | - | 학위 유형 |
| degree | VARCHAR(255) | NO | - | 학위 (BACHELOR, MASTER, PHD) |
| major | VARCHAR(100) | YES | - | 전공 |
| gpa | NUMERIC(4,2) | YES | - | 학점 |
| gpa_scale | NUMERIC(4,2) | YES | 4.0 | GPA 스케일 |
| graduation_date | DATE | YES | - | 졸업일 |
| institution | VARCHAR(255) | YES | - | 기관명 |
| created_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | UUID | YES | - | 생성자 ID |
| updated_by | UUID | YES | - | 수정자 ID |

### 제약조건

- **Primary Key:** `id`
- **Foreign Key:**
  - `user_id` → `users.id`
  - `created_by` → `users.id`
  - `updated_by` → `users.id`

### 인덱스

- `academic_profiles_pkey` (Primary Key)
- `idx_academic_profiles_user_id`
- `idx_academic_profiles_degree_type`

### JPA Entity 매핑

**엔티티:** `com.goalmond.user.entity.AcademicProfile`

**주요 불일치:**
- Entity에 없는 필수 컬럼: `school_name` (NOT NULL)
- Entity에 없는 컬럼: `degree_type`, `gpa_scale`, `graduation_date`, `created_by`, `updated_by`
- Entity: `major` (NOT NULL) → DB: `major` (nullable)
- Entity: `gpa` (Double?) → DB: `gpa` (NUMERIC(4,2))

---

## financial_profiles 테이블

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | uuid_generate_v4() | Primary Key |
| user_id | UUID | NO | - | 사용자 ID (Foreign Key) |
| budget_range | VARCHAR | NO | - | 예산 범위 |
| total_budget_usd | INTEGER | YES | - | 총 예산 (USD) |
| tuition_limit_usd | INTEGER | YES | - | 등록금 한도 (USD) |
| funding_source | TEXT | YES | - | 자금 출처 |
| created_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | UUID | YES | - | 생성자 ID |
| updated_by | UUID | YES | - | 수정자 ID |

### 제약조건

- **Primary Key:** `id`
- **Foreign Key:**
  - `user_id` → `users.id`
  - `created_by` → `users.id`
  - `updated_by` → `users.id`

### 인덱스

- `financial_profiles_pkey` (Primary Key)
- `idx_financial_profiles_user_id`

### JPA Entity 매핑

**엔티티:** `com.goalmond.user.entity.FinancialProfile`

**주요 불일치:**
- Entity에 없는 컬럼: `total_budget_usd`, `tuition_limit_usd`, `created_by`, `updated_by`

---

## user_preferences 테이블

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | uuid_generate_v4() | Primary Key |
| user_id | UUID | NO | - | 사용자 ID (Foreign Key) |
| target_major | VARCHAR | YES | - | 목표 전공 |
| target_location | VARCHAR | YES | - | 목표 지역 |
| career_goal | TEXT | YES | - | 진로 목표 |
| preferred_track | VARCHAR | YES | - | 선호 트랙 |
| created_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | UUID | YES | - | 생성자 ID |
| updated_by | UUID | YES | - | 수정자 ID |

### 제약조건

- **Primary Key:** `id`
- **Foreign Key:**
  - `user_id` → `users.id`
  - `created_by` → `users.id`
  - `updated_by` → `users.id`

### 인덱스

- `user_preferences_pkey` (Primary Key)
- `idx_user_preferences_user_id`
- `idx_user_preferences_target_major`

### JPA Entity 매핑

**엔티티:** `com.goalmond.user.entity.UserPreference`

**주요 불일치:**
- Entity: `preferredMajor` (NOT NULL) → DB: `target_major` (nullable)
- Entity: `careerTrack` → DB: `preferred_track`
- Entity에 없는 컬럼: `target_location`, `career_goal`, `created_by`, `updated_by`

---

## audit_logs 테이블

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | uuid_generate_v4() | Primary Key |
| table_name | VARCHAR | NO | - | 테이블명 |
| record_id | UUID | NO | - | 레코드 ID |
| action | VARCHAR | NO | - | 액션 (CREATE, UPDATE, DELETE) |
| actor_id | UUID | YES | - | 실행자 ID |
| old_value | JSONB | YES | - | 변경 전 값 (JSON) |
| new_value | JSONB | YES | - | 변경 후 값 (JSON) |
| before_data | TEXT | YES | - | 변경 전 데이터 |
| after_data | TEXT | YES | - | 변경 후 데이터 |
| user_id | UUID | NO | - | 사용자 ID |
| ip_address | VARCHAR | NO | - | IP 주소 |
| created_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMPTZ | YES | CURRENT_TIMESTAMP | 수정 시간 |
| created_by | UUID | YES | - | 생성자 ID |
| updated_by | UUID | YES | - | 수정자 ID |

### 제약조건

- **Primary Key:** `id`
- **Foreign Key:**
  - `actor_id` → `users.id`
  - `created_by` → `users.id`
  - `updated_by` → `users.id`

### 인덱스

- `audit_logs_pkey` (Primary Key)
- `idx_audit_logs_table_name`
- `idx_audit_logs_record_id`
- `idx_audit_logs_action`
- `idx_audit_logs_actor_id`
- `idx_audit_logs_created_at`

### JPA Entity 매핑

**엔티티:** `com.goalmond.audit.entity.AuditLog` (extends `AuditEntity`)

**주요 불일치:**
- Entity에 없는 컬럼: `old_value`, `new_value` (JSONB), `actor_id`, `updated_at`, `created_by`, `updated_by`
- Entity: `userId` → DB: `user_id` + `actor_id`

---

## conversations 테이블 (AI Consultant Service)

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | gen_random_uuid() | Primary Key |
| user_id | VARCHAR(255) | NO | - | 사용자 ID |
| tenant_id | VARCHAR(50) | NO | - | 테넌트 ID |
| title | VARCHAR(255) | YES | - | 제목 |
| status | VARCHAR(20) | NO | 'ACTIVE' | 상태 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |

### 제약조건

- **Primary Key:** `id`

### 인덱스

- `conversations_pkey` (Primary Key)
- `idx_conversations_user_tenant` (user_id, tenant_id)
- `idx_conversations_tenant`
- `idx_conversations_status`
- `idx_conversations_created_at`

---

## messages 테이블 (AI Consultant Service)

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | gen_random_uuid() | Primary Key |
| conversation_id | UUID | NO | - | 대화 ID (Foreign Key) |
| role | VARCHAR(20) | NO | - | 역할 |
| original_content | TEXT | NO | - | 원본 콘텐츠 |
| masked_content | TEXT | YES | - | 마스킹된 콘텐츠 |
| llm_response | TEXT | YES | - | LLM 응답 |
| masked_tokens | JSONB | YES | - | 마스킹된 토큰 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |

### 제약조건

- **Primary Key:** `id`
- **Foreign Key:**
  - `conversation_id` → `conversations.id` (ON DELETE CASCADE)

### 인덱스

- `messages_pkey` (Primary Key)
- `idx_messages_conversation`
- `idx_messages_created_at`
- `idx_messages_role`

---

## documents 테이블 (AI Consultant Service)

### 컬럼 정보

| 컬럼명 | 타입 | NULL 허용 | 기본값 | 설명 |
|--------|------|-----------|--------|------|
| id | UUID | NO | gen_random_uuid() | Primary Key |
| title | VARCHAR(255) | NO | - | 제목 |
| content | TEXT | NO | - | 내용 |
| embedding | VECTOR(1536) | YES | - | 임베딩 벡터 |
| metadata | JSONB | YES | - | 메타데이터 |
| tenant_id | VARCHAR(50) | YES | - | 테넌트 ID |
| source_url | VARCHAR(500) | YES | - | 소스 URL |
| document_type | VARCHAR(50) | YES | - | 문서 유형 |
| created_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 생성 시간 |
| updated_at | TIMESTAMP | NO | CURRENT_TIMESTAMP | 수정 시간 |

### 제약조건

- **Primary Key:** `id`

### 인덱스

- `documents_pkey` (Primary Key)
- `idx_documents_tenant`
- `idx_documents_type`
- `idx_documents_created_at`
- `idx_documents_embedding` (HNSW 인덱스, 벡터 유사도 검색용)

---

## UUID 타입 사용

모든 테이블의 `id` 컬럼은 PostgreSQL의 `UUID` 타입을 사용합니다.

**JPA Entity 설정:**
- `@Column(columnDefinition = "BINARY(16)")` 사용 시 불일치 발생
- PostgreSQL UUID 타입을 기본으로 사용해야 함

---

## 타임스탬프 타입

### BaseEntity를 상속받는 테이블

- `created_at`, `updated_at`: `TIMESTAMPTZ` (nullable, 기본값 CURRENT_TIMESTAMP)

### AI Consultant Service 테이블

- `created_at`, `updated_at`: `TIMESTAMP` (NOT NULL, 기본값 CURRENT_TIMESTAMP)

---

## Flyway 마이그레이션 히스토리

**테이블:** `flyway_schema_history`

현재 적용된 마이그레이션:
- V1: Baseline
- V2: ensure ai tables in public

---

## 참고사항

1. **스네이크 케이스:** 모든 컬럼명은 스네이크 케이스(snake_case)를 사용합니다.
2. **UUID 생성:** 대부분의 테이블은 `uuid_generate_v4()`를 사용하지만, AI Consultant Service 테이블은 `gen_random_uuid()`를 사용합니다.
3. **타임스탬프:** User Service 테이블은 `TIMESTAMPTZ`를 사용하고, AI Consultant Service 테이블은 `TIMESTAMP`를 사용합니다.
4. **Audit 필드:** 대부분의 테이블에 `created_by`, `updated_by` 필드가 있습니다.
