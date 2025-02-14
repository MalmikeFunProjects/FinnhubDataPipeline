from execute_ksql.execute_ksql_request import ExecuteKsqlRequest
from execute_ksql.make_ksql_request import MakeKsqlRequest
from set_kafka_topics.add_kafka_topics import AddKafkaTopics
from utils.enums import StorageType
import utils.settings as UTILS

class KsqlHandler:
    """
    Handles the setup of Kafka topics and execution of KSQL statements.

    This class initializes Kafka topics, verifies their creation, and executes predefined KSQL statements
    to create streams and tables.
    """

    def __init__(self, topics: dict[str, str]):
        """
        Initializes the KsqlHandler with the given topics and executes necessary KSQL statements.

        :param topics: A dictionary where keys are Kafka topic names and values are schema file paths.
        """
        self.make_ksql_request = MakeKsqlRequest()
        self.topics = topics
        self.add_kafka_topics()
        self.execute_ksql_request()

    def add_kafka_topics(self):
        """
        Adds and registers Kafka topics, then verifies their creation.

        :raises SystemExit: If a topic fails to be created.
        """
        AddKafkaTopics.add_kafka_topics(topics=self.topics)
        topic_names = self.topics.keys()
        for topic_name in topic_names:
            check = self.make_ksql_request.check_storage_type_exists(
                storage_type=StorageType.TOPIC, name=topic_name)
            if not check:
                print(f"Topic {topic_name} failed to create")
                exit(1)

    def execute_ksql_request(self):
        """
        Executes KSQL statements to create necessary streams and tables.
        """
        execute_ksql_request = ExecuteKsqlRequest()
        execute_ksql_request.createStockPricesStream()
        execute_ksql_request.createSymbolsStream()
        execute_ksql_request.tableCompanySymbols()
        execute_ksql_request.tableLatestPrices()
        execute_ksql_request.tableStockPrices1sAvg()
        execute_ksql_request.streamStockPrices1sAvg()
        execute_ksql_request.tableStockSummary()

if __name__ == "__main__":
    """
    Main execution block that initializes the KsqlHandler with predefined Kafka topics and schemas.
    """
    topics = {
        UTILS.KAFKA_TOPIC_COMPANY_PROFILES: UTILS.SCHEMA_SP500_COMPANY_PROFILES,
        UTILS.KAFKA_TOPIC_TRADES: UTILS.SCHEMA_TRADES,
        UTILS.KAFKA_TOPIC_SYMBOLS: UTILS.SCHEMA_STOCK_SYMBOLS
    }
    KsqlHandler(topics=topics)
