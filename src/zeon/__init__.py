# -*- coding: utf-8 -*-
"""
**Zeon** is a micro-framework for creating `JSON` web applications with ease.

{GET|POST|PUT|DELETE|PATCH}
"""

import asyncio

# import decimal
import datetime
import json
import logging
import multiprocessing
import signal
import threading
import time
import typing
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace as Obj
from urllib.parse import parse_qs, urlparse

# from contextlib import contextmanager

# =======================================================================================
# Logging
# =======================================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s    -  %(message)s",
    # format="%(asctime)s - %(levelname)s - %(message)s",
)

# =======================================================================================
# Globals
# =======================================================================================

HTTP_HEADERS = {"X-Content-Type-Options": "nosniff"}
HTTP_METHODS = ["POST", "GET", "PUT", "DELETE", "PATCH"]  # C.R.U.D => Patch => Remove

# =======================================================================================
# Generics
# =======================================================================================

T = typing.TypeVar("T")

# =======================================================================================
# Lazy Object
# =======================================================================================

Factory: typing.TypeAlias = typing.Callable[..., T]
"""
`LazyObject` factory function `TypeAlias`
"""


class LazyObject(typing.Generic[T]):
    """Initialize a LazyObject."""

    __slots__ = ("_factory", "_wrapped", "_lock")

    def __init__(self, factory: Factory) -> None:
        """Initialize the LazyObject with a factory function."""
        self._factory = factory
        self._wrapped: typing.Any = None  # This will hold the initialized object
        self._lock = threading.Lock()

    def _initialize(self) -> None:
        """Initialize the wrapped object if it hasn't been initialized yet."""
        if self._wrapped is None:
            with self._lock:
                if self._wrapped is None:  # Double-checked locking
                    self._wrapped = self._factory()

    # Method calls
    def __call__(self, *args: typing.Any, **kwargs: typing.Any) -> typing.Any:
        """Delegate method calls to the wrapped object."""
        self._initialize()
        return self._wrapped(*args, **kwargs)

    # Attribute-like behavior
    def __getattr__(self, name: str) -> typing.Any:
        """Delegate attribute access to the wrapped object."""
        self._initialize()
        return getattr(self._wrapped, name)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        """Delegate attribute setting to the wrapped object."""
        if name in self.__slots__:
            super().__setattr__(name, value)
        else:
            self._initialize()
            setattr(self._wrapped, name, value)

    # Dictionary-like behavior
    def __getitem__(self, key: typing.Any) -> typing.Any:
        """Support dictionary-like item access."""
        self._initialize()
        return self._wrapped[key]

    def __setitem__(self, key: typing.Any, value: typing.Any) -> None:
        """Support dictionary-like item setter."""
        self._initialize()
        self._wrapped[key] = value

    # Representation
    def __repr__(self) -> str:
        """Provide a representation of the LazyObject."""
        return (
            f"LazyObject({self._wrapped!r})"
            if self._wrapped is not None
            else "LazyObject(not initialized)"
        )


# =======================================================================================
# MultiProcessing
# =======================================================================================


class BaseProcess(multiprocessing.Process):
    """Abstract Process Worker"""

    server: typing.Any
    options: typing.Any
    on_event: typing.Any

    def __init__(self, **kwargs: typing.Any):
        """Initialize the BaseProcess with optional keyword arguments."""
        super().__init__()
        self.options = Obj(**kwargs)
        self._stop_event = multiprocessing.Event()

    def run(self):
        """Run the worker."""
        self.before_run()
        try:
            self.run_sync()
        except KeyboardInterrupt:
            pass

    def before_run(self):
        """Hook for setup before running the server."""

    def run_sync(self):
        """Run the worker synchronously."""
        threading.Thread(target=self.server, daemon=True).start()
        while not self._stop_event.is_set():
            time.sleep(1)

    def stop(self):
        """Stop the worker."""
        self._stop_event.set()

    def hook(self, event_type: str) -> None:
        """Lifecycle event hook (e.g., 'startup', 'shutdown')."""


# =======================================================================================
# JSON (Loads & Dumps)
# =======================================================================================


class JSON:
    """JSON Handler"""

    @staticmethod
    def loads(string: str) -> typing.Any:
        """Safely `deserialize` a JSON string into a Python object."""
        try:
            return json.loads(string or "")
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def dumps(data: typing.Any) -> bytes:
        """Safely `serialize` a Python object into a JSON string."""
        try:
            return json.dumps(data).encode("utf-8")
        except TypeError:
            return b"{}"


# =======================================================================================
# HTTP (Request & Handler)
# =======================================================================================


