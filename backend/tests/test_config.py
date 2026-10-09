import pytest
from pydantic import ValidationError

from config import MIN_SECRET_KEY_LENGTH, Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_missing_secret_key_fails_outside_local(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY must be set"):
        _settings(app_env="production")


def test_short_secret_key_fails_outside_local() -> None:
    with pytest.raises(ValidationError, match="at least"):
        _settings(app_env="production", secret_key="too-short")


def test_strong_secret_key_accepted_outside_local() -> None:
    key = "x" * MIN_SECRET_KEY_LENGTH
    assert _settings(app_env="production", secret_key=key).secret_key == key


def test_local_without_secret_key_gets_random_key(monkeypatch) -> None:
    monkeypatch.delenv("SECRET_KEY", raising=False)
    first = _settings(app_env="local").secret_key
    second = _settings(app_env="local").secret_key
    assert first and second
    assert first != second
    assert first != "secret_key"
