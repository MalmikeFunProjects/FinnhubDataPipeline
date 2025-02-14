from enum import Enum
from handlers.kafka_consumer import KafkaConsumer
from utils.utilities import Utilities
import utils.settings as Utils

# Enum to define the Kafka topics the consumer will interact with
# This helps ensure the consistency of topic names when consuming messages from Kafka
class KafkaTopics(Enum):
    STOCK_SUMMARY = Utils.KAFKA_TOPIC_STOCK_SUMMARY  # Topic for stock summary data
    LATEST_PRICES = Utils.KAFKA_TOPIC_LATEST_PRICES  # Topic for the latest stock prices

# Main consumer class for processing data from Kafka topics
class FinnhubConsumer:
    def __init__(self):
        """
        Initializes the FinnhubConsumer object.
        Sets up an empty dictionary for latest stock prices and
        creates a Kafka consumer instance using configurations from Utils.
        """
        self.latest_prices = {}  # Dictionary to store the latest prices of stocks
        # Kafka consumer properties (URLs and bootstrap servers from settings)
        props = {
            "schema_registry.url": Utils.SCHEMA_REGISTRY_URL,  # URL for the schema registry
            "bootstrap.servers": Utils.BOOTSTRAP_SERVERS  # Kafka bootstrap servers for connection
        }
        # Create an instance of KafkaConsumer with the provided properties
        self.kafka_consumer = KafkaConsumer(props)

    def __compute_total(self, missing_symbols: list[str], latest_prices: dict[str, float], total: float) -> float:
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
        return total

    def handle_response_data(self, topic_names: list[str]):
        """
        Handles the incoming data from the specified Kafka topics.
        Processes each message and performs actions based on the topic (either updating prices or calculating totals).

        Parameters:
            topic_names (list): List of topic names to consume data from.

        Raises:
            Exception: If an invalid list of topic names is provided (empty or not a list).
        """
        if (not isinstance(topic_names, list) or len(topic_names) <= 0):
            raise Exception("Insert valid topic names")  # Ensure valid input for topic names

        # Consume messages from the Kafka topics
        for topic, key, value in self.kafka_consumer.consume_from_kafka(topic_names):
            # Process messages based on the topic
            if (topic == KafkaTopics.LATEST_PRICES.value):
                self.latest_prices[key] = value["LAST_PRICE"]  # Update the latest stock price for the given key

            if (topic == KafkaTopics.STOCK_SUMMARY.value):
                if value is not None:
                    # Remove any non-printable characters from the symbol list
                    symbols = {Utilities.remove_no_printable_characters(item) for item in value["SYMBOLS"]}
                    # Determine the missing symbols by comparing with existing latest prices
                    missing_symbols = list(self.latest_prices.keys() - symbols)
                    # Compute the total price by including the missing stock prices
                    total = self.__compute_total(
                        missing_symbols=missing_symbols,
                        latest_prices=self.latest_prices,
                        total=value["TOTAL_PRICE"]
                    )
                    # Calculate the combined list of all symbols (either from the latest prices or stock summary)
                    all_symbols = self.latest_prices.keys() if len(self.latest_prices) == len(
                        missing_symbols)+len(symbols) else list(set(missing_symbols) | symbols)

                    # Output the processed data (can be used for logging or monitoring)
                    print("-"*30)
                    print(f"{topic}, Timestamp: {key}, Total Price:{total}, Symbols: {all_symbols}")
                    print("-"*30)

# Main execution of the script
if __name__ == "__main__":
    # List of topic names derived from the KafkaTopics Enum
    topic_names = [member.value for member in KafkaTopics]

    # Instantiate the FinnhubConsumer and start processing the response data
    finnhub_consumer = FinnhubConsumer()
    finnhub_consumer.handle_response_data(topic_names=topic_names)
