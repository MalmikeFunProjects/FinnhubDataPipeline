from enum import Enum
import logging
from cassandra.cqlengine.models import Model

from cassandra_client.setup_client import SetupClient
from cassandra_client.cassandra_client import CassandraConfig, CassandraClient
from handlers.kafka_consumer import KafkaConsumer
from utils.utilities import Utilities
from utils.funtion_timer import FunctionTimer
import utils.settings as Utils
import cassandra_client.models as models

logging.basicConfig(level=logging.INFO)


# Enum to define the Kafka topics the consumer will interact with
# This helps ensure the consistency of topic names when consuming messages from Kafka
class KafkaTopics(Enum):
    STOCK_SUMMARY = Utils.KAFKA_TOPIC_STOCK_SUMMARY  # Topic for stock summary data
    LATEST_PRICES = Utils.KAFKA_TOPIC_LATEST_PRICES  # Topic for the latest stock prices
    COMPANY_SYMBOLS = Utils.KAFKA_TOPIC_COMPANY_SYMBOLS  # Topic for company symbols
    STOCK_PRICES_1S = Utils.KAFKA_TOPIC_STOCK_PRICES_1S

# Main consumer class for processing data from Kafka topics
class FinnhubConsumer:
    def __init__(self, cassandra_config: CassandraConfig = None):
        """
        Initializes the FinnhubConsumer object.
        Sets up an empty dictionary for latest stock prices and
        creates a Kafka consumer instance using configurations from Utils.
        """
        # Kafka consumer properties (URLs and bootstrap servers from settings)
        props = {
            "schema_registry.url": Utils.SCHEMA_REGISTRY_URL,  # URL for the schema registry
            "bootstrap.servers": Utils.BOOTSTRAP_SERVERS  # Kafka bootstrap servers for connection
        }
        # Create an instance of KafkaConsumer with the provided properties
        self.kafka_consumer = KafkaConsumer(props)

        self.cassandra_config = cassandra_config
        self.setup_cassandra_client()
        self.latest_prices = {}
        self.function_timer = FunctionTimer()

    def __compute_total(
        self,
        current_symbol_prices: dict[str, float],
        missing_symbols: list[str],
        latest_prices: dict[str, float],
        total: float
    ) -> dict[str, any]:
        """
        Helper function to compute the total price based on the missing symbols and their latest prices.

        Parameters:
            missing_symbols (list): List of stock symbols that have missing prices.
            latest_prices (dict): A dictionary of the latest prices for stocks.
            total (float): The current total price before including the missing symbols.

        Returns:
            float: The updated total price after adding the prices of the missing symbols.
        """
        for symbol in missing_symbols:
            total += latest_prices[symbol]  # Add the price for each missing symbol to the total
            current_symbol_prices[symbol] = latest_prices[symbol]  # Add the symbol and price to the list of current symbol prices
        return {"total": total, "all_symbol_prices": current_symbol_prices}

    def setup_cassandra_client(self):
        setup_client = SetupClient(config=self.cassandra_config)
        classModels = Utilities.get_classes_from_module(module=models, base_class=Model)
        # Ensure the table schema is synchronized before writing data
        setup_client.setup_tables(classModels, logging=logging)

    def add_data_to_cassandra(self, topic_names: list[str]):
        with CassandraClient(self.cassandra_config) as cassandra_client:
            try:
                self.handle_response_data(topic_names=topic_names, cassandra_client=cassandra_client)
                self.function_timer.cancel_all_timers()
                cassandra_client.clear_batch(add_batch_data=True)
            except Exception as e:
                logging.error(f"Error processing stream: {e}")
                try:
                    self.function_timer.cancel_all_timers()
                    cassandra_client.clear_batch(add_batch_data=True)
                except Exception as batch_e:
                    logging.error(f"Failed to commit final batch: {batch_e}")

    def handle_response_data(self, topic_names: list[str], cassandra_client: CassandraClient):
        """
        Handles the incoming data from the specified Kafka topics.
        Processes each message and performs actions based on the topic (either updating prices or calculating totals).

        Parameters:
            topic_names (list): List of topic names to consume data from.

        Raises:
            Exception: If an invalid list of topic names is provided (empty or not a list).
        """
        latest_prices: dict[str, float] = {}  # Dictionary to store the latest prices of stocks
        if (not isinstance(topic_names, list) or len(topic_names) <= 0):
            raise Exception("Insert valid topic names")  # Ensure valid input for topic names
        logging.info(f"STARTING: 0 records processed")
        # Consume messages from the Kafka topics
        for topic, key, value in self.kafka_consumer.consume_from_kafka(topic_names):
            try:
                latest_prices = self.handle_latest_prices(cassandra_client, latest_prices, topic, key, value)
                self.handle_stock_summary(cassandra_client, latest_prices, topic, key, value)
                self.handle_company_symbols(cassandra_client, topic, key, value)
                self.handle_stock_price_1s(cassandra_client, topic, key, value)
            except Exception as e:
                logging.error(f"Error processing topic {topic}, key: {key}, value: {value}: {e}")
                raise e

    def handle_latest_prices(self, cassandra_client: CassandraClient, latest_prices: dict[str, float], topic: KafkaTopics, key: str, value: dict[str, any]):
        if(topic == KafkaTopics.LATEST_PRICES.value):
            latest_prices[key] = value["LAST_PRICE"]
            data = {"symbol": key, "last_price": value["LAST_PRICE"], "event_timestamp": value["EVENT_TIMESTAMP"]}
            try:
                count = cassandra_client.add_batch_data(batch_size=100, CustomModel=models.LatestPrice, data=data, batch_duration=5)
                logging.info(f"Batch size: {count}, Current topic: {topic}")
                logging.info("-"*60)
            except Exception as e:
                logging.error(f"Error adding {topic} to Cassandra: {e}")
                raise e
        return latest_prices

    def handle_stock_summary(self, cassandra_client: CassandraClient, latest_prices: dict[str, float], topic: KafkaTopics, key: str, value: dict[str, any]):
        if(topic == KafkaTopics.STOCK_SUMMARY.value):
            if value is not None:
                # Remove any non-printable characters from the symbol list
                symbols = {Utilities.remove_no_printable_characters(item) for item in value["SYMBOLS"]}
                if "SYMBOL_PRICES" not in value:
                    symbol_prices = {}
                else:
                    symbol_prices = {
                        Utilities.remove_no_printable_characters(item["key"]): item["value"]
                        for item in value["SYMBOL_PRICES"]
                        if "key" in item and "value" in item
                    }
                # Determine the missing symbols by comparing with existing latest prices
                missing_symbols = list(latest_prices.keys() - symbol_prices.keys())
                # Compute the total price by including the missing stock prices
                computed_values = self.__compute_total(
                    current_symbol_prices = symbol_prices,
                    missing_symbols=missing_symbols,
                    latest_prices=latest_prices,
                    total=value["TOTAL_PRICE"]
                )
                total, all_symbol_prices = computed_values.values()

                data = {
                    "event_timestamp": key,
                    "total_price": total,
                    "symbol_prices": all_symbol_prices
                }
                try:
                    count = cassandra_client.add_batch_data(batch_size=100, CustomModel=models.StockSummary, data=data, batch_duration=5)
                    logging.info(f"Batch size: {count}, Current topic: {topic}")
                    logging.info("-"*60)
                except Exception as e:
                    logging.error(f"Error adding {topic} to Cassandra: {e}")
                    raise e

    def handle_company_symbols(self, cassandra_client: CassandraClient, topic: KafkaTopics, key: str, value: dict[str, any]):
        if(topic == KafkaTopics.COMPANY_SYMBOLS.value):
            if key is not None:
                try:
                    count = cassandra_client.add_batch_data(batch_size=10, CustomModel=models.CompanySymbol, data={"symbol": key}, only_unique=True)
                    logging.info(f"Batch size: {count}, Current topic: {topic}")
                    logging.info("-"*60)
                except Exception as e:
                    logging.error(f"Error adding {topic} to Cassandra: {e}")
                    raise e


    def handle_stock_price_1s(self, cassandra_client: CassandraClient, topic: KafkaTopics, key: str, value: dict[str, any]):
        if(topic == KafkaTopics.STOCK_PRICES_1S.value):
            if value is not None:
                data = {
                    "event_timestamp": value["EVENT_TIMESTAMP"],
                    "symbol": key,
                    "avg_price": value["AVG_PRICE"],
                    "count": value["COUNT"]
                }
                try:
                    count = cassandra_client.add_batch_data(batch_size=100, CustomModel=models.StockPrice1s, data=data, batch_duration=5)
                    logging.info(f"Batch size: {count}, Current topic: {topic}")
                    logging.info("-"*60)
                except Exception as e:
                    logging.error(f"Error adding {topic} to Cassandra: {e}")
                    raise e

# Main execution of the script
if __name__ == "__main__":
    cassandra_config = CassandraConfig(
        hosts=Utils.CASSANDRA_HOSTS,
        port=Utils.CASSANDRA_PORT,
        keyspace=Utils.CASSANDRA_KEYSPACE,
        retry_attempts=Utils.CASSANDRA_RETRY_ATTEMPTS,
        retry_delay=Utils.CASSANDRA_RETRY_DELAY
    )

    # List of topic names derived from the KafkaTopics Enum
    topic_names = [member.value for member in KafkaTopics]

    # Instantiate the FinnhubConsumer and start processing the response data
    finnhub_consumer = FinnhubConsumer(cassandra_config=cassandra_config)
    finnhub_consumer.add_data_to_cassandra(topic_names=topic_names)
