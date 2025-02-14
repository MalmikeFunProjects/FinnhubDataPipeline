
from execute_ksql.ksql_handler_methods import KsqlHandlerMethods
from utils.enums import StorageType


class MakeKsqlRequest:
    """
    A class for making requests to the ksqlDB server.
    """

    def __init__(self):
        """
        Initializes the MakeKsqlRequest class with a KsqlHandlerMethods instance.
        """
        self.ksqlHandlerMethodsl = KsqlHandlerMethods()
        self.headers = self.ksqlHandlerMethodsl.headers()

    def handle_request(self, statement: str, streamsProperties={}, request_type: str = "query"):
        """
        Handles a ksqlDB request.

        :param statement: The ksqlDB query statement.
        :param streamsProperties: Additional stream properties, default is empty.
        :param request_type: The type of request, default is "query".
        :return: The response from the ksqlDB server.
        """
        payload = self.ksqlHandlerMethodsl.payload(
            statement=statement, streamsProperties=streamsProperties)
        return self.ksqlHandlerMethodsl.request(headers=self.headers, payload=payload, request_type=request_type)

    def show_storage_type(self, storage_type: StorageType):
        """
        Retrieves details of a specific storage type in ksqlDB.

        :param storage_type: The storage type to retrieve (STREAM, TABLE, etc.).
        :return: The response containing storage details.
        """
        statement = f"SHOW {storage_type.value};"
        return self.handle_request(statement=statement, request_type="ksql")

    def check_storage_type_exists(self, storage_type: StorageType, name: str):
        """
        Checks if a specific storage type exists in ksqlDB.

        :param storage_type: The type of storage to check.
        :param name: The name of the storage to check for existence.
        :return: True if the storage exists, False otherwise.
        """
        response = self.show_storage_type(storage_type)
        return any(s_type["name"] == name for s_type in response[0][storage_type.value])

    def check__exists(self, stream_name: str):
        """
        Checks if a stream exists in ksqlDB.

        :param stream_name: The name of the stream to check.
        :return: True if the stream exists, False otherwise.
        """
        response = self.show_storage_type(StorageType.STREAM)
        return any(stream["name"] == stream_name for stream in response[0]["streams"])

    def drop_stream(self, stream_name: str):
        """
        Drops a stream if it exists in ksqlDB.

        :param stream_name: The name of the stream to drop.
        :return: The response from the ksqlDB server.
        """
        statement = f"DROP STREAM IF EXISTS {stream_name};"
        return self.handle_request(statement=statement)

    def create_stream(self,
                      stream_name: str,
                      kafka_topic: str,
                      value_format: str,
                      partitions: int,
                      column_defs: list[str] = None):
        """
        Creates a new stream in ksqlDB.

        :param stream_name: The name of the stream.
        :param kafka_topic: The Kafka topic backing the stream.
        :param value_format: The format of the values in the stream (e.g., AVRO, JSON).
        :param partitions: The number of partitions for the Kafka topic.
        :param column_defs: Optional list of column definitions.
        :return: The response from the ksqlDB server.
        """
        column_str = f"({', '.join(column_defs)})" if column_defs is not None else ""
        statement = f"""
          CREATE STREAM {stream_name} {column_str} WITH (
          KAFKA_TOPIC='{kafka_topic}',
          VALUE_FORMAT='{value_format}',
          PARTITIONS={partitions}
          );
        """
        return self.handle_request(statement=statement, request_type="ksql")
