from enum import Enum
from typing import Any
from httpx import Response
import requests
import json

from set_kafka_topics.set_kafka_topics import SetUpKafkaTopics
from utils.utilities import Utilities
import utils.settings as UTILS


class AddKafkaTopics:
    @staticmethod
    def add_kafka_topics(topics: dict[str, str]):
        bootstrap_servers = UTILS.BOOTSTRAP_SERVERS
        schema_registry_url = UTILS.SCHEMA_REGISTRY_URL
        setUpKafkaTopics = SetUpKafkaTopics(
            schema_registry_url=schema_registry_url, bootstrap_servers=bootstrap_servers)

        try:
            for topic_name, schema_path in topics.items():
                schema = Utilities.load_schema(schema_path)
                setUpKafkaTopics.register_schema(
                    avro_schema=schema, topic_name=topic_name)
        except Exception as e:
            raise e

        try:
            setUpKafkaTopics.register_topic(
                topic_names=topics.keys(),
                partitions=int(UTILS.KAFKA_PARTITIONS),
                replication_factor=int(UTILS.KAFKA_REPLICATION_FACTOR)
            )
        except Exception as e:
            raise e


class ExecuteKsql:
    def headers(self):
        return {"Content-Type": "application/vnd.ksql.v1+json"}

    def stream_properties(self):
        return {"auto.offset.reset": "earliest"}

    def payload(self, statement: str, streamsProperties={}):
        return {"ksql": statement, "streamsProperties": streamsProperties}

    def stream_payload(self, statement: str, streamsProperties={}):
        return {"sql": statement, "properties": streamsProperties}

    def request(self, headers: dict[str, str], payload: dict[str, Any], request_type: str = "ksql") -> Response:
        response = requests.post(
            f"{UTILS.KSQLDB_URL}/{request_type}", headers=headers, data=json.dumps(payload))
        if (response.status_code == 200):
            # response_text = response.text.strip()
            # json_objects = response_text.split("\n")
            # parsed_objects = [json.loads(obj) for obj in json_objects if obj]
            # print(parsed_objects)  # Print parsed JSON objects
            return response.json()
        else:
            raise Exception(f"Error: {response.text}")


class StorageType(Enum):
    STREAMS = "streams"
    TABLES = "tables"
    TOPICS = "topics"


class MakeKsqlRequest:
    def __init__(self):
        self.executeKsql = ExecuteKsql()
        self.headers = self.executeKsql.headers()
        # self.makeKsqlStreamRequest = MakeKsqlStreamRequest()

    def handle_request(self, statement: str, streamsProperties={}, request_type: str = "query"):
        payload = self.executeKsql.payload(
            statement=statement, streamsProperties=streamsProperties)
        return self.executeKsql.request(headers=self.headers, payload=payload, request_type=request_type)

    def show_storage_type(self, storage_type: StorageType):
        statement = f"SHOW {storage_type.value};"
        return self.handle_request(statement=statement, request_type="ksql")

    def check_storage_type_exists(self, storage_type: StorageType, name: str):
        response = self.show_storage_type(storage_type)
        return any(s_type["name"] == name for s_type in response[0][storage_type.value])

    def check__exists(self, stream_name: str):
        response = self.show_streams()
        return any(stream["name"] == stream_name for stream in response[0]["streams"])

    def drop_stream(self, stream_name: str):
        statement = f"DROP STREAM IF EXISTS {stream_name};"
        return self.handle_request(statement=statement)

    def create_stream(self,
                      stream_name: str,
                      kafka_topic: str,
                      value_format: str,
                      partitions: int,
                      column_defs: list[str] = None):
        column_str = f"({", ".join(column_defs)
                         })" if column_defs is not None else ""
        statement = f"""
          CREATE STREAM {stream_name} {column_str} WITH (
          KAFKA_TOPIC='{kafka_topic}',
          VALUE_FORMAT='{value_format}',
          PARTITIONS={partitions}
          );
        """
        return self.handle_request(statement=statement, request_type="ksql")


