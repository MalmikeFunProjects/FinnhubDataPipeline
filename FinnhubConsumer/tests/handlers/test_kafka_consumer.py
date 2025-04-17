import pytest
from unittest.mock import MagicMock, patch
from app.handlers.kafka_consumer import KafkaConsumer


class TestKafkaConsumer:
    @pytest.fixture
    def kafka_props(self):
        return {
            'schema_registry.url': 'http://localhost:8081',
            'bootstrap.servers': 'localhost:9092'
        }

    @patch("app.handlers.kafka_consumer.SchemaRegistryClient")
    @patch("app.handlers.kafka_consumer.AvroDeserializer")
    @patch("app.handlers.kafka_consumer.DeserializingConsumer")
    def test_consume_from_kafka_yields_records(
        self, mock_des_consumer, mock_avro_deserializer, mock_schema_registry_client, kafka_props
    ):
        mock_msg = MagicMock()
        mock_msg.topic.return_value = "test-topic"
        mock_msg.key.return_value = "test-key"
        mock_msg.value.return_value = {"field": "value"}
        mock_msg.error.return_value = None

        consumer_instance = MagicMock()
        consumer_instance.poll.side_effect = [mock_msg, KeyboardInterrupt()]
        mock_des_consumer.return_value = consumer_instance

        consumer = KafkaConsumer(kafka_props)
        result = list(consumer.consume_from_kafka(["test-topic"]))

        assert result == [("test-topic", "test-key", {"field": "value"})]
        consumer_instance.subscribe.assert_called_once_with(topics=["test-topic"])
        consumer_instance.close.assert_called_once()
