import time
import numpy as np

from gather_data.finnhub_gather_data import FinnhubGatherData
from gather_data.finnhub_trades import FinnhubTrades
from handlers.kafka_producer import KafkaProducer
import utils.settings as UTILS


class FinnhubProducer:
    """
    A class to handle the production and publishing of financial data to Kafka topics.
    It fetches company profiles, stock symbols, and trade data from Finnhub and
    publishes them to Kafka topics.

    Methods:
        __init__: Initializes the producer with the required data from Finnhub.
        publishSP500CompanyProfiles: Publishes the S&P 500 company profiles to Kafka.
        publishStockSymbols: Publishes the stock symbols to Kafka.
        publishTrades: Publishes the trades data to Kafka.
    """

    def __init__(self):
        """
        Initializes the FinnhubProducer object. It fetches company profiles and
        sets up the tickers (stock symbols) to be used for trade data.

        The tickers are initially set to a predefined list (from UTILS.TEST_TICKERS).
        """
        self.finnhub_gather_data = FinnhubGatherData()  # Instance to fetch Finnhub data
        self.company_profiles = self.finnhub_gather_data.get_company_profiles()  # Get company profiles from Finnhub
        # self.tickers = self.finnhub_gather_data.get_us_big_tech_tickers(self.company_profiles).unique()
        # Set tickers to a predefined list for simplicity and reliability
        self.tickers = np.array(UTILS.TEST_TICKERS)

    def publishSP500CompanyProfiles(self):
        """
        Publishes the S&P 500 company profiles to Kafka.
        This method prepares the data using the company profiles gathered from Finnhub
        and sends it to the Kafka topic specified in the configuration.
        """
        config = {
            'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,  # Kafka server settings
            'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,  # Schema registry settings
            'schema.name': UTILS.KAFKA_TOPIC_COMPANY_PROFILES  # Kafka topic for company profiles
        }
        producer = KafkaProducer(props=config)  # Kafka producer instance
        producer.publishUsingDataFrames(
            topic=UTILS.KAFKA_TOPIC_COMPANY_PROFILES,  # Kafka topic for company profiles
            df=self.company_profiles,  # DataFrame containing company profiles
            key=self.finnhub_gather_data.sp500_key_name  # Key to be used in the Kafka message
        )

    def publishStockSymbols(self):
        """
        Publishes a list of stock symbols to Kafka.
        This method takes a list of stock symbols (tickers) and publishes them to the Kafka
        topic specified in the configuration.
        """
        config = {
            'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,  # Kafka server settings
            'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,  # Schema registry settings
            'schema.name': UTILS.KAFKA_TOPIC_SYMBOLS  # Kafka topic for stock symbols
        }
        stock_symbols = self.tickers.tolist()  # Convert tickers (Numpy array) to list
        key = "Symbol"  # Key for the stock symbol data
        producer = KafkaProducer(props=config)  # Kafka producer instance
        producer.publishUsingList(
            topic=UTILS.KAFKA_TOPIC_SYMBOLS,  # Kafka topic for stock symbols
            items=stock_symbols,  # List of stock symbols
            key=key  # Key to be used in the Kafka message
        )

    def publishTrades(self):
        """
        Publishes trade data to Kafka by starting a websocket connection.
        This method creates an instance of FinnhubTrades, which listens for trade data
        from the specified tickers and sends it to the Kafka topic specified in the configuration.
        """
        config = {
            'bootstrap.servers': UTILS.BOOTSTRAP_SERVERS,  # Kafka server settings
            'schema_registry.url': UTILS.SCHEMA_REGISTRY_URL,  # Schema registry settings
            'schema.name': UTILS.KAFKA_TOPIC_TRADES  # Kafka topic for trades data
        }
        producer = KafkaProducer(props=config)  # Kafka producer instance
        # Create an instance of FinnhubTrades to start listening for trades data
        trades = FinnhubTrades(tickers=self.tickers, producer=producer, max_messages=None)
        trades.start_websocket()  # Start the WebSocket to receive and publish trades


if __name__ == "__main__":
    """
    The main execution of the FinnhubProducer. It initializes the producer and calls the
    methods to publish company profiles, stock symbols, and trade data to Kafka.
    """
    finnhubProducer = FinnhubProducer()  # Instantiate the FinnhubProducer
    finnhubProducer.publishSP500CompanyProfiles()  # Publish S&P 500 company profiles to Kafka
    finnhubProducer.publishStockSymbols()  # Publish stock symbols to Kafka
    finnhubProducer.publishTrades()  # Publish trade data to Kafka
