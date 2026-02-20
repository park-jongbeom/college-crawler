"""URL 탐색기를 위한 서비스 모듈."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from functools import lru_cache
from typing import Iterable, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TARGET_KEYWORDS = ["career", "placement", "program", "academics"]
UNSUPPORTED_EXTENSIONS = (".pdf", ".docx", ".ppt", ".pptx", ".xlsx")


class CrawlingStrategy(ABC):
    """UrlFinder가 사용할 수 있는 탐색 전략 인터페이스."""

    @abstractmethod
    def search(self, base_url: str) -> Set[str]:
        ...


class GoogleSearchStrategy(CrawlingStrategy):
    """Google Search API 연동 전략(구현 예정)."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @lru_cache(maxsize=128)
    def search(self, base_url: str) -> Set[str]:
        raise NotImplementedError("Google Search integration is pending")


class InternalLinkStrategy(CrawlingStrategy):
    """내부 링크 탐색 중심의 기본 전략."""

    def __init__(
        self,
        session: Optional[requests.Session] = None,
        max_depth: int = 2,
        target_keywords: Optional[Iterable[str]] = None,
    ):
        self.session = session or requests.Session()
        self.max_depth = max_depth
        self.target_keywords = [kw.lower() for kw in (target_keywords or DEFAULT_TARGET_KEYWORDS)]

    def _is_keyword(self, url: str, anchor_text: str) -> bool:
        normalized_url = url.lower()
        normalized_anchor = anchor_text.lower()
        return any(
            keyword in normalized_url or keyword in normalized_anchor
            for keyword in self.target_keywords
        )

    @lru_cache(maxsize=128)
    def search(self, base_url: str) -> Set[str]:
        parsed_base = urlparse(base_url)
        if not parsed_base.scheme or not parsed_base.netloc:
            return set()

        queue = deque([(base_url, 0)])
        visited = {base_url}
        found_urls: Set[str] = set()
        allowed_netloc = parsed_base.netloc

        while queue:
            current_url, current_depth = queue.popleft()

            try:
                response = self.session.get(current_url, timeout=30)
                response.raise_for_status()
            except requests.exceptions.ConnectionError as exc:
                if current_url == base_url:
                    raise exc
                continue
            except requests.exceptions.RequestException:
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            for link in soup.find_all("a", href=True):
                absolute_url = urljoin(current_url, link["href"])
                parsed_link = urlparse(absolute_url)

                if parsed_link.scheme not in ("http", "https"):
                    continue
                if parsed_link.netloc != allowed_netloc:
                    continue

                next_depth = current_depth + 1
                if next_depth > self.max_depth:
                    continue
                if absolute_url in visited:
                    continue

                visited.add(absolute_url)

                if absolute_url.lower().endswith(UNSUPPORTED_EXTENSIONS):
                    continue

                if self._is_keyword(absolute_url, link.get_text("", strip=True)):
                    found_urls.add(absolute_url)
                    continue

                queue.append((absolute_url, next_depth))

        return found_urls


class UrlFinder:
    """학교 홈페이지에서 경력/프로그램 관련 URL을 찾는 책임을 가집니다."""

    def __init__(
        self,
        strategies: Optional[List[CrawlingStrategy]] = None,
        google_api_key: Optional[str] = None,
        max_depth: int = 2,
    ):
        self.session = requests.Session()
        default_strategies: List[CrawlingStrategy] = strategies or [
            InternalLinkStrategy(session=self.session, max_depth=max_depth)
        ]
        if google_api_key:
            default_strategies.append(GoogleSearchStrategy(google_api_key))
        self.strategies = default_strategies

    def find_target_urls(self, school_homepage_url: str) -> List[str]:
        """대상 학교 홈페이지에서 타겟 URL 목록을 반환합니다."""
        found_urls: Set[str] = set()
        for strategy in self.strategies:
            found_urls |= strategy.search(school_homepage_url)
        return list(found_urls)
