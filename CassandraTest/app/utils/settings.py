import os
from dotenv import load_dotenv

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
