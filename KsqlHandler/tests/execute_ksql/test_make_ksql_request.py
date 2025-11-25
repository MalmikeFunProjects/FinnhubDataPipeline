import pytest
from unittest.mock import patch, MagicMock
from app.execute_ksql.make_ksql_request import MakeKsqlRequest
from app.utils.enums import StorageType

class TestMakeKsqlRequest:
    @pytest.fixture
    def mock_ksql_handler(self):
        with patch("app.execute_ksql.make_ksql_request.KsqlHandlerMethods") as MockHandler:
            mock_instance = MockHandler.return_value
            mock_instance.headers.return_value = {"Content-Type": "application/vnd.ksql.v1+json"}
            mock_instance.payload.return_value = {"ksql": "mock-statement", "streamsProperties": {}}
            mock_instance.request.return_value = [{"streams": [{"name": "STOCK_PRICES"}]}]
            yield mock_instance


    @pytest.fixture
    def make_ksql(self, mock_ksql_handler):
        return MakeKsqlRequest()


    def test_init_sets_headers(self, mock_ksql_handler):
        req = MakeKsqlRequest()
        assert req.headers == {"Content-Type": "application/vnd.ksql.v1+json"}


    def test_handle_request_calls_payload_and_request(self, make_ksql, mock_ksql_handler):
        statement = "SELECT * FROM foo;"
        result = make_ksql.handle_request(statement=statement)
        mock_ksql_handler.payload.assert_called_with(statement=statement, streamsProperties={})
        mock_ksql_handler.request.assert_called()
        assert result == [{"streams": [{"name": "STOCK_PRICES"}]}]


    def test_show_storage_type_calls_handle_request(self, make_ksql):
        with patch.object(make_ksql, "handle_request", return_value="ok") as mock_handle:
            res = make_ksql.show_storage_type(StorageType.STREAM)
            mock_handle.assert_called_with(statement="SHOW streams;", request_type="ksql")
            assert res == "ok"


    def test_check_storage_type_exists_returns_true(self, make_ksql):
        # "STOCK_PRICES" is mocked as present in `mock_ksql_handler`
        result = make_ksql.check_storage_type_exists(StorageType.STREAM, "STOCK_PRICES")
        assert result is True


    def test_check_storage_type_exists_returns_false(self, make_ksql, mock_ksql_handler):
        mock_ksql_handler.request.return_value = [{"streams": [{"name": "OTHER_STREAM"}]}]
        result = make_ksql.check_storage_type_exists(StorageType.STREAM, "STOCK_PRICES")
        assert result is False


    def test_check__exists_alias_returns_true(self, make_ksql):
        result = make_ksql.check__exists("STOCK_PRICES")
        assert result is True


    def test_drop_stream_calls_handle_request(self, make_ksql):
        with patch.object(make_ksql, "handle_request", return_value="Dropped") as mock_handle:
            response = make_ksql.drop_stream("MY_STREAM")
            mock_handle.assert_called_once()
            assert "DROP STREAM IF EXISTS MY_STREAM" in mock_handle.call_args[1]["statement"]
            assert response == "Dropped"


    def test_create_stream_sends_correct_statement(self, make_ksql):
        with patch.object(make_ksql, "handle_request", return_value="Stream Created") as mock_handle:
            response = make_ksql.create_stream(
                stream_name="NEW_STREAM",
                kafka_topic="my-topic",
                value_format="AVRO",
                partitions=1,
                column_defs=["symbol VARCHAR", "price DOUBLE"]
            )
            stmt = mock_handle.call_args[1]["statement"]
            assert "CREATE STREAM NEW_STREAM" in stmt
            assert "symbol VARCHAR" in stmt
            assert "KAFKA_TOPIC='my-topic'" in stmt
            assert response == "Stream Created"
