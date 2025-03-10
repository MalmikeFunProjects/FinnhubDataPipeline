from dataclasses import dataclass
import time
from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import RetryPolicy, RoundRobinPolicy, ExponentialReconnectionPolicy
from cassandra.cluster import Cluster, BatchStatement, NoHostAvailable, AuthenticationFailed
from cassandra.cqlengine.models import Model
from cassandra.cqlengine.query import BatchQuery


import logging

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



class CassandraClient:
    def __init__(self, config: CassandraConfig):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.config = config
        self.session = None
        self.cluster = None
        self.prepared_statements = {}
        self.current_batch = BatchQuery()
        self.batch_size = 100
        self.connect_to_cassandra()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()

    def connect_to_cassandra(self):
        attempts = 0
        while attempts < self.config.retry_attempts:
            try:
                self.logger.info(f"Connecting to Cassandra at {self.config.hosts}: {self.config.port}. Attempt {attempts + 1}/{self.config.retry_attempts}...")

                # Configure authenctication if credentials are provided
                auth_provider = PlainTextAuthProvider(
                    username=self.config.username,
                    password=self.config.password
                ) if self.config.username and self.config.password else None

                # Create cluster
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

                self.session = self.cluster.connect()

                if self.config.keyspace:
                    self.session.set_keyspace(self.config.keyspace)

                connection.register_connection(self.config.connection_name, session=self.session)
                connection.set_default_connection(self.config.connection_name)

                self.logger.info("Connected to Cassandra")
                return

            except (NoHostAvailable, AuthenticationFailed)  as e:
                attempts += 1
                self.logger.error(f"Connection attempt {attempts}   failed: {str(e)}")
                if attempts >= self.config.retry_attempts:
                    self.logger.error(f"Failed to connect to Cassandra after {self.config.retry_attempts} attempts.")
                    raise ConnectionError(f"Failed to connect to Cassandra: {str(e)}.")

                time.sleep(self.config.retry_delay)
            except Exception as e:
                self.logger.error(f"An unexpected error occurred: {str(e)}")
                raise


    def close_connection(self):
        if self.session:
            try:
                self.logger.info("Closing Cassandra connection...")
                self.session.shutdown()
            except Exception as e:
                self.logger.error(f"Error closing Cassandra connection: {str(e)}")

        if self.cluster:
            try:
                self.logger.info("Closing Cassandra cluster...")
                self.cluster.shutdown()
            except Exception as e:
                self.logger.error(f"Error closing Cassandra cluster: {str(e)}")

    def get_session(self):
        return self.session

    def execute_query(self, query, params=None, consistency_level=None):
        try:
            if consistency_level:
                return self.session.execute(query, params or {}, consistency_level=consistency_level)
            else:
                return self.session.execute(query, params or {})
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")

    def get_prepared_statement(self, query):
        if query not in self.prepared_statements:
            self.prepared_statements[query] = self.session.prepare(query)
        return self.prepared_statements[query]

    def sync_table(self, CustomModel: Model.__class__):
        from cassandra.cqlengine.management import sync_table
        sync_table(CustomModel)

    def add_data_using_model(self, CustomModel: Model.__class__, data: dict):
        return CustomModel.create(**data)

    def get_all_items_by_model(self, CustomModel: Model.__class__):
        return CustomModel.objects.all()

    def get_limited_items_by_model(self, CustomModel: Model.__class__, limit: int):
        return CustomModel.objects.limit(limit)


    def get_item_by_key_data(self, CustomModel: Model.__class__, key_data: dict):
        return CustomModel.objects.get(**key_data)

    def add_batch_data(self, batch_size: int = 100, CustomModel: Model.__class__ = None, data: dict = None):
        if(CustomModel and data):
            CustomModel.batch(self.current_batch).create(**data)
        if(len(self.current_batch.queries) >= batch_size):
            self.current_batch.execute()
            self.logger.info("Batch written to cassandra")
            self.current_batch = BatchQuery()

    def clear_batch(self, add_batch_data: bool = False):
        if(add_batch_data):
            self.current_batch.execute()
            self.logger.info("Batch written to cassandra")
        self.current_batch = BatchQuery()
