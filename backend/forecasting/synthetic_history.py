"""Synthetic procurement history for training the delivery-delay forecaster.

The hand-written corpus in backend/data/ has three POs, which is enough to demo
anomaly detection but far too few to fit a gradient-boosted model. This module
generates a multi-year history in exactly the same document shapes
(core/dataset_schema.py): vendors, contracts, purchase orders, GRNs, invoices.

Delays are driven by hidden vendor traits and observable context, so a model
has real signal to learn:
  - vendor reliability (baseline delay) that drifts over time
  - category lead-time risk and a monsoon effect (Jun-Sep) on site logistics
  - vendor load: how many POs are still open with the vendor when we order
  - order size relative to the SKU's typical quantity
  - quarter-end crunch, PO-level shocks shared by all lines, rare disruptions

The hidden traits never appear in the documents. Features are rebuilt from the
documents alone in forecasting/features.py, the same way they would be from
real ingested data.

The history ends before the hand-written corpus begins (March 2026) and reuses
its three vendor IDs, so the two can be concatenated into one timeline.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import numpy as np

from core.dataset_schema import (
    Contract,
    GoodsReceiptNote,
    Invoice,
    PurchaseOrder,
    VendorRecord,
)

# Category -> (default promised lead days, monsoon sensitivity, SKU catalogue).
# SKU tuple: (sku, description, base unit price INR, typical qty).
CATEGORIES: dict[str, tuple[int, float, list[tuple[str, str, float, int]]]] = {
    "Structural steel": (21, 1.0, [
        ("STL-500", "TMT Bars 500D", 67000.0, 150),
        ("STL-550", "TMT Bars 550D", 71000.0, 120),
        ("STL-ISMB", "ISMB 300 Beams", 74000.0, 60),
    ]),
    "Concrete": (7, 1.4, [
        ("RMC-M30", "ReadyMix Concrete M30", 3600.0, 200),
        ("RMC-M40", "ReadyMix Concrete M40", 4300.0, 150),
    ]),
    "MEP supplies": (30, 0.4, [
        ("CBL-25", "25mm Copper Cable (Roll)", 2400.0, 100),
        ("CBL-16", "16mm Copper Cable (Roll)", 1650.0, 140),
        ("DB-8W", "8-Way Distribution Board", 5200.0, 40),
    ]),
    "Cement": (10, 1.2, [
        ("CEM-OPC53", "OPC 53 Grade Cement (50kg bag)", 390.0, 2000),
        ("CEM-PPC", "PPC Cement (50kg bag)", 360.0, 2500),
    ]),
    "Aggregates": (5, 1.8, [
        ("AGG-20", "20mm Coarse Aggregate (cu.m)", 1450.0, 300),
        ("SND-M", "Manufactured Sand (cu.m)", 1200.0, 350),
    ]),
    "Formwork": (18, 0.6, [
        ("FRM-PLY18", "18mm Shuttering Plywood (sheet)", 1850.0, 400),
        ("FRM-PROP", "Adjustable Steel Prop", 950.0, 600),
    ]),
    "Plumbing": (25, 0.5, [
        ("PIP-CPVC1", "1in CPVC Pipe (3m)", 420.0, 500),
        ("PIP-HDPE4", "4in HDPE Pipe (6m)", 2900.0, 120),
    ]),
    "Waterproofing": (14, 0.9, [
        ("WPF-MEMB", "APP Membrane 4mm (roll)", 3100.0, 80),
        ("WPF-CHEM", "Crystalline Waterproofing (25kg)", 4800.0, 60),
    ]),
}

# The three vendors already in backend/data/vendors.json keep their IDs, names,
# and categories so the generated history lines up with the demo corpus.
SEED_VENDORS = [
    ("VEN-0042", "Northstar Steelworks", "Structural steel"),
    ("VEN-0107", "Apex ReadyMix Pvt. Ltd.", "Concrete"),
    ("VEN-0033", "Kaveri Electricals", "MEP supplies"),
]

EXTRA_VENDOR_NAMES = [
    "Deccan Rebar Co.", "Vindhya Structurals", "Sahyadri Concrete Works", "Ganga RMC Solutions",
    "Tapti Power Systems", "Konark Electricals", "Ultra Bharat Cement Traders",
    "Narmada Cement Depot", "Godavari Stone Crushers", "Western Ghats Aggregates",
    "Shree Formwork Systems", "Rajput Scaffolding", "Aqua Flow Pipes", "Indus Plumbing Supply",
    "SealTech Waterproofing", "Monsoon Shield Coatings", "Bharat Steel Traders",
    "Coastal ReadyMix", "Prakash Cables", "Hindustan Aggregates", "Mahanadi Cement Agency",
    "Om Sai Formwork",
]

HISTORY_START = date(2024, 1, 1)
HISTORY_END = date(2026, 2, 28)  # the demo corpus starts with POs in March 2026
OVERBILL_TOLERANCE = 0.02


@dataclass
class _VendorTraits:
    """Hidden ground truth. Never written into any document."""

    base_delay: float  # mean days late at month 0
    drift_per_month: float  # reliability trend
    volatility: float  # noise scale
    load_sensitivity: float  # extra days per open PO
    disruption_prob: float  # chance of a large one-off slip per PO
    anomaly_prob: float  # chance an invoice is irregular
    shortfall_prob: float  # chance a line is short-shipped
    po_rate: float  # POs per month


def _months_between(a: date, b: date) -> float:
    return (b - a).days / 30.44


def _quarter_end(d: date) -> date:
    q_end_month = 3 * ((d.month - 1) // 3 + 1)
    nxt = date(d.year + (q_end_month == 12), q_end_month % 12 + 1, 1)
    return nxt - timedelta(days=1)


def _make_vendors(rng: np.random.Generator, n_extra: int) -> list[tuple[str, str, str]]:
    cats = list(CATEGORIES)
    vendors = list(SEED_VENDORS)
    for i, name in enumerate(EXTRA_VENDOR_NAMES[:n_extra]):
        vendors.append((f"VEN-{200 + i:04d}", name, cats[i % len(cats)]))
    return vendors


def _make_traits(rng: np.random.Generator, vendor_id: str) -> _VendorTraits:
    # Make the seed vendors resemble their demo stories: Kaveri runs late.
    base = {"VEN-0033": 6.0, "VEN-0042": 1.5, "VEN-0107": 0.5}.get(
        vendor_id, float(rng.normal(-2.0, 3.5))
    )
    return _VendorTraits(
        base_delay=base,
        drift_per_month=float(rng.normal(0.0, 0.18)),
        volatility=float(rng.uniform(1.0, 4.5)),
        load_sensitivity=float(rng.uniform(0.0, 1.2)),
        disruption_prob=float(rng.uniform(0.01, 0.08)),
        anomaly_prob=float(rng.beta(1.5, 12)),
        shortfall_prob=float(rng.uniform(0.0, 0.06)),
        po_rate=float(rng.uniform(2.0, 7.0)),
    )


def generate_history(
    seed: int = 7,
    n_extra_vendors: int = 22,
    start: date = HISTORY_START,
    end: date = HISTORY_END,
) -> dict[str, list[dict]]:
    """Return {"vendors", "contracts", "pos", "grns", "invoices"} as plain dicts.

    Each list matches the shape of the corresponding file in backend/data/.
    The output is fully determined by the arguments.
    """
    rng = np.random.default_rng(seed)
    vendors = _make_vendors(rng, n_extra_vendors)
    traits = {vid: _make_traits(rng, vid) for vid, _, _ in vendors}

    vendor_docs: list[dict] = []
    contracts: list[dict] = []
    pos: list[dict] = []
    grns: list[dict] = []
    invoices: list[dict] = []

    po_seq, grn_seq, ctr_seq = 100001, 500001, 200
    inv_seq: dict[int, int] = {}

    # (vendor_id, completion_date) for every PO placed so far, to compute load.
    open_pos: dict[str, list[date]] = {vid: [] for vid, _, _ in vendors}

    # Annual contracts per vendor, renewed every January with fresh terms.
    vendor_contracts: dict[str, list[tuple[date, int, float]]] = {}
    for vid, name, cat in vendors:
        default_days, _, catalogue = CATEGORIES[cat]
        terms = []
        for year in range(start.year, end.year + 1):
            eff = date(year, 1, 1) + timedelta(days=int(rng.integers(0, 20)))
            days = max(3, round(default_days * rng.uniform(0.8, 1.3)))
            penalty = float(rng.choice([0.0, 0.25, 0.5, 1.0], p=[0.25, 0.25, 0.35, 0.15]))
            clauses = [{
                "ref": "§3.1",
                "text": f"Supplier shall deliver within {days} days of the purchase order date.",
                "delivery_days": days,
            }]
            if penalty > 0:
                clauses.append({
                    "ref": "§8.7",
                    "text": (
                        f"Liquidated damages: A {penalty}% weekly penalty applies for "
                        "deliveries received after the agreed deadline."
                    ),
                    "penalty_pct": penalty,
                    "delivery_days": days,
                })
            sku, desc, price, _ = catalogue[0]
            clauses.append({
                "ref": "§4.2",
                "text": f"Unit pricing for {desc} is fixed at ₹{price:,.0f} for {year}.",
            })
            contracts.append({
                "id": f"CTR-{year}-{ctr_seq:03d}",
                "vendor_id": vid,
                "title": f"{cat} Supply Agreement {year}",
                "clauses": clauses,
                "effective_date": eff.isoformat(),
            })
            ctr_seq += 1
            terms.append((eff, days, penalty))
        vendor_contracts[vid] = terms

    # Walk the calendar month by month, placing POs for each vendor.
    month = date(start.year, start.month, 1)
    while month <= end:
        nxt = date(month.year + (month.month == 12), month.month % 12 + 1, 1)
        days_in_month = (nxt - month).days
        for vid, name, cat in vendors:
            tr = traits[vid]
            _, monsoon_sens, catalogue = CATEGORIES[cat]
            for _ in range(int(rng.poisson(tr.po_rate))):
                po_date = month + timedelta(days=int(rng.integers(0, days_in_month)))
                if po_date > end:
                    continue
                active = [t for t in vendor_contracts[vid] if t[0] <= po_date]
                if not active:
                    continue
                _, promised_days, _ = active[-1]
                expected = po_date + timedelta(days=promised_days)

                load = sum(1 for done in open_pos[vid] if done > po_date)
                months_in = _months_between(start, po_date)
                monsoon = 1.0 if expected.month in (6, 7, 8, 9) else 0.0
                q_crunch = 1.0 if (_quarter_end(po_date) - po_date).days <= 10 else 0.0
                po_shock = float(rng.normal(0, tr.volatility * 0.6))
                if rng.random() < tr.disruption_prob:
                    po_shock += float(rng.uniform(10, 35))

                n_lines = int(rng.choice([1, 2, 3, 4], p=[0.45, 0.3, 0.17, 0.08]))
                idx = rng.choice(len(catalogue), size=min(n_lines, len(catalogue)), replace=False)
                items, grn_events = [], []
                for j in idx:
                    sku, desc, base_price, typical = catalogue[j]
                    qty = max(1, round(typical * rng.lognormal(0, 0.45)))
                    inflation = 1 + 0.03 * months_in / 12
                    price = round(base_price * inflation * rng.uniform(0.97, 1.03))
                    items.append({
                        "sku": sku, "description": desc, "qty": qty,
                        "unit_price": float(price), "total": float(price * qty),
                    })
                    delay = (
                        tr.base_delay
                        + tr.drift_per_month * months_in
                        + 3.5 * monsoon * monsoon_sens
                        + tr.load_sensitivity * load
                        + 2.5 * np.log(qty / typical)
                        + 1.5 * q_crunch
                        + po_shock
                        + rng.normal(0, tr.volatility * 0.5)
                    )
                    done = max(po_date + timedelta(days=1), expected + timedelta(days=round(delay)))
                    received_qty = qty
                    if rng.random() < tr.shortfall_prob:
                        received_qty = max(1, int(qty * rng.uniform(0.85, 0.97)))
                    if received_qty == qty and qty > 1 and rng.random() < 0.15:
                        # Partial delivery: the remainder arrives on the completion date.
                        first_qty = int(qty * rng.uniform(0.4, 0.8))
                        first_day = po_date + timedelta(
                            days=int(rng.integers(1, max(2, (done - po_date).days)))
                        )
                        grn_events.append((first_day, sku, desc, first_qty, price))
                        grn_events.append((done, sku, desc, qty - first_qty, price))
                    else:
                        grn_events.append((done, sku, desc, received_qty, price))

                po_id = f"PO-{po_seq}"
                po_seq += 1
                completion = max(e[0] for e in grn_events)
                open_pos[vid].append(completion)
                delivered = completion <= end
                pos.append({
                    "id": po_id, "vendor_id": vid, "items": items,
                    "total": float(sum(i["total"] for i in items)),
                    "currency": "INR", "date": po_date.isoformat(),
                    "status": "closed" if delivered else "approved",
                })

                # GRNs only exist for receipts on or before the end of history.
                by_day: dict[date, list[dict]] = {}
                for day, sku, desc, q, price in grn_events:
                    if day <= end:
                        by_day.setdefault(day, []).append({
                            "sku": sku, "description": desc, "qty": q,
                            "unit_price": float(price), "total": float(price * q),
                        })
                for day in sorted(by_day):
                    grns.append({
                        "id": f"GRN-{grn_seq}", "po_id": po_id, "vendor_id": vid,
                        "received_date": day.isoformat(), "items": by_day[day],
                    })
                    grn_seq += 1

                if not delivered:
                    continue
                inv_date = completion + timedelta(days=int(rng.integers(0, 6)))
                if inv_date > end:
                    continue
                inv_items = [dict(i) for i in items]
                anomalous = rng.random() < tr.anomaly_prob
                kind = rng.choice(["overbill", "duplicate"]) if anomalous else None
                if kind == "overbill":
                    k = int(rng.integers(0, len(inv_items)))
                    bump = rng.uniform(1.05, 1.2)
                    inv_items[k]["unit_price"] = float(round(inv_items[k]["unit_price"] * bump))
                    inv_items[k]["total"] = inv_items[k]["unit_price"] * inv_items[k]["qty"]
                copies = 2 if kind == "duplicate" else 1
                for c in range(copies):
                    d = inv_date + timedelta(days=2 * c)
                    if d > end:
                        break
                    seq = inv_seq.get(d.year, 10001)
                    inv_seq[d.year] = seq + 1
                    invoices.append({
                        "id": f"INV-{d.year}-{seq}", "po_id": po_id, "vendor_id": vid,
                        "items": inv_items,
                        "total": float(sum(i["total"] for i in inv_items)),
                        "invoice_date": d.isoformat(),
                        "due_date": (d + timedelta(days=30)).isoformat(),
                    })
        month = nxt

    # A short trailing risk history per vendor, in the demo corpus's shape.
    for vid, name, cat in vendors:
        tr = traits[vid]
        hist = []
        for w in range(8):
            drifted = tr.base_delay + tr.drift_per_month * (_months_between(start, end) - w / 4)
            raw = 50 + 4 * drifted + 100 * tr.anomaly_prob + rng.normal(0, 2)
            score = int(np.clip(raw, 0, 100))
            hist.append({"week": f"W{8 - w}", "score": score})
        vendor_docs.append({
            "id": vid, "name": name, "category": cat, "risk_history": hist[::-1],
        })

    pos.sort(key=lambda p: (p["date"], p["id"]))
    grns.sort(key=lambda g: (g["received_date"], g["id"]))
    invoices.sort(key=lambda i: (i["invoice_date"], i["id"]))
    return {
        "vendors": vendor_docs, "contracts": contracts, "pos": pos,
        "grns": grns, "invoices": invoices,
    }


_MODELS = {
    "vendors": VendorRecord,
    "contracts": Contract,
    "pos": PurchaseOrder,
    "grns": GoodsReceiptNote,
    "invoices": Invoice,
}


def validate_corpus(corpus: dict[str, list[dict]]) -> None:
    """Raise if any document does not match core/dataset_schema.py."""
    for key, model in _MODELS.items():
        for doc in corpus.get(key, []):
            model.model_validate(doc)


def load_corpus(data_dir: Path) -> dict[str, list[dict]]:
    """Read vendors/contracts/pos/grns/invoices.json from a directory."""
    corpus = {}
    for key in _MODELS:
        path = data_dir / f"{key}.json"
        corpus[key] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    validate_corpus(corpus)
    return corpus


def merge_corpora(*corpora: dict[str, list[dict]]) -> dict[str, list[dict]]:
    """Concatenate corpora. Vendor records are de-duplicated by ID, first one wins."""
    merged: dict[str, list[dict]] = {key: [] for key in _MODELS}
    seen_vendors: set[str] = set()
    for corpus in corpora:
        for key in _MODELS:
            for doc in corpus.get(key, []):
                if key == "vendors":
                    if doc["id"] in seen_vendors:
                        continue
                    seen_vendors.add(doc["id"])
                merged[key].append(doc)
    return merged


def write_corpus(corpus: dict[str, list[dict]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, docs in corpus.items():
        (out_dir / f"{key}.json").write_text(
            json.dumps(docs, indent=1, ensure_ascii=False), encoding="utf-8"
        )
