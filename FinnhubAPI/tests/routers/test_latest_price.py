# from fastapi import WebSocket, WebSocketDisconnect
# import pytest
# import asyncio
# from datetime import datetime, timedelta
# from unittest.mock import patch, MagicMock, AsyncMock
# from app.database.models.LatestPrice import LatestPrice

# # Define your MockCassandraClient first - but don't import any app modules yet!
# class MockCassandraClient:
#     def __init__(self, *args, **kwargs):
#         pass

#     def __enter__(self):
#         return self

#     def __exit__(self, *args):
#         pass

#     def sync_table(self, *args, **kwargs):
#         return None

#     def query_time_partitioned_data(self, *args, **kwargs):
#         # Return mock data that matches your expected format
#         filters = kwargs.get('filters', {})
#         if(filters.get('symbol') == "AAPL"):
#             return {"records": AAPL_SAMPLE_DATA}
#         elif(filters.get('symbol') == "MSFT"):
#             return {"records": MSFT_SAMPLE_DATA}
#         else:
#             return {"records": ALL_SAMPLE_DATA_FOR_DB}

# AAPL_SAMPLE_DATA = [
#     LatestPrice(event_timestamp=int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000), symbol="AAPL", last_price=150.25),
#     LatestPrice(event_timestamp=int((datetime.now() - timedelta(minutes=4)).timestamp() * 1000), symbol="AAPL", last_price=150.50),
#     LatestPrice(event_timestamp=int((datetime.now() - timedelta(minutes=3)).timestamp() * 1000), symbol="AAPL", last_price=150.75),
# ]

# MSFT_SAMPLE_DATA = [
#     LatestPrice(event_timestamp=int((datetime.now() - timedelta(minutes=2)).timestamp() * 1000), symbol="MSFT", last_price=300.10),
#     LatestPrice(event_timestamp=int((datetime.now() - timedelta(minutes=1)).timestamp() * 1000), symbol="MSFT", last_price=300.25),
# ]
# ALL_SAMPLE_DATA_FOR_DB = AAPL_SAMPLE_DATA + MSFT_SAMPLE_DATA


# # Apply patches at module level - BEFORE any imports from your app
# # Use the decorator form of pytest.fixture
# @pytest.fixture(scope="session", autouse=True)
# def mock_dependencies():
#     """Apply all mocks before any imports happen"""
#     # Create all the necessary patches
#     cassandra_client_patch = patch('app.database.cassandra_client.CassandraClient', MockCassandraClient)
#     config_patch = patch('app.database.cassandra_config.get_cassandra_config',
#                          return_value={"contact_points": ["localhost"], "port": 9042, "keyspace": "market"})

#     # Start the patches
#     cassandra_client_patch.start()
#     config_patch.start()

#     # Yield to run the tests
#     yield

#     # Stop patches after tests
#     cassandra_client_patch.stop()
#     config_patch.stop()

# # Now it's safe to import the app components - AFTER the mocks are in place
# @pytest.fixture
# def test_app(mock_dependencies):
#     # Only import here after mocks are established
#     from fastapi import FastAPI
#     from fastapi.testclient import TestClient
#     from app.main import app
#     from app.routers.latest_price_router import latest_price_router

#     return TestClient(app)

# # Mock for the CassandraMapper after imports are safe
# @pytest.fixture
# def setup_mapper_mock(mock_dependencies):
#     """Setup the CassandraMapper mock"""
#     # Now it's safe to import from the app
#     from app.routers.models import LatestPrice

#     # Create sample LatestPrice objects
#     sample_prices = [
#         LatestPrice(event_timestamp=record["event_timestamp"],
#                   symbol=record["symbol"],
#                   last_price=record["last_price"])
#         for record in ALL_SAMPLE_DATA_FOR_DB
#     ]

#     # Create the mock
#     with patch('app.services.latest_price_service.CassandraMapper') as mock_mapper:
#         mapper_instance = mock_mapper.return_value
#         mapper_instance.to_pydantic_list.return_value = sample_prices
#         yield mapper_instance

# @pytest.fixture
# def mock_websocket():
#     """Mock WebSocket client"""
#     from fastapi import WebSocket
#     mock_ws = AsyncMock(spec=WebSocket)
#     mock_ws.client = "test_client_id"
#     mock_ws.recieve_text = AsyncMock()
#     return mock_ws

# # WebSocket connection manager mock
# @pytest.fixture
# def mock_connection_manager():
#      # Create an async context manager class
#     class AsyncContextManager:
#         async def __aenter__(self):
#             return "test_client_id"

#         async def __aexit__(self, exc_type, exc_val, exc_tb):
#             return None

#     # Create a mock context manager factory function
#     async_context = MagicMock(return_value=AsyncContextManager())

#     # Create the manager mock with the async context method
#     with patch('app.routers.latest_price_router.get_connection_manager') as mock_get_manager:
#         manager = AsyncMock()
#         # Set the connection_context method to return our async context manager
#         manager.connection_context = async_context
#         manager.send_json = AsyncMock()

#         # Return the mock manager when get_connection_manager is called
#         mock_get_manager.return_value = manager
#         yield manager

# # WebSocket test (using pytest-asyncio)
# @pytest.mark.asyncio
# async def test_websocket_endpoint(mock_dependencies, mock_connection_manager, setup_mapper_mock):
#     from app.routers.latest_price_router import LatestPriceRouter

