from dataclasses import dataclass
import time
from cassandra.cqlengine import connection
from cassandra.auth import PlainTextAuthProvider
from cassandra.policies import RetryPolicy, RoundRobinPolicy, ExponentialReconnectionPolicy
from cassandra.cluster import Cluster, NoHostAvailable, AuthenticationFailed
from cassandra.cqlengine.models import Model

from utils.utilities import Utilities, TimeReturnType

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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
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

    def sync_table(self, CustomModel: type[Model]):
        from cassandra.cqlengine.management import sync_table
        logging.info(type(CustomModel))
        sync_table(CustomModel)

    def add_data_using_model(self, CustomModel: type[Model], data: dict):
        return CustomModel.create(**data)

    def get_all_items_by_model(self, CustomModel: type[Model]):
        return CustomModel.objects.all()

    def get_limited_items_by_model(self, CustomModel: type[Model], limit: int):
        return CustomModel.objects.limit(limit)

    def get_item_by_key_data(self, CustomModel: type[Model], key_data: dict):
        return CustomModel.objects.get(**key_data)

    def get_limited_items_by_filter(self, CustomModel: type[Model], filter: dict, order_by: str = None, limit: int = None):
        query = CustomModel.objects.filter(**filter).allow_filtering()
        if order_by:
            query = query.order_by(order_by)
        if limit:
            query = query.limit(limit)
        return query

    def get_all_items_by_partition_date(self, CustomModel: type[Model], batch_size: int=100, set_start_date: int=None, data_filter_properties: dict[str, any] = {}) -> dict[str, list[type[Model]]| dict[str, any] ]| None:
        if "last_processed_timestamp" not in data_filter_properties or set_start_date is not None:
            set_start_date = set_start_date or 2
            data_filter_properties["last_processed_timestamp"] = Utilities.adjust_datetime(duration={'days': set_start_date}, start_of_day=True)

        if "start_date" not in data_filter_properties or set_start_date is not None:
            set_start_date = set_start_date or 2
            data_filter_properties["start_date"] = Utilities.adjust_datetime(duration={'days': set_start_date}, return_type=TimeReturnType.DATE)


        print(f"Current record date: {data_filter_properties["start_date"]}, batch size: {batch_size}")
        filter = {
            "partition_date": data_filter_properties["start_date"],
            "insertion_timestamp__gt": data_filter_properties["last_processed_timestamp"]
        }
        if "extra_filters" in data_filter_properties:
            filter.update(data_filter_properties["extra_filters"])

        records = self.get_limited_items_by_filter(
            CustomModel=CustomModel,
            filter=filter,
            limit=batch_size
        )

        records_list = list(records)
        remaining_batch_size = batch_size - len(records_list) if records_list else batch_size
        if not records_list or remaining_batch_size > 0 :
            # add a date
            current_date = Utilities.adjust_datetime(return_type=TimeReturnType.DATE)
            if data_filter_properties["start_date"] < current_date:
                data_filter_properties["start_date"] = Utilities.adjust_datetime(
                    duration={'days': 1},
                    return_type=TimeReturnType.DATE,
                    previous_date=False,
                    original_date=data_filter_properties["start_date"]
                )
                print(f"Adjusting record date: {data_filter_properties["start_date"]}, batch size: {remaining_batch_size}")
                response_data = self.get_all_items_by_partition_date(CustomModel=CustomModel, batch_size=remaining_batch_size, data_filter_properties=data_filter_properties)
                if response_data["records_list"]:
                    records_list.extend(response_data["records_list"])

        if records_list:
            data_filter_properties["last_processed_timestamp"] = records_list[-1].insertion_timestamp
            data_filter_properties["start_date"] = records_list[-1].partition_date

        return {"records_list": records_list, "data_filter_properties": data_filter_properties}


