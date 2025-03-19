import asyncio
import json
import logging
import time
from fastapi import APIRouter, HTTPException, WebSocketDisconnect
from fastapi import WebSocket
from typing import List

from routers.models import StockSummary
from services.stock_summary_service import StockSummaryService

logging.basicConfig(level=logging.INFO)

class StockSummaryRouter():
    def __init__(self):
        self.stock_summary_service = StockSummaryService(StockSummary)
        self.router = APIRouter(prefix="/stock_summary", tags=["stock_summary"])
        self.setup_routes()
        self.run_ws = True

    def setup_routes(self):
        #HTTP routes
        self.router.add_api_route("/", self.get_stock_summary, methods=["GET"], response_model=List[StockSummary])
        self.router.add_api_route("/{limit}", self.get_stock_summary, methods=["GET"], response_model=List[StockSummary])
        # WebSocket routes
        self.router.websocket("/ws")(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            logging.info("WebSocket connected!")
            # Start a task to send stock updates
            self.websocket_task = asyncio.create_task(self.get_stock_summary_ws(websocket))
            # Keep the connection open and handle incoming messages
            while True:
                data = await websocket.receive_text()
                await self.__action_stock_summary_task(data, websocket)
                print(f"Received data: {data}")

        except WebSocketDisconnect as e:
            logging.error("WebSocket disconnected: {e}")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            self.websocket_task.cancel()
            websocket.close()
            logging.info("WebSocket connection closed.")

    async def __action_stock_summary_task(self, data: str, websocket: WebSocket):
        try:
            action = json.loads(data)
            if action["action"] == "stop":
                self.run_ws = False
                if hasattr(self, "websocket_task") and not self.websocket_task.done():
                    self.websocket_task.cancel()
                await websocket.send_text("Stopping stock summary updates...")
            elif action["action"] == "start":
                self.run_ws = True
                if hasattr(self, "websocket_task") and not self.websocket_task.done():
                    self.websocket_task.cancel()
                self.websocket_task = asyncio.create_task(self.get_stock_summary_ws(websocket))

        except Exception as e:
            logging.error(f"Error applying action {action["action"]} to stock summary task: {e}")


    async def get_stock_summary_ws(self, websocket: WebSocket) -> List[StockSummary]:
        logging.info("Starting stock summary updates over WebSocket")
        reset_start_date = 2
        self.run_ws = True

        try:
            await websocket.send_text("Starting stock summary updates 1...")
            while self.run_ws:
                stock_summary = self.stock_summary_service.get_stock_summary(batch_size=100, reset_start_date=reset_start_date)
                if not stock_summary:
                    stock_summary = []
                await websocket.send_text(f"Size of stock summary: {len(stock_summary)}")
                if(len(stock_summary) == 0):
                    break
                for stock in stock_summary:
                    await websocket.send_json(stock.model_dump())
                reset_start_date = None
                await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Error sending data to WebSocket: {e}")

    async def get_stock_summary(self, limit: int=100) -> List[StockSummary]:
        stock_summary = self.stock_summary_service.get_stock_summary(batch_size=limit)
        if not stock_summary:
            raise HTTPException(status_code=404, detail=f"Stock summary not found")
        return stock_summary

stock_summary_router = StockSummaryRouter().router

