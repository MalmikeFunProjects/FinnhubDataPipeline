from execute_ksql.execute_ksql_request import ExecuteKsqlRequest
from execute_ksql.make_ksql_request import MakeKsqlRequest
from set_kafka_topics.add_kafka_topics import AddKafkaTopics
from utils.enums import StorageType
import utils.settings as UTILS

class KsqlHandler:
    def __init__(self, topics: dict[str, str]):
        self.make_ksql_request = MakeKsqlRequest()
        self.topics = topics
        self.add_kafka_topics()
        self.execute_ksql_request()

    def add_kafka_topics(self):
        AddKafkaTopics.add_kafka_topics(topics=self.topics)
        topic_names = self.topics.keys()
        for topic_name in topic_names:
            check = self.make_ksql_request.check_storage_type_exists(
                storage_type=StorageType.TOPIC, name=topic_name)
            if (not check):
                print(f"Topic {topic_name} failed to create")
                exit(1)

    def execute_ksql_request(self):
        execute_ksql_request = ExecuteKsqlRequest()
        execute_ksql_request.createStockPricesStream()
        execute_ksql_request.createSymbolsStream()
        execute_ksql_request.tableCompanySymbols()
        execute_ksql_request.tableLatestPrices()
        execute_ksql_request.tableStockPrices1sAvg()
        execute_ksql_request.streamStockPrices1sAvg()
        execute_ksql_request.tableStockSummary()


if __name__ == "__main__":
    topics = {
        UTILS.KAFKA_TOPIC_COMPANY_PROFILES: UTILS.SCHEMA_SP500_COMPANY_PROFILES,
        UTILS.KAFKA_TOPIC_TRADES: UTILS.SCHEMA_TRADES,
        UTILS.KAFKA_TOPIC_SYMBOLS: UTILS.SCHEMA_STOCK_SYMBOLS
    }
    KsqlHandler(topics=topics)

