import dataclasses
import json
from datetime import datetime, timedelta
from functools import partial
from http import HTTPStatus
from typing import Any, Optional, Callable, Mapping, List

from tornado.httputil import HTTPHeaders
from tornado.web import Application, RequestHandler

from pyctuator.endpoints import Endpoints
from pyctuator.httptrace import TraceRecord, TraceRequest, TraceResponse
from pyctuator.impl import SBA_V2_CONTENT_TYPE
from pyctuator.impl.async_pyctuator_impl import AsyncPyctuatorImpl
from pyctuator.impl.pyctuator_router import PyctuatorRouter


# pylint: disable=abstract-method
class AsyncAbstractPyctuatorHandler(RequestHandler):
    pyctuator_router: Optional[PyctuatorRouter] = None
    dumps: Optional[Callable[[Any], str]] = None

    def initialize(self) -> None:
        self.pyctuator_router = self.application.settings.get("pyctuator_router")
        self.dumps = self.application.settings.get("custom_dumps")
        self.set_header("Content-Type", SBA_V2_CONTENT_TYPE)

    def options(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write("")


class AsyncPyctuatorHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.get_endpoints_data()))


# GET /env
class AsyncEnvHandler(AsyncAbstractPyctuatorHandler):
    async def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        env_data = await self.pyctuator_router.pyctuator_impl.get_environment()
        self.write(self.dumps(env_data))


# GET /info
class AsyncInfoHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_app_info()))


# GET /health
class AsyncHealthHandler(AsyncAbstractPyctuatorHandler):
    async def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        health = await self.pyctuator_router.pyctuator_impl.get_health()
        self.set_status(health.http_status())
        self.write(self.dumps(health))


# GET /metrics
class AsyncMetricsHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_metric_names()))


# GET "/metrics/{metric_name}"
class AsyncMetricsNameHandler(AsyncAbstractPyctuatorHandler):
    async def get(self, metric_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        metric = await self.pyctuator_router.pyctuator_impl.get_metric_measurement(metric_name)
        self.write(self.dumps(metric))


# GET /loggers
class AsyncLoggersHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.logging.get_loggers()))


# GET /loggers/{logger_name}
# POST /loggers/{logger_name}
class AsyncLoggersNameHandler(AsyncAbstractPyctuatorHandler):
    def get(self, logger_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.logging.get_logger(logger_name)))

    def post(self, logger_name: str) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        body_str = self.request.body.decode("utf-8")
        body = json.loads(body_str)
        self.pyctuator_router.pyctuator_impl.logging.set_logger_level(logger_name, body.get("configuredLevel", None))
        self.write("")


# GET /threaddump
class AsyncThreadDumpHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.get_thread_dump()))


# GET /logfile
class AsyncLogFileHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None

        range_header = self.request.headers.get("range")
        if not range_header:
            self.write(f"{self.pyctuator_router.pyctuator_impl.logfile.log_messages.get_range()}")

        else:
            str_res, start, end = self.pyctuator_router.pyctuator_impl.logfile.get_logfile(range_header)
            self.set_status(HTTPStatus.PARTIAL_CONTENT.value)
            self.add_header("Content-Type", "text/html; charset=UTF-8")
            self.add_header("Accept-Ranges", "bytes")
            self.add_header("Content-Range", f"bytes {start}-{end}/{end}")
            self.write(str_res)


# GET /httptrace
class AsyncHttpTraceHandler(AsyncAbstractPyctuatorHandler):
    def get(self) -> None:
        assert self.pyctuator_router is not None
        assert self.dumps is not None
        self.write(self.dumps(self.pyctuator_router.pyctuator_impl.http_tracer.get_httptrace()))


# pylint: disable=too-many-locals,unused-argument
class AsyncTornadoHttpPyctuator(PyctuatorRouter):
    def __init__(self, app: Application, pyctuator_impl: AsyncPyctuatorImpl, disabled_endpoints: Endpoints) -> None:
        super().__init__(app, pyctuator_impl)

        custom_dumps = partial(
            json.dumps, default=self._custom_json_serializer
        )

        app.settings.setdefault("pyctuator_router", self)
        app.settings.setdefault("custom_dumps", custom_dumps)

        # Register a log-function that records request and response in traces and than delegates to the original func
        self.delegate_log_function = app.settings.get("log_function")
        app.settings.setdefault("log_function", self._intercept_request_and_response)

        handlers: list = [(r"/pyctuator", AsyncPyctuatorHandler)]

        if Endpoints.ENV not in disabled_endpoints:
            handlers.append((r"/pyctuator/env", AsyncEnvHandler))

        if Endpoints.INFO not in disabled_endpoints:
            handlers.append((r"/pyctuator/info", AsyncInfoHandler))

        if Endpoints.HEALTH not in disabled_endpoints:
            handlers.append((r"/pyctuator/health", AsyncHealthHandler))

        if Endpoints.METRICS not in disabled_endpoints:
            handlers.append((r"/pyctuator/metrics", AsyncMetricsHandler))
            handlers.append((r"/pyctuator/metrics/(?P<metric_name>.*$)", AsyncMetricsNameHandler))

        if Endpoints.LOGGERS not in disabled_endpoints:
            handlers.append((r"/pyctuator/loggers", AsyncLoggersHandler))
            handlers.append((r"/pyctuator/loggers/(?P<logger_name>.*$)", AsyncLoggersNameHandler))

        if Endpoints.THREAD_DUMP not in disabled_endpoints:
            handlers.append((r"/pyctuator/dump", AsyncThreadDumpHandler))
            handlers.append((r"/pyctuator/threaddump", AsyncThreadDumpHandler))

        if Endpoints.LOGFILE not in disabled_endpoints:
            handlers.append((r"/pyctuator/logfile", AsyncLogFileHandler))

        if Endpoints.HTTP_TRACE not in disabled_endpoints:
            handlers.append((r"/pyctuator/trace", AsyncHttpTraceHandler))
            handlers.append((r"/pyctuator/httptrace", AsyncHttpTraceHandler))

        app.add_handlers(".*$", handlers)

    def _intercept_request_and_response(self, handler: RequestHandler) -> None:
        # Record the request and response
        record = TraceRecord(
            timestamp=datetime.now() - timedelta(seconds=handler.request.request_time()),
            principal=None,
            session=None,
            request=TraceRequest(
                method=handler.request.method or "",
                uri=handler.request.full_url(),
                headers=get_headers(handler.request.headers)
            ),
            response=TraceResponse(
                status=handler.get_status(),
                headers=get_headers(HTTPHeaders(handler._headers))
            ),
            timeTaken=int(handler.request.request_time() * 1000),
        )
        self.pyctuator_impl.http_tracer.add_record(record=record)

        # Delegate to the original log function if it exists
        if self.delegate_log_function:
            self.delegate_log_function(handler)

    def _custom_json_serializer(self, value: Any) -> Any:
        if dataclasses.is_dataclass(value):
            return dataclasses.asdict(value)

        if isinstance(value, datetime):
            return str(value)
        return None


def get_headers(headers: HTTPHeaders) -> Mapping[str, List[str]]:
    headers_dict: Mapping[str, List[str]] = {}
    for (key, value) in headers.items():
        headers_dict[key] = [value]
    return headers_dict 