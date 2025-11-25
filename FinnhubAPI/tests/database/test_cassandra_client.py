from datetime import date, timedelta
import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from cassandra.cluster import Cluster, Session, NoHostAvailable, AuthenticationFailed
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine.query import BatchQuery, LWTException


from app.database.cassandra_client import CassandraClient, CassandraConfig

class TestModel(Model):
    """Mock model class for testing"""
    processing_id = columns.UUID(primary_key=True, default=uuid.uuid4)

@pytest.fixture
def cassandra_config():
    return CassandraConfig(
        hosts=['127.0.0.1'],
        port=9042,
        keyspace='test_keyspace',
        username='test_user',
        password='test_password',
        retry_attempts=3,
        retry_delay=0.1,  # Using a small delay for faster tests
    )

@pytest.fixture
def mock_session():
    session = Mock(spec=Session)
    return session

@pytest.fixture
def mock_cluster():
    cluster = Mock(spec=Cluster)
    return cluster

@pytest.fixture
def mock_connection():
    with patch('cassandra.cqlengine.connection.register_connection') as mock_register:
        with patch('cassandra.cqlengine.connection.set_default_connection') as mock_set_default:
            yield {
                'register': mock_register,
                'set_default': mock_set_default
            }

@pytest.fixture
def mock_batch_query():
    with patch('app.cassandra_client.BatchQuery') as mock_batch:
        batch_instance = Mock()
        batch_instance.queries = []
        mock_batch.return_value = batch_instance
        yield mock_batch

