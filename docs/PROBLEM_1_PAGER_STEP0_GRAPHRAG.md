# Problem 1-Pager: Step 0 오픈소스 벤치마킹 및 패턴 이식

## 배경(Background)
- 현재 `college-crawler`는 Level 1 메타데이터 보강까지 완료되어 정량 지표 품질이 향상되었습니다.
- 다음 단계인 GraphRAG 도입을 위해서는, 검증된 오픈소스 패턴을 빠르게 학습/이식하여 시행착오를 줄여야 합니다.
- Step 0의 목적은 실제 LLM 운영 이전에, Triple 추출/청킹/정규화 파이프라인의 기술적 골격을 코드와 테스트로 확보하는 것입니다.

참고(공식/원문):
- https://github.com/microsoft/graphrag
- https://github.com/langchain-ai/langchain
- https://github.com/run-llama/llama_index

## 문제(Problem)
- 현재 코드베이스에는 GraphRAG 전용 모듈(Triple 추출 템플릿, Semantic Chunking, Entity Resolution)이 부재합니다.
- LLM 호출만으로 초기 개발을 시작하면, 테스트가 느려지고 실패 원인(프롬프트/파서/정규화)을 분리하기 어렵습니다.
- 엔터티 표기 변형(MIT vs Massachusetts Institute of Technology, ML vs Machine Learning)으로 지식 그래프 품질이 저하될 위험이 큽니다.

## 목표(Goal)
- Step 0 범위에서 아래 3개 컴포넌트를 구현하고 pytest로 검증합니다.
  1) `prompt_templates.py`: Triple 추출/정규화/관계검증 프롬프트 템플릿
  2) `chunking.py`: Semantic Chunking (의미 단위 분할 + 오버랩)
  3) `entity_resolution.py`: Alias 기반 정규화 + relation 정합성 보정
- 통합 테스트(`HTML -> Chunking -> Triple 추출 -> 정규화`)를 구성해 파이프라인 동작을 보장합니다.
- 벤치마크 리포트를 작성해 다음 단계(Phase 1 스키마/서비스 구현) 입력 문서를 확정합니다.

## 비목표(Non-goals)
- 실제 운영 LLM 호출(Gemini API) 최적화/비용 튜닝은 포함하지 않습니다.
- PostgreSQL `knowledge_triples`, `entities` 마이그레이션은 Step 0 범위에서 다루지 않습니다.
- GraphSearchService(Recursive CTE) 구현은 Step 0 이후 Phase 1에서 진행합니다.

## 제약(Constraints)
- 보안
  - Secret/API Key 하드코딩 금지.
  - 테스트에서 외부 API 실호출 금지(로컬 규칙 기반 검증 사용).
- 품질
  - 신규 비즈니스 로직에는 pytest 테스트 동반.
  - 정규화는 예외를 최대한 삼키고 안전한 fallback을 제공.
- 운영성
  - 기존 크롤러 흐름을 깨지 않도록 신규 모듈은 독립 유틸로 추가.
  - 실패 시 파이프라인 중단보다 부분 스킵을 우선.
