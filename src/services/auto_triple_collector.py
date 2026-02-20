"""
Auto Triple Collector (Phase 2 자동 크롤링 확장)

84개 학교의 Career/Program/Placement 페이지를 탐색하여 Gemini Triples를 수집하고
knowledge_triples/graph signal 검증에 사용할 자료 구조를 준비합니다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.crawlers.school_crawler import SchoolCrawler
from src.services.entity_resolution import NormalizedTriple
from src.services.web_page_analyzer import WebPageAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AutoTripleCollector:
    """Career/Program 페이지를 자동으로 찾아 Triple을 수집하는 파이프라인."""

    TARGET_KEYWORDS = [
        "career",
        "careers",
        "employment",
        "outcome",
        "placement",
        "program",
        "academics",
        "student-success",
        "alumni",
        "degree",
        "pathways",
        "job",
    ]
    FALLBACK_SEGMENTS = [
        "/career-outcomes",
        "/career-services",
        "/employment-outcomes",
        "/career-center",
        "/career-paths",
        "/student-success",
        "/programs",
        "/academics/programs",
        "/programs-of-study",
        "/placement",
    ]
    MAX_TARGETS = 5

    def __init__(
        self,
        schools_json: Path,
        *,
        output_path: Path | str = Path("data/auto_triples.jsonl"),
        gemini_api_key: str | None = None,
    ) -> None:
        self.schools_json = schools_json
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.schools = self._load_schools()
        self.logger = logger
        self.analyzer: Optional[WebPageAnalyzer]
        try:
            self.analyzer = WebPageAnalyzer(gemini_api_key=gemini_api_key)
        except ValueError as exc:
            self.logger.warning(
                "Gemini API 키가 없어 Triple 추출을 생략합니다 (%s)", exc
            )
            self.analyzer = None

    def _load_schools(self) -> list[dict[str, Any]]:
        try:
            with self.schools_json.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
            return data.get("schools", [])
        except FileNotFoundError as exc:
            raise RuntimeError(f"학교 목록 파일을 찾을 수 없음: {self.schools_json}") from exc

    def run(self, limit: int | None = None) -> Dict[str, Any]:
        schools = self.schools if limit is None else self.schools[:limit]
        total_triples = 0
        processed_schools = 0

        self.logger.info(
            "AutoTripleCollector 시작 (schools=%s, output=%s)",
            len(schools),
            self.output_path,
        )

        with self.output_path.open("w", encoding="utf-8") as fp:
            for school in schools:
                report = self._collect_for_school(school)
                if report.get("routing", {}).get("skipped"):
                    fp.write(json.dumps(report, ensure_ascii=False))
                    fp.write("\n")
                    continue

                if report.get("triples"):
                    processed_schools += 1
                    total_triples += sum(entry.get("count", 0) for entry in report["triples"])

                fp.write(json.dumps(report, ensure_ascii=False))
                fp.write("\n")

        summary = {
            "schools_processed": len(schools),
            "schools_with_triples": processed_schools,
            "triples_collected": total_triples,
            "output": str(self.output_path),
        }
        self.logger.info(
            "AutoTripleCollector 완료: schools=%d, triples=%d",
            summary["schools_processed"],
            total_triples,
        )
        return summary

    def _collect_for_school(self, school: dict[str, Any]) -> Dict[str, Any]:
        name = school.get("name")
        website = school.get("website")
        result: Dict[str, Any] = {
            "school_name": name,
            "website": website,
            "discovered_urls": [],
            "triples": [],
            "routing": {},
        }

        if not name or not website:
            result["routing"]["skipped"] = True
            result["routing"]["reason"] = "정보 부족"
            self.logger.warning("학교 정보 부족으로 건너뜀: %s", school)
            return result

        try:
            with SchoolCrawler(name, website) as crawler:
                response = crawler.fetch(website, max_retry=1, timeout_seconds=15)
                if not response or not response.text.strip():
                    result["routing"]["skipped"] = True
                    result["routing"]["reason"] = "홈페이지 응답 없음"
                    return result

                candidate_urls = self._discover_candidate_urls(response.text, crawler.base_url)
                result["discovered_urls"] = candidate_urls

                for url in candidate_urls:
                    if crawler.ssl_error_detected:
                        break
                    page_response = crawler.fetch(url, max_retry=1, timeout_seconds=20)
                    if not page_response or not page_response.text.strip():
                        continue
                    page_triples = self._extract_triples_from_page(
                        html=page_response.text,
                        school_name=name,
                        source_url=url,
                    )
                    if page_triples:
                        result["triples"].append(
                            {
                                "source_url": url,
                                "count": len(page_triples),
                                "entries": page_triples,
                            }
                        )
        except Exception as exc:
            self.logger.error("Triple 자동 수집 실패: %s / %s", name, exc)
            result["routing"]["skipped"] = True
            result["routing"]["reason"] = f"예외: {exc}"
        return result

    def _discover_candidate_urls(self, html: str, base_url: str) -> List[str]:
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc.lower()
        candidates: List[str] = []

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            if not href or href.startswith("#") or href.startswith("mailto:"):
                continue

            abs_url = urljoin(base_url, href)
            parsed = urlparse(abs_url)
            if not parsed.scheme.startswith("http"):
                continue
            if parsed.netloc and parsed.netloc.lower() != base_domain:
                continue

            normalized = parsed.path.lower()
            link_text = anchor.get_text(" ", strip=True).lower()
            if any(keyword in normalized or keyword in link_text for keyword in self.TARGET_KEYWORDS):
                if abs_url not in candidates:
                    candidates.append(abs_url)
            if len(candidates) >= self.MAX_TARGETS:
                break

        for segment in self.FALLBACK_SEGMENTS:
            if len(candidates) >= self.MAX_TARGETS:
                break
            fallback = urljoin(base_url, segment)
            parsed = urlparse(fallback)
            if parsed.netloc and parsed.netloc.lower() != base_domain:
                continue
            if fallback not in candidates:
                candidates.append(fallback)

        return candidates

    def _extract_triples_from_page(
        self,
        html: str,
        school_name: str,
        source_url: str,
    ) -> List[Dict[str, Any]]:
        if not self.analyzer:
            self.logger.debug("Gemini 키 없음: Triple 추출 스킵 (%s)", school_name)
            return []

        try:
            raw_triples = self.analyzer.extract_triples(
                html=html,
                school_name=school_name,
                source_url=source_url,
            )
        except Exception as exc:
            self.logger.warning("Triples 추출 중 예외: %s / %s", school_name, exc)
            return []

        return [self._serialize_triple(triple) for triple in raw_triples]

    @staticmethod
    def _serialize_triple(triple: NormalizedTriple) -> Dict[str, Any]:
        return {
            "head": triple.head,
            "relation": triple.relation,
            "tail": triple.tail,
            "confidence": round(triple.confidence, 3),
        }
