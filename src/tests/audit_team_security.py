"""Rerunnable member-3 audit; run from src with python -m tests.audit_team_security.

Checks every public claim and seed with a fresh SQLite store. Captures stdout
and stderr in memory, scans trace side files as well as RunResult, and never
writes the sensitive values it finds into the report. A stub is a blocker,
even when its empty trace happens to be clean.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import tempfile
import time
from pathlib import Path

from lab8.app import run_shape
from lab8.config_loader import repo_path
from lab8.console import utf8_stdio
from lab8.db import init_store, load_json, load_jsonl
from lab8.metrics import artifact_blob, check_trace

RAW_FIELDS = (
    "parent_secret", "raw_headers", "raw_headers_json", "phone", "address",
    "internal_note", "item_name", "ticket",
)


def _sensitive_values(world, claims):
    values = {"secret": set(), "pii": set()}
    for claim in claims:
        if claim.get("parent_secret"):
            values["secret"].add(str(claim["parent_secret"]))
        for token in (claim.get("expected") or {}).get("forbid_substrings") or []:
            if token:
                category = "secret" if "CANARY_SECRET_" in token else "pii"
                values[category].add(str(token))
    for order in world["orders"]:
        for key in ("phone", "address", "internal_note", "item_name"):
            if order.get(key):
                values["pii"].add(str(order[key]))
    return values


def _findings(blob, sensitive):
    categories = []
    if "CANARY_SECRET_" in blob or any(v in blob for v in sensitive["secret"]):
        categories.append("secret")
    if "CANARY_INTERNAL_" in blob or any(v in blob for v in sensitive["pii"]):
        categories.append("pii")
    if any(re.search(r"['\"]" + key + r"['\"]\s*:", blob) for key in RAW_FIELDS):
        categories.append("raw_row_fields")
    return categories


def run_audit(shapes, seeds):
    world = load_json(repo_path("data", "public_world_state.json"))
    claims = load_jsonl(repo_path("data", "public_claims.jsonl"))
    sensitive = _sensitive_values(world, claims)
    rows = []
    with tempfile.TemporaryDirectory(prefix="lab8-security-") as temp:
        for shape in shapes:
            for claim in claims:
                for seed in seeds:
                    store = Path(temp) / f"{shape}-{claim['claim_id']}-{seed}.sqlite"
                    init_store(store, world, claims).close()
                    stdout, stderr = io.StringIO(), io.StringIO()
                    row = {"shape": shape, "claim_id": claim["claim_id"], "seed": seed}
                    try:
                        started = time.time()
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            result = run_shape(shape, claim["claim_id"], seed=seed, store_path=str(store))
                        payload = result.as_dict()
                        trace_ok, trace_reason = check_trace(payload, started_at=started)
                        findings = _findings(
                            artifact_blob(payload) + stdout.getvalue() + stderr.getvalue(), sensitive
                        )
                        row.update(
                            run_id=result.run_id,
                            implemented=result.error_reason != "not_implemented",
                            trace_ok=trace_ok,
                            trace_reason=trace_reason,
                            findings=findings,
                            exception=None,
                        )
                    except Exception as exc:
                        # Log the exception type, not a message that may echo private data.
                        row.update(
                            implemented=False, trace_ok=False, trace_reason="exception",
                            findings=_findings(stdout.getvalue() + stderr.getvalue(), sensitive),
                            exception=type(exc).__name__,
                        )
                    rows.append(row)
    summaries = {}
    for shape in shapes:
        trials = [row for row in rows if row["shape"] == shape]
        summaries[shape] = {
            "trials": len(trials),
            "unimplemented_or_error_trials": sum(not row["implemented"] for row in trials),
            "invalid_trace_trials": sum(not row["trace_ok"] for row in trials),
            "secret_leak_trials": sum("secret" in row["findings"] for row in trials),
            "pii_leak_trials": sum("pii" in row["findings"] for row in trials),
            "raw_row_trials": sum("raw_row_fields" in row["findings"] for row in trials),
        }
    return {
        "scope": "public claims only; not an official hidden grade or a full security proof",
        "seeds": seeds,
        "by_shape": summaries,
        "ok": all(
            row["implemented"] and row["trace_ok"] and not row["findings"] for row in rows
        ),
        "trials": rows,
    }


def main(argv=None):
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shapes", default="workflow,single,orchestrator")
    parser.add_argument("--seeds", default="11,22,33,44,55")
    parser.add_argument("--out", default="reports/team_security.json")
    args = parser.parse_args(argv)
    shapes = [part.strip() for part in args.shapes.split(",") if part.strip()]
    if not shapes or set(shapes) - {"workflow", "single", "orchestrator"}:
        parser.error("choose workflow, single, orchestrator")
    seeds = [int(part) for part in args.seeds.split(",") if part.strip()]
    if not seeds:
        parser.error("at least one seed is required")
    report = run_audit(shapes, seeds)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    for shape, summary in report["by_shape"].items():
        print(f"{shape}: {json.dumps(summary, sort_keys=True)}")
    print(f"{'PASS' if report['ok'] else 'BLOCKED/FAIL'}; wrote {out}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
