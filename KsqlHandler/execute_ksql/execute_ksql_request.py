from execute_ksql.make_ksql_request import MakeKsqlRequest
from utils.enums import StorageType
import utils.settings as UTILS


class ExecuteKsqlRequest:
    def __init__(self, partitions: int = 1):
        self.makeKsqlRequest = MakeKsqlRequest()
        self.partitions = partitions
        self.setOffset()

    def setOffset(self):
        statement = "SET 'auto.offset.reset'='earliest';"
        response = self.makeKsqlRequest.handle_request(
            statement=statement, request_type="ksql")
        print(response)

    def __createStreamFromTopic(self, props):
        check = self.makeKsqlRequest.check_storage_type_exists(
            StorageType.STREAM, props["stream_name"])
        if (not check):
            response = self.makeKsqlRequest.create_stream(
                stream_name=props["stream_name"],
                kafka_topic=props["kafka_topic"],
                value_format=props["value_format"],
                column_defs=props["column_defs"],
                partitions=self.partitions
            )
            print(response)
        else:
            print(f"Stream {props["stream_name"]} already exists")

    def __execute_statement(self, storageType: StorageType, storageName: str, statement: str):
        check = self.makeKsqlRequest.check_storage_type_exists(
            storage_type=storageType, name=storageName)
        if(not check):
            response = self.makeKsqlRequest.handle_request(
                statement=statement, request_type="ksql")
            print(response)
        else:
            print(f"{storageType.name.capitalize()} {storageName} already exists")

    def createStockPricesStream(self):
        props = {
            "stream_name": "STOCK_PRICES",
            "column_defs": ["price DOUBLE", "symbol VARCHAR", "timestamp BIGINT"],
            "kafka_topic": UTILS.KAFKA_TOPIC_TRADES,
            "value_format": "AVRO",
        }
        self.__createStreamFromTopic(props)

    def createSymbolsStream(self):
        props = {
            "stream_name": "SYMBOLS",
            "column_defs": ["SYMBOL VARCHAR", "TIMESTAMP BIGINT"],
            "kafka_topic": UTILS.KAFKA_TOPIC_SYMBOLS,
            "value_format": "AVRO",
        }
        self.__createStreamFromTopic(props)

    def tableCompanySymbols(self):
        table_name = "COMPANY_SYMBOLS"
        statement = f"""
            CREATE TABLE {table_name} WITH (
                KAFKA_TOPIC = '{table_name}',
                VALUE_FORMAT = 'AVRO',
                KEY_FORMAT = 'AVRO'
            ) AS
            SELECT
                SYMBOL,
                LATEST_BY_OFFSET(TIMESTAMP) AS TIMESTAMP
            FROM SYMBOLS
            GROUP BY SYMBOL
            EMIT CHANGES;
        """
        self.__execute_statement(storageType=StorageType.TABLE, storageName=table_name, statement=statement)

    def tableLatestPrices(self):
        table_name = "LATEST_PRICES"
        statement = f"""
            CREATE TABLE {table_name} WITH (
                KAFKA_TOPIC = '{table_name}',
                VALUE_FORMAT = 'AVRO',
                KEY_FORMAT = 'AVRO'
            ) AS
            SELECT
                sp.SYMBOL as SYMBOL,
                COALESCE(LATEST_BY_OFFSET(sp.price), CAST(0 AS DOUBLE)) AS LAST_PRICE,
                LATEST_BY_OFFSET(sp.TIMESTAMP) AS TIMESTAMP
            FROM STOCK_PRICES sp
              LEFT JOIN COMPANY_SYMBOLS cs
              ON sp.SYMBOL = cs.SYMBOL
            GROUP BY sp.SYMBOL
            EMIT CHANGES;
        """
        self.__execute_statement(storageType=StorageType.TABLE, storageName=table_name, statement=statement)

    def tableStockPrices1sAvg(self):
        table_name = "STOCK_PRICES_1S"
        statement = f"""
            CREATE TABLE {table_name} WITH (
              KAFKA_TOPIC = '{table_name}',
              VALUE_FORMAT = 'AVRO',
              KEY_FORMAT = 'AVRO'
            ) AS
            SELECT
                SYMBOL,
                COUNT(*) AS COUNT,
                AVG(PRICE) as AVG_PRICE,
                WINDOWSTART as TIMESTAMP
            FROM STOCK_PRICES
            WINDOW TUMBLING(SIZE 1 SECONDS)
            GROUP BY SYMBOL
            EMIT FINAL;
        """
        self.__execute_statement(storageType=StorageType.TABLE, storageName=table_name, statement=statement)

    def streamStockPrices1sAvg(self):
        stream_name = "STOCK_PRICES_1S_STREAM"
        topic_name = "STOCK_PRICES_1S"
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
        self.__execute_statement(storageType=StorageType.STREAM, storageName=stream_name, statement=statement)

    def tableStockSummary(self):
        table_name = "STOCK_SUMMARY"
        stream_name = "STOCK_PRICES_1S_STREAM"
        statement = f"""
            CREATE TABLE {table_name} WITH (
                KAFKA_TOPIC = '{table_name}',
                VALUE_FORMAT = 'AVRO',
                KEY_FORMAT = 'AVRO'
            ) AS
            SELECT
                TIMESTAMP,
                SUM(AVG_PRICE) AS TOTAL_PRICE,
                COLLECT_LIST(SYMBOL) AS symbols
            FROM {stream_name}
            WINDOW TUMBLING (SIZE 1 SECONDS)
            GROUP BY TIMESTAMP
            EMIT FINAL;
        """
        self.__execute_statement(storageType=StorageType.TABLE, storageName=table_name, statement=statement)

