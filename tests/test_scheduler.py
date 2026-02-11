import datetime

import pytest
import pytz

from src.scheduler import build_daily_trigger


@pytest.mark.unit
def test_build_daily_trigger_next_fire_time_asia_seoul():
    tz = pytz.timezone("Asia/Seoul")
    trigger = build_daily_trigger(timezone="Asia/Seoul", hour=2, minute=0)

    now = tz.localize(datetime.datetime(2026, 2, 11, 1, 0, 0))
    next_fire = trigger.get_next_fire_time(previous_fire_time=None, now=now)

    assert next_fire is not None
    assert next_fire.tzinfo is not None
    assert next_fire == tz.localize(datetime.datetime(2026, 2, 11, 2, 0, 0))


@pytest.mark.unit
def test_build_daily_trigger_rollover_to_next_day():
    tz = pytz.timezone("Asia/Seoul")
    trigger = build_daily_trigger(timezone="Asia/Seoul", hour=2, minute=0)

    now = tz.localize(datetime.datetime(2026, 2, 11, 2, 0, 1))
    next_fire = trigger.get_next_fire_time(previous_fire_time=None, now=now)

    assert next_fire == tz.localize(datetime.datetime(2026, 2, 12, 2, 0, 0))

