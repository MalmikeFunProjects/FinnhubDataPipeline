import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from confluent_kafka.schema_registry import SchemaRegistryError
from app.handlers.kafka_producer import KafkaProducer

class TestKafkaProducer:
    """Tests for the KafkaProducer class."""

    @pytest.fixture
    def mock_schema_registry_client(self):
        """Fixture to create a mock SchemaRegistryClient."""
        client = MagicMock()
        client.get_subjects.return_value = ["test-schema-value"]
        version_mock = MagicMock()
        version_mock.schema_id = 1
        client.get_latest_version.return_value = version_mock
        schema_mock = MagicMock()
        schema_mock.schema_str = '{"type": "record", "name": "TestSchema", "fields": [{"name": "id", "type": "string"}]}'
        client.get_schema.return_value = schema_mock
        return client


    @pytest.fixture
    def mock_producer(self):
        """Fixture to create a mock SerializingProducer."""
        producer = MagicMock()
        producer.produce.return_value = None
        producer.flush.return_value = None
        return producer


    @pytest.fixture
    def mock_serializers(self):
        """Fixture to create mock serializers."""
        key_serializer = MagicMock()
        key_serializer.return_value = b"serialized_key"
        value_serializer = MagicMock()
        value_serializer.return_value = b"serialized_value"
        return key_serializer, value_serializer


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_kafka_producer_init(self, mock_avro_serializer, mock_string_serializer,
                                mock_serializing_producer, mock_schema_registry_client_class,
                                mock_schema_registry_client, mock_producer):
        """Test the initialization of KafkaProducer."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = mock_producer
        mock_string_serializer.return_value = MagicMock()
        mock_avro_serializer.return_value = MagicMock()

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        # Act
        producer = KafkaProducer(props)

        # Assert
        mock_schema_registry_client_class.assert_called_once_with({'url': props['schema_registry.url']})
        mock_serializing_producer.assert_called_once_with({'bootstrap.servers': props['bootstrap.servers']})
        mock_schema_registry_client.get_subjects.assert_called_once()
        mock_schema_registry_client.get_latest_version.assert_called_once_with(f"{props['schema.name']}-value")
        mock_schema_registry_client.get_schema.assert_called_once()
        mock_string_serializer.assert_called_once_with('utf-8')
        mock_avro_serializer.assert_called_once()


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_get_schema_from_registry_success(self, mock_avro_serializer, mock_string_serializer,
                                            mock_serializing_producer, mock_schema_registry_client_class,
                                            mock_schema_registry_client):
        """Test successful schema retrieval from registry."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = MagicMock()
        mock_string_serializer.return_value = MagicMock()
        mock_avro_serializer.return_value = MagicMock()

        version_mock = MagicMock()
        version_mock.schema_id = 1
        mock_schema_registry_client.get_latest_version.return_value = version_mock

        schema_mock = MagicMock()
        schema_mock.schema_str = '{"type": "record", "name": "TestSchema", "fields": [{"name": "id", "type": "string"}]}'
        mock_schema_registry_client.get_schema.return_value = schema_mock

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        producer = KafkaProducer(props)
        mock_schema_registry_client.get_latest_version.assert_called_with('test-schema-value')

        args, kwargs = mock_avro_serializer.call_args
        assert 'schema_str' in kwargs
        assert kwargs['schema_str'] == schema_mock.schema_str


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_get_schema_from_registry_with_subject(self, mock_avro_serializer, mock_string_serializer,
                                                mock_serializing_producer, mock_schema_registry_client_class,
                                                mock_schema_registry_client):
        """Test schema retrieval with custom subject."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = MagicMock()
        mock_string_serializer.return_value = MagicMock()
        mock_avro_serializer.return_value = MagicMock()

        version_mock = MagicMock()
        version_mock.schema_id = 1
        mock_schema_registry_client.get_latest_version.return_value = version_mock

        schema_mock = MagicMock()
        schema_mock.schema_str = '{"type": "record", "name": "TestSchema", "fields": [{"name": "id", "type": "string"}]}'
        mock_schema_registry_client.get_schema.return_value = schema_mock

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema',
            'schema.subject': 'custom-subject'
        }

        # Act
        producer = KafkaProducer(props)
        result = producer._get_schema_from_registry('test-schema', 'custom-subject')

        # Assert
        assert result == schema_mock.schema_str
        mock_schema_registry_client.get_latest_version.assert_called_with('custom-subject')


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_get_schema_from_registry_error(self, mock_avro_serializer, mock_string_serializer,
                                        mock_serializing_producer, mock_schema_registry_client_class,
                                        mock_schema_registry_client):
        """Test schema registry error handling."""
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = MagicMock()
        mock_string_serializer.return_value = MagicMock()
        mock_avro_serializer.return_value = MagicMock()

        mock_schema_registry_client.get_latest_version.side_effect = SchemaRegistryError(404, 404, "Schema not found")

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        with pytest.raises(SchemaRegistryError, match=r"Schema not found"):
            producer = KafkaProducer(props)

    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_publish_to_kafka(self, mock_avro_serializer, mock_string_serializer,
                            mock_serializing_producer, mock_schema_registry_client_class,
                            mock_schema_registry_client, mock_producer, mock_serializers):
        """Test publishToKafka method."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = mock_producer
        key_serializer, value_serializer = mock_serializers
        mock_string_serializer.return_value = key_serializer
        mock_avro_serializer.return_value = value_serializer

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        producer = KafkaProducer(props)

        # Act
        topic = "test-topic"
        key = "test-key"
        record = {"id": "1", "name": "Test Record"}
        producer.publishToKafka(topic, key, record)

        # Assert
        mock_producer.produce.assert_called_once()
        args, kwargs = mock_producer.produce.call_args
        assert kwargs["topic"] == topic
        assert kwargs["key"] == b"serialized_key"
        assert kwargs["value"] == b"serialized_value"
        assert "on_delivery" in kwargs


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_publish_using_dataframes(self, mock_avro_serializer, mock_string_serializer,
                                    mock_serializing_producer, mock_schema_registry_client_class,
                                    mock_schema_registry_client, mock_producer):
        """Test publishUsingDataFrames method."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = mock_producer
        mock_string_serializer.return_value = MagicMock(return_value=b"serialized_key")
        mock_avro_serializer.return_value = MagicMock(return_value=b"serialized_value")

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        producer = KafkaProducer(props)

        # Create a test DataFrame
        df = pd.DataFrame([
            {"id": "1", "name": "Record 1"},
            {"id": "2", "name": "Record 2"},
            {"id": "3", "name": "Record 3"}
        ])

        # Mock the publishToKafka method
        producer.publishToKafka = MagicMock()

        # Act
        topic = "test-topic"
        key_column = "id"
        producer.publishUsingDataFrames(topic, df, key_column)

        # Assert
        assert producer.publishToKafka.call_count == 3
        calls = producer.publishToKafka.call_args_list
        assert calls[0][1]["topic"] == topic
        assert calls[0][1]["key"] == "1"
        assert calls[0][1]["record"] == {"id": "1", "name": "Record 1"}

        assert calls[1][1]["topic"] == topic
        assert calls[1][1]["key"] == "2"
        assert calls[1][1]["record"] == {"id": "2", "name": "Record 2"}

        assert calls[2][1]["topic"] == topic
        assert calls[2][1]["key"] == "3"
        assert calls[2][1]["record"] == {"id": "3", "name": "Record 3"}

        mock_producer.flush.assert_called_once()


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    @patch('app.handlers.kafka_producer.time.time')
    def test_publish_using_list(self, mock_time, mock_avro_serializer, mock_string_serializer,
                            mock_serializing_producer, mock_schema_registry_client_class,
                            mock_schema_registry_client, mock_producer):
        """Test publishUsingList method."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = mock_producer
        mock_string_serializer.return_value = MagicMock(return_value=b"serialized_key")
        mock_avro_serializer.return_value = MagicMock(return_value=b"serialized_value")
        mock_time.return_value = 1625097600  # Fixed timestamp for testing

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        producer = KafkaProducer(props)

        # Mock the publishToKafka method
        producer.publishToKafka = MagicMock()

        # Test items
        items = ["item1", "item2", "item3"]

        # Act
        topic = "test-topic"
        key = "item"
        producer.publishUsingList(topic, items, key)

        # Assert
        assert producer.publishToKafka.call_count == 3
        calls = producer.publishToKafka.call_args_list

        for i, item in enumerate(items):
            assert calls[i][1]["topic"] == topic
            assert calls[i][1]["key"] == key
            assert calls[i][1]["record"] == {key: item, "Event_Timestamp": 1625097600}

        assert mock_producer.flush.call_count == 3


    @patch('app.handlers.kafka_producer.SchemaRegistryClient')
    @patch('app.handlers.kafka_producer.SerializingProducer')
    @patch('app.handlers.kafka_producer.StringSerializer')
    @patch('app.handlers.kafka_producer.AvroSerializer')
    def test_publish_to_kafka_exception(self, mock_avro_serializer, mock_string_serializer,
                                    mock_serializing_producer, mock_schema_registry_client_class,
                                    mock_schema_registry_client, mock_producer):
        """Test exception handling in publishToKafka method."""
        # Arrange
        mock_schema_registry_client_class.return_value = mock_schema_registry_client
        mock_serializing_producer.return_value = mock_producer
        mock_string_serializer.return_value = MagicMock(return_value=b"serialized_key")
        mock_avro_serializer.return_value = MagicMock(return_value=b"serialized_value")

        mock_producer.produce.side_effect = Exception("Kafka connection error")

        props = {
            'bootstrap.servers': 'localhost:9092',
            'schema_registry.url': 'http://localhost:8081',
            'schema.name': 'test-schema'
        }

        producer = KafkaProducer(props)

        # Act & Assert
        topic = "test-topic"
        key = "test-key"
        record = {"id": "1", "name": "Test Record"}

        with pytest.raises(Exception, match="Kafka connection error"):
            producer.publishToKafka(topic, key, record)
