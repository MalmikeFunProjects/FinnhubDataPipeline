import pytest
from unittest.mock import MagicMock, patch
from app.execute_ksql.execute_ksql_request import ExecuteKsqlRequest
from app.utils.enums import StorageType

class TestExecuteKsqlRequest:
    @pytest.fixture
    def mock_make_ksql_request(self):
        with patch("app.execute_ksql.execute_ksql_request.MakeKsqlRequest") as Mock:
            instance = Mock.return_value
            instance.handle_request.return_value = "MOCK_RESPONSE"
            instance.check_storage_type_exists.return_value = False
            yield instance

    @pytest.fixture
    def execute_ksql(self, mock_make_ksql_request):
        return ExecuteKsqlRequest()

    def test_set_offset_called_on_init(self, mock_make_ksql_request):
        ExecuteKsqlRequest()
        mock_make_ksql_request.handle_request.assert_called_with(
            statement="SET 'auto.offset.reset'='earliest';",
            request_type="ksql"
        )

    def test_create_stock_prices_stream_creates_if_not_exists(self, execute_ksql, mock_make_ksql_request):
        execute_ksql.createStockPricesStream()
        assert mock_make_ksql_request.create_stream.called
        assert mock_make_ksql_request.create_stream.call_args[1]['stream_name'] == "STOCK_PRICES"

    def test_create_symbols_stream_creates_if_not_exists(self, execute_ksql, mock_make_ksql_request):
        execute_ksql.createSymbolsStream()
        assert mock_make_ksql_request.create_stream.called
        assert mock_make_ksql_request.create_stream.call_args[1]['stream_name'] == "SYMBOLS"

    @pytest.mark.parametrize("method, table_name", [
        ("tableCompanySymbols", "COMPANY_SYMBOLS"),
        ("tableLatestPrices", "LATEST_PRICES"),
        ("tableStockPrices1sAvg", "STOCK_PRICES_1S"),
        ("tableStockSummary", "STOCK_SUMMARY")
    ])
    def test_table_creation_calls_handle_request(self, method, table_name, execute_ksql, mock_make_ksql_request):
        getattr(execute_ksql, method)()
        mock_make_ksql_request.handle_request.assert_called()
        assert table_name in mock_make_ksql_request.handle_request.call_args[1]['statement']

    def test_stream_stock_prices_1s_avg_calls_handle_request(self, execute_ksql, mock_make_ksql_request):
        execute_ksql.streamStockPrices1sAvg()
        mock_make_ksql_request.handle_request.assert_called()
        assert "STOCK_PRICES_1S_STREAM" in mock_make_ksql_request.handle_request.call_args[1]['statement']

    def test_no_creation_if_stream_exists_prints_message(self, mock_make_ksql_request, capfd):
        mock_make_ksql_request.check_storage_type_exists.return_value = True
        executor = ExecuteKsqlRequest()
        executor.createStockPricesStream()
        out, _ = capfd.readouterr()
        assert "Stream STOCK_PRICES already exists" in out
        mock_make_ksql_request.create_stream.assert_not_called()

    def test_no_creation_if_table_exists_prints_message(self, mock_make_ksql_request, capfd):
        mock_make_ksql_request.check_storage_type_exists.return_value = True
        executor = ExecuteKsqlRequest()
        executor.tableCompanySymbols()
        out, _ = capfd.readouterr()
        assert "Table COMPANY_SYMBOLS already exists" in out
