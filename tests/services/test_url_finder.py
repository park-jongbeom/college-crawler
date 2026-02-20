"""UrlFinder 실패 시나리오를 검증하는 pytest suite."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.services.url_finder import UrlFinder


HTML_NO_KEYWORD_LINKS = """
<html>
  <body>
    <a href="https://example.edu/about">About</a>
    <a href="https://example.edu/contact">Contact</a>
  </body>
</html>
"""

HTML_ONLY_DOCUMENT_LINKS = """
<html>
  <body>
    <a href="https://example.edu/catalog.pdf">Program catalog</a>
    <a href="https://example.edu/brochure.docx">Brochure</a>
  </body>
</html>
"""


@pytest.mark.unit
@patch("src.services.url_finder.requests.Session.get")
def test_find_target_urls_propagates_connection_error(mock_get):
    """홈페이지 요청이 실패하면 ConnectionError가 그대로 전파됩니다."""
    mock_get.side_effect = requests.exceptions.ConnectionError("no route")

    finder = UrlFinder()

    with pytest.raises(requests.exceptions.ConnectionError):
        finder.find_target_urls("https://example.edu")


@pytest.mark.unit
@patch("src.services.url_finder.requests.Session.get")
def test_find_target_urls_returns_empty_when_no_keyword_links(mock_get):
    """키워드 링크가 없으면 빈 리스트가 반환되어 문제를 조기에 감지할 수 있습니다."""
    mock_response = MagicMock()
    mock_response.text = HTML_NO_KEYWORD_LINKS
    mock_get.return_value = mock_response

    finder = UrlFinder()
    urls = finder.find_target_urls("https://example.edu")

    assert urls == []


@pytest.mark.unit
@patch("src.services.url_finder.requests.Session.get")
def test_find_target_urls_filters_out_unsupported_file_types(mock_get):
    """PDF/DOCX 링크만 존재할 경우 수집 대상에 포함되지 않아야 합니다."""
    mock_response = MagicMock()
    mock_response.text = HTML_ONLY_DOCUMENT_LINKS
    mock_get.return_value = mock_response

    finder = UrlFinder()
    urls = finder.find_target_urls("https://example.edu")

    assert urls == []


@pytest.mark.unit
def test_find_target_urls_raises_on_invalid_google_api_key():
    """Google Search API 키가 유효하지 않으면 예외를 통해 알림을 줘야 합니다."""
    with patch("src.services.url_finder.requests.Session.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body></body></html>"
        mock_get.return_value = mock_response

        with patch("src.services.url_finder.GoogleSearchStrategy") as mock_search_cls:
            mock_search = MagicMock()
            mock_search.search.side_effect = ValueError("Invalid API key")
            mock_search_cls.return_value = mock_search

            finder = UrlFinder(google_api_key="bad-key")

            with pytest.raises(ValueError, match="Invalid API key"):
                finder.find_target_urls("https://example.edu")


@pytest.mark.unit
@patch("src.services.url_finder.requests.Session.get")
def test_find_target_urls_respects_max_depth_limit(mock_get):
    """깊이 3의 링크는 max_depth=2 환경에서 탐색되지 않아야 합니다."""
    page_map = {
        "https://example.edu": "<html><body><a href='https://example.edu/level1'>Level 1</a></body></html>",
        "https://example.edu/level1": "<html><body><a href='https://example.edu/level2'>Level 2</a></body></html>",
        "https://example.edu/level2": "<html><body><a href='https://example.edu/deep-career'>Deep Career</a></body></html>",
        "https://example.edu/deep-career": "<html><body><p>Career page</p></body></html>",
    }

    def _side_effect(url, timeout=30):
        if url not in page_map:
            raise ValueError(f"Unexpected URL: {url}")
        response = MagicMock()
        response.text = page_map[url]
        return response

    mock_get.side_effect = _side_effect

    finder = UrlFinder()
    finder.max_depth = 2

    urls = finder.find_target_urls("https://example.edu")

    called_urls = [call.args[0] for call in mock_get.call_args_list]
    assert all("deep-career" not in url for url in called_urls)
    assert all("deep-career" not in url for url in urls)
