import os
from dotenv import load_dotenv

from .utilities import Utilities

# Load environment variables from a .env file located in the current directory.
# This allows for sensitive information (like API keys or database credentials)
# to be kept out of the source code.

load_dotenv()

CASSANDRA_HOSTS_STR = os.getenv("CASSANDRA_HOSTS_STR")

CASSANDRA_HOSTS = Utilities.get_array_from_str(CASSANDRA_HOSTS_STR, delimiter='json')

CASSANDRA_PORT = os.getenv("CASSANDRA_PORT")

CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE")

CASSANDRA_RETRY_ATTEMPTS = int(os.getenv("CASSANDRA_RETRY_ATTEMPTS")) if os.getenv("CASSANDRA_RETRY_ATTEMPTS") else None

CASSANDRA_RETRY_DELAY = int(os.getenv("CASSANDRA_RETRY_DELAY")) if os.getenv("CASSANDRA_RETRY_DELAY") else None

CASSANDRA_USERNAME = os.getenv("CASSANDRA_USERNAME") or None

CASSANDRA_PASSWORD = os.getenv("CASSANDRA_PASSWORD") or None

CASSANDRA_CONNECTION_NAME = os.getenv("CASSANDRA_CONNECTION_NAME") or None

CASSANDRA_PROTOCOL_VERSION = int(os.getenv("CASSANDRA_PROTOCOL_VERSION")) if os.getenv("CASSANDRA_PROTOCOL_VERSION") else None

CASSANDRA_CONTROL_CONNECTION_TIMEOUT = float(os.getenv("CASSANDRA_CONTROL_CONNECTION_TIMEOUT")) if os.getenv("CASSANDRA_CONTROL_CONNECTION_TIMEOUT") else None

CASSANDRA_CONNECT_TIMEOUT = float(os.getenv("CASSANDRA_CONNECT_TIMEOUT")) if os.getenv("CASSANDRA_CONNECT_TIMEOUT") else None





