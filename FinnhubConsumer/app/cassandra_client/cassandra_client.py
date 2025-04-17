from dataclasses import dataclass
import time
from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import RetryPolicy, RoundRobinPolicy, ExponentialReconnectionPolicy
from cassandra.cluster import Cluster, BatchStatement, NoHostAvailable, AuthenticationFailed
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery, LWTException

from app.utils.funtion_timer import FunctionTimer
from app.utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("cassandra_client", log_to_console=True)

@dataclass
class CassandraConfig:
    hosts: list[str]
    port: int = 9042
    keyspace: str = None
    username: str = None
    password: str = None
    retry_attempts: int = 3
    retry_delay: int = 5
    connection_name: str = 'default'
    protocol_version: int = 4
    control_connection_timeout: float = 10.0
    connect_timeout: float = 10.0

    def __str__(self):
        return f"""
    Hosts: {self.hosts}
    Port: {self.port}
    Keyspace: {self.keyspace}
    Username: {'**********' if self.username else None}
    Password: {'**********' if self.password else None}
    Retry Attempts: {self.retry_attempts}
    Retry Delay: {self.retry_delay}
    Connection Name: {self.connection_name}
    Protocol Version: {self.protocol_version}
    Control Connection Timeout: {self.control_connection_timeout}
    Connect Timeout: {self.connect_timeout}
    """

