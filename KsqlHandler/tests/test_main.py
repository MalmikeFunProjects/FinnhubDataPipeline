import pytest
from unittest.mock import Mock, patch, call
from app.execute_ksql.execute_ksql_request import ExecuteKsqlRequest
from app.execute_ksql.make_ksql_request import MakeKsqlRequest
from app.set_kafka_topics.add_kafka_topics import AddKafkaTopics
from app.utils.enums import StorageType
import app.utils.settings as UTILS
from app.main import KsqlHandler  # Assuming this is the file where KsqlHandler is defined

@pytest.fixture
def mock_make_ksql_request():
    """Fixture for mocking MakeKsqlRequest class"""
    with patch('app.execute_ksql.make_ksql_request.MakeKsqlRequest') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        mock_instance.check_storage_type_exists.return_value = True
        yield mock_instance

@pytest.fixture
def mock_add_kafka_topics():
    """Fixture for mocking AddKafkaTopics class"""
    with patch('app.set_kafka_topics.add_kafka_topics.AddKafkaTopics') as mock_class:
        yield mock_class

@pytest.fixture
def mock_execute_ksql_request():
    """Fixture for mocking ExecuteKsqlRequest class"""
    with patch('app.execute_ksql.execute_ksql_request.ExecuteKsqlRequest') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def sample_topics():
    """Fixture providing sample topics dictionary"""
    return {
        "topic1": "schema1.avsc",
        "topic2": "schema2.avsc",
        "topic3": "schema3.avsc"
    }

class TestKsqlHandler:
    """Test suite for KsqlHandler class"""

    def test_init_calls_methods(self, mock_make_ksql_request, mock_add_kafka_topics,
                               mock_execute_ksql_request, sample_topics):
        """Test that __init__ calls the necessary methods"""
        with patch.object(KsqlHandler, 'add_kafka_topics') as mock_add_topics:
            with patch.object(KsqlHandler, 'execute_ksql_request') as mock_execute:
                # Instantiate KsqlHandler
                handler = KsqlHandler(topics=sample_topics)

                # Verify methods were called
                mock_add_topics.assert_called_once()
                mock_execute.assert_called_once()

                # Verify topics are set correctly
                assert handler.topics == sample_topics

   