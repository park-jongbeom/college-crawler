import pytest

from src.crawlers.parsers.statistics_parser import StatisticsParser


@pytest.mark.unit
def test_parse_ratio_to_percent_accepts_ratio_float():
    assert StatisticsParser.parse_ratio_to_percent(0.54) == 54


@pytest.mark.unit
def test_parse_ratio_to_percent_accepts_percent_int():
    assert StatisticsParser.parse_ratio_to_percent(54) == 54


@pytest.mark.unit
def test_parse_ratio_to_percent_accepts_string_percent():
    assert StatisticsParser.parse_ratio_to_percent("54%") == 54


@pytest.mark.unit
def test_parse_ratio_to_percent_rejects_out_of_range():
    assert StatisticsParser.parse_ratio_to_percent(1.54) is None
    assert StatisticsParser.parse_ratio_to_percent(154) is None
    assert StatisticsParser.parse_ratio_to_percent(-1) is None


@pytest.mark.unit
def test_parse_ratio_to_percent_handles_empty_and_na():
    assert StatisticsParser.parse_ratio_to_percent(None) is None
    assert StatisticsParser.parse_ratio_to_percent("") is None
    assert StatisticsParser.parse_ratio_to_percent("N/A") is None


@pytest.mark.unit
def test_parse_money_to_int_accepts_string_money():
    assert StatisticsParser.parse_money_to_int("$52,000") == 52000


@pytest.mark.unit
def test_parse_money_to_int_handles_none_and_invalid():
    assert StatisticsParser.parse_money_to_int(None) is None
    assert StatisticsParser.parse_money_to_int("") is None
    assert StatisticsParser.parse_money_to_int("N/A") is None
    assert StatisticsParser.parse_money_to_int("-100") is None

