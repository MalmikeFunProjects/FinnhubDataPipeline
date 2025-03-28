import asyncio
from datetime import datetime
import json
from fastapi import APIRouter, HTTPException, Query, WebSocketDisconnect, WebSocket, Depends
from fastapi import WebSocket
from typing import Dict, List, Optional

from routers.ConnectionManager import ConnectionManager, get_connection_manager
from routers.models import StockSummary
from services.stock_summary_service import StockSummaryService

from utils.default_log_setting import DefaultLogger


logger = DefaultLogger.get_err_logger("stock_summary_router", log_to_console=True)

class StockSummaryRouter():
    """Router handling stock summary endpoints and WebSocket connections"""
    def __init__(self):
        self.service = StockSummaryService(StockSummary)
        self.router = APIRouter(prefix="/stock_summary", tags=["stock_summary"])
        self.setup_routes()
        # Track active WebSocket tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}

    def setup_routes(self):
        """Configure API routes"""
        self.router.add_api_route(
            "/",
            self.get_stock_summary,
            methods=["GET"],
            response_model=List[StockSummary]
        )

        self.router.websocket("/ws")(self.websocket_endpoint)

    async def websocket_endpoint(
        self,
        websocket: WebSocket,
        manager: ConnectionManager = Depends(get_connection_manager)
    ):
        """Handle WebSocket connections for streaming stock summary data"""
        # Parse connection parameters
        connection_id = f"stock_summary_{datetime.now().timestamp()*1000}"
        query_params = dict(websocket.query_params)

        start_days_ago = self._parse_days_param(query_params.get("start_days_ago", "1"))
        since_timestamp = self._parse_timestamp_param(query_params.get("since_timestamp"))

        # Connection metadata
        metadata = {
            "type": "stock_summary",
            "connected_at": datetime.now().isoformat(),
            "start_days_ago": start_days_ago,
            "since_timestamp": since_timestamp,
            "user_agent": websocket.headers.get("user-agent", "Unknown")
        }

        # Accept and manage the connection
        async with manager.connection_context(websocket, connection_id, metadata) as client_id:
            logger.info(f"WebSocket connection started: {client_id} (stock_summary)")

            try:
                # Start streaming task
                self.active_tasks[client_id] = asyncio.create_task(
                    self._stream_stock_summary(
                        client_id=client_id,
                        start_days_ago=start_days_ago,
                        since_timestamp=since_timestamp
                    )
                )

                # Handle client messages
                while True:
                    data = await websocket.receive_text()
                    await self._handle_client_message(client_id, data)

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
                    data={"type": "control", "message": "Stock summary updates stopped"}
                )

            elif action == "start":
                # Cancel existing task if running
                self._cleanup_tasks(client_id)

                # Get parameters from payload
                payload = data.get("payload", {})
                start_days_ago = self._parse_days_param(payload.get("start_days_ago", "1"))
                since_timestamp = self._parse_timestamp_param(payload.get("since_timestamp"))

                # Create new streaming task
                self.active_tasks[client_id] = asyncio.create_task(
                    self._stream_stock_summary(
                        client_id=client_id,
                        start_days_ago=start_days_ago,
                        since_timestamp=since_timestamp
                    )
                )

                await manager.send_json(
                    client_id=client_id,
                    data={"type": "control", "message": "Stock summary updates started"}
                )


        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON from client: {message}")

        except Exception as e:
            logger.error(f"Error processing client message: {str(e)}")

    async def _stream_stock_summary(
        self,
        client_id: str,
        start_days_ago: int = 1,
        since_timestamp: Optional[int] = None,
        manager: ConnectionManager = Depends(get_connection_manager)
    ):
        """Stream stock summary data to the client"""
        logger.info(f"Starting stock summary stream for client {client_id}, start_days_ago={start_days_ago}")

        try:
            # Ensure the manager is a ConnectionManager instance
            if not isinstance(manager, ConnectionManager):
                manager = get_connection_manager()

            # Send initial batch
            initial_data = self._fetch_stock_summary(start_days_ago=start_days_ago, since_timestamp=since_timestamp)

            if not initial_data:
                await manager.send_json(
                    client_id=client_id,
                    data={"type": "info", "message": f"No data found for stock summary"}
                )
                return

            await manager.send_json(
                client_id=client_id,
                data={"type": "info", "message": f"Initial data fetched: {len(initial_data)} records"}
            )

            # Track the last timestamp we've seen
            last_timestamp = 0
            last_timestamp = await self._send_stock_summary_record_ws(
                client_id=client_id,
                last_timestamp=last_timestamp,
                stock_summary=initial_data
            )

            # Start continuous updates
            while True:
                # Fetch new stock summary since last update
                new_stock_summary = self._fetch_stock_summary(
                    since_timestamp=last_timestamp
                )

                if new_stock_summary:
                    last_timestamp = await self._send_stock_summary_record_ws(
                        client_id=client_id,
                        last_timestamp=last_timestamp,
                        stock_summary=new_stock_summary
                    )

                # Wait 5 seconds before next update
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            logger.info(f"Stock summary stream cancelled for client {client_id}")
            raise

        except Exception as e:
            logger.exception(f"Error in stock summary stream for client {client_id}: {str(e)}")
            await manager.send_json(
                client_id=client_id,
                data={"type": "error", "message": "An error occurred while streaming stock summary"}
            )

    async def _send_stock_summary_record_ws(
        self,
        client_id: str,
        last_timestamp: int=0,
        stock_summary: List[StockSummary]=[],
        manager: ConnectionManager = get_connection_manager()
    ) -> int:
        """Send a stock summary record to a WebSocket client"""
        try:
            # Ensure the manager is a ConnectionManager instance
            if not isinstance(manager, ConnectionManager):
                manager = get_connection_manager()

            # Send each stock summary record
            for stock_summary_record in stock_summary:
                # Update the last seen timestamp
                if isinstance(stock_summary_record.event_timestamp, int):
                    last_timestamp = max(last_timestamp, stock_summary_record.event_timestamp)
                await manager.send_json(
                    client_id=client_id,
                    data={"type": "stock_summary", "payload": stock_summary_record.model_dump()}
                )
            return last_timestamp
        except Exception as e:
            logger.exception(f"Error sending stock summary record to WebSocket: {str(e)}")
            raise e

    def _cleanup_tasks(self, client_id: str):
        """Cancel and remove tasks for a client"""
        if client_id in self.active_tasks:
            task = self.active_tasks[client_id]
            if not task.done():
                task.cancel()
            self.active_tasks.pop(client_id, None)

    def _parse_timestamp_param(self, timestamp: Optional[str|int]) -> Optional[int]:
        """Convert timestamp parameter to integer with validation"""
        if(type(timestamp) == int):
            return timestamp
        try:
            return int(timestamp) if timestamp else None
        except (ValueError, TypeError):
            return None


    def _parse_days_param(self, days_str: Optional[str|int]) -> int:
        """Convert days parameter to integer with validation"""
        if(type(days_str) == int):
            return days_str
        try:
            days = int(days_str) if days_str else 1
            return max(1, min(days, 30))  # Limit between 1 and 30 days
        except (ValueError, TypeError):
            return 1

    def _fetch_stock_summary(
        self,
        start_days_ago: Optional[int] = None,
        since_timestamp: Optional[int] = None,
        batch_size: int = 100
    ) -> List[StockSummary]:
        """Fetch stock summary from the service layer"""
        try:
            if start_days_ago is not None and since_timestamp is None and start_days_ago == 0:
                since_timestamp = datetime.now().timestamp() * 1000

            return self.service.get_stock_summary(
                start_days_ago=start_days_ago,
                since_timestamp=since_timestamp,
                batch_size=batch_size
            )
        except Exception as e:
            logger.exception(f"Error fetching stock summary: {str(e)}")
            return []

    async def get_stock_summary(
        self,
        since_timestamp: Optional[int] = Query(None, description="Timestamp to start fetching from"),
        start_days_ago: Optional[int] = Query(1, ge=1, le=30, description="Days to look back"),
        limit: Optional[int] = Query(100, ge=1, le=1000, description="Maximum number of records to return")
    ) -> List[StockSummary]:
        """REST API endpoint to get stock summary"""
        try:
            stock_summary = self._fetch_stock_summary(
                start_days_ago=start_days_ago,
                batch_size=limit,
                since_timestamp=since_timestamp
            )

            if not stock_summary:
                raise HTTPException(
                    status_code=404,
                    detail=f"No stock summary found for the specified parameters"
                )

            return stock_summary

        except HTTPException:
            raise

        except Exception as e:
            logger.exception(f"Error in get_stock_summary: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="An error occurred while retrieving stock summary"
            )

stock_summary_router = StockSummaryRouter().router