class TestCassandraClient:
    def test_create_auth_provider_with_credentials(self, cassandra_config):
        """Test auth provider creation with valid credentials"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        auth_provider = client._create_auth_provider()

        assert isinstance(auth_provider, PlainTextAuthProvider)
        assert auth_provider.username == cassandra_config.username
        assert auth_provider.password == cassandra_config.password

    def test_create_auth_provider_without_credentials(self, cassandra_config):
        """Test auth provider creation without credentials"""
        config = cassandra_config
        config.username = None
        config.password = None

        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = config

        auth_provider = client._create_auth_provider()

        assert auth_provider is None

    @patch('app.database.cassandra_client.Cluster')
    def test_create_cluster(self, mock_cluster_class, cassandra_config):
        """Test cluster creation with proper configuration"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        auth_provider = Mock()

        client._create_cluster(auth_provider)

        mock_cluster_class.assert_called_once()
        args, kwargs = mock_cluster_class.call_args
        assert kwargs['contact_points'] == cassandra_config.hosts
        assert kwargs['port'] == cassandra_config.port
        assert kwargs['auth_provider'] == auth_provider
        assert kwargs['protocol_version'] == cassandra_config.protocol_version
        assert kwargs['control_connection_timeout'] == cassandra_config.control_connection_timeout
        assert kwargs['connect_timeout'] == cassandra_config.connect_timeout

    def test_connect_to_cluster(self, cassandra_config):
        """Test connecting to cluster"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.cluster = Mock()
        expected_session = Mock()
        client.cluster.connect.return_value = expected_session

        session = client._connect_to_cluster()

        client.cluster.connect.assert_called_once()
        assert session == expected_session

    def test_configure_keyspace(self, cassandra_config):
        """Test keyspace configuration"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = Mock()

        client._configure_keyspace()

        client.session.set_keyspace.assert_called_once_with(cassandra_config.keyspace)

    def test_configure_keyspace_none(self, cassandra_config):
        """Test keyspace configuration when keyspace is None"""
        config = cassandra_config
        config.keyspace = None

        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = config
        client.session = Mock()

        client._configure_keyspace()

        client.session.set_keyspace.assert_not_called()

    def test_register_connection(self, cassandra_config, mock_connection):
        """Test connection registration"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = Mock()

        client._register_connection()

        mock_connection['register'].assert_called_once_with(
            cassandra_config.connection_name,
            session=client.session
        )
        mock_connection['set_default'].assert_called_once_with(cassandra_config.connection_name)

    @patch('app.database.cassandra_client.logger')
    def test_handle_connection_error(self, mock_logger, cassandra_config):
        """Test handling connection error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        exception = Exception("test error")

        client._handle_connection_error(2, exception)

        mock_logger.error.assert_called_once_with("Connection attempt 2 failed: test error")

    @patch('app.database.cassandra_client.time.sleep')
    def test_wait_before_retry(self, mock_sleep, cassandra_config):
        """Test wait before retry"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        result = cassandra_config.retry_delay * (2 ** (0 -1)) # 0 is the default attempt passed to _wait_before_retry()

        client._wait_before_retry()

        mock_sleep.assert_called_once_with(result)

    @patch('app.database.cassandra_client.logger')
    def test_log_connection_attempt(self, mock_logger, cassandra_config):
        """Test logging connection attempt"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        client._log_connection_attempt(1)

        expected_message = f"Connecting to Cassandra at {cassandra_config.hosts}: {cassandra_config.port}. Attempt 2/{cassandra_config.retry_attempts}..."
        mock_logger.info.assert_called_once_with(expected_message)

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_create_cluster')
    @patch.object(CassandraClient, '_connect_to_cluster')
    @patch.object(CassandraClient, '_configure_keyspace')
    @patch.object(CassandraClient, '_register_connection')
    @patch('app.database.cassandra_client.logger')
    def test_connect_to_cassandra_success(
        self, mock_logger, mock_register_conn, mock_configure_keyspace,
        mock_connect_to_cluster, mock_create_cluster, mock_create_auth,
        mock_log_attempt, cassandra_config
    ):
        """Test successful connection to Cassandra"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.connected = False
        mock_auth = Mock()
        mock_cluster = Mock()
        mock_session = Mock()

        mock_create_auth.return_value = mock_auth
        mock_create_cluster.return_value = mock_cluster
        mock_connect_to_cluster.return_value = mock_session

        # Connect
        client.connect_to_cassandra()

        # Verify
        mock_log_attempt.assert_called_once_with(0)
        mock_create_auth.assert_called_once()
        mock_create_cluster.assert_called_once_with(mock_auth)
        mock_connect_to_cluster.assert_called_once()
        mock_configure_keyspace.assert_called_once()
        mock_register_conn.assert_called_once()
        mock_logger.info.assert_called_once_with("Connected to Cassandra successfully")
        assert client.cluster == mock_cluster
        assert client.session == mock_session

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_handle_connection_error')
    @patch.object(CassandraClient, '_wait_before_retry')
    @patch('app.database.cassandra_client.logger')
    def test_connect_to_cassandra_retry_then_success(
        self, mock_logger, mock_wait, mock_handle_error,
        mock_create_auth, mock_log_attempt, cassandra_config
    ):
        """Test connection with a retry and then success"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = False
        client.config = cassandra_config

        # Mock _create_auth_provider to always succeed
        mock_auth = Mock()
        mock_create_auth.return_value = mock_auth

        # Set up side effects for _create_cluster: fail first, succeed second
        side_effects = [
            NoHostAvailable(message="host unavailable", errors={"error": Exception("host unavailable")}),  # First call fails
            Mock()  # Second call succeeds
        ]

        with patch.object(
            CassandraClient, '_create_cluster',
            side_effect=side_effects
        ) as mock_create_cluster:
            with patch.object(
                CassandraClient, '_connect_to_cluster',
                return_value=Mock()
            ) as mock_connect:
                with patch.object(
                    CassandraClient, '_configure_keyspace'
                ) as mock_configure:
                    with patch.object(
                        CassandraClient, '_register_connection'
                    ) as mock_register:
                        # Connect
                        client.connect_to_cassandra()

        # Verify
        assert mock_log_attempt.call_count == 2
        assert mock_create_auth.call_count == 2
        assert mock_handle_error.call_count == 1
        assert mock_wait.call_count == 1
        mock_logger.info.assert_called_once_with("Connected to Cassandra successfully")

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_create_cluster')
    @patch.object(CassandraClient, '_handle_connection_error')
    @patch.object(CassandraClient, '_wait_before_retry')
    @patch('app.database.cassandra_client.logger')
    def test_connect_to_cassandra_max_retries(
        self, mock_logger, mock_wait, mock_handle_error,
        mock_create_cluster, mock_create_auth, mock_log_attempt,
        cassandra_config
    ):
        """Test connection failing after max retries"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = False
        client.config = cassandra_config
        exception = NoHostAvailable(message="host unavailable", errors={"error": Exception("host unavailable")})

        # Mock _create_auth_provider to always succeed
        mock_auth = Mock()
        mock_create_auth.return_value = mock_auth

        # Configure _create_cluster to always fail
        mock_create_cluster.side_effect = exception

        # Connect (should fail)
        with pytest.raises(ConnectionError) as excinfo:
            client.connect_to_cassandra()

        # Verify
        assert "Failed to connect to Cassandra" in str(excinfo.value)
        assert mock_log_attempt.call_count == cassandra_config.retry_attempts
        assert mock_create_auth.call_count == cassandra_config.retry_attempts
        assert mock_create_cluster.call_count == cassandra_config.retry_attempts
        assert mock_handle_error.call_count == cassandra_config.retry_attempts
        assert mock_wait.call_count == cassandra_config.retry_attempts - 1  # No wait after last attempt
        assert mock_logger.error.call_count >= 1

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_create_cluster')
    @patch('app.database.cassandra_client.logger')
    def test_connect_to_cassandra_unexpected_error(
        self, mock_logger, mock_create_cluster,
        mock_create_auth, mock_log_attempt, cassandra_config
    ):
        """Test connection with an unexpected error"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = False
        client.config = cassandra_config
        exception = ValueError("Unexpected error")

        # Mock _create_auth_provider to always succeed
        mock_auth = Mock()
        mock_create_auth.return_value = mock_auth

        # Configure _create_cluster to raise an unexpected error
        mock_create_cluster.side_effect = exception

        # Connect (should fail)
        with pytest.raises(ValueError) as excinfo:
            client.connect_to_cassandra()

        # Verify
        assert "Unexpected error" in str(excinfo.value)
        mock_log_attempt.assert_called_once_with(0)
        mock_create_auth.assert_called_once()
        mock_create_cluster.assert_called_once_with(mock_auth)
        mock_logger.error.assert_called_once_with("Unexpected error connecting to Cassandra: Unexpected error")

    def test_enter_exit_context_manager(self, cassandra_config):
        """Test context manager protocol implementation"""
        with patch.object(CassandraClient, 'connect_to_cassandra') as mock_connect:
            with patch.object(CassandraClient, 'close_connection') as mock_close:
                client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
                client.connected = False
                client.config = cassandra_config

                # Simulate context manager use
                with client as ctx:
                    pass

                # Verify
                mock_close.assert_called_once()
                assert ctx == client

    @patch('app.database.cassandra_client.logger')
    def test_close_connection_with_session(self, mock_logger, cassandra_config):
        """Test closing connection when session exists"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = Mock()
        client.cluster = Mock()
        client.connected = True

        client.close_connection()

        assert mock_logger.info.call_count == 2
        assert client.session is None
        assert client.cluster is None
        assert client.connected is False

    @patch('app.database.cassandra_client.logger')
    def test_close_connection_without_session(self, mock_logger, cassandra_config):
        """Test closing connection when session is None"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = None
        client.cluster = None
        client.connected = True

        client.close_connection()

        # Only one log message (for cluster shutdown) should be logged
        assert mock_logger.info.call_count == 0
        assert client.session is None
        assert client.cluster is None
        assert client.connected is False

    @patch('app.database.cassandra_client.logger')
    def test_close_connection_with_exceptions(self, mock_logger, cassandra_config):
        """Test closing connection with exceptions"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = Mock()
        client.cluster = Mock()

        # Configure mocks to raise exceptions
        client.session.shutdown.side_effect = Exception("Session shutdown error")
        client.cluster.shutdown.side_effect = Exception("Cluster shutdown error")

        client.close_connection()

        # Verify
        client.session.shutdown.assert_called_once()
        client.cluster.shutdown.assert_called_once()
        assert mock_logger.error.call_count == 2
        assert mock_logger.info.call_count == 2

    def test_get_session(self, cassandra_config):
        """Test get_session method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session

        result = client.get_session()

        assert result == mock_session

    def test_execute_query(self, cassandra_config):
        """Test execute_query method with default consistency"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session
        expected_result = Mock()
        mock_session.execute.return_value = expected_result

        query = "SELECT * FROM test"
        params = {"param": "value"}
        result = client.execute_query(query, params)

        mock_session.execute.assert_called_once_with(query, params)
        assert result == expected_result

    def test_execute_query_with_consistency_level(self, cassandra_config):
        """Test execute_query method with custom consistency level"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session
        expected_result = Mock()
        mock_session.execute.return_value = expected_result
        consistency_level = Mock()

        query = "SELECT * FROM test"
        params = {"param": "value"}
        result = client.execute_query(query, params, consistency_level)

        mock_session.execute.assert_called_once_with(query, params, consistency_level=consistency_level)
        assert result == expected_result

    @patch('app.database.cassandra_client.logger')
    def test_execute_query_with_error(self, mock_logger, cassandra_config):
        """Test execute_query method with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session
        error_msg = "Query error"
        mock_session.execute.side_effect = Exception(error_msg)

        query = "SELECT * FROM test"
        with pytest.raises(Exception):
            result = client.execute_query(query)
            assert result is None

        mock_session.execute.assert_called_once_with(query, {})
        mock_logger.error.assert_called_once_with(f"Error executing query '{query}': {error_msg}")

    def test_get_prepared_statement_new(self, cassandra_config):
        """Test get_prepared_statement creating a new statement"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.prepared_statements = {}
        mock_session = Mock()
        client.session = mock_session
        expected_statement = Mock()
        mock_session.prepare.return_value = expected_statement

        query = "SELECT * FROM test WHERE id = ?"
        statement = client.get_prepared_statement(query)

        mock_session.prepare.assert_called_once_with(query)
        assert statement == expected_statement
        assert query in client.prepared_statements
        assert client.prepared_statements[query] == expected_statement

    def test_get_prepared_statement_cached(self, cassandra_config):
        """Test get_prepared_statement using a cached statement"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        mock_statement = Mock()
        query = "SELECT * FROM test WHERE id = ?"
        client.prepared_statements = {query: mock_statement}
        mock_session = Mock()
        client.session = mock_session

        statement = client.get_prepared_statement(query)

        mock_session.prepare.assert_not_called()
        assert statement == mock_statement

    @patch('app.database.cassandra_client.logger')
    def test_get_prepared_statement_with_error(self, mock_logger, cassandra_config):
        """Test execute_query method with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.prepared_statements = {}
        mock_session = Mock()
        client.session = mock_session
        error_msg = "Prepare error"
        mock_session.prepare.side_effect = Exception(error_msg)

        query = "SELECT * FROM test WHERE id = ?"
        with pytest.raises(Exception):
            result = client.get_prepared_statement(query)
            assert result is None

        mock_session.prepare.assert_called_once_with(query)
        mock_logger.error.assert_called_once_with(f"Error preparing statement '{query}': {error_msg}")

    @patch('cassandra.cqlengine.management.sync_table')
    @patch('app.database.cassandra_client.logger')
    def test_sync_table(self, mock_logger, mock_sync_table, cassandra_config):
        """Test sync_table method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        client.sync_table(TestModel)

        mock_sync_table.assert_called_once_with(TestModel)
        mock_logger.info.call_count == 2
        mock_logger.info.assert_called_with(f"Table sync complete for {TestModel.__name__}")

    @patch('cassandra.cqlengine.management.sync_table')
    @patch('app.database.cassandra_client.logger')
    def test_sync_table_with_error(self, mock_logger, mock_sync_table, cassandra_config):
        """Test execute_query method with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        error_msg = "Sync error"
        mock_sync_table.side_effect = Exception(error_msg)

        with pytest.raises(Exception):
            client.sync_table(TestModel)

        mock_sync_table.assert_called_once_with(TestModel)
        mock_logger.error.assert_called_once_with(f"Error syncing table for {TestModel.__name__}: {error_msg}")

    def test_create_item(self, cassandra_config):
        """Test add_data_using_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        test_data = {"id": 1, "name": "test"}
        expected_result = Mock()

        with patch.object(TestModel, 'create', return_value=expected_result) as mock_create:
            result = client.create_item(TestModel, test_data)

            mock_create.assert_called_once_with(**test_data)
            assert result == expected_result

    @patch('app.database.cassandra_client.logger')
    def test_create_item_with_error(self, mock_logger, cassandra_config):
        """Test add_data_using_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        test_data = {"id": 1, "name": "test"}
        error_msg = "Create item error"

        with patch.object(TestModel, 'create', side_effect=Exception(error_msg)) as mock_create:
            with pytest.raises(Exception):
                result = client.create_item(TestModel, test_data)
                assert result == None

            mock_create.assert_called_once_with(**test_data)
            mock_logger.error.assert_called_once_with(f"Error creating {TestModel.__name__}: {error_msg}")

    def test_get_all_items(self, cassandra_config):
        """Test get_all_items_by_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        mock_all = Mock()
        mock_objects.all.return_value = mock_all

        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_all_items(TestModel)

            mock_objects.all.assert_called_once()
            assert result == mock_all

    def test_get_item_by_keys(self, cassandra_config):
        """Test get_item_by_key_data method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        mock_item = Mock()
        mock_objects.get.return_value = mock_item
        key_data = {"id": 1}

        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_item_by_keys(TestModel, key_data)

            mock_objects.get.assert_called_once_with(**key_data)
            assert result == mock_item

    @patch('app.database.cassandra_client.logger')
    def test_get_item_by_with_error(self, mock_logger, cassandra_config):
        """Test get_item_by_key_data method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        error_msg = "Get item error"
        mock_objects.get.side_effect = Exception(error_msg)

        key_data = {"id": 1}

        with patch.object(TestModel, 'objects', mock_objects):
            with pytest.raises(Exception):
                result = client.get_item_by_keys(TestModel, key_data)
                assert result == None

            mock_objects.get.assert_called_once_with(**key_data)
            mock_logger.error.assert_called_once_with(f"Error getting {TestModel.__name__} by keys {key_data}: {error_msg}")

    def test_execute_prepared_statement(self, cassandra_config):
        """Test execute_prepared_statement method with proper parameters"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()

        # Create mocks for the prepared statement flow
        mock_stmt = Mock()
        mock_bound_stmt = Mock()
        mock_result = Mock()

        # Set up the chain of method calls
        client.get_prepared_statement = Mock(return_value=mock_stmt)
        mock_stmt.bind.return_value = mock_bound_stmt
        client.session.execute.return_value = mock_result

        # Execute the test
        query = "SELECT * FROM test WHERE id = ?"
        params = [1]
        result = client.execute_prepared_statement(query, params)

        # Verify
        client.get_prepared_statement.assert_called_once_with(query)
        mock_stmt.bind.assert_called_once_with(params)
        client.session.execute.assert_called_once_with(mock_bound_stmt)
        assert result == mock_result

    def test_execute_prepared_statement_with_consistency(self, cassandra_config):
        """Test execute_prepared_statement with consistency level"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()
        consistency_level = Mock(name="consistency_level")

        # Create mocks for the prepared statement flow
        mock_stmt = Mock()
        mock_bound_stmt = Mock()
        mock_result = Mock()

        # Set up the chain of method calls
        client.get_prepared_statement = Mock(return_value=mock_stmt)
        mock_stmt.bind.return_value = mock_bound_stmt
        client.session.execute.return_value = mock_result

        # Execute the test
        query = "SELECT * FROM test WHERE id = ?"
        params = [1]
        result = client.execute_prepared_statement(query, params, consistency_level)

        # Verify
        client.get_prepared_statement.assert_called_once_with(query)
        mock_stmt.bind.assert_called_once_with(params)
        assert mock_bound_stmt.consistency_level == consistency_level
        client.session.execute.assert_called_once_with(mock_bound_stmt)
        assert result == mock_result

    def test_execute_prepared_statement_with_default_consistency(self, cassandra_config):
        """Test execute_prepared_statement with default consistency level"""
        config = cassandra_config
        config.consistency_level = Mock(name="default_consistency_level")

        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = config
        client.session = Mock()

        # Create mocks for the prepared statement flow
        mock_stmt = Mock()
        mock_bound_stmt = Mock()
        mock_result = Mock()

        # Set up the chain of method calls
        client.get_prepared_statement = Mock(return_value=mock_stmt)
        mock_stmt.bind.return_value = mock_bound_stmt
        client.session.execute.return_value = mock_result

        # Execute the test
        query = "SELECT * FROM test WHERE id = ?"
        params = [1]
        result = client.execute_prepared_statement(query, params)

        # Verify
        client.get_prepared_statement.assert_called_once_with(query)
        mock_stmt.bind.assert_called_once_with(params)
        assert mock_bound_stmt.consistency_level == config.consistency_level
        client.session.execute.assert_called_once_with(mock_bound_stmt)
        assert result == mock_result

    @patch('app.database.cassandra_client.logger')
    def test_execute_prepared_statement_with_error(self, mock_logger, cassandra_config):
        """Test execute_prepared_statement method with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()

        # Create mocks and set up error
        mock_stmt = Mock()
        error_msg = "Execute prepared statement error"
        client.get_prepared_statement = Mock(return_value=mock_stmt)
        mock_stmt.bind.side_effect = Exception(error_msg)

        # Execute the test
        query = "SELECT * FROM test WHERE id = ?"
        params = [1]

        with pytest.raises(Exception):
            client.execute_prepared_statement(query, params)

        # Verify
        client.get_prepared_statement.assert_called_once_with(query)
        mock_stmt.bind.assert_called_once_with(params)
        mock_logger.error.assert_called_once_with(f"Error executing prepared statement '{query}': {error_msg}")

    def test_get_items_by_filter_basic(self, cassandra_config):
        """Test get_items_by_filter with basic options"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Create mocks for query chain
        mock_objects = Mock()
        mock_filter = Mock()
        mock_allow_filtering = Mock()

        # Chain setup
        mock_objects.filter.return_value = mock_filter
        mock_filter.allow_filtering.return_value = mock_allow_filtering

        # Test data
        filter_dict = {"field1": "value1", "field2": "value2"}

        # Patch the model's objects property
        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_items_by_filter(
                model_class=TestModel,
                filter_dict=filter_dict
            )

        # Verify
        mock_objects.filter.assert_called_once_with(**filter_dict)
        mock_filter.allow_filtering.assert_called_once()
        assert result == mock_allow_filtering

    def test_get_items_by_filter_all_options(self, cassandra_config):
        """Test get_items_by_filter with all options"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Create mocks for query chain
        mock_objects = Mock()
        mock_filter = Mock()
        mock_allow_filtering = Mock()
        mock_order_by = Mock()
        mock_limit = Mock()

        # Chain setup
        mock_objects.filter.return_value = mock_filter
        mock_filter.allow_filtering.return_value = mock_allow_filtering
        mock_allow_filtering.order_by.return_value = mock_order_by
        mock_order_by.limit.return_value = mock_limit

        # Test data
        filter_dict = {"field1": "value1", "field2": "value2"}
        order_by_field = "timestamp"
        limit_value = 10

        # Patch the model's objects property
        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_items_by_filter(
                model_class=TestModel,
                filter_dict=filter_dict,
                order_by=order_by_field,
                limit=limit_value,
                allow_filtering=True
            )

        # Verify
        mock_objects.filter.assert_called_once_with(**filter_dict)
        mock_filter.allow_filtering.assert_called_once()
        mock_allow_filtering.order_by.assert_called_once_with(order_by_field)
        mock_order_by.limit.assert_called_once_with(limit_value)
        assert result == mock_limit

    def test_get_items_by_filter_no_allow_filtering(self, cassandra_config):
        """Test get_items_by_filter without allow_filtering"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Create mocks for query chain
        mock_objects = Mock()
        mock_filter = Mock()
        mock_order_by = Mock()
        mock_limit = Mock()

        # Chain setup
        mock_objects.filter.return_value = mock_filter
        mock_filter.order_by.return_value = mock_order_by
        mock_order_by.limit.return_value = mock_limit

        # Test data
        filter_dict = {"field1": "value1", "field2": "value2"}
        order_by_field = "timestamp"
        limit_value = 10

        # Patch the model's objects property
        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_items_by_filter(
                model_class=TestModel,
                filter_dict=filter_dict,
                order_by=order_by_field,
                limit=limit_value,
                allow_filtering=False
            )

        # Verify
        mock_objects.filter.assert_called_once_with(**filter_dict)
        mock_filter.allow_filtering.assert_not_called()
        mock_filter.order_by.assert_called_once_with(order_by_field)
        mock_order_by.limit.assert_called_once_with(limit_value)
        assert result == mock_limit

    @patch('app.database.cassandra_client.logger')
    def test_get_items_by_filter_with_error(self, mock_logger, cassandra_config):
        """Test get_items_by_filter with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Create mocks for query chain
        mock_objects = Mock()
        error_msg = "Filter error"
        mock_objects.filter.side_effect = Exception(error_msg)

        # Test data
        filter_dict = {"field1": "value1", "field2": "value2"}

        # Patch the model's objects property
        with patch.object(TestModel, 'objects', mock_objects):
            with pytest.raises(Exception):
                client.get_items_by_filter(
                    model_class=TestModel,
                    filter_dict=filter_dict
                )

        # Verify
        mock_objects.filter.assert_called_once_with(**filter_dict)
        mock_logger.error.assert_called_once_with(f"Error filtering {TestModel.__name__}: {error_msg}")

    @patch('app.utils.utilities.Utilities.adjust_datetime')
    def test_query_time_partitioned_data_basic(self, mock_adjust_datetime, cassandra_config):
        """Test query_time_partitioned_data with basic functionality"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.connected = True

        # Mock dates
        end_date = date(2023, 1, 3)
        start_date = date(2023, 1, 1)

        # Configure adjust_datetime return values
        mock_adjust_datetime.side_effect = [end_date, start_date]

        # Test data
        partition_field = "day"
        timestamp_field = "created_at"

        # Create mock for get_items_by_filter
        mock_results_day1 = [Mock(created_at=1000), Mock(created_at=2000)]
        mock_results_day2 = [Mock(created_at=3000), Mock(created_at=4000)]
        mock_results_day3 = [Mock(created_at=5000)]

        # Create a side effect for get_items_by_filter
        def mock_get_items_by_filter(*args, **kwargs):
            filter_dict = kwargs.get('filter_dict', {})
            day = filter_dict.get(partition_field)

            if day == start_date:
                return mock_results_day1
            elif day == start_date + timedelta(days=1):
                return mock_results_day2
            elif day == start_date + timedelta(days=2):
                return mock_results_day3
            return []

        client.get_items_by_filter = Mock(side_effect=mock_get_items_by_filter)

        # Execute the test
        result = client.query_time_partitioned_data(
            model_class=TestModel,
            partition_field=partition_field,
            timestamp_field=timestamp_field,
            start_date_time=start_date,
            end_date_time=end_date
        )

        # # Verify
        expected_calls = [
            call(
                model_class=TestModel,
                filter_dict={partition_field: start_date},
                order_by=None,
                limit=100,
                allow_filtering=True
            ),
            call(
                model_class=TestModel,
                filter_dict={partition_field: start_date + timedelta(days=1)},
                order_by=None,
                limit=98,  # 100 - 2 from day 1
                allow_filtering=True
            ),
            call(
                model_class=TestModel,
                filter_dict={partition_field: start_date + timedelta(days=2)},
                order_by=None,
                limit=96,  # 100 - 2 from day 1 - 2 from day 2
                allow_filtering=True
            )
        ]
        client.get_items_by_filter.assert_has_calls(expected_calls)

        # # Check result
        assert result["records"] == mock_results_day1 + mock_results_day2 + mock_results_day3
        assert result["continuation_token"] == 5000  # last timestamp

    @patch('app.utils.utilities.Utilities.adjust_datetime')
    def test_query_time_partitioned_data_with_integer_timestamps(self, mock_adjust_datetime, cassandra_config):
        """Test query_time_partitioned_data with integer timestamps"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Mock dates
        end_date = date(2023, 1, 1)
        start_date = date(2023, 1, 1)

        # Configure adjust_datetime return values
        mock_adjust_datetime.side_effect = [end_date, start_date]

        # Test data
        partition_field = "day"
        timestamp_field = "created_at"
        start_timestamp = 1000
        end_timestamp = 5000

        # Create mock for get_items_by_filter
        mock_results = [Mock(created_at=2000), Mock(created_at=3000)]
        client.get_items_by_filter = Mock(return_value=mock_results)

        # Execute the test
        result = client.query_time_partitioned_data(
            model_class=TestModel,
            partition_field=partition_field,
            timestamp_field=timestamp_field,
            start_date_time=start_timestamp,
            end_date_time=end_timestamp
        )

        # Verify
        expected_filter = {
            partition_field: start_date,
            f"{timestamp_field}__gt": start_timestamp,
            f"{timestamp_field}__lt": end_timestamp
        }

        client.get_items_by_filter.assert_called_with(
            model_class=TestModel,
            filter_dict=expected_filter,
            order_by=None,
            limit=100,
            allow_filtering=True
        )

        # Check result
        assert result["records"] == mock_results
        assert result["continuation_token"] == 3000  # last timestamp

    @patch('app.utils.utilities.Utilities.adjust_datetime')
    def test_query_time_partitioned_data_inclusive_bounds(self, mock_adjust_datetime, cassandra_config):
        """Test query_time_partitioned_data with inclusive timestamp bounds"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Mock dates
        end_date = date(2023, 1, 1)
        start_date = date(2023, 1, 1)

        # Configure adjust_datetime return values
        mock_adjust_datetime.side_effect = [end_date, start_date]

        # Test data
        partition_field = "day"
        timestamp_field = "created_at"
        start_timestamp = 1000
        end_timestamp = 5000

        # Create mock for get_items_by_filter
        mock_results = [Mock(created_at=2000), Mock(created_at=3000)]
        client.get_items_by_filter = Mock(return_value=mock_results)

        # Execute the test
        result = client.query_time_partitioned_data(
            model_class=TestModel,
            partition_field=partition_field,
            timestamp_field=timestamp_field,
            start_date_time=start_timestamp,
            end_date_time=end_timestamp,
            gt_inclusive=True,
            lt_inclusive=True
        )

        # Verify
        expected_filter = {
            partition_field: start_date,
            f"{timestamp_field}__gte": start_timestamp,
            f"{timestamp_field}__lte": end_timestamp
        }

        client.get_items_by_filter.assert_called_with(
            model_class=TestModel,
            filter_dict=expected_filter,
            order_by=None,
            limit=100,
            allow_filtering=True
        )

        # Check result
        assert result["records"] == mock_results
        assert result["continuation_token"] == 3000  # last timestamp

    @patch('app.utils.utilities.Utilities.adjust_datetime')
    @patch('app.database.cassandra_client.logger')
    def test_query_time_partitioned_data_with_error(self, mock_logger, mock_adjust_datetime, cassandra_config):
        """Test query_time_partitioned_data with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        # Mock dates
        end_date = date(2023, 1, 2)
        start_date = date(2023, 1, 1)

        # Configure adjust_datetime return values
        mock_adjust_datetime.side_effect = [end_date, start_date]

        # Set up error in get_items_by_filter
        error_msg = "Query error"
        client.get_items_by_filter = Mock(side_effect=Exception(error_msg))

        # Execute the test
        with pytest.raises(Exception):
            client.query_time_partitioned_data(
                model_class=TestModel,
                partition_field="day",
                timestamp_field="created_at",
                start_date_time=start_date,
                end_date_time=end_date
            )

        # Verify
        mock_logger.error.assert_called_once_with(f"Error querying time-partitioned data: {error_msg}")

    @patch('cassandra.cqlengine.query.BatchQuery')
    def test_batch_operations(self, mock_batch_query_class, cassandra_config):
        """Test batch_operations execution"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config

        # Set up mocks
        mock_batch_instance = Mock()
        mock_batch_query_class.return_value.__enter__.return_value = mock_batch_instance

        # Prepare statements and parameters
        prepared_statements = [
            Mock(name="stmt1"),
            Mock(name="stmt2")
        ]
        bound_statements = [
            Mock(name="bound1"),
            Mock(name="bound2")
        ]

        # Chain setup
        prepared_statements[0].bind.return_value = bound_statements[0]
        prepared_statements[1].bind.return_value = bound_statements[1]

        # Client setup for get_prepared_statement
        client.get_prepared_statement = Mock(side_effect=prepared_statements)

        # Operations to batch
        operations = [
            ("INSERT INTO test (id, name) VALUES (?, ?)", [1, "Test 1"]),
            ("UPDATE test SET name = ? WHERE id = ?", ["Test 2", 2])
        ]

        # Execute the test
        client.batch_operations(operations)

        # Verify
        assert client.get_prepared_statement.call_count == 2
        client.get_prepared_statement.assert_has_calls([
            call(operations[0][0]),
            call(operations[1][0])
        ])

        prepared_statements[0].bind.assert_called_once_with(operations[0][1])
        prepared_statements[1].bind.assert_called_once_with(operations[1][1])

        mock_batch_instance.add_query.assert_has_calls([
            call(bound_statements[0]),
            call(bound_statements[1])
        ])

    @patch('app.database.cassandra_client.logger')
    @patch('cassandra.cqlengine.query.BatchQuery')
    def test_batch_operations_with_error(self, mock_batch_query_class, mock_logger, cassandra_config):
        """Test batch_operations with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config

        # Set up error
        error_msg = "Batch operation error"
        mock_batch_query_class.side_effect = Exception(error_msg)

        # Operations to batch
        operations = [
            ("INSERT INTO test (id, name) VALUES (?, ?)", [1, "Test 1"])
        ]

        # Execute the test
        with pytest.raises(Exception):
            client.batch_operations(operations)

        # Verify
        mock_logger.error.assert_called_once_with(f"Error executing batch operations: {error_msg}")

    def test_health_check_connected(self, cassandra_config):
        """Test health_check when connected and healthy"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()

        # Mock execute_query to return a non-empty result
        client.execute_query = Mock(return_value=[{"release_version": "3.11.0"}])

        # Execute the test
        result = client.health_check()

        # Verify
        client.execute_query.assert_called_once_with("SELECT release_version FROM system.local")
        assert result is True

    def test_health_check_not_connected(self, cassandra_config):
        """Test health_check when not connected"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = False
        client.config = cassandra_config
        client.session = None

        # Execute the test
        result = client.health_check()

        # Verify
        assert result is False

    def test_health_check_empty_result(self, cassandra_config):
        """Test health_check when query returns empty result"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()

        # Mock execute_query to return an empty result
        client.execute_query = Mock(return_value=[])

        # Execute the test
        result = client.health_check()

        # Verify
        client.execute_query.assert_called_once_with("SELECT release_version FROM system.local")
        assert result is False

    @patch('app.database.cassandra_client.logger')
    def test_health_check_with_error(self, mock_logger, cassandra_config):
        """Test health_check when query raises an exception"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.connected = True
        client.config = cassandra_config
        client.session = Mock()

        # Mock execute_query to raise an exception
        error_msg = "Connection error"
        client.execute_query = Mock(side_effect=Exception(error_msg))

        # Execute the test
        result = client.health_check()

        # Verify
        client.execute_query.assert_called_once_with("SELECT release_version FROM system.local")
        mock_logger.error.assert_called_once_with(f"Health check failed: {error_msg}")
        assert result is False
