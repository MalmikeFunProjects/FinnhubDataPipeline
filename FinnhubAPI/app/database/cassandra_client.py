from dataclasses import dataclass
import time
from datetime import date, datetime, timedelta
from typing import List, Dict, Any, Optional, Type, TypeVar, Generic, Union, Tuple

from cassandra.cqlengine import connection, CQLEngineException
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import RetryPolicy, RoundRobinPolicy, ExponentialReconnectionPolicy
from cassandra.cluster import Cluster, NoHostAvailable, AuthenticationFailed, Session
from cassandra.cqlengine.models import Model
from cassandra.query import PreparedStatement
from cassandra.cqlengine.query import AbstractQuerySet

from utils.utilities import Utilities, TimeReturnType
from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("cassandra_client", log_to_console=True)

# Type variable for Model subclasses
T = TypeVar('T', bound=Model)

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
    consistency_level: Optional[int] = None

    def __str__(self) -> str:
        """String representation of the configuration (with masked credentials)"""
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
            Consistency Level: {self.consistency_level}
            """

class CassandraClient:
    """
    Client for Cassandra database operations

    Provides a simplified interface for common Cassandra operations with
    connection pooling, retry logic, and prepared statement caching.
    """
    def __init__(self, config: CassandraConfig):
        """
        Initialize the Cassandra client

        Args:
            config: Configuration for Cassandra connection
        """
        self.config = config
        self.session = None
        self.cluster = None
        self.prepared_statements: Dict[str, PreparedStatement] = {}
        self.current_batch_dict = {}
        self.batch_size = 100
        self.connected = False

    def __enter__(self):
        """Context manager entry point"""
        self.connect_to_cassandra()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit point"""
        self.close_connection()

    def connect_to_cassandra(self):
        """
        Establish connection to Cassandra cluster

        Attempts to connect multiple times based on retry_attempts config
        Raises ConnectionError if all attempts fail
        """
        if self.connected:
            return
        attempts = 0
        last_exception = None
        while attempts < self.config.retry_attempts:
            try:
                logger.info(
                    f"Connecting to Cassandra at {self.config.hosts}: {self.config.port}. "
                    f"Attempt {attempts + 1}/{self.config.retry_attempts}..."
                )

                # Configure authenctication if credentials are provided
                auth_provider = None
                if self.config.username and self.config.password:
                    auth_provider = PlainTextAuthProvider(
                        username=self.config.username,
                        password=self.config.password
                    )

                # Initialize cluster with optimized settings
                self.cluster = Cluster(
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

                # Connect and set keyspace if provided
                self.session = self.cluster.connect()
                if self.config.keyspace:
                    self.session.set_keyspace(self.config.keyspace)

                # Register connection for cqlengine
                connection.register_connection(
                    self.config.connection_name,
                    session=self.session
                )
                connection.set_default_connection(self.config.connection_name)
                self.connected = True
                logger.info("Connected to Cassandra successfully")
                return

            except (NoHostAvailable, AuthenticationFailed) as e:
                attempts += 1
                last_exception = e
                logger.error(f"Connection attempt {attempts} failed: {str(e)}")

                if attempts >= self.config.retry_attempts:
                    logger.error(f"Failed to connect after {self.config.retry_attempts} attempts")
                    break

                # Wait before retry with exponential backoff
                wait_time = self.config.retry_delay * (2 ** (attempts - 1))
                logger.info(f"Waiting {wait_time} seconds before next attempt")
                time.sleep(wait_time)

            except Exception as e:
                logger.error(f"Unexpected error connecting to Cassandra: {str(e)}")
                last_exception = e
                break

        # If we got here, all connection attempts failed
        error_msg = f"Failed to connect to Cassandra: {str(last_exception)}"
        logger.error(error_msg)
        raise ConnectionError(error_msg)

    def close_connection(self) -> None:
        """Close connection to Cassandra cluster"""
        if self.session:
            try:
                logger.info("Closing Cassandra session")
                self.session.shutdown()
                self.session = None
            except Exception as e:
                logger.error(f"Error closing Cassandra session: {str(e)}")

        if self.cluster:
            try:
                logger.info("Closing Cassandra cluster")
                self.cluster.shutdown()
                self.cluster = None
            except Exception as e:
                logger.error(f"Error closing Cassandra cluster: {str(e)}")

        self.connected = False

    def get_session(self) -> Session:
        """
        Get the current Cassandra session

        Returns:
            Active Cassandra session

        Raises:
            ConnectionError: If not connected to Cassandra
        """
        if not self.session or not self.connected:
            raise ConnectionError("Not connected to Cassandra")
        return self.session

    def execute_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        consistency_level: Optional[int] = None
    ) -> Any:
        """
        Execute a CQL query

        Args:
            query: CQL query string
            params: Query parameters
            consistency_level: Override default consistency level

        Returns:
            Query result

        Raises:
            Exception: If query execution fails
        """
        if not self.connected:
            self.connect_to_cassandra()

        try:
            if consistency_level or self.config.consistency_level:
                return self.session.execute(
                    query,
                    params or {},
                    consistency_level=consistency_level or self.config.consistency_level
                )
            else:
                return self.session.execute(query, params or {})
        except Exception as e:
            logger.error(f"Error executing query '{query}': {str(e)}")
            raise

    def get_prepared_statement(self, query: str) -> PreparedStatement:
        """
        Get or create a prepared statement

        Caches prepared statements for reuse

        Args:
            query: CQL query string

        Returns:
            Prepared statement
        """
        if not self.connected:
            self.connect_to_cassandra()

        if query not in self.prepared_statements:
            try:
                self.prepared_statements[query] = self.session.prepare(query)
            except Exception as e:
                logger.error(f"Error preparing statement '{query}': {str(e)}")
                raise

        return self.prepared_statements[query]

    def execute_prepared_statement(
        self,
        query: str,
        params: List[Any] = None,
        consistency_level: Optional[int] = None
    ) -> Any:
        """
        Execute a prepared statement

        Args:
            query: CQL query string to prepare
            params: List of parameters for the prepared statement
            consistency_level: Override default consistency level

        Returns:
            Query result

        Raises:
            Exception: If execution fails
        """
        if not self.connected:
            self.connect_to_cassandra()

        try:
            stmt = self.get_prepared_statement(query)
            bound_stmt = stmt.bind(params or [])

            if consistency_level or self.config.consistency_level:
                bound_stmt.consistency_level = consistency_level or self.config.consistency_level

            return self.session.execute(bound_stmt)
        except Exception as e:
            logger.error(f"Error executing prepared statement '{query}': {str(e)}")
            raise

    def sync_table(self, model_class: Type[Model]) -> None:
        """
        Sync a table schema with Cassandra

        Args:
            model_class: Cassandra model class

        Raises:
            Exception: If sync fails
        """
        from cassandra.cqlengine.management import sync_table

        try:
            logger.info(f"Syncing table for {model_class.__name__}")
            sync_table(model_class)
            logger.info(f"Table sync complete for {model_class.__name__}")
        except Exception as e:
            logger.error(f"Error syncing table for {model_class.__name__}: {str(e)}")
            raise

    def create_item(self, model_class: Type[T], data: Dict[str, Any]) -> T:
        """
        Create a new record using the model

        Args:
            model_class: Cassandra model class
            data: Dictionary of field values

        Returns:
            Created model instance

        Raises:
            Exception: If creation fails
        """
        try:
            return model_class.create(**data)
        except Exception as e:
            logger.error(f"Error creating {model_class.__name__}: {str(e)}")
            raise

    def get_all_items(self, model_class: Type[T]) -> AbstractQuerySet:
        """
        Get all items of a model

        Args:
            model_class: Cassandra model class

        Returns:
            QuerySet of all items
        """
        return model_class.objects.all()

    def get_item_by_keys(self, model_class: Type[T], key_data: Dict[str, Any]) -> T:
        """
        Get a single item by primary key values

        Args:
            model_class: Cassandra model class
            key_data: Dictionary of primary key values

        Returns:
            Model instance

        Raises:
            DoesNotExist: If item not found
        """
        try:
            return model_class.objects.get(**key_data)
        except Exception as e:
            logger.error(f"Error getting {model_class.__name__} by keys {key_data}: {str(e)}")
            raise

    def get_items_by_filter(
        self,
        model_class: Type[T],
        filter_dict: Dict[str, Any],
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        allow_filtering: bool = True
    ) -> AbstractQuerySet:
        """
        Get items matching a filter

        Args:
            model_class: Cassandra model class
            filter_dict: Dictionary of filter conditions
            order_by: Field to order results by
            limit: Maximum number of results
            allow_filtering: Whether to allow filtering on non-indexed fields

        Returns:
            QuerySet of matching items
        """
        try:
            query = model_class.objects.filter(**filter_dict)

            if allow_filtering:
                query = query.allow_filtering()

            if order_by:
                query = query.order_by(order_by)

            if limit is not None:
                query = query.limit(limit)

            return query
        except Exception as e:
            logger.error(f"Error filtering {model_class.__name__}: {str(e)}")
            raise

    def query_time_partitioned_data(
        self,
        model_class: Type[T],
        partition_field: str,
        timestamp_field: str,
        start_date_time: Optional[date | datetime | int] = None,
        end_date_time: Optional[date | datetime | int] = None,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        page_size: int = 100,
        allow_filtering: bool = True
    ) -> Tuple[List[T], Optional[int]]:
        """
        Query time-partitioned data with efficient pagination

        Designed for tables partitioned by date with timestamps in each row.
        Returns both the results and a continuation token for pagination.

        Args:
            model_class: Cassandra model class
            partition_field: Field containing the partition date
            timestamp_field: Field containing the event timestamp
            start_timestamp: Minimum timestamp to include
            end_timestamp: Maximum timestamp to include
            start_date: Starting partition date (computed from start_timestamp if not provided)
            filters: Additional filters to apply
            page_size: Maximum records to return

        Returns:
            Tuple of (results list, continuation timestamp or None if no more results)
        """
        try:
            # Use filters or empty dict if None
            query_filters = filters.copy() if filters else {}

            end_date = Utilities.adjust_datetime(
                original_date=end_date_time,
                return_type=TimeReturnType.DATE
            )
            start_date = Utilities.adjust_datetime(
                original_date=start_date_time,
                duration={'days': 1} if not start_date_time else None,
                return_type=TimeReturnType.DATE
            )

            # Add timestamp filters if provided
            if isinstance(start_date_time, int):
                query_filters[f"{timestamp_field}__gt"] = start_date_time
            if isinstance(end_date_time, int):
                query_filters[f"{timestamp_field}__lt"] = end_date_time

            # Query results
            all_results = []
            current_date = start_date
            remaining = page_size

            # Process each date partition until we have enough results
            while current_date <= end_date and remaining > 0:
                # Set partition for current date
                query_filters[partition_field] = current_date

                # Query this partition
                partition_results = list(self.get_items_by_filter(
                    model_class=model_class,
                    filter_dict=query_filters,
                    order_by=order_by,
                    limit=remaining,
                    allow_filtering=allow_filtering
                ))

                # Add results to our collection
                all_results.extend(partition_results)

                # Update remaining count
                remaining -= len(partition_results)

                # Move to next date
                current_date += timedelta(days=1)

                # Stop if we have a full page
                if len(all_results) >= page_size:
                    break

            # Determine continuation token
            continuation_token = None
            if all_results:
                # Use the timestamp of the last result as the continuation token
                continuation_token = getattr(all_results[-1], timestamp_field)

            return {"records": all_results, "continuation_token": continuation_token}

        except Exception as e:
            logger.error(f"Error querying time-partitioned data: {str(e)}")
            raise

    def batch_operations(self, operations: List[Tuple[str, List]]) -> None:
        """
        Execute multiple operations in a batch

        Args:
            operations: List of (prepared statement query, parameters) tuples

        Raises:
            Exception: If batch execution fails
        """
        if not self.connected:
            self.connect_to_cassandra()

        try:
            from cassandra.query import BatchStatement
            from cassandra.cqlengine import BatchQuery

            # Use cqlengine BatchQuery for model operations
            with BatchQuery() as batch:
                for query, params in operations:
                    prepared = self.get_prepared_statement(query)
                    bound = prepared.bind(params)
                    batch.add_query(bound)

        except Exception as e:
            logger.error(f"Error executing batch operations: {str(e)}")
            raise

    def health_check(self) -> bool:
        """
        Check if the connection to Cassandra is healthy

        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            if not self.connected or not self.session:
                return False

            # Execute a simple query to check connection
            result = self.execute_query("SELECT release_version FROM system.local")
            return len(list(result)) > 0
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
