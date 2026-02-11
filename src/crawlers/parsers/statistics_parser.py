"""
College Scorecard 등 외부 소스의 정량 지표를 정규화하는 파서.

- 크롤러 파이프라인은 실패하더라도 계속 진행되어야 하므로, 파서는 예외를 던지지 않고 None을 반환하는 방식을 우선합니다.
"""

from __future__ import annotations

import re
from typing import Any, Optional


_MONEY_RE = re.compile(r"[^0-9.]")


class StatisticsParser:
    """정량 지표(퍼센트/금액 등) 정규화 유틸."""

    @staticmethod
    def parse_ratio_to_percent(value: Any) -> Optional[int]:
        """
        비율/퍼센트 입력을 0~100 정수(%)로 정규화합니다.

        허용 입력 예:
        - 0.54, "0.54"  -> 54
        - 54, "54", "54%" -> 54
        - None, "", "N/A" -> None
        """
        if value is None:
            return None

        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return StatisticsParser._ratio_number_to_percent(value)

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            if s.lower() in {"n/a", "na", "null", "none", "-"}:
                return None
            s = s.replace("%", "").strip()
            try:
                num = float(s)
            except ValueError:
                return None
            return StatisticsParser._ratio_number_to_percent(num)

        return None

    @staticmethod
    def _ratio_number_to_percent(num: float) -> Optional[int]:
        if num != num:  # NaN
            return None
        if num < 0:
            return None

        # Scorecard는 0~1 ratio로 제공되는 경우가 많습니다.
        if 0 <= num <= 1:
            percent = round(num * 100)
        elif num <= 100:
            # 1보다 큰 소수(예: 1.54)는 ratio 오입력일 가능성이 높아 방어적으로 거부합니다.
            # (DB에는 정수 %로 저장하므로, 여기서는 명확한 케이스만 허용)
            if 1 < num < 2 and abs(num - round(num)) > 1e-9:
                return None
            percent = round(num)
        else:
            return None

        if percent < 0 or percent > 100:
            return None
        return int(percent)

    @staticmethod
    def parse_money_to_int(value: Any) -> Optional[int]:
        """
        금액/수입 입력을 정수(달러)로 정규화합니다.

        허용 입력 예:
        - 52000 -> 52000
        - 52000.0 -> 52000
        - "$52,000" -> 52000
        - None, "", "N/A" -> None
        """
        if value is None:
            return None
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value >= 0 else None
        if isinstance(value, float):
            if value != value or value < 0:
                return None
            return int(round(value))

        if isinstance(value, str):
            s = value.strip()
            if not s:
                return None
            if s.lower() in {"n/a", "na", "null", "none", "-"}:
                return None
            # 음수 방지: 정규화 과정에서 '-'가 제거되어 양수로 바뀌는 것을 막습니다.
            if s.startswith("-"):
                return None
            cleaned = _MONEY_RE.sub("", s)
            if not cleaned:
                return None
            try:
                num = float(cleaned)
            except ValueError:
                return None
            if num < 0:
                return None
            return int(round(num))

        return None

