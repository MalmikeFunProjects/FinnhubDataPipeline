import os
from dotenv import load_dotenv

# Load environment variables from a .env file
# This loads all the environment variables from a .env file into the current Python environment
load_dotenv()

# Retrieve specific environment variables using os.getenv
# These variables contain essential configuration settings for the application

# API key for accessing Finnhub services
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

# File path to a local file containing S&P 500 company profiles
SP500_COMPANY_PROFILES_FILE_PATH = os.getenv("SP500_COMPANY_PROFILES_FILE_PATH")

# URL for accessing the list of S&P 500 companies
SP500_COMPANIES_URL = os.getenv("SP500_COMPANIES_URL")

# URL for accessing US big tech companies' information
US_BIG_TECH_URL = os.getenv("US_BIG_TECH_URL")

# Schemas for various data types used in the application (retrieved from the schema registry)
SCHEMA_TRADES = os.getenv("SCHEMA_TRADES")
SCHEMA_SP500_COMPANY_PROFILES = os.getenv("SCHEMA_SP500_COMPANY_PROFILES")
SCHEMA_STOCK_SYMBOLS = os.getenv("SCHEMA_STOCK_SYMBOLS")

# Configuration for the Kafka schema registry and servers
SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")

# Kafka topics for different types of messages (company profiles, trades, stock symbols)
KAFKA_TOPIC_COMPANY_PROFILES = os.getenv("KAFKA_TOPIC_COMPANY_PROFILES")
KAFKA_TOPIC_TRADES = os.getenv("KAFKA_TOPIC_TRADES")
KAFKA_TOPIC_SYMBOLS = os.getenv("KAFKA_TOPIC_SYMBOLS")

# A list of test tickers for market symbols to be used for testing purposes
TEST_TICKERS = ['BINANCE:BTCUSDT', 'BINANCE:ETHUSDC', 'BINANCE:ETHUSDP', 'BINANCE:ETHUSDT', 'BINANCE:BTCUSDC']
