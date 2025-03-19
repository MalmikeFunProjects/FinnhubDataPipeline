from database.cassandra_client import CassandraConfig
import utils.settings as Utils

def get_cassandra_config():
    return CassandraConfig(
        hosts=Utils.CASSANDRA_HOSTS or None,
        port=Utils.CASSANDRA_PORT or 9042,
        keyspace=Utils.CASSANDRA_KEYSPACE or None,
        retry_attempts=Utils.CASSANDRA_RETRY_ATTEMPTS or 3,
        retry_delay=Utils.CASSANDRA_RETRY_DELAY or 5,
        username=Utils.CASSANDRA_USERNAME or None,
        password=Utils.CASSANDRA_PASSWORD or None,
        connection_name=Utils.CASSANDRA_CONNECTION_NAME or 'default',
        protocol_version=Utils.CASSANDRA_PROTOCOL_VERSION or 4,
        control_connection_timeout=Utils.CASSANDRA_CONTROL_CONNECTION_TIMEOUT or 10.0,
        connect_timeout=Utils.CASSANDRA_CONNECT_TIMEOUT or 10.0,
    )
