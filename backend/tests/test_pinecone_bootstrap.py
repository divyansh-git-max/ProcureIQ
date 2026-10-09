from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from config import settings
from db import bootstrap


@pytest.fixture
def pinecone(monkeypatch) -> MagicMock:
    client = MagicMock()
    monkeypatch.setattr(bootstrap, "Pinecone", MagicMock(return_value=client))
    monkeypatch.setattr(settings, "pinecone_api_key", "test-key")
    monkeypatch.setattr(settings, "pinecone_index_name", "procureiq-test")
    monkeypatch.setattr(settings, "embedding_dimension", 384)
    return client


def test_creates_index_with_embedding_dimension(pinecone) -> None:
    pinecone.has_index.return_value = False

    bootstrap.bootstrap_pinecone()

    assert pinecone.create_index.call_args.kwargs["dimension"] == 384


def test_existing_index_with_matching_dimension_is_accepted(pinecone) -> None:
    pinecone.has_index.return_value = True
    pinecone.describe_index.return_value = SimpleNamespace(dimension=384)

    bootstrap.bootstrap_pinecone()

    pinecone.create_index.assert_not_called()


def test_existing_index_with_wrong_dimension_raises(pinecone) -> None:
    pinecone.has_index.return_value = True
    pinecone.describe_index.return_value = SimpleNamespace(dimension=1536)

    with pytest.raises(bootstrap.PineconeDimensionMismatch, match="1536"):
        bootstrap.bootstrap_pinecone()


def test_skipped_without_api_key(monkeypatch) -> None:
    factory = MagicMock()
    monkeypatch.setattr(bootstrap, "Pinecone", factory)
    monkeypatch.setattr(settings, "pinecone_api_key", None)

    bootstrap.bootstrap_pinecone()

    factory.assert_not_called()
