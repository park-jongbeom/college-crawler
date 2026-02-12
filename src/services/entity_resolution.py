"""
GraphRAG Step 0 Entity Resolution.

참고 자료:
- https://github.com/langchain-ai/langchain
- https://github.com/microsoft/graphrag
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Iterable

from src.services.prompt_templates import Triple


_SPECIAL_RE = re.compile(r"[^a-zA-Z0-9\s,&\-]")
_SPACE_RE = re.compile(r"\s+")


def _norm_key(value: str) -> str:
    lowered = value.lower().strip()
    lowered = lowered.replace(".", "").replace("-", " ")
    lowered = _SPECIAL_RE.sub("", lowered)
    lowered = _SPACE_RE.sub(" ", lowered).strip()
    return lowered


@dataclass(frozen=True)
class NormalizedTriple:
    """정규화가 적용된 Triple."""

    head: str
    relation: str
    tail: str
    confidence: float


class EntityResolver:
    """동의어/표기 변형을 canonical entity로 정규화합니다."""

    RELATIONS = {
        "LOCATED_IN",
        "OFFERS",
        "DEVELOPS",
        "LEADS_TO",
        "HIRES_FROM",
        "REQUIRES",
        "PARTNERS_WITH",
    }

    CANONICAL_ALIASES: dict[str, list[str]] = {
        "Machine Learning": ["ML", "machine learning", "machine-learning", "machinelearning"],
        "Deep Learning": ["DL", "deep learning", "deep-learning"],
        "Computer Science": ["CS", "CompSci", "Computer Sci", "Comp Sci"],
        "Data Science": ["DS", "DataSci", "Data Sci"],
        "Cloud Computing": ["Cloud", "Cloud Comp", "cloud computing"],
        "Software Engineering": ["SE", "Software Eng", "Software Engineer Program"],
        "Artificial Intelligence": ["AI", "A.I.", "artificial intelligence"],
        "Data Scientist": ["data scientist", "data-scientist"],
        "AI Engineer": ["ai engineer", "ai-engineer"],
        "Software Engineer": ["software engineer", "swe"],
        "Product Manager": ["PM", "product manager"],
        "Google": ["Google Inc", "Google LLC", "Alphabet", "Google, Inc."],
        "Microsoft": ["MSFT", "Microsoft Corp", "Microsoft Corporation"],
        "Amazon": ["Amazon.com", "AWS", "Amazon Inc"],
        "Meta": ["Facebook", "Meta Platforms", "Meta Inc"],
        "Apple": ["Apple Inc", "Apple Computer"],
        "Tesla": ["Tesla Inc", "Tesla Motors"],
        "Stanford University": ["Stanford", "Stanford Univ", "SU"],
        "Massachusetts Institute of Technology": ["MIT", "M.I.T."],
        "Carnegie Mellon University": ["CMU", "Carnegie Mellon"],
        "University of California, Berkeley": ["UC Berkeley", "Berkeley", "UCB"],
        "University of California, Los Angeles": ["UCLA", "UC Los Angeles"],
        "University of Southern California": ["USC", "Southern California University"],
        "New York University": ["NYU"],
        "San Jose State University": ["SJSU", "San Jose State"],
        "Santa Monica College": ["SMC", "Santa Monica CC"],
        "California": ["CA", "Calif."],
        "New York": ["NY", "N.Y."],
        "Massachusetts": ["MA", "Mass."],
        "Washington": ["WA", "Wash."],
        "Palo Alto, California": ["Palo Alto CA"],
        "Seattle, Washington": ["Seattle WA"],
    }

    def __init__(self) -> None:
        self._alias_to_canonical: dict[str, str] = {}
        all_keys: list[str] = []
        for canonical, aliases in self.CANONICAL_ALIASES.items():
            key = _norm_key(canonical)
            self._alias_to_canonical[key] = canonical
            all_keys.append(key)
            for alias in aliases:
                alias_key = _norm_key(alias)
                self._alias_to_canonical[alias_key] = canonical
                all_keys.append(alias_key)
        self._known_keys = sorted(set(all_keys))

    def normalize(self, entity_name: str, entity_type: str = "Unknown") -> str:
        """엔티티 이름을 canonical 표기로 정규화합니다."""
        raw = (entity_name or "").strip()
        if not raw:
            return ""
        key = _norm_key(raw)
        if key in self._alias_to_canonical:
            return self._alias_to_canonical[key]

        # 향후 고도화를 위한 경량 fuzzy matching.
        near = get_close_matches(key, self._known_keys, n=1, cutoff=0.93)
        if near:
            return self._alias_to_canonical[near[0]]

        # fallback: 특수문자 제거 + Title Case
        cleaned = _SPECIAL_RE.sub(" ", raw)
        cleaned = _SPACE_RE.sub(" ", cleaned).strip()
        if entity_type.lower() in {"skill", "program", "job"}:
            return cleaned.title()
        return cleaned

    def normalize_relation(self, relation: str) -> str:
        """Ontology relation set으로 정규화합니다."""
        normalized = (relation or "").strip().upper().replace("-", "_").replace(" ", "_")
        return normalized if normalized in self.RELATIONS else "RELATED_TO"

    def normalize_triples(self, triples: Iterable[Triple | NormalizedTriple]) -> list[NormalizedTriple]:
        """Triple 리스트의 head/tail/relation을 정규화합니다."""
        normalized: list[NormalizedTriple] = []
        for triple in triples:
            head = self.normalize(triple.head)
            tail = self.normalize(triple.tail)
            relation = self.normalize_relation(triple.relation)
            confidence = float(triple.confidence)
            normalized.append(
                NormalizedTriple(
                    head=head,
                    relation=relation,
                    tail=tail,
                    confidence=max(0.0, min(1.0, confidence)),
                )
            )
        return self._dedupe(normalized)

    @staticmethod
    def _dedupe(triples: Iterable[NormalizedTriple]) -> list[NormalizedTriple]:
        seen: set[tuple[str, str, str]] = set()
        result: list[NormalizedTriple] = []
        for triple in triples:
            key = (triple.head.lower(), triple.relation, triple.tail.lower())
            if key in seen:
                continue
            seen.add(key)
            result.append(triple)
        return result
