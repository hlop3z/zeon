import asyncio
import contextlib
import logging

from starlette.applications import Starlette
from starlette.background import BackgroundTask
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket, WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_client_ip(request):
    """
    Retrieve the client's IP address from the request.
    """
    client_host = request.client.host  # Get the IP address from the client's connection
    forwarded_for = request.headers.get("x-forwarded-for")  # Check for proxy headers
    ip_address = forwarded_for.split(",")[0] if forwarded_for else client_host
    return ip_address


# Internal: Whoami
async def client_whoami(request):
    """
    Client's IP/Auth.
    """
    client_ip = await get_client_ip(request)
    token_value = request.cookies.get("jwtoken", "user_id@domain_name.com")
    return JSONResponse({"whoami": client_ip, "token": token_value})


# Internal Task (Background Daemons)
async def send_welcome_email(to_address: str):
    """
    Simulate Task.
    """
    logger.info(f"Sending welcome email to {to_address}...")
    # Replace with actual email sending logic
    await asyncio.sleep(1)
    logger.info(f"Welcome email sent to {to_address}!")


# Route: HTTP endpoint
async def http_endpoint(request):
    """
    Handle HTTP Requests.
    """
    task = BackgroundTask(send_welcome_email, to_address="user_email@example.com")
    response = HTMLResponse(
        "<html><body style='background:black; color: white;'><h1>Hello, world!</h1></body></html>",
        background=task,
    )
    return response


# Route: WebSocket endpoint
async def webs_endpoint(websocket: WebSocket):
    """
    Handle WebSocket connections.
    """
    await websocket.accept()
    try:
        logger.info("WebSocket connection established.")
        await websocket.send_text("Hello, WebSocket!")
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")
    except Exception as e:
        logger.error(f"Error in WebSocket communication: {e}")
    finally:
        await websocket.close()


# Application Lifespan
@contextlib.asynccontextmanager
async def lifespan(app):
    """
    Context manager to define startup and shutdown events.
    """
    logger.info("Application is starting up!")
    yield
    logger.info("Application is shutting down!")


# Application Instance
app = Starlette(
    lifespan=lifespan,
    routes=[
        Route("/", http_endpoint),  # HTTP endpoint
        WebSocketRoute("/ws", webs_endpoint),  # WebSocket endpoint
        # System: Who-Am-I & Health-Check
        Route("/whoami", client_whoami),
        Route("/health", lambda request: JSONResponse({"status": "ok"})),
    ],
)
"""
Application Handler (`HTTP`/`WS`)
"""