#     websocket = MagicMock(spec=WebSocket)
#     websocket.query_params = {"symbol": "BTC", "start_days_ago": "1"}
#     websocket.receive_text = AsyncMock()
#     # Add receive_text method as AsyncMock with 1-second delay
#     async def delayed_receive_text():
#         await asyncio.sleep(1)  # 1-second delay
#         return ["", "", WebSocketDisconnect(code=1000)]
#     websocket.receive_text.side_effect = ["", "", WebSocketDisconnect(code=1000)]
#     websocket.headers = {"user-agent": "TestAgent"}

#     # Mock the service method to return some test data
#     test_price = LatestPrice(
#         symbol="BTC",
#         price=50000.0,
#         event_timestamp=int(datetime.now().timestamp() * 1000)
#     )

#     # Create the router with mocked dependencies
#     router = LatestPriceRouter()

#     with patch.object(router, '_fetch_latest_prices') as mock_fetch:
#         with patch.object(router, '_stream_latest_prices') as mock_stream:
#             mock_fetch.return_value = [test_price]

#             # Create a task for the _stream_latest_prices method
#             mock_task = asyncio.Future()
#             mock_stream.return_value = mock_task
#             router.active_tasks = {}

#             # Call the endpoint method
#             try:
#                 await router.websocket_endpoint(websocket, mock_connection_manager)
#                 router._cleanup_tasks("test_client_id")
#             except WebSocketDisconnect:
#                 pass
#             except Exception as e:
#                 if str(e) != "Test done":
#                     raise

#             router._cleanup_tasks("test_client_id")

#             # Verify that the stream task was created with correct parameters
#             mock_stream.assert_called_once()
#             call_args = mock_stream.call_args[1]
#             assert call_args["client_id"] == "test_client_id"
#             assert call_args["symbol"] == "BTC"
#             assert call_args["start_days_ago"] == 1

#             # Now let's verify that manager.send_json is called within _stream_latest_prices
#             # We'll simulate this by calling the _send_price_record_ws method directly

#             # Create a separate patch for _send_price_record_ws to execute its body
#             with patch.object(router, '_send_price_record_ws', wraps=router._send_price_record_ws) as wrapped_send:
#                 # Call the method directly
#                 await router._send_price_record_ws(
#                     client_id="test_client_id",
#                     last_timestamp=0,
#                     latest_prices=[test_price],
#                     manager=mock_connection_manager
#                 )

#                 # Verify manager.send_json was called with the expected data
#                 mock_connection_manager.send_json.assert_called_with(
#                     client_id="test_client_id",
#                     data={"type": "latest_price", "payload": test_price.model_dump()}
#                 )

#             router._cleanup_tasks("test_client_id")

#     # Mock the _stream_latest_prices method
#     # router._stream_latest_prices = AsyncMock()
#     # with patch.object(router, '_stream_latest_prices', wraps=router._stream_latest_prices) as spy_stream:
#     #     # Mock websocket client
#     #     mock_websocket = AsyncMock(spec=WebSocket)
#     #     mock_websocket.query_params = {"symbol": "AAPL", "start_days_ago": "1"}
#     #     mock_websocket.receive_text = AsyncMock()
#     #     mock_websocket.receive_text.side_effect = ["", "", WebSocketDisconnect(code=1000)]

#     #     # Start the websocket endpoint in a task so we can control its lifecycle
#     #     endpoint_task = asyncio.create_task(
#     #         router.websocket_endpoint(mock_websocket, mock_connection_manager)
#     #     )
#     #     # Give the task time to create and start the _stream_latest_prices task
#     #     print(router.active_tasks)
#     #     await asyncio.sleep(0.1)

#     #     print(router.active_tasks)

#     #     # Now cancel the endpoint task
#     #     endpoint_task.cancel()
#     #     try:
#     #         await endpoint_task
#     #     except asyncio.CancelledError:
#     #         pass

#     #     spy_stream.assert_called_once()
#     #     call_args = spy_stream.call_args[1]
#     #     assert call_args['client_id'] == "test_client_id"
#     #     assert call_args['symbol'] == "AAPL"
#     #     assert call_args['start_days_ago'] == 1
#     #     assert call_args['since_timestamp'] is None

#     #     mock_connection_manager.send_json.assert_called()

#         # # Test the websocket endpoint
#         # try:
#         #     await router.websocket_endpoint(mock_websocket, mock_connection_manager)
#         # except Exception as e:
#         #     if str(e) != "Test done":
#         #         raise

#         # # Check that connection was accepted
#         # mock_connection_manager.connection_context.assert_called_once()

#         # # Give the scheduled task a chance to run
#         # # await asyncio.sleep(0.1)

#         # router._stream_latest_prices.assert_called_once_with(
#         #     client_id="test_client_id",
#         #     symbol="AAPL",
#         #     start_days_ago=1,
#         #     since_timestamp=None
#         # )
#         # router._stream_latest_prices.assert_called_once()

#         # # Check that we tried to send data
#         # assert mock_connection_manager.send_json.called

# # REST API test
# def test_get_latest_price(test_app):
#     """Test getting latest prices via REST API"""
#     response = test_app.get("/latest_price/AAPL")
#     assert response.status_code == 200

#     # Parse the response
#     data = response.json()
#     assert len(data) > 0

#     # Verify structure
#     assert "event_timestamp" in data[0]
#     assert "symbol" in data[0]
#     assert "last_price" in data[0]

#     # Verify filtering works
#     assert all(price["symbol"] == "AAPL" for price in data)
