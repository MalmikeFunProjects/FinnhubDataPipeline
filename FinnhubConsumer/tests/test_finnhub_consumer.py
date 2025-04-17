import pytest
from unittest.mock import patch, MagicMock

from app.finnhub_consumer import FinnhubConsumer, KafkaTopics
from app.cassandra_client.cassandra_client import CassandraConfig

class TestFinnhubConsumer:
    @pytest.fixture
    def mock_cassandra_config(self):
        return CassandraConfig(
            hosts=["localhost"],
            port=9042,
            keyspace="test_keyspace",
            retry_attempts=3,
            retry_delay=1
        )

    @pytest.fixture
    def consumer(self, mock_cassandra_config):
        with patch("app.finnhub_consumer.KafkaConsumer") as MockKafkaConsumer, \
            patch("app.finnhub_consumer.SetupClient") as MockSetupClient, \
            patch("app.finnhub_consumer.Utilities.get_classes_from_module", return_value=[]), \
            patch("app.finnhub_consumer.FunctionTimer"):

            MockKafkaConsumer.return_value.consume_from_kafka.return_value = []
            return FinnhubConsumer(cassandra_config=mock_cassandra_config)

    def test_init_sets_kafka_and_timer(self, consumer):
        assert hasattr(consumer, "kafka_consumer")
        assert hasattr(consumer, "function_timer")
        assert isinstance(consumer.latest_prices, dict)

    def test_compute_total_adds_missing_prices(self, consumer):
        current_prices = {"AAPL": 150.0}
        missing = ["GOOG"]
        latest = {"GOOG": 2800.0}
        total = 150.0

        result = consumer._FinnhubConsumer__compute_total(current_prices, missing, latest, total)

        assert result["total"] == 2950.0
        assert "GOOG" in result["all_symbol_prices"]

    @patch("app.finnhub_consumer.CassandraClient")
    @patch("app.finnhub_consumer.FinnhubConsumer.handle_response_data")
    def test_add_data_to_cassandra_calls_methods(self, mock_handle_data, MockCassandraClient, consumer):
        mock_client_instance = MagicMock()
        MockCassandraClient.return_value.__enter__.return_value = mock_client_instance

        topic_names = ["test_topic"]
        consumer.add_data_to_cassandra(topic_names)

        mock_handle_data.assert_called_once()
        assert mock_client_instance.clear_batch.called

    def test_handle_response_data_raises_with_invalid_topics(self, consumer):
        with pytest.raises(Exception, match="Insert valid topic names"):
            consumer.handle_response_data([], MagicMock())

    @patch("app.finnhub_consumer.CassandraClient")
    def test_handle_latest_prices_adds_price(self, MockCassandraClient, consumer):
        mock_client = MagicMock()
        latest = {}
        value = {"LAST_PRICE": 123.45, "EVENT_TIMESTAMP": "2024-01-01T00:00:00"}

        updated = consumer.handle_latest_prices(mock_client, latest, KafkaTopics.LATEST_PRICES.value, "AAPL", value)

        assert updated["AAPL"] == 123.45
        mock_client.add_batch_data.assert_called_once()

    @patch("app.finnhub_consumer.CassandraClient")
    def test_handle_company_symbols(self, MockCassandraClient, consumer):
        mock_client = MagicMock()

        consumer.handle_company_symbols(mock_client, KafkaTopics.COMPANY_SYMBOLS.value, "MSFT", {})
        mock_client.add_batch_data.assert_called_once()

    @patch("app.finnhub_consumer.CassandraClient")
    def test_handle_stock_price_1s(self, MockCassandraClient, consumer):
        mock_client = MagicMock()
        value = {
            "EVENT_TIMESTAMP": "2024-01-01T00:00:00",
            "AVG_PRICE": 100.0,
            "COUNT": 10
        }

        consumer.handle_stock_price_1s(mock_client, KafkaTopics.STOCK_PRICES_1S.value, "AAPL", value)
        mock_client.add_batch_data.assert_called_once()

    @patch("app.finnhub_consumer.FinnhubConsumer._FinnhubConsumer__compute_total")
    @patch("app.finnhub_consumer.Utilities.remove_no_printable_characters", side_effect=lambda x: x)
    def test_handle_stock_summary(self, mock_remove, mock_compute_total, consumer):
        mock_client = MagicMock()
        value = {
            "SYMBOL_PRICES": [{"key": "AAPL", "value": 150}],
            "TOTAL_PRICE": 150
        }

        mock_compute_total.return_value = {"total": 150, "all_symbol_prices": {"AAPL": 150}}

        consumer.handle_stock_summary(mock_client, {}, KafkaTopics.STOCK_SUMMARY.value, "2024-01-01", value)
        mock_client.add_batch_data.assert_called_once()

    @patch("app.finnhub_consumer.logger")
    def test_handle_stock_summary_logs_if_invalid_data(self, mock_logger, consumer):
        mock_client = MagicMock()
        value = {
            "TOTAL_PRICE": 200  # Missing SYMBOL_PRICES entirely
        }

        # Should not raise, just log
        consumer.handle_stock_summary(mock_client, {}, KafkaTopics.STOCK_SUMMARY.value, "2024-01-01", value)
        mock_client.add_batch_data.assert_called_once()

    @patch("app.finnhub_consumer.logger")
    def test_handle_company_symbols_logs_and_raises(self, mock_logger, consumer):
        mock_client = MagicMock()
        mock_client.add_batch_data.side_effect = Exception("duplicate key")

        with pytest.raises(Exception, match="duplicate key"):
            consumer.handle_company_symbols(mock_client, KafkaTopics.COMPANY_SYMBOLS.value, "AAPL", {})

        assert mock_logger.error.call_count >= 1

    @patch("app.finnhub_consumer.logger")
    def test_handle_stock_price_1s_missing_fields(self, mock_logger, consumer):
        mock_client = MagicMock()
        # Missing AVG_PRICE and COUNT
        value = {
            "EVENT_TIMESTAMP": "2024-01-01T00:00:00"
        }

        with pytest.raises(KeyError):
            consumer.handle_stock_price_1s(mock_client, KafkaTopics.STOCK_PRICES_1S.value, "AAPL", value)

        # Should not call add_batch_data because of missing fields
        mock_client.add_batch_data.assert_not_called()

    @patch("app.finnhub_consumer.logger")
    @patch("app.finnhub_consumer.FinnhubConsumer.handle_latest_prices", side_effect=Exception("fail"))
    def test_handle_response_data_logs_error(self, mock_handle_latest, mock_logger, consumer):
        mock_client = MagicMock()
        consumer.kafka_consumer.consume_from_kafka = MagicMock(return_value=[
            (KafkaTopics.LATEST_PRICES.value, "AAPL", {"LAST_PRICE": 123.4, "EVENT_TIMESTAMP": "2024-01-01"})
        ])

        with pytest.raises(Exception, match="fail"):
            consumer.handle_response_data([KafkaTopics.LATEST_PRICES.value], mock_client)

        assert mock_logger.error.call_count >= 1
