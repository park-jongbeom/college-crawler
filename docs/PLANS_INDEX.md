# 계획 문서 인덱스

이 프로젝트의 모든 계획 문서는 **통합 관리**됩니다.

## 통합 문서 위치

**경로**: `/media/ubuntu/data120g/ai-consulting-plans/`

모든 AI 유학 상담 고도화 관련 계획, 벤치마크, 구현 가이드가 이 위치에서 중앙 집중 관리됩니다.

## 주요 문서 바로가기

### 마스터 계획
- [전체 고도화 계획](../../ai-consulting-plans/00_MASTER_PLAN/ai_유학_상담_고도화_마스터플랜.md)
- [AI Enhancement Plan 2026](../../ai-consulting-plans/00_MASTER_PLAN/AI_ENHANCEMENT_PLAN_2026.md)

### GraphRAG 구축
- [Step 0: 오픈소스 벤치마킹](../../ai-consulting-plans/01_GRAPHRAG/step0_오픈소스_벤치마킹.md)
- [Phase 1-3 상세 계획](../../ai-consulting-plans/01_GRAPHRAG/)

### 현재 RAG 시스템
- [RAG 아키텍처](../../ai-consulting-plans/02_RAG_CURRENT/RAG_ARCHITECTURE.md)
- [데이터 검증 계획](../../ai-consulting-plans/02_RAG_CURRENT/RAG_DATA_VERIFICATION_PLAN.md)
- [매칭 시스템 개선](../../ai-consulting-plans/02_RAG_CURRENT/AI_MATCHING_IMPROVEMENT_GUIDE.md)

### 벤치마크 리포트
- [오픈소스 분석 결과](../../ai-consulting-plans/04_BENCHMARKS/)

## 이 프로젝트 관련 문서

### 현재 위치 (college-crawler/docs/)
- `AI_ENHANCEMENT_PLAN_2026.md` - 메인 계획 (통합 폴더에 링크됨)
- `DATABASE_SCHEMA.md` - 크롤러 DB 스키마
- `MONITORING_DASHBOARD.md` - 모니터링 대시보드

### 크롤러 구현
- `src/crawlers/school_crawler.py` - 학교 크롤링
- `src/services/scorecard_enrichment_service.py` - College Scorecard
- `src/crawlers/parsers/statistics_parser.py` - 통계 파싱

## 문서 업데이트 방법

1. **계획 문서**: `/media/ubuntu/data120g/ai-consulting-plans/`에서 직접 수정
2. **구현 문서**: 각 프로젝트 `docs/`에서 수정
3. **버전 관리**: Git으로 변경 이력 추적

---

**최종 업데이트**: 2026-02-12  
**다음 단계**: Step 0 오픈소스 벤치마킹 완료
