import time
import pytest
from unittest.mock import patch, MagicMock
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns

from app.cassandra_client.setup_client import SetupClient
from app.cassandra_client.cassandra_client import CassandraConfig


class DummyModel(Model):
    partition_date = columns.Date(
            primary_key=True,
            partition_key=True,
            default=time.time())


class TestSetupClient:
    @pytest.fixture
    def config(self):
        return CassandraConfig(
            hosts=["127.0.0.1"],
            keyspace="test_keyspace",
            username="user",
            password="pass"
        )

    @pytest.fixture
    def setup_client(self, config):
        return SetupClient(config)

    @pytest.fixture
    def custom_models(self):
        return {"Dummy": DummyModel}

    @patch("app.cassandra_client.setup_client.logger")
    @patch("app.cassandra_client.setup_client.CassandraClient")
    def test_setup_tables(self, mock_cassandra_client, mock_logger, setup_client, custom_models):
        # Create a mock instance for the context manager
        mock_client_instance = MagicMock()
        mock_cassandra_client.return_value.__enter__.return_value = mock_client_instance
