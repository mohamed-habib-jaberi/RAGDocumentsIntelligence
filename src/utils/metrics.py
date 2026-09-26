"""Provide reusable metrics utilities for the application."""

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP Requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP Request Latency', ['method', 'endpoint'])

class PrometheusMiddleware(BaseHTTPMiddleware):
    """Collect request counts and latency metrics for every HTTP response."""
    async def dispatch(self, request: Request, call_next):

        """Measure an HTTP request and publish its latency and status metrics."""
        start_time = time.time()

        # Process the request
        response = await call_next(request)

        # Record metrics after request is processed
        duration = time.time() - start_time
        endpoint = request.url.path

        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(duration)
        REQUEST_COUNT.labels(method=request.method, endpoint=endpoint, status=response.status_code).inc()

        return response

def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics middleware and endpoint
    """
    # Add Prometheus middleware
    app.add_middleware(PrometheusMiddleware)

    @app.get("/TrhBVe_m5gg2002_E5VVqS", include_in_schema=False)
    def metrics():
        """Expose the current Prometheus metrics in the text exposition format."""
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
