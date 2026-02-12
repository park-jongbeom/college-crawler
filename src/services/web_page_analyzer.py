"""
WebPageAnalyzer: HTML 콘텐츠 분석 및 Triple 추출 통합 서비스.

크롤링된 HTML 콘텐츠를 분석하여 지식 그래프 Triples를 추출합니다.
"""

from __future__ import annotations

from typing import Any

from src.services.triple_extraction_service import TripleExtractionService
from src.services.entity_resolution import NormalizedTriple


class WebPageAnalyzer:
    """HTML 콘텐츠 분석 및 Triple 추출을 담당하는 서비스."""

    def __init__(
        self,
        gemini_api_key: str | None = None,
        model_name: str = "gemini-2.0-flash",
        confidence_threshold: float = 0.8,
    ) -> None:
        """
        WebPageAnalyzer 초기화.

        Args:
            gemini_api_key: Gemini API 키 (없으면 GEMINI_API_KEY 환경변수 사용)
            model_name: 사용할 Gemini 모델명
            confidence_threshold: 최소 Confidence 점수
        """
        self.triple_extractor = TripleExtractionService(
            api_key=gemini_api_key,
            model_name=model_name,
            confidence_threshold=confidence_threshold,
        )

    def analyze_html(
        self,
        html: str,
        school_name: str | None = None,
        source_url: str | None = None,
    ) -> dict[str, Any]:
        """
        HTML 콘텐츠를 분석하여 Triples를 추출합니다.

        Args:
            html: 분석할 HTML 문자열
            school_name: 학교명 (컨텍스트 제공용)
            source_url: 출처 URL (메타데이터용)

        Returns:
            분석 결과 딕셔너리:
            {
                "triples": [NormalizedTriple, ...],
                "triple_count": int,
                "source_url": str | None,
                "school_name": str | None
            }
        """
        if not html or not html.strip():
            return {
                "triples": [],
                "triple_count": 0,
                "source_url": source_url,
                "school_name": school_name,
            }

        # Triple 추출
        triples = self.triple_extractor.extract_from_html(
            html=html,
            school_name=school_name,
            source_url=source_url,
        )

        return {
            "triples": triples,
            "triple_count": len(triples),
            "source_url": source_url,
            "school_name": school_name,
        }

    def extract_triples(
        self,
        html: str,
        school_name: str | None = None,
        source_url: str | None = None,
    ) -> list[NormalizedTriple]:
        """
        HTML에서 Triples만 추출합니다 (간편 메서드).

        Args:
            html: 분석할 HTML 문자열
            school_name: 학교명
            source_url: 출처 URL

        Returns:
            정규화된 Triples 리스트
        """
        result = self.analyze_html(html=html, school_name=school_name, source_url=source_url)
        return result["triples"]
