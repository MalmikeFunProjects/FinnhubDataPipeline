import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers.stock_summary_router import stock_summary_router
from routers.latest_price_router import latest_price_router
from routers.company_symbols_router import company_symbol_router
from routers.stock_price_1s_router import stock_price_1s_router
from routers.web_sockets_stat_router import web_socket_stats_router
from contextlib import asynccontextmanager
from utils.default_log_setting import DefaultLogger
from routers.ConnectionManager import get_connection_manager
from middleware.log_requests import LogRequestMiddleware

# Force stdout to be unbuffered
sys.stdout.reconfigure(line_buffering=True)

# Create a logger
logger = DefaultLogger.get_err_logger("fastapi_app", log_to_console=True)

# Lifespan setup for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup: Initialize any resources here
    logger.info("Initializing application resources")

    # Create background tasks
    cleanup_task = asyncio.create_task(cleanup_inactive_connections())
    yield

    # Cleanup: Cancel background tasks
    logger.info("Shutting down application resources")
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

# Background task to clean up inactive connections
async def cleanup_inactive_connections():
    """Background task to periodically clean up inactive WebSocket connections"""
    manager = get_connection_manager()
    try:
        while True:
            # Clean up connections inactive for more than 5 minutes
            await manager.cleanup_inactive_connections(300)
            # Run every minute
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        logger.info("Connection cleanup task cancelled")


# Create FastAPI app with lifespan
app = FastAPI(title="Finnhub API", lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
LogRequestMiddleware(app, logger)

app.include_router(web_socket_stats_router)
app.include_router(stock_summary_router)
app.include_router(latest_price_router)
app.include_router(company_symbol_router)
app.include_router(stock_price_1s_router)

# Main function to run the application
if __name__ == "__main__":
    logger.info("Starting uvicorn server")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, workers=1)
