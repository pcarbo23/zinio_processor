import pytest
from src.utils.time_formatter import format_hindenburg_time

def test_format_hindenburg_time_under_sixty():
    assert format_hindenburg_time(0.0) == "00.000"
    assert format_hindenburg_time(10000.0) == "10.000"
    assert format_hindenburg_time(19480.0) == "19.480"
    assert format_hindenburg_time(59900.0) == "59.900"

def test_format_hindenburg_time_over_sixty():
    assert format_hindenburg_time(60000.0) == "01:00.000"
    assert format_hindenburg_time(90000.0) == "01:30.000"
    assert format_hindenburg_time(264199.0) == "04:24.199"
    assert format_hindenburg_time(1564016.0) == "26:04.016"

def test_format_hindenburg_time_over_one_hour():
    assert format_hindenburg_time(3600000.0) == "1:00:00.000"
    assert format_hindenburg_time(4262061.0) == "1:11:02.061"
    assert format_hindenburg_time(7200500.0) == "2:00:00.500"

def test_format_hindenburg_time_negative():
    with pytest.raises(ValueError):
        format_hindenburg_time(-1000.0)

def test_format_hindenburg_time_rounding_edge():
    # 59999.9 rounded to nearest millisecond is 60000 -> "01:00.000"
    assert format_hindenburg_time(59999.9) == "01:00.000"

