import pytest
from unittest.mock import patch, MagicMock
from app.execute_ksql.ksql_handler_methods import KsqlHandlerMethods

# Sample data
sample_statement = "SELECT * FROM my_stream;"
sample_props = {"auto.offset.reset": "latest"}

class TestKsqlHandlerMethods:
    """
    Tests for the KsqlHandlerMethods class.
    """
    def test_headers_returns_correct_content_type(self):
        kh = KsqlHandlerMethods()
        headers = kh.headers()
        assert headers == {"Content-Type": "application/vnd.ksql.v1+json"}


    def test_stream_properties_returns_default(self):
        kh = KsqlHandlerMethods()
        props = kh.stream_properties()
        assert props == {"auto.offset.reset": "earliest"}


    def test_payload_returns_expected_format(self):
        kh = KsqlHandlerMethods()
        payload = kh.payload(statement=sample_statement, streamsProperties=sample_props)
        assert payload == {"ksql": sample_statement, "streamsProperties": sample_props}


    def test_stream_payload_returns_expected_format(self):
        kh = KsqlHandlerMethods()
        payload = kh.stream_payload(statement=sample_statement, streamsProperties=sample_props)
        assert payload == {"sql": sample_statement, "properties": sample_props}


    @patch("app.execute_ksql.ksql_handler_methods.requests.post")
    def test_request_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "ok"}
        mock_post.return_value = mock_response

        kh = KsqlHandlerMethods()
        response = kh.request(
            headers={"Content-Type": "application/json"},
            payload={"ksql": sample_statement},
            request_type="ksql"
        )

        assert response == {"result": "ok"}
        mock_post.assert_called_once()


    @patch("app.execute_ksql.ksql_handler_methods.requests.post")
    def test_request_failure_raises_exception(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        kh = KsqlHandlerMethods()

        with pytest.raises(Exception) as excinfo:
            kh.request(
                headers={"Content-Type": "application/json"},
                payload={"ksql": sample_statement},
                request_type="ksql"
            )

        assert "Error: Bad Request" in str(excinfo.value)
