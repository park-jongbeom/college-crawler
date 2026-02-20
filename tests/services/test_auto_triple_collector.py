"""
AutoTripleCollector 단위 테스트.

Phase 2 자동 크롤링 확장 파이프라인의 핵심 컴포넌트를 검증합니다.
Gemini API / HTTP 요청은 모두 mock으로 처리합니다.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.auto_triple_collector import AutoTripleCollector
from src.services.entity_resolution import NormalizedTriple


# ---------------------------------------------------------------------------
# 테스트용 Fixture
# ---------------------------------------------------------------------------

def _make_schools_json(tmp_path: Path, schools: list) -> Path:
    """임시 학교 JSON 파일을 생성합니다."""
    p = tmp_path / "schools.json"
    p.write_text(json.dumps({"schools": schools}), encoding="utf-8")
    return p


SAMPLE_SCHOOLS = [
    {"name": "Stanford University", "website": "https://stanford.edu"},
    {"name": "MIT", "website": "https://mit.edu"},
]

SAMPLE_HTML = """
<html>
<body>
  <nav>
    <a href="/career-outcomes">Career Outcomes</a>
    <a href="/programs">Programs</a>
    <a href="https://external.com/link">External</a>
    <a href="#anchor">Anchor</a>
    <a href="mailto:info@school.edu">Email</a>
  </nav>
  <p>Stanford graduates go on to careers at Google and Microsoft.</p>
