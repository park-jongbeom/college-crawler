import pytest

from src.integrations.college_scorecard_client import ScorecardStats
from src.services.scorecard_enrichment_service import ScorecardEnrichmentService


class _FakeClient:
    def __init__(self, stats):
        self._stats = stats

    def fetch_school_stats(self, school_name: str, state=None, city=None):
        return self._stats


@pytest.mark.unit
def test_enrich_school_returns_update_fields_and_audit_meta():
    stats = ScorecardStats(
        scorecard_id=111,
        school_name="X University",
        state="CA",
        city="LA",
        acceptance_rate_percent=25,
        graduation_rate_percent=60,
        average_salary_usd=50000,
    )

    svc = ScorecardEnrichmentService(client=_FakeClient(stats))
    update, audit = svc.enrich_school("X University", state="CA", city="LA")

    assert update == {"acceptance_rate": 25, "graduation_rate": 60, "average_salary": 50000}
    assert audit["scorecard"]["matched"] is True
    assert audit["scorecard"]["scorecard_id"] == 111


@pytest.mark.unit
def test_enrich_school_handles_no_match():
    svc = ScorecardEnrichmentService(client=_FakeClient(None))
    update, audit = svc.enrich_school("Y University")
    assert update == {}
    assert audit["scorecard"]["matched"] is False

