"""Turn a procurement corpus into a tabular dataset for delivery-delay models.

One row per purchase-order line. Everything is derived from the documents
themselves (vendors, contracts, POs, GRNs, invoices), so the same code runs on
synthetic history and on real ingested data.

Targets
  delay_days  days between the promised date and the date the line was fully
              received (negative = early)
  is_late     1 when delay_days > 0

When is a line "received"?
  When cumulative GRN quantity reaches the ordered quantity. If it never does
  but the PO has been invoiced, the line is treated as closed short on its last
  GRN date (received_shortfall = 1). Otherwise the line is still open and its
  targets are NaN: keep those rows for scoring, drop them for training.

Leakage rules
  Every feature is known on the PO date. Vendor and SKU history only counts
  lines whose label became known (label_known_date) strictly before the PO
  date, and invoices dated strictly before it. Open-PO load counts POs placed
  strictly before and not yet closed as of the PO date.
  Use time_split() rather than a random split when evaluating.

Categoricals (vendor_id, vendor_category, sku) are kept as raw string columns
with pandas "category" dtype, so LightGBM, CatBoost and XGBoost
(enable_categorical=True) can each use their native handling.
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from forecasting.synthetic_history import CATEGORIES, OVERBILL_TOLERANCE

FALLBACK_LEAD_DAYS = 14
EWM_ALPHA = 0.3
WINDOW_DAYS = 90

ID_COLUMNS = [
    "po_id", "line_no", "po_date", "expected_date", "received_date", "label_known_date",
]
TARGET_COLUMNS = ["delay_days", "is_late"]
CATEGORICAL_COLUMNS = ["vendor_id", "vendor_category", "sku"]
NUMERIC_COLUMNS = [
    # order
    "qty", "unit_price", "line_total", "po_total", "po_n_lines", "line_share_of_po",
    "log_qty",
    # calendar
    "po_month", "po_quarter", "po_dayofweek", "days_to_quarter_end",
    "expected_month", "expected_in_monsoon",
    # contract terms
    "promised_lead_days", "penalty_pct", "has_penalty_clause", "contract_age_days",
    # vendor load at order time
    "vendor_open_pos", "vendor_open_value", "vendor_pos_last_90d",
    # vendor delivery history (as of PO date)
    "vendor_prior_lines", "vendor_prior_mean_delay", "vendor_prior_std_delay",
    "vendor_prior_late_rate", "vendor_last_delay", "vendor_ewm_delay",
    "vendor_mean_delay_90d", "vendor_late_rate_90d", "vendor_lines_90d",
    "days_since_vendor_last_receipt", "vendor_prior_shortfall_rate",
    "vendor_trend_delay",
    # vendor invoice history (as of PO date)
    "vendor_prior_invoices", "vendor_prior_invoice_anomaly_rate",
    # SKU / category history (as of PO date, across vendors)
    "sku_prior_lines", "sku_prior_mean_delay", "category_prior_mean_delay",
    # SKU size relative to that vendor's prior orders
    "qty_vs_vendor_sku_mean",
]
FEATURE_COLUMNS = CATEGORICAL_COLUMNS + NUMERIC_COLUMNS


def _d(s: str) -> np.datetime64:
    return np.datetime64(s, "D")


def _contract_terms(contracts: list[dict]) -> dict[str, list[tuple]]:
    """vendor_id -> [(effective_date, delivery_days|None, penalty_pct)] sorted by date."""
    terms: dict[str, list[tuple]] = {}
    for c in contracts:
        days = next(
            (cl["delivery_days"] for cl in c["clauses"] if cl.get("delivery_days")), None
        )
        penalty = max((cl.get("penalty_pct") or 0.0 for cl in c["clauses"]), default=0.0)
        terms.setdefault(c["vendor_id"], []).append((_d(c["effective_date"]), days, penalty))
    for v in terms.values():
        v.sort(key=lambda t: t[0])
    return terms


def _resolve_terms(terms: list[tuple], po_date: np.datetime64, category: str):
    """Latest active contract's penalty, and the latest active delivery term.

    A contract without a delivery clause inherits the vendor's previous
    delivery term, then the category default.
    """
    active = [t for t in terms if t[0] <= po_date]
    if not active:
        return CATEGORIES.get(category, (FALLBACK_LEAD_DAYS,))[0], 0.0, np.nan
    eff, _, penalty = active[-1]
    days = next((t[1] for t in reversed(active) if t[1]), None)
    if days is None:
        days = CATEGORIES.get(category, (FALLBACK_LEAD_DAYS,))[0]
    return days, penalty, float((po_date - eff).astype(int))


def _line_receipts(pos: list[dict], grns: list[dict], invoices: list[dict]) -> dict:
    """(po_id, sku) -> (received_date, shortfall flag, label_known_date).

    A short-closed line was last received on its final GRN date, but nobody
    knew it was closed until the PO was invoiced, so its label becomes known
    on the first invoice date.
    """
    receipts: dict[tuple[str, str], list[tuple[np.datetime64, int]]] = {}
    for g in grns:
        for it in g["items"]:
            receipts.setdefault((g["po_id"], it["sku"]), []).append(
                (_d(g["received_date"]), it["qty"])
            )
    first_invoice: dict[str, np.datetime64] = {}
    for i in invoices:
        d = _d(i["invoice_date"])
        first_invoice[i["po_id"]] = min(d, first_invoice.get(i["po_id"], d))
    out = {}
    for po in pos:
        for it in po["items"]:
            events = sorted(receipts.get((po["id"], it["sku"]), []))
            cum, done = 0, None
            for day, q in events:
                cum += q
                if cum >= it["qty"]:
                    done = day
                    break
            if done is not None:
                out[(po["id"], it["sku"])] = (done, 0, done)
            elif events and po["id"] in first_invoice:
                last = events[-1][0]
                out[(po["id"], it["sku"])] = (last, 1, max(last, first_invoice[po["id"]]))
            else:
                out[(po["id"], it["sku"])] = (None, 0, None)
    return out


def _invoice_anomalies(pos: list[dict], invoices: list[dict]) -> pd.DataFrame:
    """Flag invoices that overbill the PO price or duplicate an earlier invoice."""
    po_prices = {
        po["id"]: {it["sku"]: it["unit_price"] for it in po["items"]} for po in pos
    }
    seen: set[tuple] = set()
    rows = []
    for inv in sorted(invoices, key=lambda i: (i["invoice_date"], i["id"])):
        prices = po_prices.get(inv["po_id"], {})
        overbill = any(
            it["sku"] in prices and it["unit_price"] > prices[it["sku"]] * (1 + OVERBILL_TOLERANCE)
            for it in inv["items"]
        )
        key = (inv["po_id"], round(inv["total"], 2))
        duplicate = key in seen
        seen.add(key)
        rows.append({
            "vendor_id": inv["vendor_id"],
            "t": _d(inv["invoice_date"]),
            "anomaly": int(overbill or duplicate),
        })
    return pd.DataFrame(rows, columns=["vendor_id", "t", "anomaly"])


class _AsOf:
    """Point-in-time aggregates over one group's events, sorted by time.

    Every query counts only events with time strictly before the query time.
    """

    def __init__(self, times: np.ndarray, values: np.ndarray):
        times = times.astype("datetime64[D]")
        order = np.argsort(times, kind="stable")
        self.t = times[order]
        self.v = values[order].astype(float)
        self.cs = np.concatenate([[0.0], np.cumsum(self.v)])
        self.cs2 = np.concatenate([[0.0], np.cumsum(self.v**2)])
        ewm = np.empty(len(self.v))
        acc = np.nan
        for i, x in enumerate(self.v):
            acc = x if np.isnan(acc) else EWM_ALPHA * x + (1 - EWM_ALPHA) * acc
            ewm[i] = acc
        self.ewm = ewm

    def _idx(self, q: np.ndarray) -> np.ndarray:
        return np.searchsorted(self.t, q, side="left")

    def count(self, q, window: int | None = None):
        hi = self._idx(q)
        lo = self._idx(q - np.timedelta64(window, "D")) if window else 0
        return hi - lo

    def mean(self, q, window: int | None = None):
        hi = self._idx(q)
        lo = self._idx(q - np.timedelta64(window, "D")) if window else np.zeros_like(hi)
        n = hi - lo
        with np.errstate(invalid="ignore", divide="ignore"):
            return np.where(n > 0, (self.cs[hi] - self.cs[lo]) / n, np.nan)

    def std(self, q):
        n = self._idx(q)
        with np.errstate(invalid="ignore", divide="ignore"):
            m = self.cs[n] / n
            var = self.cs2[n] / n - m**2
            return np.where(n > 1, np.sqrt(np.maximum(var, 0) * n / np.maximum(n - 1, 1)), np.nan)

    def last(self, q):
        n = self._idx(q)
        return np.where(n > 0, self.v[np.maximum(n - 1, 0)], np.nan)

    def last_ewm(self, q):
        n = self._idx(q)
        return np.where(n > 0, self.ewm[np.maximum(n - 1, 0)], np.nan)

    def days_since_last(self, q):
        n = self._idx(q)
        gap = (q - self.t[np.maximum(n - 1, 0)]).astype(float)
        return np.where(n > 0, gap, np.nan)


def _apply_asof(df: pd.DataFrame, events: pd.DataFrame, key: str, value: str, fn) -> None:
    """For each group in df[key], build _AsOf over matching events and call fn(rows, asof)."""
    groups = {k: g for k, g in events.groupby(key)} if len(events) else {}
    for k, rows in df.groupby(key, observed=True):
        g = groups.get(k)
        times = g["t"].to_numpy() if g is not None else np.array([], dtype="datetime64[D]")
        vals = g[value].to_numpy() if g is not None else np.array([], dtype=float)
        fn(rows.index, rows["po_date"].to_numpy().astype("datetime64[D]"), _AsOf(times, vals))


def build_feature_table(corpus: dict[str, list[dict]]) -> pd.DataFrame:
    """Build the PO-line training/scoring table from a corpus dict.

    The corpus has the keys "vendors", "contracts", "pos", "grns", "invoices",
    each a list of documents shaped like core/dataset_schema.py.
    """
    vendors = {v["id"]: v for v in corpus["vendors"]}
    terms = _contract_terms(corpus["contracts"])
    receipts = _line_receipts(corpus["pos"], corpus["grns"], corpus["invoices"])

    rows = []
    for po in corpus["pos"]:
        po_date = _d(po["date"])
        vid = po["vendor_id"]
        cat = vendors.get(vid, {}).get("category", "Unknown")
        lead, penalty, age = _resolve_terms(terms.get(vid, []), po_date, cat)
        expected = po_date + np.timedelta64(int(lead), "D")
        for n, it in enumerate(po["items"], start=1):
            done, short, known = receipts[(po["id"], it["sku"])]
            rows.append({
                "po_id": po["id"], "line_no": n, "po_date": po_date,
                "expected_date": expected, "received_date": done,
                "label_known_date": known,
                "vendor_id": vid, "vendor_category": cat, "sku": it["sku"],
                "qty": it["qty"], "unit_price": it["unit_price"], "line_total": it["total"],
                "po_total": po["total"], "po_n_lines": len(po["items"]),
                "promised_lead_days": lead, "penalty_pct": penalty,
                "has_penalty_clause": int(penalty > 0), "contract_age_days": age,
                "received_shortfall": short,
            })
    df = pd.DataFrame(rows)
    for col in ("po_date", "expected_date", "received_date", "label_known_date"):
        df[col] = pd.to_datetime(df[col])
    df = df.sort_values(["po_date", "po_id", "line_no"]).reset_index(drop=True)

    delivered = df["received_date"].notna()
    df["delay_days"] = (df["received_date"] - df["expected_date"]).dt.days.astype(float)
    df["is_late"] = np.where(delivered, (df["delay_days"] > 0).astype(float), np.nan)

    # Order and calendar features.
    df["line_share_of_po"] = df["line_total"] / df["po_total"]
    df["log_qty"] = np.log1p(df["qty"])
    df["po_month"] = df["po_date"].dt.month
    df["po_quarter"] = df["po_date"].dt.quarter
    df["po_dayofweek"] = df["po_date"].dt.dayofweek
    q_end = df["po_date"] + pd.offsets.QuarterEnd(0)
    df["days_to_quarter_end"] = (q_end - df["po_date"]).dt.days
    df["expected_month"] = df["expected_date"].dt.month
    df["expected_in_monsoon"] = df["expected_month"].isin([6, 7, 8, 9]).astype(int)

    # Events: one per received line, timed at the date its label became known.
    ev = df.loc[delivered, ["vendor_id", "vendor_category", "sku", "label_known_date",
                            "delay_days", "is_late", "received_shortfall", "qty"]].copy()
    ev = ev.rename(columns={"label_known_date": "t"})
    ev["t"] = ev["t"].to_numpy().astype("datetime64[D]")
    ev["vendor_sku"] = ev["vendor_id"] + "|" + ev["sku"]
    df["vendor_sku"] = df["vendor_id"] + "|" + df["sku"]

    def vendor_delay(idx, q, a):
        df.loc[idx, "vendor_prior_lines"] = a.count(q)
        df.loc[idx, "vendor_prior_mean_delay"] = a.mean(q)
        df.loc[idx, "vendor_prior_std_delay"] = a.std(q)
        df.loc[idx, "vendor_last_delay"] = a.last(q)
        df.loc[idx, "vendor_ewm_delay"] = a.last_ewm(q)
        df.loc[idx, "vendor_mean_delay_90d"] = a.mean(q, WINDOW_DAYS)
        df.loc[idx, "vendor_lines_90d"] = a.count(q, WINDOW_DAYS)
        df.loc[idx, "days_since_vendor_last_receipt"] = a.days_since_last(q)

    def vendor_late(idx, q, a):
        df.loc[idx, "vendor_prior_late_rate"] = a.mean(q)
        df.loc[idx, "vendor_late_rate_90d"] = a.mean(q, WINDOW_DAYS)

    def vendor_short(idx, q, a):
        df.loc[idx, "vendor_prior_shortfall_rate"] = a.mean(q)

    _apply_asof(df, ev, "vendor_id", "delay_days", vendor_delay)
    _apply_asof(df, ev, "vendor_id", "is_late", vendor_late)
    _apply_asof(df, ev, "vendor_id", "received_shortfall", vendor_short)
    df["vendor_trend_delay"] = df["vendor_mean_delay_90d"] - df["vendor_prior_mean_delay"]

    def sku_delay(idx, q, a):
        df.loc[idx, "sku_prior_lines"] = a.count(q)
        df.loc[idx, "sku_prior_mean_delay"] = a.mean(q)

    def cat_delay(idx, q, a):
        df.loc[idx, "category_prior_mean_delay"] = a.mean(q)

    def vendor_sku_qty(idx, q, a):
        df.loc[idx, "vendor_sku_prior_mean_qty"] = a.mean(q)

    _apply_asof(df, ev, "sku", "delay_days", sku_delay)
    _apply_asof(df, ev, "vendor_category", "delay_days", cat_delay)
    _apply_asof(df, ev, "vendor_sku", "qty", vendor_sku_qty)
    df["qty_vs_vendor_sku_mean"] = df["qty"] / df["vendor_sku_prior_mean_qty"]

    # Invoice history.
    inv = _invoice_anomalies(corpus["pos"], corpus["invoices"])
    inv["t"] = inv["t"].to_numpy().astype("datetime64[D]")

    def vendor_inv(idx, q, a):
        df.loc[idx, "vendor_prior_invoices"] = a.count(q)
        df.loc[idx, "vendor_prior_invoice_anomaly_rate"] = a.mean(q)

    _apply_asof(df, inv, "vendor_id", "anomaly", vendor_inv)

    # Vendor load: POs placed strictly before this PO that were not yet fully
    # received on its date. A PO with any open line stays open.
    po_level = df.groupby("po_id").agg(
        vendor_id=("vendor_id", "first"), po_date=("po_date", "first"),
        po_total=("po_total", "first"), done=("label_known_date", "max"),
        any_open=("label_known_date", lambda s: s.isna().any()),
    )
    po_level.loc[po_level["any_open"], "done"] = pd.NaT
    for vid, rows in df.groupby("vendor_id"):
        p = po_level[po_level["vendor_id"] == vid]
        placed = p["po_date"].to_numpy()
        done = p["done"].to_numpy()
        val = p["po_total"].to_numpy()
        q = rows["po_date"].to_numpy()
        before = placed[None, :] < q[:, None]
        still_open = np.isnat(done)[None, :] | (done[None, :] >= q[:, None])
        recent = placed[None, :] >= (q - np.timedelta64(WINDOW_DAYS, "D"))[:, None]
        df.loc[rows.index, "vendor_open_pos"] = (before & still_open).sum(1)
        df.loc[rows.index, "vendor_open_value"] = ((before & still_open) * val[None, :]).sum(1)
        df.loc[rows.index, "vendor_pos_last_90d"] = (before & recent).sum(1)

    for col in CATEGORICAL_COLUMNS:
        df[col] = df[col].astype("category")
    df = df.drop(columns=["vendor_sku", "vendor_sku_prior_mean_qty"])
    return df[ID_COLUMNS + FEATURE_COLUMNS + ["received_shortfall"] + TARGET_COLUMNS]


def time_split(
    df: pd.DataFrame, cutoff: str | date
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split as a model retrained on `cutoff` would see the world.

    Train: lines whose label was known before the cutoff.
    Test: lines ordered on or after the cutoff and since received.
    Lines ordered before the cutoff but labelled after it are in neither.
    """
    cutoff = pd.Timestamp(cutoff)
    labelled = df["delay_days"].notna()
    train = df[labelled & (df["label_known_date"] < cutoff)]
    test = df[labelled & (df["po_date"] >= cutoff)]
    return train, test
