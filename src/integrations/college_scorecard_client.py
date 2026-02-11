"""
College Scorecard API 클라이언트.

주의:
- API 키는 환경변수 `COLLEGE_SCORECARD_API`로만 주입합니다(코드/로그에 노출 금지).
- 실패하더라도 크롤링 파이프라인이 중단되지 않도록, 본 클라이언트는 예외를 최소화하고 None을 반환하는 형태를 지향합니다.

공식 문서:
- https://collegescorecard.ed.gov/data/api-documentation/
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

import requests

from src.crawlers.parsers.statistics_parser import StatisticsParser
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


SCORECARD_BASE_URL = "https://api.data.gov/ed/collegescorecard/v1/schools"


@dataclass(frozen=True)
class ScorecardStats:
    """`schools` 업데이트에 필요한 최소 통계 필드 묶음."""

    scorecard_id: Optional[int]
    school_name: Optional[str]
    state: Optional[str]
    city: Optional[str]
    acceptance_rate_percent: Optional[int]
    graduation_rate_percent: Optional[int]
    average_salary_usd: Optional[int]


class CollegeScorecardClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout_seconds: int = 15,
        max_retries: int = 3,
        base_url: str = SCORECARD_BASE_URL,
    ) -> None:
        self._api_key = (api_key or os.getenv("COLLEGE_SCORECARD_API") or "").strip() or None
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._base_url = base_url
        self._session = requests.Session()
        self._cache: Dict[Tuple[str, Optional[str], Optional[str]], Optional[ScorecardStats]] = {}

    def is_enabled(self) -> bool:
        return bool(self._api_key)

    def fetch_school_stats(
        self,
        school_name: str,
        state: Optional[str] = None,
        city: Optional[str] = None,
        per_page: int = 5,
    ) -> Optional[ScorecardStats]:
        """
        학교 이름(+옵션 state/city)로 Scorecard 검색 후, 가장 적합한 1개 레코드를 정규화하여 반환합니다.
        """
        name_key = (school_name or "").strip()
        if not name_key:
            return None

        cache_key = (name_key.lower(), (state or "").strip() or None, (city or "").strip() or None)
        if cache_key in self._cache:
            return self._cache[cache_key]

        if not self._api_key:
            logger.info("COLLEGE_SCORECARD_API 미설정: Scorecard enrichment를 건너뜁니다.")
            self._cache[cache_key] = None
            return None

        params: Dict[str, Any] = {
            "api_key": self._api_key,
            "school.name": name_key,
            "per_page": per_page,
            "page": 0,
            # 필요한 하위 오브젝트만 가져옵니다(응답 크기/파싱 안정성).
            "fields": "id,school,latest.admissions,latest.completion,latest.earnings",
            "keys_nested": "true",
        }
        if state:
            params["school.state"] = state
        if city:
            params["school.city"] = city

        data = self._get_with_retry(params)
        results = (data or {}).get("results") or []
        best = self._select_best_match(name_key, results, state=state, city=city)
        stats = self._extract_stats(best)
        self._cache[cache_key] = stats
        return stats

    def _get_with_retry(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        last_error: Optional[str] = None
        for attempt in range(1, self._max_retries + 1):
            try:
                resp = self._session.get(self._base_url, params=params, timeout=self._timeout_seconds)
                if resp.status_code == 429:
                    # 레이트리밋: 짧게 백오프 후 재시도
                    wait = attempt * 2
                    logger.warning(f"Scorecard 429(rate limit). {wait}s 후 재시도합니다(시도 {attempt}/{self._max_retries}).")
                    time.sleep(wait)
                    continue

                if resp.status_code >= 400:
                    # 키/요청 URL 노출 방지: params 전체를 로깅하지 않습니다.
                    last_error = f"HTTP {resp.status_code}"
                    logger.warning(f"Scorecard 요청 실패: {last_error}")
                    return None

                return resp.json()
            except requests.RequestException as e:
                last_error = str(e)
                wait = attempt * 2
                logger.warning(f"Scorecard 요청 예외: {e} (시도 {attempt}/{self._max_retries}), {wait}s 후 재시도")
                time.sleep(wait)
            except ValueError as e:
                # JSON 파싱 실패
                last_error = str(e)
                logger.warning(f"Scorecard 응답 JSON 파싱 실패: {e}")
                return None

        logger.warning(f"Scorecard 요청 최종 실패: {last_error}")
        return None

    @staticmethod
    def _normalize_name(name: str) -> str:
        return "".join(ch.lower() for ch in name if ch.isalnum())

    def _select_best_match(
        self,
        query_name: str,
        results: list[dict],
        state: Optional[str],
        city: Optional[str],
    ) -> Optional[dict]:
        if not results:
            return None

        qn = self._normalize_name(query_name)

        def score(item: dict) -> int:
            school = (item or {}).get("school") or {}
            name = school.get("name") or ""
            sn = self._normalize_name(str(name))
            s = 0
            if sn == qn:
                s += 100
            elif qn and sn and (qn in sn or sn in qn):
                s += 60

            if state and (school.get("state") == state):
                s += 10
            if city and (school.get("city") == city):
                s += 5
            return s

        return max(results, key=score)

    @staticmethod
    def _extract_stats(item: Optional[dict]) -> Optional[ScorecardStats]:
        if not item:
            return None

        school = (item.get("school") or {}) if isinstance(item, dict) else {}
        latest = (item.get("latest") or {}) if isinstance(item, dict) else {}

        admissions = latest.get("admissions") or {}
        completion = latest.get("completion") or {}
        earnings = latest.get("earnings") or {}

        admission_rate = StatisticsParser.parse_ratio_to_percent(admissions.get("admission_rate", {}).get("overall"))
        completion_4yr = StatisticsParser.parse_ratio_to_percent(completion.get("completion_rate_4yr_150nt"))
        completion_2yr = StatisticsParser.parse_ratio_to_percent(completion.get("completion_rate_2yr_150nt"))
        graduation_rate = completion_4yr if completion_4yr is not None else completion_2yr

        # 자료의 버전/코호트에 따라 earnings 필드가 비어있을 수 있으므로 방어적으로 처리합니다.
        salary = StatisticsParser.parse_money_to_int(earnings.get("6_yrs_after_entry"))

        scorecard_id = item.get("id")
        try:
            scorecard_id_int = int(scorecard_id) if scorecard_id is not None else None
        except (TypeError, ValueError):
            scorecard_id_int = None

        return ScorecardStats(
            scorecard_id=scorecard_id_int,
            school_name=school.get("name"),
            state=school.get("state"),
            city=school.get("city"),
            acceptance_rate_percent=admission_rate,
            graduation_rate_percent=graduation_rate,
            average_salary_usd=salary,
        )