class KsqlSpecificRequest:
    def __init__(self, partitions: int = 1):
        self.makeKsqlRequest = MakeKsqlRequest()
        self.partitions = partitions
        self.setOffset()

    def setOffset(self):
        statement = "SET 'auto.offset.reset'='earliest';"
        response = self.makeKsqlRequest.handle_request(
            statement=statement, request_type="ksql")
        print(response)

    def createStockPricesStream(self):
        stream_name = "STOCK_PRICES"
        column_defs = ["price DOUBLE", "symbol VARCHAR", "timestamp BIGINT"]
        kafka_topic = UTILS.KAFKA_TOPIC_TRADES
        value_format = "AVRO"
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.STREAMS, stream_name)
        if (not check):
            response = self.makeKsqlRequest.create_stream(
                stream_name=stream_name,
                kafka_topic=kafka_topic,
                value_format=value_format,
                column_defs=column_defs,
                partitions=self.partitions
            )
            print(response)
        else:
            print(f"Stream {stream_name} already exists")

    def tableStockPrices1sAvg(self):
        table_name = "STOCK_PRICES_1S"
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.TABLES, table_name)
        if (not check):
            statement = f"""
              CREATE TABLE {table_name} AS
              SELECT
                  symbol,
                  WINDOWSTART AS TIMESTAMP,
                  COUNT(*) AS COUNT,
                  AVG(PRICE) AS AVG_PRICE
              FROM STOCK_PRICES
              WINDOW TUMBLING (SIZE 1 SECONDS)
              GROUP BY SYMBOL
              EMIT FINAL;
            """
            response = self.makeKsqlRequest.handle_request(
                statement=statement, request_type="ksql")
            print(response)
        else:
            print(f"Table {table_name} already exists")

    def streamStockPrices1sAvg(self):
        stream_name = "STOCK_PRICES_1S_STREAM"
        topic_name = "STOCK_PRICES_1S"
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.STREAMS, stream_name)
        if (not check):
            statement = f"""
              CREATE STREAM {stream_name} (
                  SYMBOL VARCHAR KEY,
                  AVG_PRICE DOUBLE,
                  TIMESTAMP BIGINT
              ) WITH (
                  KAFKA_TOPIC = '{topic_name}',
                  VALUE_FORMAT = 'AVRO',
                  WINDOW_TYPE = 'TUMBLING',
                  WINDOW_SIZE = '1 SECONDS'
              );
            """
            response = self.makeKsqlRequest.handle_request(
                statement=statement, request_type="ksql")
            print(response)
        else:
            print(f"Stream {stream_name} already exists")

    def tableStockSummary(self):
        table_name = "STOCK_SUMMARY"
        stream_name = "STOCK_PRICES_1S_STREAM"
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.TABLES, table_name)
        if (not check):
            statement = f"""
                CREATE TABLE {table_name} AS
                SELECT
                    TIMESTAMP,
                    SUM(avg_price) AS total_avg_price,
                    COLLECT_LIST(SYMBOL) AS symbols
                FROM {stream_name}
                WINDOW TUMBLING (SIZE 1 SECONDS)
                GROUP BY TIMESTAMP
                EMIT CHANGES;
            """
            self.makeKsqlRequest.handle_request(
                statement=statement, request_type="ksql")
        else:
            print(f"Table {table_name} already exists")

    def streamStockSummary(self):
        stream_name = "STOCK_SUMMARY_STREAM"
        topic_name = "STOCK_SUMMARY"
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.STREAMS, stream_name)
        if (not check):
            statement = f"""
              CREATE STREAM {stream_name} (
                  TIMESTAMP BIGINT KEY,
                  total_avg_price DOUBLE,
                  SYMBOLS ARRAY<VARCHAR(STRING)>
              ) WITH (
                  KAFKA_TOPIC = '{topic_name}',
                  VALUE_FORMAT = 'AVRO',
                  WINDOW_TYPE = 'TUMBLING',
                  WINDOW_SIZE = '1 SECONDS'
              );
            """
            response = self.makeKsqlRequest.handle_request(
                statement=statement, request_type="ksql")
            print(response)
        else:
            print(f"Stream {stream_name} already exists")


if __name__ == "__main__":
    make_ksql_request = MakeKsqlRequest()
    topics = {
        UTILS.KAFKA_TOPIC_COMPANY_PROFILES: UTILS.SCHEMA_SP500_COMPANY_PROFILES,
        UTILS.KAFKA_TOPIC_TRADES: UTILS.SCHEMA_TRADES,
        UTILS.KAFKA_TOPIC_SYMBOLS: UTILS.SCHEMA_STOCK_SYMBOLS
    }
    AddKafkaTopics.add_kafka_topics(topics=topics)
    topics = [UTILS.KAFKA_TOPIC_COMPANY_PROFILES,
              UTILS.KAFKA_TOPIC_TRADES,
              UTILS.KAFKA_TOPIC_SYMBOLS]
    # Check that all topics exist
    for topic_name in topics:
        check = make_ksql_request.check_storage_type_exists(
            storage_type=StorageType.TOPICS, name=topic_name)
        if (not check):
            print(f"Topic {topic_name} failed to create")
            exit(1)

    kafka_topic = UTILS.KAFKA_TOPIC_TRADES
    ksqlSpecificRequest = KsqlSpecificRequest()
    ksqlSpecificRequest.createStockPricesStream()
    ksqlSpecificRequest.tableStockPrices1sAvg()
    ksqlSpecificRequest.streamStockPrices1sAvg()
    ksqlSpecificRequest.tableStockSummary()
    ksqlSpecificRequest.streamStockSummary()
