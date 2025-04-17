import pytest
from datetime import datetime, date, time, timezone
import json
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

# Import the classes and enums from your module
# Assuming the module is named "utilities_module"
from app.utils.utilities import (
    Utilities,
    TimeDeltaType,
    TimeReturnType
)


class MockBaseClass:
    pass


class MockChildClass1(MockBaseClass):
    pass


class MockChildClass2(MockBaseClass):
    pass


class NotChildClass:
    pass


# Create a mock module for testing get_classes_from_module
mock_module = MagicMock()
mock_module.__name__ = "mock_module"
sys.modules["mock_module"] = mock_module
mock_module.MockChildClass1 = MockChildClass1
mock_module.MockChildClass2 = MockChildClass2
mock_module.NotChildClass = NotChildClass


class TestUtilities:

    def test_get_classes_from_module(self):
        # Test with mock module
        result = Utilities.get_classes_from_module(
            sys.modules["mock_module"], MockBaseClass)

        # Should contain both child classes
        assert len(result) == 2
        assert "MockChildClass1" in result
        assert "MockChildClass2" in result
        assert result["MockChildClass1"] == MockChildClass1
        assert result["MockChildClass2"] == MockChildClass2

        # Should not contain base class or non-child class
        assert "MockBaseClass" not in result
        assert "NotChildClass" not in result

    def test_get_array_from_str_with_comma_delimiter(self):
        # Test with comma delimiter
        result = Utilities.get_array_from_str("a,b,c")
        assert result == ["a", "b", "c"]

        # Test with empty string
        result = Utilities.get_array_from_str("")
        assert result == [""]

        # Test with None
        result = Utilities.get_array_from_str(None)
        assert result is None

    def test_get_array_from_str_with_custom_delimiter(self):
        # Test with custom delimiter
        result = Utilities.get_array_from_str("a|b|c", delimiter="|")
        assert result == ["a", "b", "c"]

    def test_get_array_from_str_with_json(self):
        # Test with valid JSON array
        json_str = '["a", "b", "c"]'
        result = Utilities.get_array_from_str(json_str, delimiter="json")
        assert result == ["a", "b", "c"]

        # Test with valid JSON object
        json_obj = '{"key1": "value1", "key2": "value2"}'
        result = Utilities.get_array_from_str(json_obj, delimiter="json")
        assert result == {"key1": "value1", "key2": "value2"}

        # Test with invalid JSON
        with patch('builtins.print') as mock_print:
            result = Utilities.get_array_from_str(
                "invalid json", delimiter="json")
            mock_print.assert_called_once()
            assert "Error decoding JSON string" in mock_print.call_args[0][0]

    def test_ms_to_datetime(self, monkeypatch):
        # Test with specific timestamp
        ts = 1618012800000  # 2021-04-10 00:00:00 UTC

        # Create a mock datetime object
        mock_dt = MagicMock()
        mock_dt.strftime.return_value = "2021-04-10 00:00:00"

        # Create a mock module with a fromtimestamp method
        class MockDatetime:
            @staticmethod
            def fromtimestamp(timestamp, tz=None):
                assert timestamp == ts / 1000
                assert tz == "UTC"
                return mock_dt

        # Apply the monkeypatch at the module level where Utilities is defined
        import app.utils.utilities
        monkeypatch.setattr(app.utils.utilities, 'datetime', MockDatetime)

        # Test with timezone
        result = Utilities.ms_to_datetime(ts, timezone="UTC")

        # Verify the result
        assert result == "2021-04-10 00:00:00"
        assert mock_dt.strftime.call_args[0][0] == "%Y-%m-%d %H:%M:%S"

    def test_datetime_to_ms(self):
        # Test with datetime object
        dt = datetime(2021, 4, 10, 0, 0, 0)
        result = Utilities.datetime_to_ms(dt)
        expected = int(dt.timestamp() * 1000)
        assert result == expected

        # Test with string
        dt_str = "2021-04-10 00:00:00"
        result = Utilities.datetime_to_ms(dt_str)
        expected = int(datetime.strptime(
            dt_str, "%Y-%m-%d %H:%M:%S").timestamp() * 1000)
        assert result == expected

    def test_current_datetime_in_ms(self, monkeypatch):
        # Mock the current time to have a predictable test
        mock_now = datetime(2021, 4, 10, 0, 0, 0)
        expected_ms = int(mock_now.timestamp() * 1000)

        # Create a mock module with a now method
        class MockDatetime:
            @staticmethod
            def now():
                return mock_now

        import app.utils.utilities
        monkeypatch.setattr(app.utils.utilities, 'datetime', MockDatetime)

        result = Utilities.current_datetime_in_ms()
        assert result == expected_ms

    def test_current_datetime(self, monkeypatch):
        # Mock the current time to have a predictable test
        mock_now = datetime(2021, 4, 10, 0, 0, 0)
        expected_str = "2021-04-10 00:00:00"

        # Create a mock module with a now method
        class MockDatetime:
            @staticmethod
            def now():
                return mock_now

        import app.utils.utilities
        monkeypatch.setattr(app.utils.utilities, 'datetime', MockDatetime)

        result = Utilities.current_datetime()
        assert result == expected_str

    @pytest.mark.parametrize(
        "duration, return_type, original_date, start_of_day, previous_date, date_format, expected",
        [
            # Test subtracting 2 days, returning milliseconds
            (
                {TimeDeltaType.DAYS: 2},
                TimeReturnType.MS,
                datetime(2021, 4, 10),
                False,
                True,
                "%Y-%m-%d %H:%M:%S",
                int(datetime(2021, 4, 8).timestamp() * 1000)
            ),
            # Test adding 1 hour, returning datetime
            (
                {TimeDeltaType.HOURS: 1},
                TimeReturnType.DATETIME,
                datetime(2021, 4, 10, 12, 0),
                False,
                False,
                "%Y-%m-%d %H:%M:%S",
                datetime(2021, 4, 10, 13, 0)
            ),
            # Test subtracting 30 minutes, returning date
            (
                {TimeDeltaType.MINUTES: 30},
                TimeReturnType.DATE,
                datetime(2021, 4, 10, 0, 15),
                False,
                True,
                "%Y-%m-%d %H:%M:%S",
                date(2021, 4, 9)
            ),
            # Test with start_of_day=True
            (
                {TimeDeltaType.DAYS: 1},
                TimeReturnType.DATETIME,
                datetime(2021, 4, 10, 12, 30),
                True,
                True,
                "%Y-%m-%d %H:%M:%S",
                datetime(2021, 4, 9, 0, 0)
            ),
            # Test with string format return
            (
                {TimeDeltaType.WEEKS: 1},
                TimeReturnType.STR_FORMAT,
                datetime(2021, 4, 10),
                False,
                True,
                "%Y-%m-%d",
                "2021-04-03"
            ),
            # Test with multiple duration components
            (
                {TimeDeltaType.DAYS: 1, TimeDeltaType.HOURS: 6},
                TimeReturnType.DATETIME,
                datetime(2021, 4, 10, 12, 0),
                False,
                True,
                "%Y-%m-%d %H:%M:%S",
                datetime(2021, 4, 9, 6, 0)
            ),
            # Test with date object as input
            (
                {TimeDeltaType.DAYS: 5},
                TimeReturnType.DATE,
                date(2021, 4, 10),
                False,
                True,
                "%Y-%m-%d",
                date(2021, 4, 5)
            ),
            # Test with millisecond timestamp as input
            (
                {TimeDeltaType.DAYS: 1},
                TimeReturnType.MS,
                int(datetime(2021, 4, 10).timestamp() * 1000),
                False,
                True,
                "%Y-%m-%d",
                int(datetime(2021, 4, 9).timestamp() * 1000)
            ),
            # Test with second timestamp as input
            (
                {TimeDeltaType.DAYS: 1},
                TimeReturnType.MS,
                int(datetime(2021, 4, 10).timestamp()),
                False,
                True,
                "%Y-%m-%d",
                int(datetime(2021, 4, 9).timestamp() * 1000)
            ),
            # Test with None duration (should not change the date)
            (
                None,
                TimeReturnType.DATETIME,
                datetime(2021, 4, 10),
                False,
                True,
                "%Y-%m-%d",
                datetime(2021, 4, 10)
            ),
        ]
    )
    def test_adjust_datetime(self, duration, return_type, original_date, start_of_day, previous_date, date_format, expected):
        # Convert duration dict from TimeDeltaType to strings
        if duration:
            duration = {k.value: v for k, v in duration.items()}

        result = Utilities.adjust_datetime(
            duration=duration,
            return_type=return_type,
            original_date=original_date,
            start_of_day=start_of_day,
            previous_date=previous_date,
            date_format=date_format
        )

        assert result == expected

    def test_adjust_datetime_invalid_return_type(self):
        # Test with invalid return type
        with pytest.raises(ValueError) as excinfo:
            Utilities.adjust_datetime(
                duration={TimeDeltaType.DAYS.value: 1},
                return_type="invalid_type",
                original_date=datetime(2021, 4, 10)
            )
        assert "Invalid return type" in str(excinfo.value)

    def test_adjust_datetime_invalid_original_date(self):
        # Test with invalid original_date type
        with pytest.raises(ValueError) as excinfo:
            Utilities.adjust_datetime(
                duration={TimeDeltaType.DAYS.value: 1},
                return_type=TimeReturnType.DATETIME,
                original_date="not a datetime object"
            )
        assert "Invalid original_date type" in str(excinfo.value)
