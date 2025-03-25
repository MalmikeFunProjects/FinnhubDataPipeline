from fastapi import FastAPI, Request
from utils.Logger import Logger
import time

class LogRequestMiddleware:
    def __init__(self, app: FastAPI, logger: Logger):
        self.logger = logger
        app.middleware("http")(self.log_requests)

    async def log_requests(self, request: Request, call_next):
        request_id = str(int(time.time() * 1000))
        with self.logger.context_manager(request_id=request_id):
            method = request.method
            path = request.url.path
            query = request.url.query
            client_host = request.client.host if request.client else "unknown"
            self.logger.info(f"Request {method} {path}{f'?{query}' if query else ''} from {client_host}")

            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            self.logger.info(f"Response {response.status_code} sent in {process_time:.4f}s")

            return response




