import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Retrieve environment variables related to KSQL DB URLs
KSQLDB_URL = os.getenv("KSQLDB_URL")
KSQL_WS_URL = os.getenv("KSQL_WS_URL")

# Retrieve environment variables for Avro schema names used in Kafka topics
SCHEMA_TRADES = os.getenv("SCHEMA_TRADES")
SCHEMA_SP500_COMPANY_PROFILES = os.getenv("SCHEMA_SP500_COMPANY_PROFILES")
SCHEMA_STOCK_SYMBOLS = os.getenv("SCHEMA_STOCK_SYMBOLS")

# Retrieve environment variables for the schema registry URL and Kafka bootstrap servers
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")

# Kafka topic names for different use cases
KAFKA_TOPIC_COMPANY_PROFILES = os.getenv("KAFKA_TOPIC_COMPANY_PROFILES")
KAFKA_TOPIC_TRADES = os.getenv("KAFKA_TOPIC_TRADES")
KAFKA_TOPIC_SYMBOLS = os.getenv("KAFKA_TOPIC_SYMBOLS")

# Kafka configuration settings for partitioning and replication
KAFKA_PARTITIONS = os.getenv("KAFKA_PARTITIONS")
KAFKA_REPLICATION_FACTOR = os.getenv("KAFKA_REPLICATION_FACTOR")
