
from execute_ksql.ksql_handler_methods import KsqlHandlerMethods
from utils.enums import StorageType


class MakeKsqlRequest:
    def __init__(self):
        self.ksqlHandlerMethodsl = KsqlHandlerMethods()
        self.headers = self.ksqlHandlerMethodsl.headers()

    def handle_request(self, statement: str, streamsProperties={}, request_type: str = "query"):
        payload = self.ksqlHandlerMethodsl.payload(
            statement=statement, streamsProperties=streamsProperties)
        return self.ksqlHandlerMethodsl.request(headers=self.headers, payload=payload, request_type=request_type)

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

