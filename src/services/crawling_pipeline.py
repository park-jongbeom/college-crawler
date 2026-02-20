"""크롤링 파이프라인 런처."""
from __future__ import annotations

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Dict, List

from src.services.auto_triple_collector import AutoTripleCollector
from src.services.url_finder import UrlFinder

logger = logging.getLogger(__name__)


class CrawlingPipeline:
    """UrlFinder + AutoTripleCollector를 연결하는 파이프라인 런처."""

    def __init__(
        self,
        url_finder: UrlFinder,
        collector_cls: type[AutoTripleCollector],
        *,
        status_path: Path | str = Path("data/crawling_status.json"),
        max_workers: int = 4,
    ):
        self.url_finder = url_finder
        self.collector_cls = collector_cls
        self.status_path = Path(status_path)
        self.max_workers = max_workers
        self._status_lock = Lock()
        self._status = self._load_status()

    def _load_status(self) -> Dict[str, str]:
        if self.status_path.exists():
            try:
                return json.loads(self.status_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _persist_status(self) -> None:
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        with self.status_path.open("w", encoding="utf-8") as fp:
            json.dump(self._status, fp, ensure_ascii=False, indent=2)

    def _school_key(self, school: Dict[str, str]) -> str:
        return school.get("website") or school.get("name") or "<unknown>"

    def _should_skip(self, school: Dict[str, str]) -> bool:
        key = self._school_key(school)
        return self._status.get(key) == "completed"

    def _record_status(self, school: Dict[str, str], status: str) -> None:
        key = self._school_key(school)
        with self._status_lock:
            self._status[key] = status
            self._persist_status()

    def _process_school(self, school: Dict[str, str]) -> Dict[str, int]:
        name = school.get("name")
        homepage = school.get("website")

        if not homepage:
            logger.debug("학교 홈페이지 누락으로 건너뜀: %s", name)
            self._record_status(school, "skipped")
            return {"triples_collected": 0}

        candidate_urls = self.url_finder.find_target_urls(homepage)
        if not candidate_urls:
            logger.info("UrlFinder가 URL을 찾지 못해 AutoTripleCollector를 건너뜀: %s", homepage)
            self._record_status(school, "skipped")
            return {"triples_collected": 0}

        try:
            collector = self.collector_cls(school=school, candidate_urls=candidate_urls)
            summary = collector.run()
            self._record_status(school, "completed")
            return summary if isinstance(summary, dict) else {"triples_collected": 0}
        except Exception as exc:
            logger.exception("AutoTripleCollector 실행 실패 (school=%s): %s", name, exc)
            self._record_status(school, "failed")
            return {"triples_collected": 0}

    def run(self, schools: List[Dict[str, str]]) -> int:
        """ThreadPoolExecutor 기반으로 여러 학교를 동시에 처리합니다."""
        total_triples = 0
        pending = [school for school in schools if not self._should_skip(school)]
        if not pending:
            logger.info("모든 학교가 이미 처리되었거나 상태 파일에 완료로 기록됨.")
            return 0

        with ThreadPoolExecutor(max_workers=min(len(pending), self.max_workers)) as executor:
            futures = {executor.submit(self._process_school, school): school for school in pending}
            for future in as_completed(futures):
                try:
                    summary = future.result()
                except Exception as exc:
                    logger.exception("학교 처리 중 예외 발생: %s", exc)
                    continue
                total_triples += summary.get("triples_collected", 0) or 0

        if total_triples == 0:
            logger.warning("CrawlingPipeline 결과 Triple이 0개입니다.")
        return total_triples
