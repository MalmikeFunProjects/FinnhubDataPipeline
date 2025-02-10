import os
from dotenv import load_dotenv

load_dotenv()
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
SP500_COMPANY_PROFILES_FILE_PATH = os.getenv("SP500_COMPANY_PROFILES_FILE_PATH")
SP500_COMPANIES_URL = os.getenv("SP500_COMPANIES_URL")
US_BIG_TECH_URL = os.getenv("US_BIG_TECH_URL")

SCHEMA_TRADES = os.getenv("SCHEMA_TRADES")
SCHEMA_SP500_COMPANY_PROFILES = os.getenv("SCHEMA_SP500_COMPANY_PROFILES")
SCHEMA_STOCK_SYMBOLS = os.getenv("SCHEMA_STOCK_SYMBOLS")

SCHEMA_REGISTRY_URL = os.getenv("SCHEMA_REGISTRY_URL")
BOOTSTRAP_SERVERS = os.getenv("BOOTSTRAP_SERVERS")
KAFKA_TOPIC_COMPANY_PROFILES = os.getenv("KAFKA_TOPIC_COMPANY_PROFILES")
KAFKA_TOPIC_TRADES = os.getenv("KAFKA_TOPIC_TRADES")
KAFKA_TOPIC_SYMBOLS = os.getenv("KAFKA_TOPIC_SYMBOLS")

TEST_TICKERS=['BINANCE:BTCUSDT', 'BINANCE:ETHUSDC', 'BINANCE:ETHUSDP', 'BINANCE:ETHUSDT', 'BINANCE:BTCUSDC']


