import os
from dotenv import load_dotenv

from .utilities import Utilities

# Load environment variables from a .env file located in the current directory.
# This allows for sensitive information (like API keys or database credentials)
# to be kept out of the source code.

load_dotenv()

# Retrieve the SCHEMA_REGISTRY_URL from the environment variables
# This URL points to the schema registry for registering and managing schemas
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")

# Retrieve the BOOTSTRAP_SERVERS from the environment variables
# This is a comma-separated list of Kafka brokers used to connect to the Kafka cluster
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")

# Retrieve the Kafka topic for the latest stock prices from environment variables
# This is the topic where the latest stock prices are published to or consumed from
KAFKA_TOPIC_LATEST_PRICES = os.getenv("KAFKA_TOPIC_LATEST_PRICES")

# Retrieve the Kafka topic for the stock summary from environment variables
# This topic is used for the stock summary data (for example, aggregates of stock price data)
KAFKA_TOPIC_STOCK_SUMMARY = os.getenv("KAFKA_TOPIC_STOCK_SUMMARY")

KAFKA_TOPIC_COMPANY_SYMBOLS = os.getenv("KAFKA_TOPIC_COMPANY_SYMBOLS")

KAFKA_TOPIC_STOCK_PRICES_1S = os.getenv("KAFKA_TOPIC_STOCK_PRICES_1S")

CASSANDRA_HOSTS_STR = os.getenv("CASSANDRA_HOSTS_STR")

CASSANDRA_HOSTS = Utilities.get_array_from_str(CASSANDRA_HOSTS_STR, delimiter='json')

CASSANDRA_PORT = os.getenv("CASSANDRA_PORT")

CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE")

CASSANDRA_RETRY_ATTEMPTS = int(os.getenv("CASSANDRA_RETRY_ATTEMPTS"))

CASSANDRA_RETRY_DELAY = int(os.getenv("CASSANDRA_RETRY_DELAY"))


