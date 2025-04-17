import pytest
from unittest.mock import MagicMock, patch
from app.set_kafka_topics.set_kafka_topics import SetUpKafkaTopics
from app.utils.utilities import Utilities
from app.utils.settings import BOOTSTRAP_SERVERS, SCHEMA_REGISTRY_URL, KAFKA_PARTITIONS, KAFKA_REPLICATION_FACTOR
from app.set_kafka_topics.add_kafka_topics import AddKafkaTopics

class TestAddKafkaTopics:
    """
    Test class for AddKafkaTopics.
    """
    # Test: Successfully add Kafka topics
    @patch.object(SetUpKafkaTopics, 'register_schema')
    @patch.object(SetUpKafkaTopics, 'register_topic')
    @patch.object(Utilities, 'load_schema')
    @patch('app.utils.settings.BOOTSTRAP_SERVERS', new='localhost:9092')
    @patch('app.utils.settings.SCHEMA_REGISTRY_URL', new='http://localhost:8081')
    @patch('app.utils.settings.KAFKA_PARTITIONS', new=1)
    @patch('app.utils.settings.KAFKA_REPLICATION_FACTOR', new=1)
    def test_add_kafka_topics_success(self, mock_load_schema, mock_register_topic, mock_register_schema):
        # Arrange
        mock_load_schema.return_value = {'type': 'record', 'name': 'test', 'fields': []}  # Mocked schema
        mock_register_schema.return_value = None  # Simulate successful schema registration
        mock_register_topic.return_value = None  # Simulate successful topic registration

        topics = {'test_topic': 'path/to/schema.avro'}

        # Act
        AddKafkaTopics.add_kafka_topics(topics)

        # Assert
        mock_load_schema.assert_called_once_with('path/to/schema.avro')
        mock_register_schema.assert_called_once_with(
            avro_schema={'type': 'record', 'name': 'test', 'fields': []},
            topic_name='test_topic'
        )
        mock_register_topic.assert_called_once_with(
            topic_names=list(topics.keys()),
            partitions=1,
            replication_factor=1
        )


    # Test: Exception while loading schema
    @patch.object(SetUpKafkaTopics, 'register_schema')
    @patch.object(SetUpKafkaTopics, 'register_topic')
    @patch.object(Utilities, 'load_schema')
    def test_add_kafka_topics_schema_load_exception(self, mock_load_schema, mock_register_topic, mock_register_schema):
        # Arrange
        mock_load_schema.side_effect = Exception("Error loading schema")  # Simulate schema loading error

        topics = {'test_topic': 'path/to/schema.avro'}

        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            AddKafkaTopics.add_kafka_topics(topics)

        assert "Error registering schema" in str(excinfo.value)
        mock_load_schema.assert_called_once_with('path/to/schema.avro')
        mock_register_schema.assert_not_called()
        mock_register_topic.assert_not_called()


    # Test: Exception while registering schema
    @patch.object(SetUpKafkaTopics, 'register_schema')
    @patch.object(SetUpKafkaTopics, 'register_topic')
    @patch.object(Utilities, 'load_schema')
    def test_add_kafka_topics_schema_register_exception(self, mock_load_schema, mock_register_topic, mock_register_schema):
        # Arrange
        mock_load_schema.return_value = {'type': 'record', 'name': 'test', 'fields': []}
        mock_register_schema.side_effect = Exception("Error registering schema")  # Simulate error in schema registration

        topics = {'test_topic': 'path/to/schema.avro'}

        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            AddKafkaTopics.add_kafka_topics(topics)

        assert "Error registering schema" in str(excinfo.value)
        mock_register_schema.assert_called_once_with(
            avro_schema={'type': 'record', 'name': 'test', 'fields': []},
            topic_name='test_topic'
        )
        mock_register_topic.assert_not_called()


    # Test: Exception while registering topics
    @patch.object(SetUpKafkaTopics, 'register_schema')
    @patch.object(SetUpKafkaTopics, 'register_topic')
    @patch.object(Utilities, 'load_schema')
    def test_add_kafka_topics_topic_register_exception(self, mock_load_schema, mock_register_topic, mock_register_schema):
        # Arrange
        mock_load_schema.return_value = {'type': 'record', 'name': 'test', 'fields': []}
        mock_register_schema.return_value = None  # Simulate successful schema registration
        mock_register_topic.side_effect = Exception("Error registering topic")  # Simulate topic registration error

        topics = {'test_topic': 'path/to/schema.avro'}

        # Act & Assert
        with pytest.raises(Exception) as excinfo:
            AddKafkaTopics.add_kafka_topics(topics)

        assert "Error registering topic" in str(excinfo.value)
        mock_register_topic.assert_called_once_with(
            topic_names=list(topics.keys()),
            partitions=1,
            replication_factor=1
        )


    # Test: Check if utility methods are used correctly
    @patch.object(SetUpKafkaTopics, 'register_schema')
    @patch.object(SetUpKafkaTopics, 'register_topic')
    @patch.object(Utilities, 'load_schema')
    def test_add_kafka_topics_called_utilities(self, mock_load_schema, mock_register_topic, mock_register_schema):
        # Arrange
        mock_load_schema.return_value = {'type': 'record', 'name': 'test', 'fields': []}
        mock_register_schema.return_value = None
        mock_register_topic.return_value = None

        topics = {'test_topic': 'path/to/schema.avro'}

        # Act
        AddKafkaTopics.add_kafka_topics(topics)

        # Assert
        mock_load_schema.assert_called_once_with('path/to/schema.avro')
        mock_register_schema.assert_called_once_with(
            avro_schema={'type': 'record', 'name': 'test', 'fields': []},
            topic_name='test_topic'
        )
        mock_register_topic.assert_called_once_with(
            topic_names=list(topics.keys()),
            partitions=1,
            replication_factor=1
        )
