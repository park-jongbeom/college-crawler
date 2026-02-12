"""
GraphRAG Triple Extraction Service.

Gemini API를 사용하여 HTML 콘텐츠에서 지식 그래프 Triples를 추출합니다.

참고 자료:
- https://ai.google.dev/api/rest
- https://github.com/microsoft/graphrag
"""

from __future__ import annotations

import json
import os
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from src.crawlers.chunking import Chunk, SemanticChunker
from src.services.entity_resolution import EntityResolver, NormalizedTriple
from src.services.prompt_templates import TRIPLE_EXTRACTION_PROMPT, Triple


class TripleExtractionService:
    """HTML 콘텐츠에서 지식 그래프 Triples를 추출하는 서비스."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.0-flash",
        chunk_size: int = 1000,
        overlap: int = 200,
        confidence_threshold: float = 0.8,
    ) -> None:
        """
        TripleExtractionService 초기화.

        Args:
            api_key: Gemini API 키 (없으면 GEMINI_API_KEY 환경변수 사용)
            model_name: 사용할 Gemini 모델명
            chunk_size: 청킹 시 최대 문자 수
            overlap: 청킹 오버랩 문자 수
            confidence_threshold: 최소 Confidence 점수 (이 값 이상만 반환)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY 환경변수 또는 api_key 파라미터가 필요합니다.")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.chunker = SemanticChunker()
        self.resolver = EntityResolver()
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.confidence_threshold = confidence_threshold

    def extract_from_html(
        self, html: str, school_name: str | None = None, source_url: str | None = None
    ) -> list[NormalizedTriple]:
        """
        HTML 콘텐츠에서 Triples를 추출합니다.

        Args:
            html: 원본 HTML 문자열
            school_name: 학교명 (컨텍스트 제공용)
            source_url: 출처 URL (메타데이터용)

        Returns:
            정규화된 Triples 리스트 (Confidence >= threshold)
        """
        if not html or not html.strip():
            return []

        # 1. Semantic Chunking
        chunks = self.chunker.chunk_html(html, chunk_size=self.chunk_size, overlap=self.overlap)
        if not chunks:
            return []

        # 2. 각 청크에서 Triple 추출
        all_triples: list[Triple] = []
        for chunk in chunks:
            triples = self._extract_from_chunk(chunk.text, school_name=school_name)
            all_triples.extend(triples)

        # 3. Entity Resolution (정규화)
        normalized = self.resolver.normalize_triples(all_triples)

        # 4. Confidence 필터링
        filtered = [
            triple
            for triple in normalized
            if triple.confidence >= self.confidence_threshold
        ]

        return filtered

    def _extract_from_chunk(self, text: str, school_name: str | None = None) -> list[Triple]:
        """
        단일 텍스트 청크에서 Triples를 추출합니다.

        Args:
            text: 추출할 텍스트
            school_name: 학교명 (컨텍스트 제공용)

        Returns:
            추출된 Triples 리스트
        """
        if not text or not text.strip():
            return []

        # 프롬프트 구성
        prompt = TRIPLE_EXTRACTION_PROMPT.format(text=text)
        if school_name:
            prompt = f"School context: {school_name}\n\n{prompt}"

        try:
            # Gemini API 호출
            response: GenerateContentResponse = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # JSON 파싱
            triples = self._parse_response(response_text)
            return triples

        except Exception as e:
            # 에러 발생 시 빈 리스트 반환 (로깅은 상위에서 처리)
            print(f"Triple 추출 실패: {e}")
            return []

    def _parse_response(self, response_text: str) -> list[Triple]:
        """
        Gemini API 응답을 파싱하여 Triple 리스트로 변환합니다.

        Args:
            response_text: API 응답 텍스트 (JSON 형식)

        Returns:
            파싱된 Triple 리스트
        """
        try:
            # JSON 코드 블록 제거 (```json ... ```)
            cleaned = response_text.strip()
            if cleaned.startswith("```"):
                # 첫 번째 ``` 제거
                cleaned = cleaned.split("```", 1)[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:].strip()
                # 마지막 ``` 제거
                if cleaned.endswith("```"):
                    cleaned = cleaned.rsplit("```", 1)[0].strip()

            # JSON 파싱
            data = json.loads(cleaned)
            triples_data = data.get("triples", [])

            triples: list[Triple] = []
            for item in triples_data:
                head = item.get("head", "").strip()
                relation = item.get("relation", "").strip()
                tail = item.get("tail", "").strip()
                confidence = float(item.get("confidence", 0.8))

                if head and relation and tail:
                    triples.append(
                        Triple(
                            head=head,
                            relation=relation,
                            tail=tail,
                            confidence=confidence,
                        )
                    )

            return triples

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"응답 파싱 실패: {e}, 응답: {response_text[:200]}")
            return []
