"""Judge-the-judge: calibrate a replayed LLM judge against human labels.

    python -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 5

Default backend is REPLAY (the judge verdicts are stored in the CSV, zero key).
Floors (lecture S6): kappa >= 0.6, precision >= 0.8, recall >= 0.7.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats

FLOORS = {"kappa": 0.6, "precision": 0.8, "recall": 0.7}


def calibrate(path: Path) -> dict:
    with path.open(encoding="utf-8", newline="") as source:
        rows = list(csv.DictReader(source))
    human = [r["human"].strip().upper() for r in rows]
    judge = [r["judge"].strip().upper() for r in rows]
    p, r = stats.precision_recall(human, judge)
    errors = {}
    try:
        k = stats.cohen_kappa(human, judge)
    except ValueError as exc:
        k = float("nan")
        errors["kappa"] = str(exc)
    cm = stats.confusion(human, judge)
    spec = cm["tn"] / (cm["tn"] + cm["fp"]) if cm["tn"] + cm["fp"] else 0.0
    obs = (cm["tp"] + cm["fp"]) / len(rows)
    try:
        corrected = round(stats.rogan_gladen(obs, r, spec), 3)
    except ValueError as exc:
        corrected = None
        errors["rogan_gladen"] = str(exc)
    res = {"n": len(rows), "precision": round(p, 3), "recall": round(r, 3),
           "kappa": round(k, 3) if math.isfinite(k) else None,
           "confusion": cm, "observed_fail_rate": round(obs, 3),
           "corrected_fail_rate": corrected,
           "disagreements": [x for x, h, j in zip(rows, human, judge) if h != j]}
    # Rounding is for display only: e.g. P=0.7996 must not pass a floor of 0.8.
    raw_metrics = {"precision": p, "recall": r, "kappa": k}
    res["passed"] = all(raw_metrics[m] >= floor for m, floor in FLOORS.items())
    if errors:
        res["calibration_errors"] = errors
    return res


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.judge")
    ap.add_argument("--csv", required=True)
    ap.add_argument("--audit", type=int, default=0, help="print N disagreements to audit by hand")
    ap.add_argument("--out", help="write calibration evidence as JSON (generated, never hand-edited)")
    args = ap.parse_args(argv)
    res = calibrate(Path(args.csv))
    print(f"n={res['n']} P={res['precision']} R={res['recall']} kappa={res['kappa']} {res['confusion']}")
    print(f"fail rate observed {res['observed_fail_rate']} -> corrected {res['corrected_fail_rate']}")
    for metric, error in res.get("calibration_errors", {}).items():
        print(f"  undefined {metric}: {error}")
    for row in res["disagreements"][: args.audit]:
        print(f"  {row['item_id']} human={row['human']} judge={row['judge']} | {row['reply'][:90]}")
    print("PASS floors" if res["passed"] else "FAIL floors", FLOORS)
    if args.out:
        path = Path(args.out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"source": args.csv, "floors": FLOORS, **res},
                                   ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        print(f"wrote {path}")
    return 0 if res["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
