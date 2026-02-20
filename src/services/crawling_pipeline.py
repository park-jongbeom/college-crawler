"""크롤링 파이프라인 런처."""
from __future__ import annotations

import logging
from typing import Iterable, List

from src.services.auto_triple_collector import AutoTripleCollector
from src.services.url_finder import UrlFinder

logger = logging.getLogger(__name__)


class CrawlingPipeline:
    """UrlFinder + AutoTripleCollector를 연결하는 파이프라인 스켈레톤."""

    def __init__(
        self,
        url_finder: UrlFinder,
        collector_cls: type[AutoTripleCollector],
    ):
        self.url_finder = url_finder
        self.collector_cls = collector_cls

    def run(self, schools: List[dict[str, str]]) -> None:
        """파이프라인 실행 (구현 예정)."""
        raise NotImplementedError("CrawlingPipeline.run is not implemented yet")
