import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.gather_data.finnhub_gather_data import FinnhubGatherData
from app.gather_data.finnhub_trades import FinnhubTrades
from app.handlers.kafka_producer import KafkaProducer
from app.utils import settings as UTILS
from app.finnhub_producer import FinnhubProducer

class TestFinnhubProducer:
    @pytest.fixture
    def mock_finnhub_gather_data(self):
        """Fixture to mock FinnhubGatherData"""
        mock = Mock(spec=FinnhubGatherData)
        # Setup the mock to return test data
        mock.get_company_profiles.return_value = {"symbol": ["AAPL", "MSFT"], "name": ["Apple Inc", "Microsoft Corp"]}
        mock.sp500_key_name = "symbol"
        return mock


    @pytest.fixture
    def mock_kafka_producer(self):
        """Fixture to mock KafkaProducer"""
        return Mock(spec=KafkaProducer)

    def test_init(self, mock_finnhub_gather_data):
        """Test initialization of FinnhubProducer"""
        with patch('app.finnhub_producer.FinnhubGatherData', return_value=mock_finnhub_gather_data):
            producer = FinnhubProducer()

            # Verify that get_company_profiles was called
            mock_finnhub_gather_data.get_company_profiles.assert_called_once()

            # Verify that company_profiles were set correctly
            assert producer.company_profiles == {"symbol": ["AAPL", "MSFT"], "name": ["Apple Inc", "Microsoft Corp"]}

            # Verify that tickers were set from UTILS.TEST_TICKERS
            np.testing.assert_array_equal(producer.tickers, np.array(UTILS.TEST_TICKERS))

    def test_publishSP500CompanyProfiles(self, mock_finnhub_gather_data, mock_kafka_producer):
        """Test publishing of S&P 500 company profiles"""
        with patch('app.finnhub_producer.FinnhubGatherData', return_value=mock_finnhub_gather_data), \
             patch('app.finnhub_producer.KafkaProducer', return_value=mock_kafka_producer):

            producer = FinnhubProducer()
            producer.publishSP500CompanyProfiles()

            # Verify KafkaProducer was initialized with the correct config
            expected_config = {
                'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,
                'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,
                'schema.name': UTILS.KAFKA_TOPIC_COMPANY_PROFILES
            }

            # Verify publishUsingDataFrames was called with the correct parameters
            mock_kafka_producer.publishUsingDataFrames.assert_called_once_with(
                topic=UTILS.KAFKA_TOPIC_COMPANY_PROFILES,
                df=producer.company_profiles,
                key=mock_finnhub_gather_data.sp500_key_name
            )

    def test_publishStockSymbols(self, mock_finnhub_gather_data, mock_kafka_producer):
        """Test publishing of stock symbols"""
        with patch('app.finnhub_producer.FinnhubGatherData', return_value=mock_finnhub_gather_data), \
             patch('app.finnhub_producer.KafkaProducer', return_value=mock_kafka_producer):

            producer = FinnhubProducer()
            producer.publishStockSymbols()

            # Verify KafkaProducer was initialized with the correct config
            expected_config = {
                'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,
                'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,
                'schema.name': UTILS.KAFKA_TOPIC_SYMBOLS
            }

            # Verify publishUsingList was called with the correct parameters
            mock_kafka_producer.publishUsingList.assert_called_once_with(
                topic=UTILS.KAFKA_TOPIC_SYMBOLS,
                items=producer.tickers.tolist(),
                key="Symbol"
            )

    def test_publishTrades(self, mock_finnhub_gather_data, mock_kafka_producer):
        """Test publishing of trades data"""
        with patch('app.finnhub_producer.FinnhubGatherData', return_value=mock_finnhub_gather_data), \
             patch('app.finnhub_producer.KafkaProducer', return_value=mock_kafka_producer), \
             patch('app.finnhub_producer.FinnhubTrades') as mock_finnhub_trades_class:

            # Setup the mock for FinnhubTrades
            mock_finnhub_trades = Mock(spec=FinnhubTrades)
            mock_finnhub_trades_class.return_value = mock_finnhub_trades

            producer = FinnhubProducer()
            producer.publishTrades()

            # Verify FinnhubTrades was initialized with the correct parameters
            mock_finnhub_trades_class.assert_called_once_with(
                tickers=producer.tickers,
                producer=mock_kafka_producer,
                max_messages=None
            )

            # Verify start_websocket was called
            mock_finnhub_trades.start_websocket.assert_called_once()
