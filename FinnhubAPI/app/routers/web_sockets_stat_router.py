from typing import Dict
from fastapi import APIRouter, Depends

from routers.ConnectionManager import get_connection_manager, ConnectionManager

from utils.default_log_setting import DefaultLogger

logger = DefaultLogger.get_err_logger("fastapi_app", log_to_console=True)


class WebsocketStats():
    def __init__(self):
        self.router = APIRouter(prefix="/websocket_stats", tags=["websocket_stats"])
        self.setup_routes()

    def setup_routes(self):
        #HTTP routes
        self.router.add_api_route("/", self.get_websocket_stats, methods=["GET"])

    async def get_websocket_stats(manager: ConnectionManager = Depends(get_connection_manager)):
        # Ensure the manager is a ConnectionManager instance
        if not isinstance(manager, ConnectionManager):
            manager = get_connection_manager()
            
        return {
            "total_connections": manager.get_connection_count(),
            "rooms": {
                group_name.replace("room:", ""): manager.get_group_count(group_name)
                for group_name in manager.groups
                if group_name.startswith("room:")
            }
        }

web_socket_stats_router = WebsocketStats().router
