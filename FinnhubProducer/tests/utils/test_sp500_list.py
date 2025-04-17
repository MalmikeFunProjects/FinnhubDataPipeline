import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.utils.settings import SP500_COMPANIES_URL, US_BIG_TECH_URL
from app.utils.sp500_list import SP500_list  # Assuming the class is in this module


class TestSP500List:

    @patch('app.utils.sp500_list.pd')
    def test_get_sp500_list(self, mock_pd):
        """Test that get_sp500_list correctly processes the fetched data."""
        # Create a mock response for pd.read_html
        mock_table = pd.DataFrame({
            'Symbol': ['AAPL', 'MSFT', 'AMZN'],
            'Security': ['Apple Inc', 'Microsoft Corp', 'Amazon.com Inc'],
            'Extra Column': ['Not needed', 'Not needed', 'Not needed']
        })
        mock_pd.read_html.return_value = [mock_table]

        # Call the function
        result = SP500_list.get_sp500_list()

        # Verify that read_html was called with the correct URL
        mock_pd.read_html.assert_called_once_with(SP500_COMPANIES_URL)

        # Verify the result contains only the expected columns
        assert list(result.columns) == ['Symbol', 'Security']

        # Verify the data is preserved correctly
        assert len(result) == 3
        assert result.iloc[0]['Symbol'] == 'AAPL'
        assert result.iloc[0]['Security'] == 'Apple Inc'

    @patch('app.utils.sp500_list.pd')
    def test_get_us_big_tech(self, mock_pd):
        """Test that get_us_big_tech correctly filters and formats the data."""
        # Create a mock response for pd.read_html
        mock_table1 = pd.DataFrame({'Header': ['This is table 1']})
        mock_table2 = pd.DataFrame({
            'Company': ['Apple Inc.', 'Microsoft Corp', 'Amazon.com Inc.', 'Alibaba Group'],
            'Country (origin)': ['US', 'US', 'US', 'China']
        })
        mock_pd.read_html.return_value = [mock_table1, mock_table2]

        # Call the function
        result = SP500_list.get_us_big_tech()

        # Verify that read_html was called with the correct URL
        mock_pd.read_html.assert_called_once_with(US_BIG_TECH_URL)

        # Verify the result is as expected
        expected = 'Apple Inc|Microsoft Corp|Amazon.com Inc'
        assert result == expected

        # Check that only US companies are included
        assert 'Alibaba Group' not in result

        # Verify Inc. is replaced with Inc
        assert 'Inc.' not in result
        assert 'Inc' in result

    @patch('app.utils.sp500_list.pd.read_html')
    def test_get_sp500_list_network_error(self, mock_read_html):
        """Test that network errors are properly propagated."""
        # Simulate a network error
        mock_read_html.side_effect = Exception("Network error")

        # Verify the error is propagated
        with pytest.raises(Exception) as exc_info:
            SP500_list.get_sp500_list()

        assert "Network error" in str(exc_info.value)

    @patch('app.utils.sp500_list.pd.read_html')
    def test_get_us_big_tech_empty_data(self, mock_read_html):
        """Test handling of empty data in the get_us_big_tech method."""
        # Return empty tables
        mock_read_html.return_value = [
            pd.DataFrame(),
            pd.DataFrame({'Company': [], 'Country (origin)': []})
        ]

        # Should return an empty string since there are no US tech companies
        result = SP500_list.get_us_big_tech()
        assert result == ""
