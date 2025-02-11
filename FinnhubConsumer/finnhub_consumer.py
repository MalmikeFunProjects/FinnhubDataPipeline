
from enum import Enum
from handlers.kafka_consumer import KafkaConsumer
from utils.utilities import Utilities
import utils.settings as Utils

class KafkaTopics(Enum):
    STOCK_SUMMARY = Utils.KAFKA_TOPIC_STOCK_SUMMARY
    LATEST_PRICES = Utils.KAFKA_TOPIC_LATEST_PRICES

class FinnhubConsumer:
    def __init__(self):
        self.latest_prices = {}
        props = {
            "schema_registry.url": Utils.SCHEMA_REGISTRY_URL,
            "bootstrap.servers": Utils.BOOTSTRAP_SERVERS
        }
        self.kafka_consumer = KafkaConsumer(props)

    def __compute_total(self, missing_symbols: list[str], latest_prices: dict[str, float], total: float) -> float:
        for symbol in missing_symbols:
            total += latest_prices[symbol]
        return total

    def handle_response_data(self, topic_names: list[str]):
        if (not isinstance(topic_names, list) or len(topic_names) <= 0):
            raise Exception("Insert valid topic names")
        for topic, key, value in self.kafka_consumer.consume_from_kafka(topic_names):
            if (topic == KafkaTopics.LATEST_PRICES.value):
                self.latest_prices[key] = value["LAST_PRICE"]

            if (topic == KafkaTopics.STOCK_SUMMARY.value):
                if value is not None:
                    symbols = {Utilities.remove_no_printable_characters(
                        item) for item in value["SYMBOLS"]}
                    missing_symbols = list(self.latest_prices.keys() - symbols)
                    total = self.__compute_total(
                        missing_symbols=missing_symbols,
                        latest_prices=self.latest_prices,
                        total=value["TOTAL_PRICE"]
                    )
                    all_symbols = self.latest_prices.keys() if len(self.latest_prices) == len(
                        missing_symbols)+len(symbols) else list(set(missing_symbols) | symbols)
                    print("-"*30)
                    print(f"{topic}, Timestamp: {key}, Total Price:{total}, Symbols: {all_symbols}")
                    print("-"*30)


if __name__ == "__main__":
    topic_names = [member.value for member in KafkaTopics]
    finnhub_consumer = FinnhubConsumer()
    finnhub_consumer.handle_response_data(topic_names=topic_names)

