import time, uuid, logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

# Request logging Middleware that logs the method, path, and response time for every request
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    force=True,     # prioritize this logger instead of using the default
    handlers=[
        logging.StreamHandler(),    # stdout — captured by the logging DaemonSet
        # logging.FileHandler("app.log", encoding="utf-8")  # disabled: /app is read-only with readOnlyRootFilesystem
    ]
)
logger = logging.getLogger(__name__)

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next): # call_next(request) forwards request to route handler
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time)*1000
        logger.info(
            f"{request.method} {request.url.path} "
            f"→ {response.status_code} | {duration_ms:.2f}ms"
        )
        return response

# Request ID middleware that attaches a unique "X-Request-ID" header to every response.
class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request:Request, call_next):
        response_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = response_id
        return response