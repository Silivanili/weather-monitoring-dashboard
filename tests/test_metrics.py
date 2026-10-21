from fastapi.testclient import TestClient
from prometheus_client import REGISTRY

from app.main import app

client = TestClient(app)


def sample_value(name: str, **labels: str) -> float:
    return REGISTRY.get_sample_value(name, labels) or 0.0


def test_metrics_endpoint_exports_prometheus_format():
    client.get("/health")  # Seed the labelled histogram series.
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain;")
    assert "weather_http_requests_total" in response.text
    assert "weather_http_request_duration_seconds_bucket" in response.text


def test_request_counter_records_matched_route_and_status():
    labels = {"method": "GET", "route": "/health", "status": "200"}
    before = sample_value("weather_http_requests_total", **labels)

    response = client.get("/health")

    assert response.status_code == 200
    assert sample_value("weather_http_requests_total", **labels) == before + 1


def test_latency_histogram_observes_requests():
    labels = {"method": "GET", "route": "/health"}
    before = sample_value("weather_http_request_duration_seconds_count", **labels)

    client.get("/health")

    assert sample_value("weather_http_request_duration_seconds_count", **labels) == before + 1


def test_metrics_scrapes_do_not_increment_http_counter():
    labels = {"method": "GET", "route": "/metrics", "status": "200"}
    before = sample_value("weather_http_requests_total", **labels)

    client.get("/metrics")
    client.get("/metrics")

    assert sample_value("weather_http_requests_total", **labels) == before


def test_unmatched_paths_are_grouped_and_query_strings_not_recorded():
    labels = {"method": "GET", "route": "unmatched", "status": "404"}
    before = sample_value("weather_http_requests_total", **labels)

    response = client.get("/not-a-route?token=sensitive-test-value")
    metrics = client.get("/metrics")

    assert response.status_code == 404
    assert sample_value("weather_http_requests_total", **labels) == before + 1
    assert "sensitive-test-value" not in metrics.text
    assert "/not-a-route" not in metrics.text
