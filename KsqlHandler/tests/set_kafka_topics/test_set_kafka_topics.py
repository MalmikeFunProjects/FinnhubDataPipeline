import pytest
from unittest.mock import MagicMock, patch
from confluent_kafka.cimpl import KafkaException
from confluent_kafka.admin import AdminClient, NewTopic
from confluent_kafka.schema_registry import SchemaRegistryClient, Schema
from confluent_kafka.schema_registry.error import SchemaRegistryError

# Import the class to test
from confluent_kafka.admin import TopicMetadata
from app.set_kafka_topics.set_kafka_topics import SetUpKafkaTopics


class TestSetUpKafkaTopics:
    """Test suite for the SetUpKafkaTopics class."""

    @pytest.fixture
    def mock_admin_client(self):
        """Fixture for mocking the AdminClient."""
        with patch('confluent_kafka.admin.AdminClient') as mock_admin:
            mock_instance = MagicMock()
            mock_admin.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_schema_registry_client(self):
        """Fixture for mocking the SchemaRegistryClient."""
        with patch('confluent_kafka.schema_registry.SchemaRegistryClient') as mock_sr:
            mock_instance = MagicMock()
            mock_sr.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def test_setup(self, mock_admin_client, mock_schema_registry_client):
        """Fixture for creating a test instance with mocked dependencies."""
        with patch('app.set_kafka_topics.set_kafka_topics.AdminClient', return_value=mock_admin_client):
            with patch('app.set_kafka_topics.set_kafka_topics.SchemaRegistryClient', return_value=mock_schema_registry_client):
                setup = SetUpKafkaTopics("http://schema-registry:8081", "kafka:9092")
                yield setup, mock_admin_client, mock_schema_registry_client

    def test_init(self, test_setup):
        """Test the initialization of SetUpKafkaTopics."""
        setup, mock_admin, mock_sr = test_setup

        assert setup.schema_registry_url == "http://schema-registry:8081"
        assert setup.admin_client == mock_admin
        assert setup.schema_registry_client == mock_sr

    def test_check_topic_exists_true(self, test_setup):
        """Test check_topic_exists returns True when topic doesn't exist."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to return a list of topics that doesn't include our test topic
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {"existing-topic": None}
        mock_admin.list_topics.return_value = mock_topic_list

        # Check a topic that doesn't exist
        result = setup.check_topic_exists("non-existing-topic")

        assert result is True
        mock_admin.list_topics.assert_called_once()

    def test_check_topic_exists_false(self, test_setup):
        """Test check_topic_exists returns False when topic exists."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to return a list of topics that includes our test topic
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {"test-topic": None}
        mock_admin.list_topics.return_value = mock_topic_list

        # Check a topic that exists
        result = setup.check_topic_exists("test-topic")

        assert result is False
        mock_admin.list_topics.assert_called_once()

    def test_register_schema_success(self, test_setup):
        """Test successful schema registration."""
        setup, _, mock_sr = test_setup

        avro_schema = '{"type": "record", "name": "test", "fields": [{"name": "field1", "type": "string"}]}'
        topic_name = "test-topic"

        # Mock the register_schema method to return a schema ID
        mock_sr.register_schema.return_value = 123

        # Call the method
        setup.register_schema(avro_schema, topic_name)

        # Verify the schema registry client was called correctly
        mock_sr.register_schema.assert_called_once()

        # Get the arguments passed to register_schema
        call_args = mock_sr.register_schema.call_args
        assert call_args[0][0] == "test-topic-value"  # The subject name
        assert isinstance(call_args[1]["schema"], Schema)  # The schema object

    def test_register_schema_registry_error(self, test_setup):
        """Test schema registration failure due to SchemaRegistryError."""
        setup, _, mock_sr = test_setup

        avro_schema = '{"type": "record", "name": "test", "fields": [{"name": "field1", "type": "string"}]}'
        topic_name = "test-topic"

        # Mock the register_schema method to raise a SchemaRegistryError
        mock_sr.register_schema.side_effect = SchemaRegistryError(400, 400, "Invalid schema")

        # Verify the exception is propagated
        with pytest.raises(SchemaRegistryError):
            setup.register_schema(avro_schema, topic_name)

    def test_register_schema_general_error(self, test_setup):
        """Test schema registration failure due to general Exception."""
        setup, _, mock_sr = test_setup

        avro_schema = '{"type": "record", "name": "test", "fields": [{"name": "field1", "type": "string"}]}'
        topic_name = "test-topic"

        # Mock the register_schema method to raise a general Exception
        mock_sr.register_schema.side_effect = Exception("Connection error")

        # Verify the exception is propagated
        with pytest.raises(Exception):
            setup.register_schema(avro_schema, topic_name)

    def test_register_topic_no_topics_to_create(self, test_setup):
        """Test register_topic when all topics already exist."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to indicate that topics already exist
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {"topic1": None, "topic2": None}
        mock_admin.list_topics.return_value = mock_topic_list

        # Call the method with topics that already exist
        setup.register_topic(["topic1", "topic2"])

        # Verify create_topics was not called since all topics exist
        mock_admin.create_topics.assert_not_called()

    def test_register_topic_create_topics(self, test_setup):
        """Test register_topic when topics need to be created."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to indicate that topics don't exist
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {"existing-topic": None}
        mock_admin.list_topics.return_value = mock_topic_list

        # Mock the future results for create_topics
        mock_future = MagicMock()
        mock_admin.create_topics.return_value = {"new-topic": mock_future}

        # Call the method with topics that need to be created
        setup.register_topic(["new-topic"])

        # Verify create_topics was called with the correct NewTopic objects
        mock_admin.create_topics.assert_called_once()

        # Extract the first argument (list of NewTopic objects)
        topics_arg = mock_admin.create_topics.call_args[0][0]
        assert len(topics_arg) == 1
        assert isinstance(topics_arg[0], NewTopic)
        assert topics_arg[0].topic == "new-topic"
        assert topics_arg[0].num_partitions == 1
        assert topics_arg[0].replication_factor == 1

    def test_register_topic_with_custom_partitions_and_replication(self, test_setup):
        """Test register_topic with custom partitions and replication factor."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to indicate that topics don't exist
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {}
        mock_admin.list_topics.return_value = mock_topic_list

        # Mock the future results for create_topics
        mock_future = MagicMock()
        mock_admin.create_topics.return_value = {"new-topic": mock_future}

        # Call the method with custom partitions and replication factor
        setup.register_topic(["new-topic"], partitions=3, replication_factor=2)

        # Verify create_topics was called with the correct NewTopic objects
        mock_admin.create_topics.assert_called_once()

        # Extract the first argument (list of NewTopic objects)
        topics_arg = mock_admin.create_topics.call_args[0][0]
        assert len(topics_arg) == 1
        assert isinstance(topics_arg[0], NewTopic)
        assert topics_arg[0].topic == "new-topic"
        assert topics_arg[0].num_partitions == 3
        assert topics_arg[0].replication_factor == 2

    def test_register_topic_creation_failure(self, test_setup):
        """Test register_topic when topic creation fails."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to indicate that topics don't exist
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {}
        mock_admin.list_topics.return_value = mock_topic_list

        # Mock the future results to raise a KafkaException
        mock_future = MagicMock()
        mock_future.result.side_effect = KafkaException("Topic creation failed")
        mock_admin.create_topics.return_value = {"new-topic": mock_future}

        # Call the method - should not raise the exception but should print an error
        with patch('builtins.print') as mock_print:
            setup.register_topic(["new-topic"])

            # Verify the error message was printed
            mock_print.assert_called_with("Failed to create topic new-topic: Topic creation failed")

    def test_register_topic_general_exception(self, test_setup):
        """Test register_topic when a general exception occurs."""
        setup, mock_admin, _ = test_setup

        # Setup the mock to indicate that topics don't exist
        mock_topic_list = MagicMock()
        mock_topic_list.topics = {}
        mock_admin.list_topics.return_value = mock_topic_list

        # Mock create_topics to raise an exception
        mock_admin.create_topics.side_effect = Exception("General error")

        # Verify the exception is propagated
        with pytest.raises(Exception, match="General error"):
            setup.register_topic(["new-topic"])
