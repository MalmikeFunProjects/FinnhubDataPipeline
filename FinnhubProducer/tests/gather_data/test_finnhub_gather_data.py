import pytest
import pandas as pd
from unittest.mock import Mock, patch

from app.gather_data.finnhub_sp500 import FinnhubSP500
from app.gather_data.finnhub_gather_data import FinnhubGatherData  # Assuming the class is in this file


class TestFinnhubGatherData:
    """Tests for the FinnhubGatherData class."""

    @pytest.fixture
    def mock_finnhub_sp500(self):
        """Create a mock FinnhubSP500 instance."""
        mock = Mock(spec=FinnhubSP500)
        mock.key_name = "S&P 500"
        mock.us_big_tech_str_list = "Microsoft|Apple|Amazon|Google|Meta|Facebook|Alphabet"
        return mock

    @pytest.fixture
    def sample_company_profiles(self):
        """Create a sample DataFrame of company profiles."""
        return pd.DataFrame({
            "Ticker": ["MSFT", "AAPL", "AMZN", "GOOGL", "META", "XOM", "JPM", "JNJ"],
            "Name": ["Microsoft Corp", "Apple Inc", "Amazon.com Inc", "Alphabet Inc",
                     "Meta Platforms Inc", "Exxon Mobil Corp", "JPMorgan Chase & Co", "Johnson & Johnson"],
            "Exchange": ["NASDAQ", "NASDAQ", "NASDAQ", "NASDAQ", "NASDAQ", "NYSE", "NYSE", "NYSE"],
            "Industry": ["Software", "Technology", "E-Commerce", "Internet", "Social Media",
                         "Energy", "Banking", "Healthcare"]
        })

    def test_init(self, mock_finnhub_sp500):
        """Test that the class initializes properly and inherits attributes."""
        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()

            assert gatherer.finnhubSP500 == mock_finnhub_sp500
            assert gatherer.sp500_key_name == "S&P 500"
            assert gatherer.us_big_tech_str_list == "Microsoft|Apple|Amazon|Google|Meta|Facebook|Alphabet"

    def test_get_company_profiles(self, mock_finnhub_sp500, sample_company_profiles):
        """Test that get_company_profiles returns the DataFrame from FinnhubSP500."""
        mock_finnhub_sp500.sp500_company_profiles.return_value = sample_company_profiles

        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()
            result = gatherer.get_company_profiles()

            mock_finnhub_sp500.sp500_company_profiles.assert_called_once()
            pd.testing.assert_frame_equal(result, sample_company_profiles)

    def test_get_us_big_tech_tickers(self, mock_finnhub_sp500, sample_company_profiles):
        """Test that get_us_big_tech_tickers correctly filters out US Big Tech companies."""
        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()
            result = gatherer.get_us_big_tech_tickers(sample_company_profiles)

            # Expected result: tech companies from sample data
            expected = pd.Series(["MSFT", "AAPL", "AMZN", "GOOGL", "META"],
                                 index=[0, 1, 2, 3, 4],
                                 name="Ticker")

            pd.testing.assert_series_equal(result, expected)

    def test_get_us_big_tech_tickers_empty_result(self, mock_finnhub_sp500):
        """Test when no companies match the big tech criteria."""
        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()

            # Create a DataFrame with no tech companies
            non_tech_df = pd.DataFrame({
                "Ticker": ["XOM", "JPM", "JNJ"],
                "Name": ["Exxon Mobil Corp", "JPMorgan Chase & Co", "Johnson & Johnson"],
                "Industry": ["Energy", "Banking", "Healthcare"]
            })

            result = gatherer.get_us_big_tech_tickers(non_tech_df)
            expected = pd.Series([], name="Ticker", dtype=object)

            pd.testing.assert_series_equal(result, expected)

    def test_get_us_big_tech_tickers_type_error(self, mock_finnhub_sp500):
        """Test that TypeError is raised when not passing a DataFrame."""
        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()

            with pytest.raises(TypeError, match="sp500_company_profiles must be a pandas DataFrame"):
                gatherer.get_us_big_tech_tickers("not a dataframe")

            with pytest.raises(TypeError, match="sp500_company_profiles must be a pandas DataFrame"):
                gatherer.get_us_big_tech_tickers(None)

    def test_get_us_big_tech_tickers_key_error(self, mock_finnhub_sp500):
        """Test that KeyError is raised when the DataFrame doesn't have a 'Name' column."""
        with patch('app.gather_data.finnhub_gather_data.FinnhubSP500', return_value=mock_finnhub_sp500):
            gatherer = FinnhubGatherData()

            # DataFrame without 'Name' column
            invalid_df = pd.DataFrame({
                "Ticker": ["MSFT", "AAPL"],
                "Symbol": ["Microsoft", "Apple"]  # Not 'Name'
            })

            with pytest.raises(KeyError, match="sp500_company_profiles must contain a 'Name' column"):
                gatherer.get_us_big_tech_tickers(invalid_df)
