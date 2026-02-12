"""
GraphRAG Step 0 프롬프트 템플릿 및 로컬 검증용 Triple 추출 유틸.

참고 자료:
- https://github.com/microsoft/graphrag
- https://github.com/langchain-ai/langchain
- https://github.com/run-llama/llama_index
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Iterable


TRIPLE_EXTRACTION_PROMPT = """
You are an expert at extracting knowledge graph triples from educational text.

[Entity Types]
- School: Educational institutions (e.g., Stanford University, MIT)
- Program: Academic programs/majors (e.g., Computer Science, Data Science)
- Company: Employers (e.g., Google, Microsoft)
- Job: Job titles (e.g., AI Engineer, Data Scientist)
- Skill: Technical/professional skills (e.g., Machine Learning, Python)
- Location: Cities/States (e.g., Palo Alto CA, New York NY)

[Relation Types]
- LOCATED_IN: School is located in Location
- OFFERS: School offers Program
- DEVELOPS: Program develops Skill
- LEADS_TO: Program leads to Job
- HIRES_FROM: Company hires from School
- REQUIRES: Job requires Skill
- PARTNERS_WITH: School partners with Company

[Few-shot Example #1]
Text: "Stanford's Computer Science program teaches Machine Learning and graduates work at Google."
Output:
{
  "triples": [
    {"head": "Stanford University", "relation": "OFFERS", "tail": "Computer Science", "confidence": 0.95},
    {"head": "Computer Science", "relation": "DEVELOPS", "tail": "Machine Learning", "confidence": 0.93},
    {"head": "Google", "relation": "HIRES_FROM", "tail": "Stanford University", "confidence": 0.91}
  ]
}

[Few-shot Example #2]
Text: "MIT is located in Cambridge, Massachusetts and partners with Amazon."
Output:
{
  "triples": [
    {"head": "Massachusetts Institute of Technology", "relation": "LOCATED_IN", "tail": "Cambridge, Massachusetts", "confidence": 0.94},
    {"head": "Massachusetts Institute of Technology", "relation": "PARTNERS_WITH", "tail": "Amazon", "confidence": 0.90}
  ]
}

[Few-shot Example #3]
Text: "The Data Science program prepares students for Data Scientist roles that require Python."
Output:
{
  "triples": [
    {"head": "Data Science", "relation": "LEADS_TO", "tail": "Data Scientist", "confidence": 0.88},
    {"head": "Data Scientist", "relation": "REQUIRES", "tail": "Python", "confidence": 0.87}
  ]
}

Now extract triples from:
{text}

Return JSON only.
"""


ENTITY_NORMALIZATION_PROMPT = """
Normalize entity names for a study-abroad knowledge graph.

Rules:
1) Resolve abbreviations (e.g., MIT -> Massachusetts Institute of Technology, ML -> Machine Learning)
2) Keep canonical title casing
3) Remove noisy suffixes like Inc., LLC when unnecessary
4) Keep semantic meaning unchanged
5) Return JSON only

Input:
{entities}

Output:
{
  "normalized_entities": [
    {"raw": "MIT", "normalized": "Massachusetts Institute of Technology", "entity_type": "School"}
  ]
}
"""


RELATION_VALIDATION_PROMPT = """
Validate relation labels for the ontology below and correct invalid labels.

Allowed relations:
- LOCATED_IN
- OFFERS
- DEVELOPS
- LEADS_TO
- HIRES_FROM
- REQUIRES
- PARTNERS_WITH

Input triples:
{triples}

Return JSON only:
{
  "validated_triples": [
    {"head": "...", "relation": "OFFERS", "tail": "...", "confidence": 0.90}
  ]
}
"""


@dataclass(frozen=True)
class Triple:
    """추출된 지식 그래프 Triple."""

    head: str
    relation: str
    tail: str
    confidence: float


_SPACE_RE = re.compile(r"\s+")
_PROGRAM_RE = re.compile(r"([A-Z][A-Za-z& ]{2,40})\s+program", re.IGNORECASE)
_LOCATION_RE = re.compile(
    r"(?:located in|in)\s+([A-Z][a-zA-Z]+(?:,\s*[A-Z][a-zA-Z]+){0,2})", re.IGNORECASE
)


def _clean_text(value: str) -> str:
    cleaned = _SPACE_RE.sub(" ", value).strip()
    return cleaned.rstrip(".,;: ")


def _dedupe_triples(triples: Iterable[Triple]) -> list[Triple]:
    seen: set[tuple[str, str, str]] = set()
    result: list[Triple] = []
    for triple in triples:
        key = (triple.head.lower(), triple.relation, triple.tail.lower())
        if key in seen:
            continue
        seen.add(key)
        result.append(triple)
    return result


def extract_triples_rule_based(text: str, school_name: str | None = None) -> list[Triple]:
    """
    Step 0 통합 테스트용 경량 Triple 추출기.

    LLM 호출 없이도 파이프라인 검증이 가능하도록 대표 패턴만 규칙 기반으로 추출합니다.
    """
    if not text or not text.strip():
        return []

    src = _clean_text(text)
    school = _clean_text(school_name or "Unknown School")
    triples: list[Triple] = []

    program_match = _PROGRAM_RE.search(src)
    program = _clean_text(program_match.group(1)) if program_match else ""
    if program:
        triples.append(Triple(head=school, relation="OFFERS", tail=program, confidence=0.92))

    if "teaches" in src.lower() or "focuses on" in src.lower() or "emphasizes" in src.lower():
        skill_candidates = [
            "Machine Learning",
            "Deep Learning",
            "Data Science",
            "Python",
            "Cloud Computing",
            "Algorithms",
        ]
        for skill in skill_candidates:
            if re.search(rf"\b{re.escape(skill)}\b", src, re.IGNORECASE):
                if program:
                    triples.append(
                        Triple(head=program, relation="DEVELOPS", tail=skill, confidence=0.89)
                    )

    if re.search(r"\bwork at\b|\bhired by\b|\bgraduates work at\b", src, re.IGNORECASE):
        companies = ["Google", "Microsoft", "Amazon", "Tesla", "Meta", "Apple"]
        for company in companies:
            if re.search(rf"\b{re.escape(company)}\b", src, re.IGNORECASE):
                triples.append(Triple(head=company, relation="HIRES_FROM", tail=school, confidence=0.88))

    location_match = _LOCATION_RE.search(src)
    if location_match:
        location = _clean_text(location_match.group(1))
        triples.append(Triple(head=school, relation="LOCATED_IN", tail=location, confidence=0.85))

    if re.search(r"\bcareer as\b|\bcareers as\b|\bprepare[s]?\b", src, re.IGNORECASE):
        jobs = ["Data Scientist", "AI Engineer", "Software Engineer"]
        for job in jobs:
            if re.search(rf"\b{re.escape(job)}\b", src, re.IGNORECASE):
                if program:
                    triples.append(Triple(head=program, relation="LEADS_TO", tail=job, confidence=0.84))

    return _dedupe_triples(triples)


def triple_to_dict(triple: Triple) -> dict[str, Any]:
    """Triple을 JSON 직렬화 가능한 dict로 변환."""
    return {
        "head": triple.head,
        "relation": triple.relation,
        "tail": triple.tail,
        "confidence": float(triple.confidence),
    }
