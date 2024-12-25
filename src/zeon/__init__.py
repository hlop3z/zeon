# -*- coding: utf-8 -*-
"""
**Zeon** is a micro-framework for creating `JSON` web applications with ease.
"""

import datetime
import decimal
import json
import logging
import multiprocessing
import signal
import threading
import time
import typing
from abc import ABC, abstractmethod
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

# =======================================================================================
# Logging
# =======================================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


# =======================================================================================
# JSON (Loads & Dumps)
# =======================================================================================


class JSON:
    """JSON (Deserialize & Serialize)"""

    @staticmethod
    def loads(string: str) -> typing.Any:
        """
        Safely `deserialize` a JSON string into a Python object.

        Args:
            json_string (str): A JSON-formatted string.

        Returns:
            Any: The `deserialized` Python object.
        """
        try:
            return json.loads(string)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def dumps(data: typing.Any) -> bytes:
        """
        Safely `serialize` a Python object into a JSON-formatted `UTF-8` encoded string.

        Args:
            data (Any): The Python object to serialize.

        Returns:
            bytes: The `serialized` JSON string encoded in `UTF-8`.
        """
        try:
            return json.dumps(data).encode("utf-8")
        except TypeError:
            return b"{}"


# =======================================================================================
# Scalars
# =======================================================================================


class ID(str):
    """Database ID"""


class Text(str):
    """Big Strings"""


class BigInt(int):
    """Big Integer"""

    # dumps()
    # loads()


SCALAR = SimpleNamespace(
    # Database
    id=ID,
    # Basics
    int=int,
    float=float,
    bool=bool,
    string=str,
    # Object/Array
    dict=dict,
    list=list,
    # DateTime (Strings)
    date=datetime.date,
    time=datetime.time,
    date_time=datetime.datetime,
    # Numbers (Strings)
    decimal=decimal.Decimal,
    big_int=BigInt,
    # Extras (Strings)
    text=Text,
)

# =======================================================================================
# MultiProcessing
# =======================================================================================


class MethodNotFoundError(Exception):
    """Raised when a required method is missing from a class implementation."""

    def __init__(self, class_name: str, method_name: str):
        super().__init__(
            f"<class '{class_name}'> is missing required method: `{method_name}`"
        )


class AbstractWorker(ABC):
    """Abstract Worker Base Class."""

    REQUIRED_METHODS: list[str] = ["server", "on_event"]

    server: typing.Any
    options: typing.Any
    on_event: typing.Any

    @abstractmethod
    def _create_stop_event(self):
        """Initialize a stop event."""

    def _validate_required_methods(self):
        """Ensure required methods are implemented in the subclass."""
        for method in self.REQUIRED_METHODS:
            if not hasattr(self, method):
                raise MethodNotFoundError(self.__class__.__name__, method)

    def __init__(self, **kwargs):
        self.options = SimpleNamespace(**kwargs)
        self._stop_event = self._create_stop_event()
        self._validate_required_methods()

    def run(self):
        """Run the worker."""
        self.before()
        try:
            self.run_sync()
        except KeyboardInterrupt:
            pass

    def before(self):
        """Hook for setup before running the server."""

    def run_sync(self):
        """Run the worker synchronously."""
        self.on_event("startup")
        threading.Thread(target=self.server, daemon=True).start()
        while self.active:
            time.sleep(1)
        self.on_event("shutdown")

    def stop(self):
        """Stop the worker."""
        self._stop_event.set()

    @property
    def active(self):
        """Check if the worker is active."""
        return not self._stop_event.is_set()


class BaseProcess(AbstractWorker, multiprocessing.Process):
    """Abstract Process Worker."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        multiprocessing.Process.__init__(self)

    def _create_stop_event(self):
        """Initialize a multiprocessing stop event."""
        return multiprocessing.Event()


# =======================================================================================
# HTTP (Request & Handler)
# =======================================================================================


class HTTPRequest:
    """HTTP — Request"""

    http: BaseHTTPRequestHandler
    method: str

    def _initialize(self):
        """Parse `url` and initialize `values`."""
        # URL Parse
        parsed_path = urlparse(self.http.path)
        # Set Values
        self.path = parsed_path.path
        self.query = parse_qs(parsed_path.query)
        self.content_length = int(self.http.headers.get("Content-Length", 0))

    def __init__(self, handler: BaseHTTPRequestHandler, method: str):
        self.http = handler
        self.method = method
        self._initialize()

    def response(
        self,
        data: typing.Any = None,
        status_code: int = 200,
        content_type: str = "application/json",
    ):
        """Send http `response`."""
        # Send `status_code`
        self.http.send_response(status_code)
        # Send `headers`
        self.http.send_header("Content-Type", content_type)
        self.http.send_header("Connection", "close")  # Close connection
        self.http.end_headers()  # Flush headers
        # Send `data`
        self.http.wfile.write(data)

    def get_input(self):
        """Read http `request`."""
        if self.content_length > 0:
            return self.http.rfile.read(self.content_length).decode("utf-8")
        return None

    def input(self):
        """Read http `request` as `JSON`."""
        return JSON.loads(self.get_input())


class HTTPHandler(BaseHTTPRequestHandler):
    """HTTP — Handler"""

    def _handle_http(self, method):
        """Handle data for {Get|Post|Put|Delete|Patch} requests."""
        request = HTTPRequest(self, method)

        inputs = request.input()
        # {GET | POST | PUT | DELETE | PATCH}
        print(type(inputs), inputs)

        # Return
        request.response(JSON.dumps({"input": inputs}))

    def do_OPTIONS(self):  # pylint: disable=invalid-name
        """Handle `OPTIONS` request."""
        self.send_response(200)
        self.send_header("Allow", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.end_headers()

    def do_GET(self):  # pylint: disable=invalid-name
        """Handle `GET` request."""
        request = HTTPRequest(self, "GET")
        html_template = "<html><body><h1>Hello, World!</h1></body></html>"
        request.response(html_template.encode("utf-8"), content_type="text/html")

    def do_POST(self):  # pylint: disable=invalid-name
        """Handle `POST` request."""
        self._handle_http("POST")

    def do_PUT(self):  # pylint: disable=invalid-name
        """Handle `PUT` request."""
        self._handle_http("PUT")

    def do_DELETE(self):  # pylint: disable=invalid-name
        """Handle `DELETE` request."""
        self._handle_http("DELETE")

    def do_PATCH(self):  # pylint: disable=invalid-name
        """Handle `PATCH` request."""
        self._handle_http("PATCH")


# =======================================================================================
# HTTP (Server) with BaseProcess
# =======================================================================================


class HTTPServer(BaseProcess):
    """Custom Process Worker for running an HTTP server."""

    server_class = ThreadingHTTPServer
    handler_class = HTTPHandler

    def on_event(self, event_type: str):
        """Run on events"""
        logging.info("Options  : %s", self.options.__dict__)
        logging.info("Event    : %s", event_type)

    def server(self):
        """Run the HTTP server."""
        options = self.options.__dict__
        host = options.get("host", "")
        port = options.get("port", 8000)
        httpd = self.server_class((host, port), self.handler_class)

        logging.info("Starting server on port %s...", port)

        # Run Server
        httpd.serve_forever()


def start_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the HTTP server."""
    worker = HTTPServer(name="PythonHTTP", host=host, port=port)
    worker.start()

    def stop_server(*_) -> None:
        """Signal handler for stopping the server."""
        logging.info("Stopping server...")
        worker.stop()

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)


# =======================================================================================
# Main / Test
# =======================================================================================

if __name__ == "__main__":
    start_server()
