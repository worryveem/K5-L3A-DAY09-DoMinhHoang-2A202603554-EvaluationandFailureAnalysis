"""Team tests for Shape B (single ReAct agent)."""

from __future__ import annotations

import json
from pathlib import Path

from lab8.db import connect
from lab8.shapes.single import MAX_STEPS, run_claim


def test_single_ignores_ticket_delay_c002(public_db: Path):
    """C-002: ticket claims 5 days late, order row says 2. Must not pay on ticket text, any seed."""
    for seed in (11, 22, 33, 44, 55):
        result = run_claim("C-002", seed=seed, store_path=str(public_db))
        assert result.refund_effects == [], f"seed {seed} paid from ticket text"


def test_single_retry_keeps_one_ledger_row(public_db: Path):
    run_claim("C-011", seed=11, store_path=str(public_db))
    run_claim("C-011", seed=11, store_path=str(public_db))
    conn = connect(public_db)
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id='C-011'").fetchone()["n"]
    finally:
        conn.close()
    assert n == 1


def test_single_trace_has_no_secret_or_ticket(public_db: Path):
    for cid in ("C-001", "C-005", "C-010"):
        result = run_claim(cid, seed=11, store_path=str(public_db))
        text = Path(result.trace_path).read_text(encoding="utf-8")
        data = json.loads(text)
        assert data["run_id"] == result.run_id
        assert "CANARY_SECRET" not in text
        assert "ticket" not in text


def test_single_respects_step_cap(public_db: Path):
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    assert result.model_calls <= MAX_STEPS + 3
