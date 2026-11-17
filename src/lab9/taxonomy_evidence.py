"""M1: replay taxonomy evidence and fixed controls without unfinished M2/M3 graders.

Run from src/: python -m lab9.taxonomy_evidence
Diagnostic shapes use the starter's existing bug switches only in this process.
They do not change lab8, public variants, metric specs, or gate behavior.
The output is trace evidence, not an eval baseline or an instructor anchor key.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path

from lab8.console import utf8_stdio
from lab8.shapes import SHAPES
from lab9.evalset import SOURCE, load_jsonl, sha12
from lab9.trace_case import investigate
from lab9.variant_agent import make_shape


@dataclass(frozen=True)
class EvidenceCase:
    fm: str
    shape: str
    claim: str
    seed: int
    first_bad_kind: str
    bug: str | None = None


CASES = (
    EvidenceCase("FM-01", "m1_leaky_trace", "C-010", 11, "debug_claim_row", "leaky_trace"),
    EvidenceCase("FM-02", "seeded_regression", "C-007", 11, "reply"),
    EvidenceCase("FM-03", "swarm", "C-002", 55, "model_override"),
    EvidenceCase("FM-03", "seeded_regression", "C-002", 11, "model_override"),
    EvidenceCase("FM-04", "slice_regression", "C-014", 11, "proposal"),
    EvidenceCase("FM-05", "seeded_regression", "C-014", 11, "proposal"),
    EvidenceCase("FM-06", "m1_stale_clause", "C-006", 11, "quote", "stale_clause"),
    EvidenceCase("FM-07", "m1_sibling_refund", "C-010", 11, "batch_refund", "sibling_refund"),
    EvidenceCase("FM-08", "m1_misreport", "C-008", 11, "reply", "misreport"),
)


def summarize(case: dict) -> dict:
    """Keep evidence useful while withholding the intentionally leaked debug row."""
    trial, label = case["trial"], case["label"]
    events = []
    for step, event in enumerate(trial["events"], start=1):
        payload = event.get("payload")
        if event["kind"] == "debug_claim_row":
            payload = {"fields": sorted(payload), "forbidden_value_redacted": True}
        events.append({"step": step, "kind": event["kind"], "payload": payload})
    reason = trial["lab8_reason"]
    if reason and reason.startswith("forbidden_substring:"):
        reason = "forbidden_substring:[REDACTED]"
    result = trial["result"]
    return {
        "run_id": result["run_id"],
        "claim_id": result["claim_id"],
        "status": result["status"],
        "proposal_amount": result["proposal_amount"],
        "snapshot": trial["snapshot"],
        "unexpected_rows": trial["unexpected_rows"],
        "lab8_pass": trial["lab8_pass"],
        "lab8_reason": reason,
        "expected": {key: label[key] for key in ("status", "refund_vnd", "refund_count")},
        "events": events,
    }


def collect() -> dict:
    claims = load_jsonl(SOURCE)
    controls = {c["claim_id"]: summarize(investigate("fixed", c["claim_id"], 11)) for c in claims}
    if not all(control["lab8_pass"] for control in controls.values()):
        raise RuntimeError("A fixed@11 negative control failed; inspect the evidence before tagging")
    evidence = []
    for case in CASES:
        # Restore the process registry even if a replay fails; CI variants stay unchanged.
        previous = SHAPES.get(case.shape)
        try:
            if case.bug:
                SHAPES[case.shape] = make_shape(case.shape, {"no_override", case.bug})
            trial = summarize(investigate(case.shape, case.claim, case.seed))
        finally:
            if case.bug:
                if previous is None:
                    SHAPES.pop(case.shape, None)
                else:
                    SHAPES[case.shape] = previous
        first_bad = next(e for e in trial["events"] if e["kind"] == case.first_bad_kind)
        control = controls[case.claim]
        if case.seed != 11:
            control = summarize(investigate("fixed", case.claim, case.seed))
        if not control["lab8_pass"]:
            raise RuntimeError(f"Fixed control failed: {control['run_id']}")
        evidence.append({"failure_mode": case.fm, "source": "diagnostic_bug_switch" if case.bug else "public_shape",
                         "first_bad_event": first_bad, "trial": trial, "fixed_control": control})
    return {"run_id": f"M1-{sha12(SOURCE)}", "source_claims_sha": sha12(SOURCE),
            "note": "Explicit FM/first observable wrong event annotations; not a calibrated grader or hidden anchor key.",
            "fixed_controls": controls, "evidence": evidence}


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/m1_taxonomy_evidence.json")
    args = parser.parse_args(argv)
    report = collect()
    path = Path(args.out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['run_id']}: {len(report['fixed_controls'])} fixed controls PASS")
    for evidence in report["evidence"]:
        trial, event = evidence["trial"], evidence["first_bad_event"]
        print(f"{evidence['failure_mode']} {trial['run_id']}: step {event['step']} {event['kind']} "
              f"ledger={trial['snapshot']['refund_vnd']} lab8_pass={trial['lab8_pass']}")
    print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
