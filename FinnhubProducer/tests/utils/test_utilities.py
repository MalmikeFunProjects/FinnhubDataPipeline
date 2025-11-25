import pytest
import pandas as pd
import os
from pathlib import Path
import tempfile
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from app.utils.utilities import Utilities
from app.utils import utilities

class TestUtilities:
    """Test suite for the Utilities class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Create a sample DataFrame for testing
        self.sample_df = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['a', 'b', 'c'],
            'col3': [1.1, np.nan, 3.3]
        })

        # Create a temporary directory for file operations
        self.temp_dir = tempfile.TemporaryDirectory()

    def teardown_method(self):
        """Clean up test fixtures after each test method."""
        self.temp_dir.cleanup()

    def test_rename_df_columns(self):
        """Test renaming DataFrame columns."""
        df = self.sample_df.copy()
        column_mapping = {'col1': 'column1', 'col2': 'column2'}
        Utilities.rename_df_columns(df, column_mapping)

        assert 'column1' in df.columns
        assert 'column2' in df.columns
        assert 'col3' in df.columns
        assert 'col1' not in df.columns
        assert 'col2' not in df.columns

    def test_from_df_to_csv(self):
        """Test writing DataFrame to CSV file."""
        df = self.sample_df.copy()
        file_path = os.path.join(self.temp_dir.name, 'test_output.csv')

        Utilities.from_df_to_csv(df, file_path)

        # Verify file exists
        assert os.path.exists(file_path)

        # Read back and verify content
        df_read = pd.read_csv(file_path)
        assert df_read.shape == df.shape
        assert list(df_read.columns) == list(df.columns)

    def test_from_df_to_csv_nonexistent_dir(self):
        """Test writing to CSV in a non-existent directory."""
        df = self.sample_df.copy()
        file_path = os.path.join(self.temp_dir.name, 'nonexistent_dir', 'test_output.csv')

        with patch('app.utils.utilities.logger') as mock_logger:
            Utilities.from_df_to_csv(df, file_path)
            mock_logger.error.assert_called()

    def test_from_csv_to_df(self):
        """Test reading DataFrame from CSV file."""
        # First write a DataFrame to CSV
        df = self.sample_df.copy()
        file_path = os.path.join(self.temp_dir.name, 'test_input.csv')
        df.to_csv(file_path, index=False)

        # Read back using the utility method
        df_read = Utilities.from_csv_to_df(file_path)

        # Verify content
        assert df_read is not None
        assert df_read.shape == df.shape
        assert list(df_read.columns) == list(df.columns)

    def test_from_csv_to_df_nonexistent_file(self):
        """Test reading from a non-existent CSV file."""
        file_path = os.path.join(self.temp_dir.name, 'nonexistent_file.csv')

        with patch('app.utils.utilities.logger') as mock_logger:
            result = Utilities.from_csv_to_df(file_path)
            assert result is None

    def test_convert_nan_to_none(self):
        """Test converting NaN values to None."""
        df = self.sample_df.copy()

        # Original DataFrame has NaN in col3
        assert pd.isna(df.iloc[1, 2])

        # Convert NaN to None
        df_converted = Utilities.convert_nan_to_none(df)

        # Check if NaN is now None
        # Note: We need to use pd.isna() to check for None in pandas
        assert df_converted.iloc[1, 2] is None
        assert df_converted.iloc[0, 2] == 1.1  # Non-NaN values should remain unchanged

    def test_delivery_report_success(self):
        """Test Kafka delivery report callback with successful delivery."""
        mock_msg = MagicMock()
        mock_msg.key.return_value = "test_key"
        mock_msg.topic.return_value = "test_topic"
        mock_msg.partition.return_value = 0
        mock_msg.offset.return_value = 123

        with patch('app.utils.utilities.logger') as mock_logger:
            Utilities.delivery_report(None, mock_msg)
            mock_logger.info.assert_called_once()
            mock_logger.error.assert_not_called()

    def test_delivery_report_failure(self):
        """Test Kafka delivery report callback with failed delivery."""
        mock_msg = MagicMock()
        mock_msg.key.return_value = "test_key"
        mock_error = "Connection error"

        with patch('app.utils.utilities.logger') as mock_logger:
            Utilities.delivery_report(mock_error, mock_msg)
            mock_logger.error.assert_called_once()
            mock_logger.info.assert_not_called()

    def test_from_csv_to_df_permission_error(self):
        """Test handling permission error when reading from CSV."""
        file_path = os.path.join(self.temp_dir.name, 'test_permission.csv')

        # Create the file to avoid FileNotFoundError
        with open(file_path, 'w') as f:
            f.write("col1,col2\n1,a\n2,b")

        # Simulate a permission error
        with patch('pandas.read_csv', side_effect=PermissionError):
            with patch('app.utils.utilities.logger') as mock_logger:
                result = Utilities.from_csv_to_df(file_path)
                mock_logger.error.assert_called()
                assert result is None

    def test_from_csv_to_df_general_exception(self):
        """Test handling general exceptions when reading from CSV."""
        file_path = os.path.join(self.temp_dir.name, 'test_exception.csv')

        # Create the file to avoid FileNotFoundError
        with open(file_path, 'w') as f:
            f.write("col1,col2\n1,a\n2,b")

        # Simulate a general exception
        with patch('pandas.read_csv', side_effect=Exception("Test exception")):
            with patch('app.utils.utilities.logger') as mock_logger:
                result = Utilities.from_csv_to_df(file_path)
                mock_logger.error.assert_called()
                assert result is None