class CassandraClient:
    def __init__(self, config: CassandraConfig):
        self.config = config
        self.session = None
        self.cluster = None
        self.prepared_statements = {}
        self.current_batch_dict = {}
        self.batch_size = 100
        self.connect_to_cassandra()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def connect_to_cassandra(self):
        """
        Establishes a connection to Cassandra with retry logic.
        Raises ConnectionError if all connection attempts fail.
        """
        attempts = 0
        while attempts < self.config.retry_attempts:
            try:
                self._log_connection_attempt(attempts)

                auth_provider = self._create_auth_provider()
                self.cluster = self._create_cluster(auth_provider)
                self.session = self._connect_to_cluster()

                self._configure_keyspace()
                self._register_connection()

                logger.info("Connected to Cassandra")
                return

            except (NoHostAvailable, AuthenticationFailed) as e:
                attempts += 1
                self._handle_connection_error(attempts, e)
                if attempts >= self.config.retry_attempts:
                    error_msg = f"Failed to connect to Cassandra after {self.config.retry_attempts} attempts."
                    logger.error(error_msg)
                    raise ConnectionError(f"Failed to connect to Cassandra: {str(e)}.")

                self._wait_before_retry()
            except Exception as e:
                logger.error(f"An unexpected error occurred: {str(e)}")
                raise

        # This line shouldn't be reached due to the raise in the except block,
        # but it's here for clarity and as a safety net
        raise ConnectionError("Failed to connect to Cassandra after all retry attempts.")

    def _log_connection_attempt(self, attempts):
        """Log the current connection attempt."""
        logger.info(
            f"Connecting to Cassandra at {self.config.hosts}: {self.config.port}. "
            f"Attempt {attempts + 1}/{self.config.retry_attempts}..."
        )

    def _create_auth_provider(self):
        """Create and return an auth provider if credentials are provided."""
        if self.config.username and self.config.password:
            return PlainTextAuthProvider(
                username=self.config.username,
                password=self.config.password
            )
        return None

    def _create_cluster(self, auth_provider):
        """Create and return a Cassandra cluster instance."""
        return Cluster(
            contact_points=self.config.hosts,
            port=self.config.port,
            auth_provider=auth_provider,
            load_balancing_policy=RoundRobinPolicy(),
            default_retry_policy=RetryPolicy(),
            reconnection_policy=ExponentialReconnectionPolicy(base_delay=1, max_delay=60),
            protocol_version=self.config.protocol_version,
            control_connection_timeout=self.config.control_connection_timeout,
            connect_timeout=self.config.connect_timeout
        )

    def _connect_to_cluster(self):
        """Connect to the cluster and return the session."""
        return self.cluster.connect()

    def _configure_keyspace(self):
        """Set the keyspace if specified in the configuration."""
        if self.config.keyspace:
            self.session.set_keyspace(self.config.keyspace)

    def _register_connection(self):
        """Register and set as default connection in the CQL engine."""
        connection.register_connection(self.config.connection_name, session=self.session)
        connection.set_default_connection(self.config.connection_name)

    def _handle_connection_error(self, attempts, exception):
        """Handle connection errors by logging the error."""
        logger.error(f"Connection attempt {attempts} failed: {str(exception)}")

    def _wait_before_retry(self):
        """Wait for the configured delay before retrying."""
        time.sleep(self.config.retry_delay)

    def close_connection(self):
        if self.session:
            try:
                logger.info("Closing Cassandra connection...")
                self.session.shutdown()
            except Exception as e:
                logger.error(f"Error closing Cassandra connection: {str(e)}")

        if self.cluster:
            try:
                logger.info("Closing Cassandra cluster...")
                self.cluster.shutdown()
            except Exception as e:
                logger.error(f"Error closing Cassandra cluster: {str(e)}")

    def get_session(self):
        return self.session

    def execute_query(self, query, params=None, consistency_level=None):
        try:
            if consistency_level:
                return self.session.execute(query, params or {}, consistency_level=consistency_level)
            else:
                return self.session.execute(query, params or {})
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")

    def get_prepared_statement(self, query):
        if query not in self.prepared_statements:
            self.prepared_statements[query] = self.session.prepare(query)
        return self.prepared_statements[query]

    def sync_table(self, CustomModel: type[Model]):
        from cassandra.cqlengine.management import sync_table
        logger.info(type(CustomModel))
        sync_table(CustomModel)

    def add_data_using_model(self, CustomModel: type[Model], data: dict):
        return CustomModel.create(**data)

    def get_all_items_by_model(self, CustomModel: type[Model]):
        return CustomModel.objects.all()

    def get_limited_items_by_model(self, CustomModel: type[Model], limit: int):
        return CustomModel.objects.limit(limit)


    def get_item_by_key_data(self, CustomModel: type[Model], key_data: dict):
        return CustomModel.objects.get(**key_data)

    def add_batch_data(self, batch_size: int = 100, CustomModel: type[Model] = None, data: dict = None, only_unique: bool = False, batch_duration: int = 60):
        if(not CustomModel and not data):
            raise ValueError("CustomModel or data is required for batch queries")

        try:
            custom_model = CustomModel(**data)
            if only_unique:
                try:
                    was_applied = custom_model.if_not_exists().save()
                    # The save() method returns True if the LWT was applied, False otherwise
                    if was_applied:
                        logger.info(f"Conditional save executed for {CustomModel.__name__}")
                    else:
                        logger.info(f"Conditional save skipped for {CustomModel.__name__} - record already exists")
                    return 0
                except LWTException as lwt_ex:
                    # This is not an error, but information that the condition wasn't met
                    logger.info(f"LWT not applied for {CustomModel.__name__}: {data.get('symbol', 'unknown')} - record already exists")
                    return False
            else:
                if(CustomModel.__name__ not in self.current_batch_dict.keys()):
                    self.current_batch_dict[CustomModel.__name__] = BatchQuery()
                current_batch = self.current_batch_dict[CustomModel.__name__]

                custom_model.batch(current_batch).save()

                function_timer = FunctionTimer()
                current_batch_size = len(current_batch.queries)

                if(current_batch_size >= batch_size):
                    current_batch.execute()
                    logger.info(f"Batch {CustomModel.__name__} written to cassandra")
                    current_batch = BatchQuery()
                    self.current_batch_dict[CustomModel.__name__] = current_batch
                    function_timer.cancel_timer(CustomModel.__name__)
                elif(current_batch_size > 0):
                    kwargs={"add_batch_data": True, "CustomModel":CustomModel}
                    function_timer.run_timer_if_not_exist(
                        timer_name=CustomModel.__name__,
                        duration=batch_duration,
                        action=self.clear_batch,
                        kwargs=kwargs
                    )
                else:
                    function_timer.cancel_timer(CustomModel.__name__)

                return len(current_batch.queries)
        except Exception as e:
            logger.error(f"Error adding batch data: {str(e)}")
            raise e

    def clear_batch(self, add_batch_data: bool = False, CustomModel: type[Model] = None):
        logger.info("Clearing batch objects ...")
        if(add_batch_data):
            try:
                if(CustomModel):
                    if(CustomModel.__name__ in self.current_batch_dict.keys() and len(self.current_batch_dict[CustomModel.__name__].queries) > 0):
                        batch_size = len(self.current_batch_dict[CustomModel.__name__].queries)
                        self.current_batch_dict[CustomModel.__name__].execute()
                        logger.info(f"Batch {CustomModel.__name__} written to cassandra, size: {batch_size}")
                    self.current_batch_dict[CustomModel.__name__] = BatchQuery()
                else:
                    for key, batch in self.current_batch_dict.items():
                        batch_size = len(batch.queries)
                        if(batch_size > 0):
                            batch.execute()
                            logger.info(f"Batch {key} written to cassandra, size: {batch_size}")
                    self.current_batch_dict = {}
            except Exception as e:
                logger.error(f"Error clearing batch: {str(e)}")
                raise e
        else:
            self.current_batch_dict = {}
            logger.info("Batch objects cleared")


