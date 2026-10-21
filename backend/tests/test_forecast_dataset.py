"""Forecasting dataset: generator shape, determinism, targets, and leakage."""

from pathlib import Path

import pandas as pd
import pytest

from forecasting.features import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    build_feature_table,
    time_split,
)
from forecasting.synthetic_history import (
    generate_history,
    load_corpus,
    merge_corpora,
    validate_corpus,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def history():
    return generate_history(seed=3, n_extra_vendors=6)


@pytest.fixture(scope="module")
def table(history):
    return build_feature_table(history)


def test_history_matches_corpus_schema(history):
    validate_corpus(history)
    assert len(history["pos"]) > 300


def test_history_is_deterministic(history):
    assert generate_history(seed=3, n_extra_vendors=6) == history


def test_history_ends_before_demo_corpus_and_merges(history):
    demo = load_corpus(DATA_DIR)
    assert max(p["date"] for p in history["pos"]) < min(p["date"] for p in demo["pos"])
    merged = merge_corpora(history, demo)
    df = build_feature_table(merged)
    kaveri = df[df["po_id"] == "PO-88450"].iloc[0]
    # Kaveri's demo story: 30-day term from 2026-03-10, received 2026-04-21.
    assert kaveri["promised_lead_days"] == 30
    assert kaveri["delay_days"] == 12
    assert kaveri["vendor_prior_lines"] > 0


def test_one_row_per_po_line(history, table):
    assert len(table) == sum(len(p["items"]) for p in history["pos"])
    assert not table.duplicated(["po_id", "line_no"]).any()


def test_targets_consistent(table):
    lab = table.dropna(subset=["delay_days"])
    assert ((lab["delay_days"] > 0).astype(float) == lab["is_late"]).all()
    assert table["delay_days"].isna().any(), "lines open at the end of history stay unlabelled"


def test_categoricals_are_native(table):
    for col in CATEGORICAL_COLUMNS:
        assert isinstance(table[col].dtype, pd.CategoricalDtype)
    assert set(FEATURE_COLUMNS) <= set(table.columns)


def _truncate(corpus: dict, cutoff: str) -> dict:
    """The corpus as it would have looked on `cutoff` (documents dated before it)."""
    return {
        "vendors": corpus["vendors"],
        "contracts": [c for c in corpus["contracts"] if c["effective_date"] < cutoff],
        "pos": [p for p in corpus["pos"] if p["date"] < cutoff],
        "grns": [g for g in corpus["grns"] if g["received_date"] < cutoff],
        "invoices": [i for i in corpus["invoices"] if i["invoice_date"] < cutoff],
    }


@pytest.mark.parametrize("cutoff", ["2024-09-01", "2025-06-15"])
def test_features_do_not_use_the_future(history, table, cutoff):
    """Features for POs dated before the cutoff must not change when every
    document dated on or after the cutoff is removed."""
    past = build_feature_table(_truncate(history, cutoff))
    full = table[table["po_date"] < cutoff].reset_index(drop=True)
    cols = [c for c in FEATURE_COLUMNS if c not in CATEGORICAL_COLUMNS]
    pd.testing.assert_frame_equal(
        full[cols].astype(float), past[cols].astype(float), check_exact=False, rtol=1e-9
    )


def test_time_split_only_trains_on_known_labels(table):
    train, test = time_split(table, "2025-06-01")
    assert (train["label_known_date"] < "2025-06-01").all()
    assert (test["po_date"] >= "2025-06-01").all()
    assert len(train) and len(test)


def test_short_closed_line_counts_only_once_invoiced():
    """A short-shipped line is only known to be closed when the PO is invoiced."""
    item = {"sku": "CBL-25", "description": "Cable", "qty": 10, "unit_price": 1.0, "total": 10.0}
    short = dict(item, qty=8, total=8.0)
    corpus = {
        "vendors": [{"id": "V1", "name": "V", "category": "MEP supplies", "risk_history": []}],
        "contracts": [],
        "pos": [
            {"id": "PO-1", "vendor_id": "V1", "items": [item], "total": 10.0,
             "date": "2025-01-01", "status": "closed"},
            {"id": "PO-2", "vendor_id": "V1", "items": [item], "total": 10.0,
             "date": "2025-01-20", "status": "approved"},
            {"id": "PO-3", "vendor_id": "V1", "items": [item], "total": 10.0,
             "date": "2025-02-10", "status": "approved"},
        ],
        "grns": [{"id": "GRN-1", "po_id": "PO-1", "vendor_id": "V1",
                  "received_date": "2025-01-15", "items": [short]}],
        "invoices": [{"id": "INV-1", "po_id": "PO-1", "vendor_id": "V1", "items": [short],
                      "total": 8.0, "invoice_date": "2025-02-01", "due_date": "2025-03-01"}],
    }
    df = build_feature_table(corpus).set_index("po_id")
    assert df.loc["PO-1", "received_shortfall"] == 1
    assert df.loc["PO-1", "delay_days"] == -16  # 30-day MEP default, received day 14
    assert df.loc["PO-2", "vendor_prior_lines"] == 0  # received, but not yet known closed
    assert df.loc["PO-2", "vendor_open_pos"] == 1
    assert df.loc["PO-3", "vendor_prior_lines"] == 1
    assert df.loc["PO-3", "vendor_open_pos"] == 1  # PO-2 only; PO-1 is closed by now
