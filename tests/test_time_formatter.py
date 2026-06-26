import pytest
from src.utils.time_formatter import format_hindenburg_time

def test_format_hindenburg_time_under_sixty():
    assert format_hindenburg_time(0.0) == "00.000"
    assert format_hindenburg_time(10.0) == "10.000"
    assert format_hindenburg_time(19.48) == "19.480"
    assert format_hindenburg_time(59.9) == "59.900"

def test_format_hindenburg_time_over_sixty():
    assert format_hindenburg_time(60.0) == "01:00.000"
    assert format_hindenburg_time(90.0) == "01:30.000"
    assert format_hindenburg_time(264.199) == "04:24.199"
    assert format_hindenburg_time(1564.016) == "26:04.016"

def test_format_hindenburg_time_over_one_hour():
    assert format_hindenburg_time(3600.0) == "1:00:00.000"
    assert format_hindenburg_time(4262.061) == "1:11:02.061"
    assert format_hindenburg_time(7200.5) == "2:00:00.500"

def test_format_hindenburg_time_negative():
    with pytest.raises(ValueError):
        format_hindenburg_time(-1.0)

def test_format_hindenburg_time_rounding_edge():
    # 59.9999 rounded to 3 decimals carries over to 60.000, which is over 60s -> "01:00.000"
    assert format_hindenburg_time(59.9999) == "01:00.000"
