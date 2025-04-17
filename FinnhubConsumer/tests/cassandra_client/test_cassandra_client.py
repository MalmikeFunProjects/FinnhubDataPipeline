import uuid
import pytest
from unittest.mock import Mock, patch, MagicMock, call
from cassandra.cluster import Cluster, Session, NoHostAvailable, AuthenticationFailed
from cassandra.cqlengine.models import Model
from cassandra.cqlengine import columns
from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.cqlengine.query import BatchQuery, LWTException


from app.utils.funtion_timer import FunctionTimer
from app.cassandra_client.cassandra_client import CassandraClient, CassandraConfig

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

    @patch('app.cassandra_client.cassandra_client.Cluster')
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

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_handle_connection_error(self, mock_logger, cassandra_config):
        """Test handling connection error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        exception = Exception("test error")

        client._handle_connection_error(2, exception)

        mock_logger.error.assert_called_once_with("Connection attempt 2 failed: test error")

    @patch('app.cassandra_client.cassandra_client.time.sleep')
    def test_wait_before_retry(self, mock_sleep, cassandra_config):
        """Test wait before retry"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        client._wait_before_retry()

        mock_sleep.assert_called_once_with(cassandra_config.retry_delay)

    @patch('app.cassandra_client.cassandra_client.logger')
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
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_connect_to_cassandra_success(
        self, mock_logger, mock_register_conn, mock_configure_keyspace,
        mock_connect_to_cluster, mock_create_cluster, mock_create_auth,
        mock_log_attempt, cassandra_config
    ):
        """Test successful connection to Cassandra"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
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
        mock_logger.info.assert_called_once_with("Connected to Cassandra")
        assert client.cluster == mock_cluster
        assert client.session == mock_session

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_handle_connection_error')
    @patch.object(CassandraClient, '_wait_before_retry')
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_connect_to_cassandra_retry_then_success(
        self, mock_logger, mock_wait, mock_handle_error,
        mock_create_auth, mock_log_attempt, cassandra_config
    ):
        """Test connection with a retry and then success"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
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
        mock_logger.info.assert_called_once_with("Connected to Cassandra")

    @patch.object(CassandraClient, '_log_connection_attempt')
    @patch.object(CassandraClient, '_create_auth_provider')
    @patch.object(CassandraClient, '_create_cluster')
    @patch.object(CassandraClient, '_handle_connection_error')
    @patch.object(CassandraClient, '_wait_before_retry')
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_connect_to_cassandra_max_retries(
        self, mock_logger, mock_wait, mock_handle_error,
        mock_create_cluster, mock_create_auth, mock_log_attempt,
        cassandra_config
    ):
        """Test connection failing after max retries"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
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
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_connect_to_cassandra_unexpected_error(
        self, mock_logger, mock_create_cluster,
        mock_create_auth, mock_log_attempt, cassandra_config
    ):
        """Test connection with an unexpected error"""
        # Setup
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
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
        mock_logger.error.assert_called_once_with("An unexpected error occurred: Unexpected error")

    def test_enter_exit_context_manager(self, cassandra_config):
        """Test context manager protocol implementation"""
        with patch.object(CassandraClient, 'connect_to_cassandra') as mock_connect:
            with patch.object(CassandraClient, 'close_connection') as mock_close:
                client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
                client.config = cassandra_config

                # Simulate context manager use
                with client as ctx:
                    pass

                # Verify
                mock_close.assert_called_once()
                assert ctx == client

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_close_connection(self, mock_logger, cassandra_config):
        """Test closing connection"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        client.session = Mock()
        client.cluster = Mock()

        client.close_connection()

        client.session.shutdown.assert_called_once()
        client.cluster.shutdown.assert_called_once()
        assert mock_logger.info.call_count == 2

    @patch('app.cassandra_client.cassandra_client.logger')
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
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session

        result = client.get_session()

        assert result == mock_session

    def test_execute_query(self, cassandra_config):
        """Test execute_query method with default consistency"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
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

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_execute_query_with_error(self, mock_logger, cassandra_config):
        """Test execute_query method with error"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_session = Mock()
        client.session = mock_session
        mock_session.execute.side_effect = Exception("Query error")

        query = "SELECT * FROM test"
        result = client.execute_query(query)

        mock_session.execute.assert_called_once_with(query, {})
        mock_logger.error.assert_called_once_with("Error executing query: Query error")
        assert result is None

    def test_get_prepared_statement_new(self, cassandra_config):
        """Test get_prepared_statement creating a new statement"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
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
        client.config = cassandra_config
        mock_statement = Mock()
        query = "SELECT * FROM test WHERE id = ?"
        client.prepared_statements = {query: mock_statement}
        mock_session = Mock()
        client.session = mock_session

        statement = client.get_prepared_statement(query)

        mock_session.prepare.assert_not_called()
        assert statement == mock_statement

    @patch('cassandra.cqlengine.management.sync_table')
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_sync_table(self, mock_logger, mock_sync_table, cassandra_config):
        """Test sync_table method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config

        client.sync_table(TestModel)

        mock_sync_table.assert_called_once_with(TestModel)
        mock_logger.info.assert_called_once_with(type(TestModel))

    def test_add_data_using_model(self, cassandra_config):
        """Test add_data_using_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        test_data = {"id": 1, "name": "test"}
        expected_result = Mock()

        with patch.object(TestModel, 'create', return_value=expected_result) as mock_create:
            result = client.add_data_using_model(TestModel, test_data)

            mock_create.assert_called_once_with(**test_data)
            assert result == expected_result

    def test_get_all_items_by_model(self, cassandra_config):
        """Test get_all_items_by_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        mock_all = Mock()
        mock_objects.all.return_value = mock_all

        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_all_items_by_model(TestModel)

            mock_objects.all.assert_called_once()
            assert result == mock_all

    def test_get_limited_items_by_model(self, cassandra_config):
        """Test get_limited_items_by_model method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        mock_limited = Mock()
        mock_objects.limit.return_value = mock_limited
        limit = 10

        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_limited_items_by_model(TestModel, limit)

            mock_objects.limit.assert_called_once_with(limit)
            assert result == mock_limited

    def test_get_item_by_key_data(self, cassandra_config):
        """Test get_item_by_key_data method"""
        client = CassandraClient.__new__(CassandraClient)  # Create instance without calling __init__
        client.config = cassandra_config
        mock_objects = Mock()
        mock_item = Mock()
        mock_objects.get.return_value = mock_item
        key_data = {"id": 1}

        with patch.object(TestModel, 'objects', mock_objects):
            result = client.get_item_by_key_data(TestModel, key_data)

            mock_objects.get.assert_called_once_with(**key_data)
            assert result == mock_item

    def test_add_batch_data_missing_params(self, cassandra_config):
        """Test add_batch_data method with missing parameters"""
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config

        with pytest.raises(ValueError) as excinfo:
            client.add_batch_data()

        assert "CustomModel or data is required for batch queries" in str(excinfo.value)

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_add_batch_data_unique_record_created(self, mock_logger, cassandra_config):
        """Test add_batch_data method with unique record that doesn't exist"""
        # Create client
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config

        # Set up data
        processing_id = uuid.uuid4()
        data = {"id": 1, "name": "test", "processing_id": processing_id}

        # Create mock model class
        MockModel = Mock(spec=TestModel)
        MockModel.__name__ = "TestModel"

        # Create mock model instance
        model_instance = Mock()
        if_not_exists_mock = Mock()
        if_not_exists_mock.save.return_value = True  # Indicate LWT was applied (record didn't exist)
        model_instance.if_not_exists.return_value = if_not_exists_mock

        # Setup MockModel to return our model_instance when called
        MockModel.return_value = model_instance

        # Setup connection mocks
        with patch('app.cassandra_client.cassandra_client.connection.get_connection') as mock_get_conn, \
            patch('app.cassandra_client.cassandra_client.connection.get_cluster') as mock_get_cluster:

            # Mock cluster and session
            mock_cluster = Mock()
            mock_session = Mock()
            mock_cluster.connect.return_value = mock_session
            mock_get_cluster.return_value = mock_cluster
            mock_get_conn.return_value = mock_session

            # Set up protocol version
            mock_cluster.protocol_version = cassandra_config.protocol_version

            # Mock the connection setup that normally happens in __init__
            client.session = mock_session

            # Call the method under test
            result = client.add_batch_data(CustomModel=MockModel, data=data, only_unique=True)

            # Assert expected results
            assert result == 0  # The method returns 0 for successful unique operations
            model_instance.if_not_exists.assert_called_once()
            if_not_exists_mock.save.assert_called_once()
            # Verify log message
            mock_logger.info.assert_any_call("Conditional save executed for TestModel")

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_add_batch_data_unique_record_exists(self, mock_logger, cassandra_config):
        """Test add_batch_data method with unique record that already exists"""
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config
        processing_id = uuid.uuid4()
        data = {"id": 1, "name": "test", "processing_id": processing_id}

        # Mock the model instance behavior
        MockModel = Mock(spec=TestModel)
        MockModel.__name__ = "TestModel"
         # Create mock model instance
        model_instance = Mock()
        if_not_exists_mock = Mock()
        if_not_exists_mock.save.return_value = False  # Indicate LWT was applied (record exists)
        model_instance.if_not_exists.return_value = if_not_exists_mock

        # Setup MockModel to return our model_instance when called
        MockModel.return_value = model_instance

        # Setup connection mocks
        with patch('app.cassandra_client.cassandra_client.connection.get_connection') as mock_get_conn, \
            patch('app.cassandra_client.cassandra_client.connection.get_cluster') as mock_get_cluster:
            # Mock cluster and session
            mock_cluster = Mock()
            mock_session = Mock()
            mock_cluster.connect.return_value = mock_session
            mock_get_cluster.return_value = mock_cluster
            mock_get_conn.return_value = mock_session
            # Set up protocol version
            mock_cluster.protocol_version = cassandra_config.protocol_version

            # Mock the connection setup that normally happens in __init__
            client.session = mock_session

            # Call the method under test
            result = client.add_batch_data(CustomModel=MockModel, data=data, only_unique=True)
            # Assert expected results
            assert result == 0  # The method returns 0 for successful unique operations
            model_instance.if_not_exists.assert_called_once()
            if_not_exists_mock.save.assert_called_once()
            mock_logger.info.assert_called_with(f"Conditional save skipped for {TestModel.__name__} - record already exists")


    @patch('app.cassandra_client.cassandra_client.logger')
    def test_add_batch_data_unique_lwt_exception(self, mock_logger, cassandra_config):
        """Test add_batch_data method with LWTException"""
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config
        processing_id = uuid.uuid4()
        data = {"id": 1, "name": "test", "processing_id": processing_id, "symbol": "TEST"}

        # Mock the model instance behavior
        MockModel = Mock(spec=TestModel)
        MockModel.__name__ = "TestModel"

         # Create mock model instance
        model_instance = Mock()
        if_not_exists_mock = Mock()
        if_not_exists_mock.save.side_effect = LWTException("Record exists")
        model_instance.if_not_exists.return_value = if_not_exists_mock

        # Setup MockModel to return our model_instance when called
        MockModel.return_value = model_instance

        # Setup connection mocks
        with patch('app.cassandra_client.cassandra_client.connection.get_connection') as mock_get_conn, \
            patch('app.cassandra_client.cassandra_client.connection.get_cluster') as mock_get_cluster:
            # Mock cluster and session
            mock_cluster = Mock()
            mock_session = Mock()
            mock_cluster.connect.return_value = mock_session
            mock_get_cluster.return_value = mock_cluster
            mock_get_conn.return_value = mock_session
            # Set up protocol version
            mock_cluster.protocol_version = cassandra_config.protocol_version

            # Mock the connection setup that normally happens in __init__
            client.session = mock_session
            # Call the method under test
            result = client.add_batch_data(CustomModel=MockModel, data=data, only_unique=True)
            # Assert expected results
            assert result == False  # The method returns 0 for successful unique operations
            model_instance.if_not_exists.assert_called_once()
            if_not_exists_mock.save.assert_called_once()
            mock_logger.info.assert_called_with(f"LWT not applied for {TestModel.__name__}: TEST - record already exists")


    @patch('app.cassandra_client.cassandra_client.BatchQuery')
    @patch('app.cassandra_client.cassandra_client.FunctionTimer')
    @patch('app.cassandra_client.cassandra_client.logger')
    def test_add_batch_data_new_batch(self, mock_logger, mock_timer_class, mock_batch_query, cassandra_config):
        """Test add_batch_data method with a new batch"""
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config
        client.current_batch_dict = {}

        # Mock BatchQuery
        batch_instance = Mock()
        batch_instance.queries = [Mock()]  # One query
        mock_batch_query.return_value = batch_instance

        # Mock FunctionTimer
        mock_timer = Mock()
        mock_timer_class.return_value = mock_timer

        # Mock model instance
        model_instance = Mock()
        batch_model = Mock()
        model_instance.batch.return_value = batch_model

        processing_id = uuid.uuid4()
        data = {"id": 1, "name": "test", "processing_id": processing_id, "symbol": "TEST"}

        # Mock the model instance behavior
        MockModel = Mock(spec=TestModel)
        MockModel.__name__ = "TestModel"

        # Setup MockModel to return our model_instance when called
        MockModel.return_value = model_instance
        # Setup connection mocks
        with patch('app.cassandra_client.cassandra_client.connection.get_connection') as mock_get_conn, \
            patch('app.cassandra_client.cassandra_client.connection.get_cluster') as mock_get_cluster:
            # Mock cluster and session
            mock_cluster = Mock()
            mock_session = Mock()
            mock_cluster.connect.return_value = mock_session
            mock_get_cluster.return_value = mock_cluster
            mock_get_conn.return_value = mock_session
            # Set up protocol version
            mock_cluster.protocol_version = cassandra_config.protocol_version

            # Mock the connection setup that normally happens in __init__
            client.session = mock_session
            result = client.add_batch_data(batch_size=10, CustomModel=MockModel, data=data)
            model_instance.batch.assert_called_once_with(batch_instance)
            batch_model.save.assert_called_once()
            mock_timer.run_timer_if_not_exist.assert_called_once()
            assert result == 1

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_clear_batch_without_add_batch_data(self, mock_logger, cassandra_config):
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config
        client.current_batch_dict = {'TestModel': Mock()}

        # Run clear_batch with add_batch_data=False
        client.clear_batch(add_batch_data=False)

        # Assert that current_batch_dict is now empty
        assert client.current_batch_dict == {}
        mock_logger.info.assert_called_with("Batch objects cleared")

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_clear_batch_with_custom_model(self, mock_logger, cassandra_config):
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config

        # Setup mock batch
        batch_instance = Mock()
        batch_instance.queries = [Mock()] * 3  # simulate 3 queries
        TestModel.__name__ = "TestModel"
        client.current_batch_dict = {"TestModel": batch_instance}

        # Run clear_batch with a specific model
        client.clear_batch(add_batch_data=True, CustomModel=TestModel)

        # Verify batch was executed and reset
        batch_instance.execute.assert_called_once()
        assert isinstance(client.current_batch_dict["TestModel"], BatchQuery)
        mock_logger.info.assert_any_call("Batch TestModel written to cassandra, size: 3")

    @patch('app.cassandra_client.cassandra_client.logger')
    def test_clear_batch_all_models(self, mock_logger, cassandra_config):
        client = CassandraClient.__new__(CassandraClient)
        client.config = cassandra_config

        # Setup multiple mock batches
        batch_one = Mock()
        batch_one.queries = [Mock(), Mock()]
        batch_two = Mock()
        batch_two.queries = [Mock()]

        client.current_batch_dict = {
            "ModelOne": batch_one,
            "ModelTwo": batch_two
        }

        # Run clear_batch on all
        client.clear_batch(add_batch_data=True)

        # Assertions
        batch_one.execute.assert_called_once()
        batch_two.execute.assert_called_once()
        mock_logger.info.assert_any_call("Batch ModelOne written to cassandra, size: 2")
        mock_logger.info.assert_any_call("Batch ModelTwo written to cassandra, size: 1")
        assert client.current_batch_dict == {}
