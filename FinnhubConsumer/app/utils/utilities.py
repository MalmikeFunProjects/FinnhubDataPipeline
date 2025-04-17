import inspect
import json
import re
from app.utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("utilities", log_to_console=True)

class Utilities:
    """
    A utility class providing methods for cleaning strings by removing
    non-printable characters.
    """

    @staticmethod
    def remove_no_printable_characters(input_str: str) -> str:
        """
        Removes non-printable ASCII characters (control characters) from a string.

        Parameters:
            input_str (str): The input string to clean.

        Returns:
            str: The cleaned string with non-printable characters removed.
        """
        return re.sub(r'[\x00-\x1F]', "", input_str)

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
            logger.error(f"Error decoding JSON string: {item}")
        except Exception as e:
            logger.error(f"Error processing {item}: {e}")
