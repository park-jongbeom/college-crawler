import pytest

from src.crawlers.base_crawler import BaseCrawler


@pytest.mark.unit
def test_robots_txt_timeout_does_not_block_and_allows_fetch(monkeypatch):
    """
    robots.txt 로드가 지연/실패하더라도 크롤링이 멈추지 않고(robots 미적용),
    can_fetch()는 허용(True)으로 동작해야 합니다.
    """

    def fake_get(self, url, timeout):  # noqa: ARG001
        import requests

        raise requests.exceptions.Timeout("robots timeout")

    # BaseCrawler 내부에서 생성한 session.get을 가로채기 위해 requests.Session.get을 패치합니다.
    monkeypatch.setattr("src.crawlers.base_crawler.requests.Session.get", fake_get)

    crawler = BaseCrawler("https://example.com")
    assert crawler.robots_parser is None
    assert crawler.can_fetch("https://example.com/some/path") is True

