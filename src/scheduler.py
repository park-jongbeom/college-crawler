"""
파이썬 기반 크롤링 스케줄러 (cron 불필요)

- 컨테이너에서 root/cron 데몬 없이 동작하도록 설계
- APScheduler로 "매일 KST 새벽 2시" 실행
- 옵션으로 컨테이너 시작 시 1회 즉시 실행
"""

from __future__ import annotations

import os
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from src.main import crawl_all_schools
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _env_bool(key: str, default: bool) -> bool:
    value = os.getenv(key)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(key: str, default: int) -> int:
    value = os.getenv(key)
    if value is None or not value.strip():
        return default
    try:
        return int(value.strip())
    except ValueError:
        logger.warning(f"환경변수 {key} 값이 정수가 아님: {value!r} (default={default})")
        return default


def build_daily_trigger(timezone: str, hour: int, minute: int) -> CronTrigger:
    """매일 특정 시각 실행 트리거를 생성합니다."""
    tz = pytz.timezone(timezone)
    return CronTrigger(hour=hour, minute=minute, timezone=tz)


def run_crawl_once(limit: Optional[int] = None) -> None:
    """전체 학교 크롤링을 1회 실행합니다."""
    project_root = Path(__file__).parent.parent
    json_file = project_root / "data" / "schools_initial.json"

    logger.info("크롤링 실행 시작")
    logger.info(f"- schools_file={json_file}")
    logger.info(f"- limit={limit}")
    started_at = datetime.utcnow()

    crawl_all_schools(json_file=json_file, limit=limit)

    elapsed = (datetime.utcnow() - started_at).total_seconds()
    logger.info(f"크롤링 실행 종료 (elapsed_seconds={elapsed:.1f})")


def main() -> None:
    """
    스케줄러 진입점.

    환경변수:
    - SCHEDULER_TIMEZONE (default: Asia/Seoul)
    - SCHEDULER_DAILY_HOUR (default: 2)
    - SCHEDULER_DAILY_MINUTE (default: 0)
    - SCHEDULER_RUN_ON_STARTUP (default: true)
    - CRAWL_LIMIT (default: unset)
    """

    timezone = os.getenv("SCHEDULER_TIMEZONE", "Asia/Seoul")
    hour = _env_int("SCHEDULER_DAILY_HOUR", 2)
    minute = _env_int("SCHEDULER_DAILY_MINUTE", 0)
    run_on_startup = _env_bool("SCHEDULER_RUN_ON_STARTUP", True)
    crawl_limit_env = os.getenv("CRAWL_LIMIT")
    crawl_limit = int(crawl_limit_env) if crawl_limit_env and crawl_limit_env.isdigit() else None

    tz = pytz.timezone(timezone)
    trigger = build_daily_trigger(timezone=timezone, hour=hour, minute=minute)

    shutdown_event = threading.Event()
    scheduler = BlockingScheduler(timezone=tz)

    def _handle_signal(signum: int, _frame) -> None:
        logger.warning(f"종료 신호 수신: {signum}. 스케줄러를 종료합니다.")
        shutdown_event.set()
        try:
            scheduler.shutdown(wait=False)
        except Exception as e:
            logger.warning(f"스케줄러 종료 중 예외(무시): {e}")

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    def _job_wrapper() -> None:
        if shutdown_event.is_set():
            return
        try:
            run_crawl_once(limit=crawl_limit)
        except Exception as e:
            # 예외를 삼켜야 스케줄러 프로세스가 죽지 않습니다.
            logger.exception(f"스케줄링 크롤링 실행 중 예외: {e}")

    scheduler.add_job(
        _job_wrapper,
        trigger=trigger,
        id="daily_crawl",
        name="daily_crawl",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60 * 60,  # 1시간
    )

    # APScheduler 버전에 따라 Job.next_run_time 속성이 없을 수 있어,
    # trigger로 다음 실행 시각을 직접 계산합니다.
    now = datetime.now(tz)
    next_run = trigger.get_next_fire_time(previous_fire_time=None, now=now)
    logger.info("스케줄러 시작")
    logger.info(f"- timezone={timezone}")
    logger.info(f"- daily_time={hour:02d}:{minute:02d}")
    logger.info(f"- run_on_startup={run_on_startup}")
    logger.info(f"- next_run_time={next_run.isoformat() if next_run else None}")

    if run_on_startup:
        _job_wrapper()

    scheduler.start()


if __name__ == "__main__":
    main()

