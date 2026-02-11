"""
실패 사이트 기록/조회 유틸리티
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class FailedSiteManager:
    """실패한 사이트를 파일로 기록하고 스킵 여부를 판단합니다."""

    def __init__(self, file_path: str = "data/failed_sites.json") -> None:
        self.file_path = Path(__file__).parent.parent.parent / file_path
        self._ensure_file_exists()

    def _default_payload(self) -> dict[str, Any]:
        return {
            "ssl_verification_failed": [],
            "robots_blocked": [],
            "timeout_failed": [],
        }

    def _ensure_file_exists(self) -> None:
        if self.file_path.exists():
            return
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._save(self._default_payload())

    def _load(self) -> dict[str, Any]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return self._default_payload()
            for key in ("ssl_verification_failed", "robots_blocked", "timeout_failed"):
                data.setdefault(key, [])
            return data
        except (FileNotFoundError, json.JSONDecodeError):
            return self._default_payload()

    def _save(self, data: dict[str, Any]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def add_ssl_failure(
        self,
        name: str,
        website: str,
        error_message: str,
        note: str = "",
    ) -> None:
        """SSL 검증 실패 사이트를 추가/갱신합니다."""
        data = self._load()
        entries = data["ssl_verification_failed"]
        now = self._now_iso()
        existing = next((item for item in entries if item.get("website") == website), None)

        if existing:
            existing["last_checked_at"] = now
            existing["retry_count"] = int(existing.get("retry_count", 0)) + 1
            existing["error_message"] = error_message
            existing["skip"] = True
            if note:
                existing["note"] = note
        else:
            entries.append(
                {
                    "name": name,
                    "website": website,
                    "error_type": "SSL_CERTIFICATE_VERIFY_FAILED",
                    "error_message": error_message,
                    "first_failed_at": now,
                    "last_checked_at": now,
                    "retry_count": 1,
                    "skip": True,
                    "note": note or "SSL 인증서 검증 실패 - 사이트 확인 필요",
                }
            )

        self._save(data)

    def should_skip(self, website: str) -> tuple[bool, str | None]:
        """해당 사이트를 스킵해야 하는지 반환합니다."""
        data = self._load()
        for item in data["ssl_verification_failed"]:
            if item.get("website") == website and bool(item.get("skip", False)):
                failed_at = item.get("first_failed_at", "unknown")
                return True, f"SSL 검증 실패 이력(최초: {failed_at})"
        return False, None

    def get_failed_sites(self, category: str = "ssl_verification_failed") -> list[dict[str, Any]]:
        """실패 사이트 목록을 반환합니다."""
        data = self._load()
        sites = data.get(category, [])
        if isinstance(sites, list):
            return sites
        return []


failed_site_manager = FailedSiteManager()