</body>
</html>
"""


@pytest.fixture
def schools_file(tmp_path):
    return _make_schools_json(tmp_path, SAMPLE_SCHOOLS)


@pytest.fixture
def output_file(tmp_path):
    return tmp_path / "auto_triples.jsonl"


# ---------------------------------------------------------------------------
# 초기화 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_init_with_gemini_key(mock_analyzer_cls, schools_file, output_file):
    """Gemini 키가 있으면 WebPageAnalyzer가 초기화됩니다."""
    mock_analyzer_cls.return_value = MagicMock()

    collector = AutoTripleCollector(
        schools_json=schools_file,
        output_path=output_file,
        gemini_api_key="fake-key",
    )

    mock_analyzer_cls.assert_called_once_with(gemini_api_key="fake-key")
    assert collector.analyzer is not None
    assert len(collector.schools) == 2


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_init_without_gemini_key(mock_analyzer_cls, schools_file, output_file):
    """Gemini 키가 없으면 analyzer=None으로 초기화됩니다."""
    mock_analyzer_cls.side_effect = ValueError("API key required")

    collector = AutoTripleCollector(
        schools_json=schools_file,
        output_path=output_file,
        gemini_api_key=None,
    )

    assert collector.analyzer is None
    assert len(collector.schools) == 2


@pytest.mark.unit
def test_init_missing_schools_file(tmp_path, output_file):
    """학교 JSON 파일이 없으면 RuntimeError가 발생합니다."""
    with pytest.raises(RuntimeError, match="학교 목록 파일을 찾을 수 없음"):
        AutoTripleCollector(
            schools_json=tmp_path / "nonexistent.json",
            output_path=output_file,
        )


# ---------------------------------------------------------------------------
# URL 탐색 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_discover_candidate_urls_keyword_match(mock_analyzer_cls, schools_file, output_file):
    """TARGET_KEYWORDS를 포함하는 링크가 우선 수집됩니다."""
    mock_analyzer_cls.return_value = MagicMock()
    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")

    urls = collector._discover_candidate_urls(SAMPLE_HTML, "https://stanford.edu")

    assert "https://stanford.edu/career-outcomes" in urls
    assert "https://stanford.edu/programs" in urls


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_discover_candidate_urls_excludes_external_and_anchors(
    mock_analyzer_cls, schools_file, output_file
):
    """외부 도메인, 앵커, mailto 링크는 제외됩니다."""
    mock_analyzer_cls.return_value = MagicMock()
    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")

    urls = collector._discover_candidate_urls(SAMPLE_HTML, "https://stanford.edu")

    assert not any("external.com" in u for u in urls)
    assert not any(u.endswith("#anchor") for u in urls)
    assert not any("mailto:" in u for u in urls)


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_discover_candidate_urls_fallback_segments(mock_analyzer_cls, schools_file, output_file):
    """키워드 매칭이 없어도 FALLBACK_SEGMENTS가 후보에 포함됩니다."""
    mock_analyzer_cls.return_value = MagicMock()
    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")

    # 링크 없는 빈 페이지
    empty_html = "<html><body><p>No links here</p></body></html>"
    urls = collector._discover_candidate_urls(empty_html, "https://school.edu")

    assert len(urls) > 0
    assert all("school.edu" in u for u in urls)


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_discover_candidate_urls_max_targets(mock_analyzer_cls, schools_file, output_file):
    """MAX_TARGETS(5)를 초과하지 않습니다."""
    mock_analyzer_cls.return_value = MagicMock()
    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")

    # 10개 이상 키워드 링크가 있는 HTML
    many_links = "".join(f'<a href="/career-page-{i}">career link</a>' for i in range(20))
    html = f"<html><body>{many_links}</body></html>"

    urls = collector._discover_candidate_urls(html, "https://school.edu")

    assert len(urls) <= AutoTripleCollector.MAX_TARGETS


# ---------------------------------------------------------------------------
# Triple 직렬화 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
def test_serialize_triple():
    """NormalizedTriple이 딕셔너리로 올바르게 직렬화됩니다."""
    triple = NormalizedTriple(
        head="Stanford University",
        relation="HIRES_FROM",
        tail="Google",
        confidence=0.9345,
    )

    result = AutoTripleCollector._serialize_triple(triple)

    assert result["head"] == "Stanford University"
    assert result["relation"] == "HIRES_FROM"
    assert result["tail"] == "Google"
    assert result["confidence"] == round(0.9345, 3)


# ---------------------------------------------------------------------------
# _extract_triples_from_page 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_extract_triples_without_analyzer(mock_analyzer_cls, schools_file, output_file):
    """analyzer=None이면 빈 리스트를 반환합니다."""
    mock_analyzer_cls.side_effect = ValueError("no key")
    collector = AutoTripleCollector(schools_file, output_path=output_file)

    result = collector._extract_triples_from_page(
        html=SAMPLE_HTML,
        school_name="Stanford",
        source_url="https://stanford.edu/career",
    )

    assert result == []


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_extract_triples_with_analyzer(mock_analyzer_cls, schools_file, output_file):
    """analyzer가 있으면 추출된 Triple이 직렬화되어 반환됩니다."""
    fake_triple = NormalizedTriple("Stanford University", "OFFERS", "CS", 0.92)
    mock_analyzer = MagicMock()
    mock_analyzer.extract_triples.return_value = [fake_triple]
    mock_analyzer_cls.return_value = mock_analyzer

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    result = collector._extract_triples_from_page(
        html=SAMPLE_HTML,
        school_name="Stanford University",
        source_url="https://stanford.edu/career",
    )

    assert len(result) == 1
    assert result[0]["head"] == "Stanford University"
    assert result[0]["relation"] == "OFFERS"
    assert result[0]["tail"] == "CS"
    mock_analyzer.extract_triples.assert_called_once()


@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_extract_triples_analyzer_exception_returns_empty(
    mock_analyzer_cls, schools_file, output_file
):
    """analyzer.extract_triples가 예외를 던지면 빈 리스트로 복구합니다."""
    mock_analyzer = MagicMock()
    mock_analyzer.extract_triples.side_effect = RuntimeError("API 장애")
    mock_analyzer_cls.return_value = mock_analyzer

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    result = collector._extract_triples_from_page(
        html=SAMPLE_HTML,
        school_name="Stanford University",
        source_url="https://stanford.edu/career",
    )

    assert result == []


# ---------------------------------------------------------------------------
# _collect_for_school 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_collect_for_school_missing_info(mock_analyzer_cls, schools_file, output_file):
    """name/website 없는 학교는 skipped=True 반환합니다."""
    mock_analyzer_cls.return_value = MagicMock()
    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")

    result = collector._collect_for_school({"name": "", "website": "https://x.edu"})

    assert result["routing"]["skipped"] is True
    assert "부족" in result["routing"]["reason"]


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_collect_for_school_empty_homepage(mock_analyzer_cls, mock_crawler_cls, schools_file, output_file):
    """홈페이지 응답이 비어 있으면 skipped=True 반환합니다."""
    mock_analyzer_cls.return_value = MagicMock()
    mock_crawler = MagicMock()
    mock_crawler.__enter__ = lambda s: s
    mock_crawler.__exit__ = MagicMock(return_value=False)
    mock_crawler.fetch.return_value = None  # 응답 없음
    mock_crawler.base_url = "https://stanford.edu"
    mock_crawler_cls.return_value = mock_crawler

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    result = collector._collect_for_school(SAMPLE_SCHOOLS[0])

    assert result["routing"]["skipped"] is True
    assert "응답 없음" in result["routing"]["reason"]


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_collect_for_school_success(mock_analyzer_cls, mock_crawler_cls, schools_file, output_file):
    """정상 수집 시 triples 리스트가 채워지고 skipped=False입니다."""
    fake_triple = NormalizedTriple("Stanford University", "HIRES_FROM", "Google", 0.9)
    mock_analyzer = MagicMock()
    mock_analyzer.extract_triples.return_value = [fake_triple]
    mock_analyzer_cls.return_value = mock_analyzer

    homepage_resp = MagicMock()
    homepage_resp.text = SAMPLE_HTML
    career_resp = MagicMock()
    career_resp.text = "<html><body>Career page content</body></html>"

    mock_crawler = MagicMock()
    mock_crawler.__enter__ = lambda s: s
    mock_crawler.__exit__ = MagicMock(return_value=False)
    mock_crawler.fetch.side_effect = [homepage_resp] + [career_resp] * 10
    mock_crawler.ssl_error_detected = False
    mock_crawler.base_url = "https://stanford.edu"
    mock_crawler_cls.return_value = mock_crawler

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    result = collector._collect_for_school(SAMPLE_SCHOOLS[0])

    assert result["routing"].get("skipped") is not True
    assert len(result["triples"]) > 0


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_collect_for_school_exception_is_caught(mock_analyzer_cls, mock_crawler_cls, schools_file, output_file):
    """예외가 발생해도 skipped로 처리되고 propagate되지 않습니다."""
    mock_analyzer_cls.return_value = MagicMock()
    mock_crawler_cls.side_effect = ConnectionError("Network error")

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    result = collector._collect_for_school(SAMPLE_SCHOOLS[0])

    assert result["routing"]["skipped"] is True
    assert "예외" in result["routing"]["reason"]


# ---------------------------------------------------------------------------
# run() 테스트
# ---------------------------------------------------------------------------

@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_run_creates_output_file(mock_analyzer_cls, mock_crawler_cls, schools_file, output_file):
    """run() 후 output JSONL 파일이 생성됩니다."""
    mock_analyzer_cls.return_value = MagicMock()
    mock_crawler_cls.side_effect = ConnectionError("mock error")  # 모두 스킵처리

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    summary = collector.run()

    assert output_file.exists()
    assert summary["schools_processed"] == 2


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_run_with_limit(mock_analyzer_cls, mock_crawler_cls, tmp_path, output_file):
    """limit 파라미터가 적용되어 일부 학교만 처리됩니다."""
    many_schools = [
        {"name": f"School {i}", "website": f"https://school{i}.edu"}
        for i in range(5)
    ]
    schools_file = _make_schools_json(tmp_path, many_schools)
    mock_analyzer_cls.return_value = MagicMock()
    mock_crawler_cls.side_effect = ConnectionError("mock")

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    summary = collector.run(limit=2)

    assert summary["schools_processed"] == 2


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_run_output_is_valid_jsonl(mock_analyzer_cls, mock_crawler_cls, schools_file, output_file):
    """출력 파일의 각 줄이 유효한 JSON입니다."""
    mock_analyzer_cls.return_value = MagicMock()
    mock_crawler_cls.side_effect = ConnectionError("mock error")

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    collector.run()

    lines = output_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2  # 2개 학교
    for line in lines:
        parsed = json.loads(line)
        assert "school_name" in parsed
        assert "triples" in parsed
        assert "routing" in parsed


@pytest.mark.unit
@patch("src.services.auto_triple_collector.SchoolCrawler")
@patch("src.services.auto_triple_collector.WebPageAnalyzer")
def test_run_summary_counts_triples(mock_analyzer_cls, mock_crawler_cls, tmp_path):
    """summary의 triples_collected가 실제 수집 수를 반영합니다."""
    fake_triple = NormalizedTriple("School A", "OFFERS", "CS", 0.9)
    mock_analyzer = MagicMock()
    mock_analyzer.extract_triples.return_value = [fake_triple]
    mock_analyzer_cls.return_value = mock_analyzer

    homepage_resp = MagicMock()
    homepage_resp.text = SAMPLE_HTML
    page_resp = MagicMock()
    page_resp.text = "<html><body>Program page</body></html>"

    mock_crawler = MagicMock()
    mock_crawler.__enter__ = lambda s: s
    mock_crawler.__exit__ = MagicMock(return_value=False)
    mock_crawler.fetch.side_effect = [homepage_resp] + [page_resp] * 20
    mock_crawler.ssl_error_detected = False
    mock_crawler.base_url = "https://schoola.edu"
    mock_crawler_cls.return_value = mock_crawler

    schools_file = _make_schools_json(tmp_path, [
        {"name": "School A", "website": "https://schoola.edu"},
    ])
    output_file = tmp_path / "out.jsonl"

    collector = AutoTripleCollector(schools_file, output_path=output_file, gemini_api_key="k")
    summary = collector.run()

    assert summary["schools_with_triples"] == 1
    assert summary["triples_collected"] > 0