class HTTPRequest:
    """HTTP — Request"""

    http: BaseHTTPRequestHandler
    method: str
    path: str
    query: dict
    cookies: SimpleCookie
    content_length: int

    def __init__(self, http: BaseHTTPRequestHandler, method: str):
        # URL Parse
        parsed_path = urlparse(http.path)

        # Set Values (Path-URL)
        self.path = parsed_path.path
        self.query = parse_qs(parsed_path.query)
        # Set Values (Headers)
        self.headers = http.headers
        self.cookies = SimpleCookie(http.headers.get("Cookie"))
        # Set Values (Content-Length)
        self.content_length = int(http.headers.get("Content-Length", 0))
        # Set Values (Basics)
        self.http = http
        self.method = method

        # Private / Internals
        self._internal = Obj(cookies={}, headers=HTTP_HEADERS)

    def get_header(self, name: str):
        """Read http `header`."""
        return self.http.headers.get(name, None)

    def get_cookie(self, name: str):
        """Read http `cookie`."""
        return self.cookies[name].value if name in self.cookies else None

    def get_content(self):
        """Read http `request_body`."""
        if self.content_length > 0:
            return self.http.rfile.read(self.content_length).decode("utf-8")
        return None

    def input(self):
        """Read http `request` as `JSON`."""
        return JSON.loads(self.get_content())

    def set_cookie(
        self,
        name: str,
        value: str,
        http_only: bool = True,
        secure: bool = True,
        samesite: str = "Lax",
        expires: int = 0,  # In Minutes
    ):
        """Set a cookie with optional attributes."""
        cookie = SimpleCookie()
        cookie[name] = value

        if http_only:
            cookie[name]["httponly"] = True
        if secure:
            cookie[name]["secure"] = True
        if samesite:
            cookie[name]["samesite"] = samesite

        # Always use UTC for Expires attribute
        if expires > 0:
            the_time = datetime.datetime.now(datetime.UTC)
            exp_time = the_time + datetime.timedelta(minutes=expires)
            cookie[name]["expires"] = exp_time.strftime("%a, %d-%b-%Y %H:%M:%S GMT")

        # Register
        self._internal.cookies[name] = cookie

    def response(
        self,
        data: typing.Any = None,
        headers: dict | None = None,
        status_code: int = 200,
        content_type: str = "application/json",
    ):
        """Send http `response`."""
        # PRE - Response
        self._internal.headers.update(headers or {})
        # Send `status_code`
        self.http.send_response(status_code)
        # Send `headers`
        self.http.send_header("Content-Type", content_type)
        # self.http.send_header("Connection", "close")  # Close connection
        for key, val in self._internal.headers.items():  # Extra headers
            self.http.send_header(key, val)
        for cookie in self._internal.cookies.values():  # Cookie headers
            self.http.send_header("Set-Cookie", cookie.output(header="", sep=""))
        self.http.end_headers()  # Flush headers
        # Send `data`
        self.http.wfile.write(data)


async def handle_request(self, method):
    """Handle data for requests."""
    request = HTTPRequest(self, method)

    # Request
    inputs = request.input()
    request.set_cookie("jwtoken", "secret_pass")
    print(request.get_cookie("jwtoken"))

    # Return
    request.response(JSON.dumps(inputs))


def handle_http(self, method):
    """Common method to handle HTTP requests asynchronously."""
    asyncio.run(handle_request(self, method))


# Create Class Dynamically in Python
def create_http_handler():
    """Dynamically create an HTTPRequestHandler class."""

    def do_options(self):
        """Handle `OPTIONS` request."""
        self.send_response(200)
        self.send_header("Allow", "GET, POST, PUT, DELETE, PATCH, OPTIONS")
        self.end_headers()

    methods = {
        "do_OPTIONS": do_options,
        "do_GET": lambda self: handle_http(self, "GET"),
        "do_POST": lambda self: handle_http(self, "POST"),
        "do_PUT": lambda self: handle_http(self, "PUT"),
        "do_DELETE": lambda self: handle_http(self, "DELETE"),
        "do_PATCH": lambda self: handle_http(self, "PATCH"),
    }

    # Create the dynamic class
    return type("HTTPRequestHandler", (BaseHTTPRequestHandler,), methods)


# =======================================================================================
# HTTP (Server) with `BaseProcess`
# =======================================================================================


class HTTPServer(BaseProcess):
    """Custom Process Worker for running an HTTP server."""

    server_class = ThreadingHTTPServer
    handler_class = create_http_handler()

    def hook(self, event_type: str):
        """Run on events"""
        logging.info("Event    : %s", event_type)
        logging.info("Options  : %s", self.options.__dict__)

    def server(self):
        """Run the HTTP server."""
        options = self.options.__dict__
        host = options.get("host", "")
        port = options.get("port", 8000)
        httpd = self.server_class((host, port), self.handler_class)
        # Run Server
        httpd.serve_forever()


def start_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Run the HTTP server."""
    worker = HTTPServer(name="PythonHTTP", host=host, port=port)

    worker.hook("startup")
    worker.start()

    def stop_server(*_) -> None:
        """Signal handler for stopping the server."""
        worker.hook("shutdown")
        worker.stop()

    signal.signal(signal.SIGINT, stop_server)
    signal.signal(signal.SIGTERM, stop_server)


# =======================================================================================
# HTTP (Router)
# =======================================================================================


# =======================================================================================
# Main / Test
# =======================================================================================

if __name__ == "__main__":
    start_server()
