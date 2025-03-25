import inspect
import json
import re
from enum import Enum
from datetime import timedelta, datetime, date, time
from typing import Optional


class TimeDeltaType(Enum):
    DAYS = "days"
    SECONDS = "seconds"
    MICROSECONDS = "microseconds"
    MILLISECONDS = "milliseconds"
    MINUTES = "minutes"
    HOURS = "hours"
    WEEKS = "weeks"

class TimeReturnType(Enum):
    MS = "ms"
    DATETIME = "datetime"
    DATE = "date"
    STR_FORMAT = "str_format"

class Utilities:
    @staticmethod
    def get_classes_from_module(module: __module__, base_class: type) -> dict[str, any]:
        class_dict = {}
        for name, obj in inspect.getmembers(module):
            if inspect.isclass(obj) and issubclass(obj, base_class) and obj != base_class:
                class_dict[name] = (obj)
        return class_dict

    @staticmethod
    def get_array_from_str(item: str, delimiter=",") -> list[str] | str | None:
        if item is None:
            return item
        try:
            if delimiter == "json":
                return json.loads(item)
            else:
                return item.split(delimiter)
        except json.JSONDecodeError:
            print(f"Error decoding JSON string: {item}")
        except Exception as e:
            print(f"Error processing {item}: {e}")

    @staticmethod
    def ms_to_datetime(timestamp_ms: int, timezone: str = None) -> str:
        """Convert milliseconds since epoch to a datetime string

        Args:
            timestamp_ms (int): Timestamp in milliseconds since epoch
            timezone (str, optional): Timezone to use. Defaults to None.

        Returns:
            str: Datetime string
        """
        return datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone).strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def datetime_to_ms(datetime_val: str|datetime) -> int:
        """Convert a datetime string to milliseconds since epoch
        Args:
            datetime_val (str|datetime): Datetime value to convert

        Returns:
            int: Timestamp in milliseconds since epoch
        """
        if isinstance(datetime_val, str):
            datetime_val = datetime.strptime(datetime_val, "%Y-%m-%d %H:%M:%S")
        return int(datetime_val.timestamp() * 1000)

    @staticmethod
    def current_datetime_in_ms() -> int:
        """Current datetime in milliseconds"""
        return int(datetime.now().timestamp() * 1000)

    @staticmethod
    def current_datetime() -> str:
        """Current datetime"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def adjust_datetime(
        duration: Optional[dict[TimeDeltaType, int]] = None,
        return_type: TimeReturnType = TimeReturnType.MS,
        original_date: Optional[datetime|date|int] = None,
        start_of_day: bool = False,
        previous_date: bool = True,
        date_format: str = "%Y-%m-%d %H:%M:%S"
    ) -> int | str | datetime | date:
        """
        Calculate a previous datetime based on a given duration.

        Args:
            duration (dict[TimeDeltaType, int]): Time difference in a dictionary format (e.g., {"days": 2}).
            return_type (TimeReturnType): Desired return format (MS, STR_FORMAT, DATETIME, DATE).
            original_date (Optional[datetime]): The reference datetime. Defaults to now if not provided.
            start_of_day (bool): If True, sets the time to the start of the day.
            previous_date (bool): If True, subtracts the duration; otherwise, adds it.
            date_format (str): Format for string output if return_type is STR_FORMAT. Defaults to "%Y-%m-%d %H:%M:%S".
        Returns:
            int | str | datetime | date: The adjusted time in the specified format.
        Raises:
            ValueError: If an invalid return_type is provided.
            ValueError: If date_format is used with a non-string return_type.
        """
        original_date = original_date or datetime.now()
        if isinstance(original_date, date):
            original_date = datetime.combine(original_date, time.min)
        elif isinstance(original_date, int):
            original_date = datetime.fromtimestamp(original_date / (1000 if original_date > 1e12 else 1))
        elif not isinstance(original_date, datetime):
            raise ValueError(f"Invalid original_date type: {type(original_date)}")

        duration = duration or {}  # Default to no adjustment if duration is None

         # Apply time delta (add or subtract based on previous_date flag)
        delta = timedelta(**duration)
        adjusted_datetime = original_date - delta if previous_date else original_date + delta

        if start_of_day:
            adjusted_datetime = datetime.combine(adjusted_datetime.date(), time.min)

        # Format if return_type is string-based
        if return_type == TimeReturnType.STR_FORMAT:
            try:
                return adjusted_datetime.strftime(date_format)
            except ValueError as e:
                raise ValueError(f"Invalid date format: {date_format}. Error: {e}")

        # Mapping of return types to corresponding values
        return_type_map = {
            TimeReturnType.DATETIME: adjusted_datetime,
            TimeReturnType.DATE: adjusted_datetime.date(),
            TimeReturnType.MS: Utilities.datetime_to_ms(adjusted_datetime)
        }

        if return_type not in return_type_map:
            raise ValueError(f"Invalid return type: {return_type}")

        return return_type_map[return_type]

