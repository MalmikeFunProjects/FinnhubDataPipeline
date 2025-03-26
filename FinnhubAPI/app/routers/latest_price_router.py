import asyncio
from datetime import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, WebSocketDisconnect, Query, WebSocket
from typing import Dict, List, Optional

from routers.ConnectionManager import ConnectionManager, get_connection_manager
from routers.models import LatestPrice
from services.latest_price_service import LatestPriceService
from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("latest_price_router", log_to_console=True)

class LatestPriceRouter():
    """Router handling latest price endpoints and WebSocket connections"""
    def __init__(self):
        self.service = LatestPriceService(LatestPrice)
        self.router = APIRouter(prefix="/latest_price", tags=["latest_price"])
        self.setup_routes()
        # Track active WebSocket tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def setup_routes(self):
        """Configure API routes"""
        self.router.add_api_route(
            "/",
            self.get_latest_price,
            methods=["GET"],
            response_model=List[LatestPrice]
        )

        self.router.add_api_route(
            "/{symbol}",
            self.get_latest_price,
            methods=["GET"],
            response_model=List[LatestPrice]
        )

        self.router.websocket("/ws")(self.websocket_endpoint)

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        manager: ConnectionManager = Depends(get_connection_manager)
    ):
        """Handle WebSocket connections for streaming latest price data"""
        # Parse connection parameters
        connection_id = f"latest_price_{datetime.now().timestamp()*1000}"
        query_params = dict(websocket.query_params)

        symbol = query_params.get("symbol")
        start_days_ago = self._parse_days_param(query_params.get("start_days_ago", "1"))

        # Connection metadata
        metadata = {
            "type": "latest_price",
            "connected_at": datetime.now().isoformat(),
            "symbol": symbol,
            "start_days_ago": start_days_ago,
            "user_agent": websocket.headers.get("user-agent", "Unknown")
        }

        # Accept and manage the connection
        async with manager.connection_context(websocket, connection_id, metadata) as client_id:
            logger.info(f"WebSocket connection started: {client_id} (latest_price)")

            try:
                # Start streaming task
                self.active_tasks[client_id] = asyncio.create_task(
                    self._stream_latest_prices(
                        client_id=client_id,
                        symbol=symbol,
                        start_days_ago=start_days_ago
                    )
                )

                # Handle client messages
                while True:
                    data = await websocket.receive_text()
                    await self._handle_client_message(client_id, data, symbol)

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected: {client_id}")
                self._cleanup_tasks(client_id)

            except Exception as e:
                logger.exception(f"Error in WebSocket handler: {str(e)}")
                self._cleanup_tasks(client_id)

    async def _handle_client_message(
        self,
        client_id: str,
        message: str,
        current_symbol: Optional[str] = None,
        manager: ConnectionManager = Depends(get_connection_manager)
    ):
        """Process messages received from the client"""
        try:
            # Ensure the manager is a ConnectionManager instance
            if not isinstance(manager, ConnectionManager):
                manager = get_connection_manager()

            data = json.loads(message)
            action = data.get("action")

            if action == "stop":
                self._cleanup_tasks(client_id)
                await manager.send_json(
                    client_id=client_id,
                    data={"type": "control", "message": "Price updates stopped"}
                )

            elif action == "start":
                # Cancel existing task if running
                self._cleanup_tasks(client_id)

                # Get parameters from payload
                payload = data.get("payload", {})
                symbol = payload.get("symbol", current_symbol)
                start_days_ago = self._parse_days_param(payload.get("start_days_ago", "1"))

                # Create new streaming task
                self.active_tasks[client_id] = asyncio.create_task(
                    self._stream_latest_prices(
                        client_id=client_id,
                        symbol=symbol,
                        start_days_ago=start_days_ago
                    )
                )

                await manager.send_json(
                    client_id=client_id,
                    data={"type": "control", "message": "Price updates started"}
                )

            elif action == "change_symbol":
                payload = data.get("payload", {})
                symbol = payload.get("symbol")

                if symbol and symbol != current_symbol:
                    # Cancel existing task if running
                    self._cleanup_tasks(client_id)

                    # Create new streaming task with updated symbol
                    self.active_tasks[client_id] = asyncio.create_task(
                        self._stream_latest_prices(
                            client_id=client_id,
                            symbol=symbol,
                            start_days_ago=self._parse_days_param(payload.get("start_days_ago", "1"))
                        )
                    )

                    await manager.send_json(
                        client_id=client_id,
                        data={"type": "control", "message": f"Changed symbol to {symbol}"}
                    )

        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON from client: {message}")

        except Exception as e:
            logger.error(f"Error processing client message: {str(e)}")

    async def _stream_latest_prices(
        self,
        client_id: str,
        symbol: Optional[str] = None,
        start_days_ago: int = 1,
        manager: ConnectionManager = Depends(get_connection_manager)
    ):
        """Stream latest price data to the client"""
        logger.info(f"Starting price stream for client {client_id}, symbol={symbol}, start_days_ago={start_days_ago}")

        try:
            # Ensure the manager is a ConnectionManager instance
            if not isinstance(manager, ConnectionManager):
                manager = get_connection_manager()

            # Send initial batch
            initial_data = self._fetch_latest_prices(symbol, start_days_ago)

            if not initial_data:
                await manager.send_json(
                    client_id=client_id,
                    data={"type": "info", "message": f"No data found for {'symbol ' + symbol if symbol else 'any symbol'}"}
                )
                return

            await manager.send_json(
                client_id=client_id,
                data={"type": "info", "message": f"Initial data fetched: {len(initial_data)} records"}
            )

            # Track the last timestamp we've seen
            last_timestamp = 0
            last_timestamp = await self._send_price_record_ws(
                client_id=client_id,
                last_timestamp=last_timestamp,
                latest_prices=initial_data
            )

            # Start continuous updates
            while True:
                # Fetch new prices since last update
                new_prices = self._fetch_latest_prices(
                    symbol=symbol,
                    since_timestamp=last_timestamp
                )

                if new_prices:
                    last_timestamp = await self._send_price_record_ws(
                        client_id=client_id,
                        last_timestamp=last_timestamp,
                        latest_prices=new_prices
                    )

                # Wait 5 seconds before next update
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info(f"Price stream cancelled for client {client_id}")
            raise

        except Exception as e:
            logger.exception(f"Error in price stream for client {client_id}: {str(e)}")
            await manager.send_json(
                client_id=client_id,
                data={"type": "error", "message": "An error occurred while streaming prices"}
            )

    async def _send_price_record_ws(
        self,
        client_id: str,
        last_timestamp: int=0,
        latest_prices: List[LatestPrice]=[],
        manager: ConnectionManager = get_connection_manager()
    ) -> int:
        """Send a price record to a WebSocket client"""
        try:
            # Ensure the manager is a ConnectionManager instance
            if not isinstance(manager, ConnectionManager):
                manager = get_connection_manager()

            # Send each price record
            for price in latest_prices:
                # Update the last seen timestamp
                if isinstance(price.event_timestamp, int):
                    last_timestamp = max(last_timestamp, price.event_timestamp)
                await manager.send_json(
                    client_id=client_id,
                    data={"type": "latest_price", "payload": price.model_dump()}
                )
            return last_timestamp
        except Exception as e:
            logger.exception(f"Error sending price record to WebSocket: {str(e)}")
            raise e

    def _cleanup_tasks(self, client_id: str):
        """Cancel and remove tasks for a client"""
        if client_id in self.active_tasks:
            task = self.active_tasks[client_id]
            if not task.done():
                task.cancel()
            self.active_tasks.pop(client_id, None)

    def _parse_days_param(self, days_str: Optional[str]) -> int:
        """Convert days parameter to integer with validation"""
        try:
            days = int(days_str) if days_str else 1
            return max(1, min(days, 30))  # Limit between 1 and 30 days
        except (ValueError, TypeError):
            return 1

    def _fetch_latest_prices(
        self,
        symbol: Optional[str] = None,
        start_days_ago: Optional[int] = None,
        since_timestamp: Optional[int] = None,
        batch_size: int = 100
    ) -> List[LatestPrice]:
        """Fetch latest prices from the service layer"""
        try:
            return self.service.get_latest_prices(
                symbol=symbol,
                start_days_ago=start_days_ago,
                since_timestamp=since_timestamp,
                batch_size=batch_size
            )
        except Exception as e:
            logger.exception(f"Error fetching latest prices: {str(e)}")
            return []

    async def get_latest_price(
        self,
        symbol: Optional[str] = None,
        start_days_ago: Optional[int] = Query(1, ge=1, le=30, description="Days to look back"),
        limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of records to return")
    ) -> List[LatestPrice]:
        """REST API endpoint to get latest prices"""
        try:
            prices = self._fetch_latest_prices(
                symbol=symbol,
                start_days_ago=start_days_ago,
                batch_size=limit
            )

            if not prices:
                raise HTTPException(
                    status_code=404,
                    detail=f"No latest prices found for the specified parameters"
                )

            return prices

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(f"Error in get_latest_price: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while retrieving latest prices"
            )

latest_price_router = LatestPriceRouter().router

