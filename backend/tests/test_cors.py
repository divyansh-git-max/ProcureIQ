from fastapi.testclient import TestClient

from config import Settings
from main import cors_origins, create_app

PREFLIGHT = {"Access-Control-Request-Method": "POST"}


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, secret_key="k" * 40, **overrides)


def test_local_allows_any_origin() -> None:
    assert cors_origins(_settings(app_env="local")) == ["*"]


def test_production_parses_allowed_origins() -> None:
    settings = _settings(app_env="production", allowed_origins=" https://a.example, ,https://b.example ")
    assert cors_origins(settings) == ["https://a.example", "https://b.example"]


def test_production_preflight_only_for_allowed_origin() -> None:
    app = create_app(_settings(app_env="production", allowed_origins="https://a.example"))
    client = TestClient(app)

    allowed = client.options("/api/v1/findings", headers={"Origin": "https://a.example", **PREFLIGHT})
    denied = client.options("/api/v1/findings", headers={"Origin": "https://evil.example", **PREFLIGHT})

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "https://a.example"
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers


def test_production_without_allowed_origins_refuses_cross_origin() -> None:
    app = create_app(_settings(app_env="production"))
    response = TestClient(app).options(
        "/api/v1/findings", headers={"Origin": "https://a.example", **PREFLIGHT}
    )
    assert "access-control-allow-origin" not in response.headers
