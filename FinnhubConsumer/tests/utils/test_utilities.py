from unittest.mock import patch
import pytest
import types
import json
from app.utils.utilities import Utilities

class DummyBase:
    pass

class DummyDerived(DummyBase):
    pass

class NotRelated:
    pass

class TestUtilities:
    def test_remove_no_printable_characters(self):
        input_str = "Hello\x00World\x1F!"
        expected_output = "HelloWorld!"
        assert Utilities.remove_no_printable_characters(input_str) == expected_output

        clean_str = "JustCleanText"
        assert Utilities.remove_no_printable_characters(clean_str) == clean_str

    def test_get_classes_from_module(self):
        dummy_module = types.ModuleType("dummy_module")
        setattr(dummy_module, "DummyDerived", DummyDerived)
        setattr(dummy_module, "NotRelated", NotRelated)
        setattr(dummy_module, "DummyBase", DummyBase)

        result = Utilities.get_classes_from_module(dummy_module, DummyBase)
        assert "DummyDerived" in result
        assert "DummyBase" not in result
        assert "NotRelated" not in result
        assert result["DummyDerived"] is DummyDerived

    def test_get_array_from_str_comma_delimited(self):
        input_str = "a,b,c"
        expected = ["a", "b", "c"]
        assert Utilities.get_array_from_str(input_str) == expected

    def test_get_array_from_str_custom_delimiter(self):
        input_str = "1|2|3"
        expected = ["1", "2", "3"]
        assert Utilities.get_array_from_str(input_str, delimiter="|") == expected

    def test_get_array_from_str_json(self):
        input_str = '["apple", "banana", "cherry"]'
        expected = ["apple", "banana", "cherry"]
        assert Utilities.get_array_from_str(input_str, delimiter="json") == expected

    def test_get_array_from_str_invalid_json(self):
        invalid_json = '["apple", "banana",]'
        with patch("app.utils.utilities.logger") as mock_logger:
            result = Utilities.get_array_from_str(invalid_json, delimiter="json")
            assert result is None or isinstance(result, str)  # returns original string or None
            mock_logger.error.assert_called_once()
            assert "Error decoding JSON string" in mock_logger.error.call_args[0][0]

    def test_get_array_from_str_none_input(self):
        assert Utilities.get_array_from_str(None) is None
