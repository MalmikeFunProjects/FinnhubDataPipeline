# import pytest
# import os
# from unittest.mock import mock_open  # Can still use mock_open from unittest.mock
# from app.utils.utilities import Utilities  # Assuming your file structure

# # Define the directory where this test file resides
# TEST_DIR = os.path.dirname(os.path.abspath(__file__))
# # Define a path for a dummy schema file relative to the test directory
# DUMMY_SCHEMA_FILENAME = "dummy_schema.avsc"
# DUMMY_SCHEMA_PATH = os.path.join(TEST_DIR, DUMMY_SCHEMA_FILENAME)
# DUMMY_SCHEMA_CONTENT = '{"type": "record", "name": "TestSchema", "fields": [{"name": "id", "type": "string"}]}'


# @pytest.fixture(scope="class")
# def dummy_schema_file():
#     """
#     Pytest fixture to create and clean up the dummy schema file for the test class.
#     """
#     # Setup: Create the dummy file
#     with open(DUMMY_SCHEMA_PATH, 'w') as f:
#         f.write(DUMMY_SCHEMA_CONTENT)
#     # Optional: for visibility during test runs
#     print(f"\nSetup: Created dummy file at {DUMMY_SCHEMA_PATH}")

#     yield DUMMY_SCHEMA_PATH  # Provide the path to the tests

#     # Teardown: Remove the dummy file
#     if os.path.exists(DUMMY_SCHEMA_PATH):
#         os.remove(DUMMY_SCHEMA_PATH)
#         # Optional: for visibility
#         print(f"\nTeardown: Removed dummy file at {DUMMY_SCHEMA_PATH}")


# # Apply the fixture to the whole class
# @pytest.mark.usefixtures("dummy_schema_file")
# class TestUtilities:
#     """
#     Test suite for the Utilities class using pytest.
#     """

#     def test_load_schema_success(self, monkeypatch):
#         """
#         Test loading a schema successfully when the file exists.
#         """
#         # Mock os.path.realpath using pytest's monkeypatch fixture
#         # We mock os.path directly, not just realpath within os.path
#         original_realpath = os.path.realpath

#         def mock_realpath(path):
#             # Simulate returning the directory containing __file__
#             # In this case, __file__ is the test file's path
#             if path != os.path.dirname(__file__):
#                 return TEST_DIR
#             # Fallback for other paths if needed
#             return original_realpath(path)

#         # Patch the 'realpath' function within the 'os.path' module
#         monkeypatch.setattr(os.path, "realpath", mock_realpath)
#         # Call the method under test
#         loaded_schema = Utilities.load_schema(DUMMY_SCHEMA_FILENAME)

#         # Assert using standard assert
#         assert loaded_schema == DUMMY_SCHEMA_CONTENT

#     def test_load_schema_file_not_found(self, monkeypatch):
#         """
#         Test that FileNotFoundError is raised when the schema file does not exist.
#         """
#         # Mock os.path.realpath
#         original_realpath = os.path.realpath

#         def mock_realpath(path):
#             if path != os.path.dirname(__file__):
#                 return TEST_DIR
#             return original_realpath(path)
#         monkeypatch.setattr(os.path, "realpath", mock_realpath)

#         non_existent_file = "non_existent_schema.avsc"

#         # Assert that calling load_schema raises FileNotFoundError using pytest.raises
#         with pytest.raises(FileNotFoundError):
#             Utilities.load_schema(non_existent_file)

#     def test_load_schema_io_error(self, monkeypatch):
#         """
#         Test that IOError (or OSError) is raised during file reading.
#         Note: In Python 3.3+, IOError is an alias for OSError.
#         """
#         # Mock os.path.realpath
#         original_realpath = os.path.realpath

#         def mock_realpath(path):
#             if path != os.path.dirname(__file__):
#                 return TEST_DIR
#             return original_realpath(path)
#         monkeypatch.setattr(os.path, "realpath", mock_realpath)

#         # Mock builtins.open to raise an error
#         def mock_open_raises(*args, **kwargs):
#             # Check if the path matches the expected path before raising
#             expected_path = os.path.join(TEST_DIR, DUMMY_SCHEMA_FILENAME)
#             if args[0] == expected_path:
#                 raise IOError("Simulated I/O Error")
#             raise ValueError(f"Unexpected call to open with args: {args}")

#         monkeypatch.setattr("builtins.open", mock_open_raises)

#         # Assert that calling load_schema raises IOError/OSError
#         with pytest.raises(IOError):  # Or pytest.raises(OSError)
#             Utilities.load_schema(DUMMY_SCHEMA_FILENAME)
