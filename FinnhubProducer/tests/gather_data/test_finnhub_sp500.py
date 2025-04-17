import pytest
import pandas as pd
import asyncio
import finnhub
from unittest.mock import patch, MagicMock
from app.gather_data.finnhub_sp500 import FinnhubSP500
import requests

class TestFinnhubSP500:
    """Tests for the FinnhubSP500 class."""

    @pytest.fixture
    def mock_dependencies(self):
        """Fixture to mock all external dependencies"""
        with patch('app.gather_data.finnhub_sp500.finnhub.Client') as mock_client, \
                patch('app.gather_data.finnhub_sp500.SP500_list') as mock_sp500_list, \
                patch('app.gather_data.finnhub_sp500.Utilities') as mock_utilities:

            # Mock SP500_list
            mock_sp500_list.get_sp500_list.return_value = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT', 'AMZN', 'GOOGL'],
                'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.']
            })
            mock_sp500_list.get_us_big_tech.return_value = [
                'Apple', 'Microsoft', 'Amazon', 'Google']

            # Mock Utilities
            mock_utilities.from_csv_to_df.return_value = None

            yield {
                'client': mock_client,
                'sp500_list': mock_sp500_list,
                'utilities': mock_utilities
            }


    @pytest.fixture
    def finnhub_sp500(self, mock_dependencies):
        """Fixture to create an instance of FinnhubSP500 with mocked dependencies"""
        return FinnhubSP500()


    def test_init(self, finnhub_sp500):
        """Test initialization of FinnhubSP500"""
        assert finnhub_sp500 is not None
        assert finnhub_sp500.key_name == "Ticker"
        assert 'ticker' in finnhub_sp500.column_map
        assert 'sp500_list' in finnhub_sp500.dist_sp500_list


    @patch('app.gather_data.finnhub_sp500.Utilities')
    def test_update_sp500_list_with_no_existing_data(self, mock_utilities):
        """Test __update_sp500_list when there's no existing company profile data"""
        mock_utilities.from_csv_to_df.return_value = None

        with patch('app.gather_data.finnhub_sp500.finnhub.Client'), \
                patch('app.gather_data.finnhub_sp500.SP500_list') as mock_sp500_list:

            mock_sp500_list.get_sp500_list.return_value = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT', 'AMZN', 'GOOGL'],
                'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.']
            })
            mock_sp500_list.get_us_big_tech.return_value = [
                'Apple', 'Microsoft', 'Amazon', 'Google']

            finnhub_sp500 = FinnhubSP500()

            # Check that all companies are in sp500_list and none in sp500_company_profile
            assert len(finnhub_sp500.dist_sp500_list['sp500_list']) == 4
            assert finnhub_sp500.dist_sp500_list['sp500_company_profile'] is None


    @patch('app.gather_data.finnhub_sp500.Utilities')
    def test_update_sp500_list_with_existing_data(self, mock_utilities):
        """Test __update_sp500_list when there's existing company profile data"""
        # Mock existing company profiles
        mock_utilities.from_csv_to_df.return_value = pd.DataFrame({
            'Symbol': ['AAPL', 'MSFT'],
            'Name': ['Apple Inc.', 'Microsoft Corp.']
        })

        with patch('app.gather_data.finnhub_sp500.finnhub.Client'), \
                patch('app.gather_data.finnhub_sp500.SP500_list') as mock_sp500_list:

            mock_sp500_list.get_sp500_list.return_value = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT', 'AMZN', 'GOOGL'],
                'Security': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.']
            })
            mock_sp500_list.get_us_big_tech.return_value = [
                'Apple', 'Microsoft', 'Amazon', 'Google']

            finnhub_sp500 = FinnhubSP500()

            # Check that AAPL and MSFT are in existing profiles, AMZN and GOOGL are in new list
            # AMZN, GOOGL
            assert len(finnhub_sp500.dist_sp500_list['sp500_list']) == 2
            # AAPL, MSFT
            assert len(finnhub_sp500.dist_sp500_list['sp500_company_profile']) == 2


    @patch('app.gather_data.finnhub_sp500.time.sleep')
    def test_process_sp500_row_success(self, mock_sleep, finnhub_sp500):
        """Test __process_sp500_row with successful API response"""
        # Setup mock response
        mock_profile = {
            'country': 'US',
            'name': 'Apple Inc.',
            'ticker': 'AAPL',
            'marketCapitalization': 2000000
        }
        finnhub_sp500.finnhub_client.company_profile2 = MagicMock(
            return_value=mock_profile)

        # Test row
        row = pd.Series({'Symbol': 'AAPL', 'Security': 'Apple Inc.'})

        # Call the method
        result = finnhub_sp500._FinnhubSP500__process_sp500_row(row)

        # Check result
        assert result['ticker'] == 'AAPL'
        assert result['Symbol'] == 'AAPL'
        mock_sleep.assert_not_called()


    @patch('app.gather_data.finnhub_sp500.time.sleep')
    def test_process_sp500_row_rate_limit_retry(self, mock_sleep, finnhub_sp500):
        """Test __process_sp500_row with rate limit and retry"""
        # Setup mock responses for first call (rate limit) and second call (success)
        mock_api_response_json_error = requests.Response()
        mock_api_response_json_error.status_code = 429
        mock_api_response_json_error._content = b'{"error": "Rate limit exceeded"}'
        exception_response = finnhub.FinnhubAPIException(mock_api_response_json_error)

        finnhub_sp500.finnhub_client.company_profile2 = MagicMock(
            side_effect=[
                exception_response,
                {'country': 'US', 'name': 'Apple Inc.', 'ticker': 'AAPL'}
            ]
        )

        # Test row
        row = pd.Series({'Symbol': 'AAPL', 'Security': 'Apple Inc.'})
        # with pytest.raises(finnhub.FinnhubAPIException):
        result = finnhub_sp500._FinnhubSP500__process_sp500_row(row)

        # Check result
        assert result['ticker'] == 'AAPL'
        mock_sleep.assert_called_once()


    @patch('app.gather_data.finnhub_sp500.time.sleep')
    def test_process_sp500_row_permanent_failure(self, mock_sleep, finnhub_sp500):
        """Test __process_sp500_row with permanent failure"""
        # Setup mock to always fail
        mock_api_response_json_error = requests.Response()
        mock_api_response_json_error.status_code = 404
        mock_api_response_json_error._content = b'{"error": "Not found"}'
        exception_response = finnhub.FinnhubAPIException(mock_api_response_json_error)

        finnhub_sp500.finnhub_client.company_profile2 = MagicMock(
            side_effect=exception_response
        )

        # Test row
        row = pd.Series({'Symbol': 'AAPL', 'Security': 'Apple Inc.'})

        # Call the method
        result = finnhub_sp500._FinnhubSP500__process_sp500_row(row)

        # Check result is None due to permanent failure
        assert result is None
        mock_sleep.assert_not_called()


    @pytest.mark.asyncio
    async def test_async_process_sp500_company_profiles(self, finnhub_sp500):
        """Test __async_process_sp500_company_profiles"""
        # Mock __async_process_sp500_row to return predefined results
        async def mock_async_process(row, semaphore):
            return {'ticker': row['Symbol'], 'Symbol': row['Symbol'], 'name': row['Security']}

        # Patch the method
        with patch.object(
            finnhub_sp500,
            '_FinnhubSP500__async_process_sp500_row',
            side_effect=mock_async_process
        ):
            # Test data
            test_df = pd.DataFrame({
                'Symbol': ['AAPL', 'MSFT'],
                'Security': ['Apple Inc.', 'Microsoft Corp.']
            })

            # Call the method
            result = await finnhub_sp500._FinnhubSP500__async_process_sp500_company_profiles(test_df, 2)

            # Check results
            assert len(result) == 2
            assert result[0]['ticker'] == 'AAPL'
            assert result[1]['ticker'] == 'MSFT'


    @patch('app.gather_data.finnhub_sp500.asyncio.run')
    @patch('app.gather_data.finnhub_sp500.Utilities')
    def test_sp500_company_profiles(self, mock_utilities, mock_asyncio_run, finnhub_sp500):
        """Test sp500_company_profiles method"""
        # Mock asyncio.run to return some profiles
        new_profiles = [
            {'ticker': 'AMZN', 'Symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
            {'ticker': 'GOOGL', 'Symbol': 'GOOGL', 'name': 'Alphabet Inc.'}
        ]
        mock_asyncio_run.return_value = new_profiles

        # Mock existing profiles in the instance
        existing_profiles = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],
            'Symbol': ['AAPL', 'MSFT'],
            'name': ['Apple Inc.', 'Microsoft Corp.']
        })
        finnhub_sp500.dist_sp500_list = {
            'sp500_list': pd.DataFrame({
                'Symbol': ['AMZN', 'GOOGL'],
                'Security': ['Amazon.com Inc.', 'Alphabet Inc.']
            }),
            'sp500_company_profile': existing_profiles
        }

        # Mock utilities to return processed dataframe
        expected_result = pd.DataFrame({
            'Ticker': ['AAPL', 'MSFT', 'AMZN', 'GOOGL'],
            'Symbol': ['AAPL', 'MSFT', 'AMZN', 'GOOGL'],
            'Name': ['Apple Inc.', 'Microsoft Corp.', 'Amazon.com Inc.', 'Alphabet Inc.']
        })
        mock_utilities.convert_nan_to_none.return_value = expected_result

        # Call the method
        result = finnhub_sp500.sp500_company_profiles()

        # Check results
        pd.testing.assert_frame_equal(result, expected_result)
        mock_utilities.from_df_to_csv.assert_called_once()
        mock_utilities.rename_df_columns.assert_called_once()
        mock_utilities.convert_nan_to_none.assert_called_once()


    @pytest.mark.asyncio
    async def test_async_process_sp500_row(self, finnhub_sp500):
        """Test __async_process_sp500_row"""
        # Mock __process_sp500_row to return a known result
        with patch.object(
            finnhub_sp500,
            '_FinnhubSP500__process_sp500_row',
            return_value={'ticker': 'AAPL', 'Symbol': 'AAPL', 'name': 'Apple Inc.'}
        ):
            # Create a test row and semaphore
            row = pd.Series({'Symbol': 'AAPL', 'Security': 'Apple Inc.'})
            semaphore = asyncio.Semaphore(2)

            # Call the method
            result = await finnhub_sp500._FinnhubSP500__async_process_sp500_row(row, semaphore)

            # Check result
            assert result['ticker'] == 'AAPL'
            assert result['Symbol'] == 'AAPL'

    def test_max_retries_exceeded(self, finnhub_sp500):
        """Test that __process_sp500_row doesn't retry infinitely"""
        # Setup mock to always raise an exception for company_profile2 calls
        mock_api_response_json_error = requests.Response()
        mock_api_response_json_error.status_code = 429
        mock_api_response_json_error._content = b'{"error": "Rate limit exceeded"}'
        exception_response = finnhub.FinnhubAPIException(mock_api_response_json_error)

        finnhub_sp500.finnhub_client.company_profile2 = MagicMock(
            side_effect=exception_response
        )

        # Test row
        row = pd.Series({'Symbol': 'AAPL', 'Security': 'Apple Inc.'})

        # Mock sleep to avoid waiting in test
        with patch('app.gather_data.finnhub_sp500.time.sleep'):
            # Call the method with initial trail of 5 (should exceed max retries)
            result = finnhub_sp500._FinnhubSP500__process_sp500_row(row, trail=5)
            print("Result", result)

            # Check result is None due to exceeding max retries
            assert result is None
