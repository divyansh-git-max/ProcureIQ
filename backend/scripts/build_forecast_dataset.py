"""Build the tabular delivery-delay dataset for XGBoost / LightGBM / CatBoost.

    cd backend
    python -m scripts.build_forecast_dataset                 # write the dataset
    python -m scripts.build_forecast_dataset --benchmark     # and compare models

Steps:
  1. Generate a synthetic multi-year history (forecasting/synthetic_history.py)
     in the same document shapes as backend/data/*.json.
  2. Append the hand-written demo corpus in backend/data/ (it starts after the
     history ends, and shares its three vendor IDs).
  3. Build one row per PO line (forecasting/features.py) and write
     data/forecast/po_line_features.csv plus the raw generated documents.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from forecasting.features import build_feature_table, time_split
from forecasting.synthetic_history import (
    generate_history,
    load_corpus,
    merge_corpora,
    validate_corpus,
    write_corpus,
)

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
OUT_DIR = DATA_DIR / "forecast"
DEFAULT_CUTOFF = "2025-09-01"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--vendors", type=int, default=22, help="extra vendors beyond the demo three")
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--no-demo", action="store_true", help="skip the backend/data demo corpus")
    ap.add_argument("--benchmark", action="store_true", help="train and compare the three models")
    ap.add_argument("--cutoff", default=DEFAULT_CUTOFF, help="time-split date for --benchmark")
    args = ap.parse_args()

    history = generate_history(seed=args.seed, n_extra_vendors=args.vendors)
    validate_corpus(history)
    write_corpus(history, args.out / "history")

    corpus = history if args.no_demo else merge_corpora(history, load_corpus(DATA_DIR))
    df = build_feature_table(corpus)
    args.out.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out / "po_line_features.csv", index=False, float_format="%.6g")

    labelled = df["delay_days"].notna()
    print(f"{len(df)} PO lines ({labelled.sum()} labelled, {(~labelled).sum()} still open)")
    print(f"late rate {df.loc[labelled, 'is_late'].mean():.1%}, "
          f"mean delay {df.loc[labelled, 'delay_days'].mean():.1f} days")
    print(f"written to {args.out}")

    if args.benchmark:
        from forecasting.benchmark import run_benchmark

        train, test = time_split(df, args.cutoff)
        print(f"\ntime split at {args.cutoff}: {len(train)} train / {len(test)} test rows")
        print(run_benchmark(train, test).to_string(index=False))


if __name__ == "__main__":
    main()
