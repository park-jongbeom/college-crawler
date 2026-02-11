import pytest

from src.integrations.college_scorecard_client import CollegeScorecardClient


class _FakeResp:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


@pytest.mark.unit
def test_fetch_school_stats_selects_best_match_and_normalizes(monkeypatch):
    payload = {
        "metadata": {"total": 2, "page": 0, "per_page": 5},
        "results": [
            {
                "id": 123,
                "school": {"name": "Some University", "state": "CA", "city": "LA"},
                "latest": {
                    "admissions": {"admission_rate": {"overall": 0.12}},
                    "completion": {"completion_rate_4yr_150nt": 0.55},
                    "earnings": {"6_yrs_after_entry": 52000},
                },
            },
            {
                "id": 999,
                "school": {"name": "Exact Match University", "state": "CA", "city": "LA"},
                "latest": {
                    "admissions": {"admission_rate": {"overall": 0.5}},
                    "completion": {"completion_rate_4yr_150nt": 0.6},
                    "earnings": {"6_yrs_after_entry": 61000},
                },
            },
        ],
    }

    client = CollegeScorecardClient(api_key="test-key", max_retries=1)

    def fake_get(url, params, timeout):
        return _FakeResp(200, payload)

    monkeypatch.setattr(client._session, "get", fake_get)

    stats = client.fetch_school_stats("Exact Match University", state="CA", city="LA")
    assert stats is not None
    assert stats.scorecard_id == 999
    assert stats.acceptance_rate_percent == 50
    assert stats.graduation_rate_percent == 60
    assert stats.average_salary_usd == 61000


@pytest.mark.unit
def test_fetch_school_stats_handles_429_with_retry(monkeypatch):
    client = CollegeScorecardClient(api_key="test-key", max_retries=2)

    calls = {"n": 0}

    def fake_get(url, params, timeout):
        calls["n"] += 1
        if calls["n"] == 1:
            return _FakeResp(429, {})
        return _FakeResp(200, {"results": []})

    monkeypatch.setattr(client._session, "get", fake_get)
    monkeypatch.setattr("src.integrations.college_scorecard_client.time.sleep", lambda *_: None)

    stats = client.fetch_school_stats("Any University", state="CA")
    assert stats is None
    assert calls["n"] == 2

