"""
College Scorecard 기반 메타데이터 보강 서비스.

원칙:
- enrichment 실패는 크롤링 실패로 간주하지 않습니다(스킵 후 계속 진행).
- DB 업데이트는 값이 있는 필드만 포함합니다(None은 제외).
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from src.integrations.college_scorecard_client import CollegeScorecardClient, ScorecardStats
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ScorecardEnrichmentService:
    def __init__(self, client: Optional[CollegeScorecardClient] = None) -> None:
        self._client = client or CollegeScorecardClient()

    def enrich_school(
        self,
        school_name: str,
        state: Optional[str] = None,
        city: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Scorecard에서 메타데이터를 가져와 `schools` 업데이트용 payload와 audit용 메타를 반환합니다.

        Returns:
          - update_fields: `School` 컬럼에 바로 매핑 가능한 키/값(dict)
          - audit_meta: 감사로그/디버깅에 도움이 되는 출처/원본 요약(dict)
        """
        try:
            stats = self._client.fetch_school_stats(school_name=school_name, state=state, city=city)
            if not stats:
                return {}, {"scorecard": {"matched": False}}

            update = self._build_update_fields(stats)
            audit = {
                "scorecard": {
                    "matched": True,
                    "scorecard_id": stats.scorecard_id,
                    "matched_name": stats.school_name,
                    "matched_state": stats.state,
                    "matched_city": stats.city,
                    "normalized": {
                        "acceptance_rate_percent": stats.acceptance_rate_percent,
                        "graduation_rate_percent": stats.graduation_rate_percent,
                        "average_salary_usd": stats.average_salary_usd,
                    },
                }
            }
            return update, audit
        except Exception as e:
            # 어떤 예외든 enrichment 단계에서 흡수하고 빈 값으로 반환합니다.
            logger.warning(f"Scorecard enrichment 실패(스킵): {school_name} - {e}")
            return {}, {"scorecard": {"matched": False, "error": str(e)}}

    @staticmethod
    def _build_update_fields(stats: ScorecardStats) -> Dict[str, Any]:
        update: Dict[str, Any] = {}
        if stats.acceptance_rate_percent is not None:
            update["acceptance_rate"] = stats.acceptance_rate_percent
        if stats.graduation_rate_percent is not None:
            update["graduation_rate"] = stats.graduation_rate_percent
        if stats.average_salary_usd is not None:
            update["average_salary"] = stats.average_salary_usd

        # None 값은 제외(기존 유효값 덮어쓰기 방지)
        return {k: v for k, v in update.items() if v is not None}

