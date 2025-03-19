import asyncio
import json
import logging
import time
from fastapi import APIRouter, HTTPException, WebSocketDisconnect, Query
from fastapi import WebSocket
from typing import List, Optional

from routers.models import StockPrice1s
from services.stock_price_1s_service import StockPrice1sService


logging.basicConfig(level=logging.INFO)

class StockPrice1sRouter():
    def __init__(self):
        self.stock_price_1s_service = StockPrice1sService(StockPrice1s)
        self.router = APIRouter(prefix="/stock_price_1s", tags=["stock_price_1s"])
        self.setup_routes()
        self.run_ws = True

    def setup_routes(self):
        #HTTP routes
        self.router.add_api_route("/", self.get_stock_price_1s, methods=["GET"], response_model=List[StockPrice1s])
        self.router.add_api_route("/{symbol}", self.get_stock_price_1s, methods=["GET"], response_model=List[StockPrice1s])
        # WebSocket routes
        self.router.websocket("/ws")(self.websocket_endpoint)

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        try:
            logging.info("WebSocket connected!")
            self.websocket_task = asyncio.create_task(self.get_stock_price_1s_ws(websocket))
            # Keep the connection open and handle incoming messages
            while True:
                data = await websocket.receive_text()
                await self.__action_stock_price_1s_task(data, websocket)
                print(f"Received data: {data}")

        except WebSocketDisconnect as e:
            logging.error("WebSocket disconnected: {e}")
        except Exception as e:
            logging.error(f"WebSocket error: {e}")
        finally:
            self.websocket_task.cancel()
            websocket.close()
            logging.info("WebSocket connection closed.")

    async def __action_stock_price_1s_task(self, data: str, websocket: WebSocket):
        try:
            action = json.loads(data)
            if action["action"] == "stop":
                self.run_ws = False
                if hasattr(self, "websocket_task") and not self.websocket_task.done():
                    self.websocket_task.cancel()
                await websocket.send_text("Stopping latest price updates...")
            elif action["action"] == "start":
                symbol = action.get("symbol", None)
                start_date = action.get("start_date", 1)
                self.run_ws = True
                if hasattr(self, "websocket_task") and not self.websocket_task.done():
                    self.websocket_task.cancel()
                self.websocket_task = asyncio.create_task(self.get_stock_price_1s_ws(websocket, symbol, start_date))

        except Exception as e:
            logging.error(f"Error applying action {action["action"]} to latest price task: {e}")


    async def get_stock_price_1s_ws(self, websocket: WebSocket, start_date: int = 1, symbol: str=None) -> List[StockPrice1s]:
        logging.info("Starting latest price updates over WebSocket")
        reset_start_date = start_date
        self.run_ws = True

        try:
            await websocket.send_text("Starting latest price updates 1...")
            while self.run_ws:
                stock_price_1s = self.stock_price_1s_service.get_stock_price_1s(batch_size=100, reset_start_date=reset_start_date, symbol=symbol)
                if not stock_price_1s:
                    stock_price_1s = []
                await websocket.send_text(f"Size of latest price: {len(stock_price_1s)}")
                if(len(stock_price_1s) == 0):
                    break
                for stock_price_1s_item in stock_price_1s:
                    await websocket.send_json(stock_price_1s_item.model_dump())
                reset_start_date = None
                await asyncio.sleep(10)
        except Exception as e:
            logging.error(f"Error sending data to WebSocket: {e}")

    async def get_stock_price_1s(
            self,
            symbol: str=None,
            start_date: Optional[int] = Query(None)
            ) -> List[StockPrice1s]:
        reset_start_date = start_date
        print(f"Start date: {reset_start_date}")
        stock_price_1s = self.stock_price_1s_service.get_stock_price_1s(symbol=symbol, batch_size=100, reset_start_date=reset_start_date)
        if not stock_price_1s:
            raise HTTPException(status_code=404, detail=f"latest price not found")
        return stock_price_1s

stock_price_1s_router = StockPrice1sRouter().router

