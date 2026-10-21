"""Prometheus request metrics for the FastAPI application."""

from time import perf_counter

from fastapi import Request
from prometheus_client import Counter, Histogram
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response

HTTP_REQUESTS = Counter(
    "weather_http_requests_total",
    "Total HTTP requests, labelled by method, matched route and status.",
    ("method", "route", "status"),
)

WEATHER_STALE_CACHE_RESPONSES = Counter(
    "weather_stale_cache_responses_total",
    "Weather responses served from stale cache when the upstream provider fails.",
)


HTTP_REQUEST_DURATION = Histogram(
    "weather_http_request_duration_seconds",
    "Duration of HTTP requests in seconds.",
    ("method", "route"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


async def record_http_metrics(request: Request, call_next: RequestResponseEndpoint) -> Response:
    """Measure requests without exposing user-supplied paths or query values."""
    # Prometheus scrapes must not inflate the application's request rate.
    if request.url.path == "/metrics":
        return await call_next(request)

    started = perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        # Starlette sets the matched route after routing, including path templates.
        route = request.scope.get("route")
        route_label = getattr(route, "path", "unmatched")
        HTTP_REQUESTS.labels(request.method, route_label, str(status)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, route_label).observe(perf_counter() - started)
