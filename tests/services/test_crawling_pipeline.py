"""CrawlingPipeline 실패 시나리오(RED) 테스트."""

from unittest.mock import MagicMock, patch

import pytest

from src.services.crawling_pipeline import CrawlingPipeline


@pytest.fixture
def schools_list():
    return [
        {"name": "School Alpha", "website": "https://alpha.edu"},
        {"name": "School Beta", "website": "https://beta.edu"},
    ]


@pytest.mark.unit
def test_pipeline_skips_collector_when_urlfinder_returns_none(schools_list, tmp_path):
    """UrlFinder가 빈 URL 집합을 반환하면 AutoTripleCollector가 호출되지 않습니다."""
    url_finder = MagicMock()
    url_finder.find_target_urls.return_value = []
    collector_cls = MagicMock()

    pipeline = CrawlingPipeline(
        url_finder=url_finder,
        collector_cls=collector_cls,
        status_path=tmp_path / "status.json",
        max_workers=1,
    )

    pipeline.run(schools_list)

    collector_cls.assert_not_called()


@pytest.mark.unit
def test_pipeline_continues_when_collector_raises(schools_list, tmp_path):
    """Collector 예외가 발생해도 다음 학교로 재시도합니다."""
    url_finder = MagicMock()
    url_finder.find_target_urls.side_effect = [
        ["https://alpha.edu/career"],
        ["https://beta.edu/program"],
    ]

    first_collector = MagicMock()
    second_collector = MagicMock()
    first_collector.run.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "boom")

    collector_cls = MagicMock(side_effect=[first_collector, second_collector])

    pipeline = CrawlingPipeline(
        url_finder=url_finder,
        collector_cls=collector_cls,
        status_path=tmp_path / "status.json",
        max_workers=1,
    )

    pipeline.run(schools_list)

    assert second_collector.run.called
    assert collector_cls.call_count == 2


@pytest.mark.unit
@patch("src.services.crawling_pipeline.logger.warning")
def test_pipeline_warns_when_no_triples(mock_warning, schools_list, tmp_path):
    """수집한 Triple이 없으면 경고 로그를 남깁니다."""
    url_finder = MagicMock()
    url_finder.find_target_urls.return_value = ["https://alpha.edu/success"]

    collector = MagicMock()
    collector.run.return_value = {"triples_collected": 0}
    collector_cls = MagicMock(return_value=collector)

    pipeline = CrawlingPipeline(
        url_finder=url_finder,
        collector_cls=collector_cls,
        status_path=tmp_path / "status.json",
        max_workers=1,
    )

    pipeline.run([schools_list[0]])

    assert mock_warning.called
