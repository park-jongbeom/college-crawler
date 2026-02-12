# GraphRAG Step 0 벤치마크 리포트

## 1. 목적
Step 0의 목적은 GraphRAG 구축 전, 오픈소스 구현 패턴을 분석하여 우리 도메인(미국 유학 상담)에 맞게 빠르게 이식 가능한 최소 골격을 만드는 것입니다.

분석 대상:
- Microsoft GraphRAG
- LangChain (Graph 관련 패턴)
- LlamaIndex (청킹/KG 인덱싱 패턴)

## 2. 분석 소스
- Microsoft GraphRAG: https://github.com/microsoft/graphrag
- LangChain: https://github.com/langchain-ai/langchain
- LlamaIndex: https://github.com/run-llama/llama_index

## 3. 핵심 인사이트

### 3.1 Microsoft GraphRAG
- 문서 전처리와 엔터티/관계 추출의 분리 설계가 명확합니다.
- 추출 전 청킹 품질이 결과 품질을 크게 좌우하므로, chunk overlap과 문맥 유지가 중요합니다.
- 엔터티 해상도(Entity Resolution)를 별도 단계로 다뤄 그래프 중복 노드를 줄입니다.

우리 적용:
- `SemanticChunker`로 의미 단위 + 오버랩(기본 20%) 구현.
- `EntityResolver`를 독립 서비스로 분리.
- LLM 추출 전후를 테스트 가능한 경계로 분리.

### 3.2 LangChain
- 스키마 기반 구조화 출력(typed output) 접근이 강점입니다.
- 프롬프트에 허용 relation set을 명시하면 잘못된 라벨 생성이 줄어듭니다.
- 후처리 단계에서 정규화/검증 훅을 붙이기 쉽습니다.

우리 적용:
- `TRIPLE_EXTRACTION_PROMPT`, `ENTITY_NORMALIZATION_PROMPT`, `RELATION_VALIDATION_PROMPT` 분리.
- relation whitelist(`OFFERS`, `DEVELOPS` 등) 강제.
- 미정의 relation은 `RELATED_TO`로 안전 fallback.

### 3.3 LlamaIndex
- 청킹 전략을 도메인에 맞춰 유연하게 조정하는 철학이 유효합니다.
- 문장 경계를 고려한 분할이 retrieval/요약 품질을 개선합니다.

우리 적용:
- HTML -> section 텍스트 추출 -> sentence-aware chunking.
- 과도하게 긴 문장은 강제 슬라이싱으로 안전 처리.

## 4. Step 0 구현 산출물

1) `src/services/prompt_templates.py`
- Triple 추출 프롬프트 템플릿
- 엔터티 정규화/관계 검증 템플릿
- 로컬 테스트를 위한 경량 규칙 기반 Triple 추출 함수

2) `src/crawlers/chunking.py`
- `SemanticChunker`, `Chunk` 데이터 구조
- HTML 기반 section 추출
- 오버랩 기반 청킹 및 경계 검증

3) `src/services/entity_resolution.py`
- 30개 이상 alias 사전
- 엔터티/관계 정규화
- Triple dedupe

4) 테스트
- `tests/crawlers/test_chunking.py`
- `tests/services/test_entity_resolution.py`
- `tests/integration/test_step0_integration.py`

## 5. 리스크 및 대응
- 리스크: 규칙 기반 Triple 추출은 recall이 낮을 수 있음
  대응: Step 0 목적을 통합 파이프라인 검증으로 제한, Phase 1에서 LLM 추출기로 교체

- 리스크: 엔터티 alias 사전 커버리지 부족
  대응: 운영 로그 기반으로 alias 증분 확장

- 리스크: HTML 구조 다양성으로 청킹 품질 변동
  대응: section fallback + sentence fallback + 강제 슬라이싱 처리

## 6. 다음 단계(Phase 1 연결)
- Ontology(Entity 6, Relation 7) 고정 및 검증 룰 강화
- `knowledge_triples`, `entities` 테이블 마이그레이션
- WebPageAnalyzer에 LLM 기반 추출기 연결
- GraphSearchService(Recursive CTE) 구현
