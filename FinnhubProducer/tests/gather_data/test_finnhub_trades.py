import json
import pytest
import pandas as pd
import numpy as np
import websocket
from unittest.mock import Mock, patch, MagicMock
from app.utils import Logger
from app.utils.default_log_setting import DefaultLogger
from app.handlers.kafka_producer import KafkaProducer
from app.utils.settings import FINNHUB_API_KEY, KAFKA_TOPIC_TRADES
from app.gather_data.finnhub_trades import FinnhubTrades
import app.gather_data.finnhub_trades as finnhub_trades_module


class TestFinnhubTrades:
    """Tests for the FinnhubTrades class."""
    @pytest.fixture
    def mock_kafka_producer(self):
        """Fixture to create a mock Kafka producer."""
        producer = Mock(spec=KafkaProducer)
        producer.publishUsingDataFrames = Mock()
        return producer

    @pytest.fixture
    def finnhub_trades_instance(self, mock_kafka_producer):
        """Fixture to create a FinnhubTrades instance with a mock producer."""
        tickers = np.array(["AAPL", "MSFT", "GOOGL"])
        return FinnhubTrades(tickers=tickers, producer=mock_kafka_producer, max_messages=5)

    def test_init(self, mock_kafka_producer):
        """Test the initialization of FinnhubTrades class."""
        tickers = np.array(["AAPL", "MSFT"])
        ft = FinnhubTrades(tickers=tickers, producer=mock_kafka_producer, max_messages=10)

        assert ft.tickers.tolist() == ["AAPL", "MSFT"]
        assert ft.producer == mock_kafka_producer
        assert ft.max_messages == 10
        assert ft.message_count == 0
        assert ft.ws is None
        assert ft.column_map == {
            "c": "Trade_Condition",
            "p": "Price",
            "s": "Symbol",
            "t": "Event_Timestamp",
            "v": "Volume"
        }
        assert ft.key_name == "Symbol"

    def test_on_message_trade_data(self, finnhub_trades_instance, mock_kafka_producer):
        """Test the on_message method with valid trade data."""
        mock_ws = Mock()
        trade_message = json.dumps({
            "type": "trade",
            "data": [
                {"c": ["1"], "p": 150.5, "s": "AAPL", "t": 1633027200000, "v": 100},
                {"c": ["1"], "p": 151.0, "s": "AAPL", "t": 1633027201000, "v": 50}
            ]
        })

        finnhub_trades_instance.on_message(mock_ws, trade_message)

        # Check that publishUsingDataFrames was called with the correct args
        mock_kafka_producer.publishUsingDataFrames.assert_called_once()
        call_args = mock_kafka_producer.publishUsingDataFrames.call_args
        assert call_args[1]['topic'] == KAFKA_TOPIC_TRADES
        assert call_args[1]['key'] == "Symbol"

        # Verify the DataFrame has the expected structure and data
        df = call_args[1]['df']
        assert isinstance(df, pd.DataFrame)
        assert df.columns.tolist() == ["Trade_Condition", "Price", "Symbol", "Event_Timestamp", "Volume"]
        assert df.shape == (2, 5)
        assert df["Symbol"].tolist() == ["AAPL", "AAPL"]

        # Check that message_count was incremented
        assert finnhub_trades_instance.message_count == 1

    def test_on_message_ping(self, finnhub_trades_instance):
        """Test that on_message logs correctly when receiving a ping message"""
        # Create a mock logger
        mock_logger = MagicMock()

        with patch.object(finnhub_trades_module, 'logger', mock_logger):
            mock_ws = MagicMock(spec=websocket.WebSocketApp)
            ping_message = json.dumps({"type": "ping"})
            finnhub_trades_instance.on_message(mock_ws, ping_message)

            mock_logger.info.assert_called_once_with("Connection failed. Returning ping.")
            assert finnhub_trades_instance.message_count == 0

            finnhub_trades_instance.producer.publishUsingDataFrames.assert_not_called()
            mock_ws.close.assert_not_called()


    def test_on_message_max_messages(self, finnhub_trades_instance):
        """Test that the WebSocket closes when max_messages is reached."""
        mock_ws = Mock()
        trade_message = json.dumps({
            "type": "trade",
            "data": [{"c": ["1"], "p": 150.5, "s": "AAPL", "t": 1633027200000, "v": 100}]
        })

        # Set message_count to one less than max_messages
        finnhub_trades_instance.message_count = finnhub_trades_instance.max_messages - 1

        finnhub_trades_instance.on_message(mock_ws, trade_message)

        # Check that close was called
        mock_ws.close.assert_called_once()

    def test_on_message_json_error(self, finnhub_trades_instance):
        """Test handling of invalid JSON in the on_message method."""
        mock_ws = Mock()
        invalid_message = "This is not valid JSON"
        mock_logger = MagicMock()

        with patch.object(finnhub_trades_module, 'logger', mock_logger):
            finnhub_trades_instance.on_message(mock_ws, invalid_message)

            # Check that error was logged
            mock_logger.error.assert_called_once()
            assert "Error decoding JSON" in mock_logger.error.call_args[0][0]

    def test_on_message_missing_key(self, finnhub_trades_instance):
        """Test handling of missing keys in the on_message method."""
        mock_ws = Mock()
        # Missing 'data' key
        missing_key_message = json.dumps({"type": "trade"})

        mock_logger = MagicMock()
        with patch.object(finnhub_trades_module, 'logger', mock_logger):
            finnhub_trades_instance.on_message(mock_ws, missing_key_message)

            # Check that error was logged
            mock_logger.error.assert_called_once()
            assert "Missing expected key" in mock_logger.error.call_args[0][0]

    def test_on_error(self, finnhub_trades_instance):
        """Test the on_error method."""
        mock_ws = Mock()
        test_error = Exception("Test error")

        with pytest.raises(Exception):
            mock_logger = MagicMock()
            with patch.object(finnhub_trades_module, 'logger', mock_logger):
                finnhub_trades_instance.on_error(mock_ws, test_error)
                mock_logger.error.assert_called_once()
                assert "Websocket error" in mock_logger.error.call_args[0][0]


    def test_on_close(self, finnhub_trades_instance):
        """Test the on_close method."""
        mock_ws = Mock()

        mock_logger = MagicMock()
        with patch.object(finnhub_trades_module, 'logger', mock_logger):
            finnhub_trades_instance.on_close(mock_ws, 1000, "Normal closure")

            # Check that closure was logged
            mock_logger.info.assert_called_once()
            assert "WebSocket closed" in mock_logger.info.call_args[0][0]

    def test_on_open(self, finnhub_trades_instance):
        """Test the on_open method."""
        mock_ws = Mock()
        mock_ws.send = Mock()

        finnhub_trades_instance.on_open(mock_ws)

        # Check that subscribe messages were sent for each ticker
        assert mock_ws.send.call_count == 3
        expected_calls = [
            '{"type":"subscribe", "symbol":"AAPL"}',
            '{"type":"subscribe", "symbol":"MSFT"}',
            '{"type":"subscribe", "symbol":"GOOGL"}'
        ]
        for i, call in enumerate(mock_ws.send.call_args_list):
            assert call[0][0] == expected_calls[i]

    @patch('websocket.WebSocketApp')
    def test_start_websocket(self, mock_websocket_app, finnhub_trades_instance):
        """Test the start_websocket method."""
        mock_ws_instance = Mock()
        mock_websocket_app.return_value = mock_ws_instance

        finnhub_trades_instance.start_websocket()

        # Check WebSocketApp was created with correct URL and callbacks
        mock_websocket_app.assert_called_once()
        expected_url = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"
        assert mock_websocket_app.call_args[0][0] == expected_url

        # Check callbacks were registered
        assert mock_websocket_app.call_args[1]['on_message'] == finnhub_trades_instance.on_message
        assert mock_websocket_app.call_args[1]['on_error'] == finnhub_trades_instance.on_error
        assert mock_websocket_app.call_args[1]['on_close'] == finnhub_trades_instance.on_close

        # Check that on_open was assigned and run_forever was called
        assert mock_ws_instance.on_open == finnhub_trades_instance.on_open
        mock_ws_instance.run_forever.assert_called_once()

    def test_start_websocket_no_tickers(self):
        """Test start_websocket with no tickers provided."""
        producer = Mock(spec=KafkaProducer)
        ft = FinnhubTrades(tickers=None, producer=producer)

        with pytest.raises(ValueError) as excinfo:
            ft.start_websocket()

        assert "No tickers submitted" in str(excinfo.value)
