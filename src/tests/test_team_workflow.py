"""Team tests for shape A (workflow).

These complement the public student matrix with the properties the workflow
owner is accountable for: money from code only, full quote to the host,
idempotency and crash resume, and a trace that carries no secret or PII.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.shapes.workflow import run_claim
from tests.conftest import BY_ID, CLAIMS

SEEDS = [11, 22, 33, 44, 55]


@pytest.fixture(autouse=True)
def _isolated_traces(tmp_path, monkeypatch):
    # Trace writes to ./traces; keep test traces out of the repo.
    monkeypatch.chdir(tmp_path)


def _ledger_rows(store: Path, claim_id: str) -> int:
    conn = connect(store)
    try:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()["n"]
    finally:
        conn.close()


def _policy_denied_count(store: Path, claim_id: str) -> int:
    conn = connect(store)
    try:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM audit_events WHERE claim_id = ? AND event_type = 'policy_denied'",
            (claim_id,),
        ).fetchone()["n"]
    finally:
        conn.close()


def test_retry_same_claim_keeps_one_refund(public_db):
    first = run_claim("C-001", seed=11, store_path=str(public_db))
    second = run_claim("C-001", seed=11, store_path=str(public_db))
    assert first.status == "resolved"
    assert second.status == "resolved"
    assert _ledger_rows(public_db, "C-001") == 1
    conn = connect(public_db)
    try:
        assert committed_audit_count(conn, "C-001") == 1
        assert int(get_refund(conn, "C-001")["amount_vnd"]) == 35000
    finally:
        conn.close()


def test_crash_after_effect_propagates_and_resume_pays_once(public_db):
    with pytest.raises(InjectedCrash):
        run_claim(
            "C-001", seed=11, store_path=str(public_db), crash_at="after_effect_before_checkpoint"
        )
    resumed = run_claim("C-001", seed=11, store_path=str(public_db))
    assert resumed.status == "resolved"
    assert _ledger_rows(public_db, "C-001") == 1
    assert resumed.committed_audit_count == 1


@pytest.mark.parametrize("seed", SEEDS)
def test_ticket_delay_is_ignored_on_every_seed(public_db, seed):
    # C-002: ticket claims 5 days late, the order row says 2. The order row wins.
    result = run_claim("C-002", seed=seed, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.model_calls == 0
    assert _ledger_rows(public_db, "C-002") == 0


def test_full_quote_is_passed_and_host_pays_only_the_difference(public_db):
    # C-014: order already got 30000 shipping; damage entitlement is 150000.
    result = run_claim("C-014", seed=11, store_path=str(public_db))
    assert result.status == "resolved"
    assert result.proposal_amount == 150000
    assert [int(e["amount_vnd"]) for e in result.refund_effects] == [120000]


def test_order_already_refunded_is_denied_by_host_with_audit(public_db):
    # C-013: shape must still call the host so policy_denied is recorded.
    result = run_claim("C-013", seed=11, store_path=str(public_db))
    assert result.status == "denied"
    assert result.proposal_amount == 35000
    assert result.refund_effects == []
    assert _policy_denied_count(public_db, "C-013") >= 1


def test_missing_order_id_needs_info_without_ledger_write(public_db):
    result = run_claim("C-004", seed=11, store_path=str(public_db))
    assert result.status == "needs_info"
    assert result.proposal_amount == 0
    assert _ledger_rows(public_db, "C-004") == 0
    assert _policy_denied_count(public_db, "C-004") == 0


def test_unknown_claim_fails_without_exception(public_db):
    result = run_claim("C-DOES-NOT-EXIST", seed=11, store_path=str(public_db))
    assert result.status == "failed"
    assert result.error_reason == "unknown_claim"
    assert Path(result.trace_path).is_file()


@pytest.mark.parametrize("claim_id", [row["claim_id"] for row in CLAIMS])
def test_trace_contract_and_no_secret_or_pii(public_db, claim_id):
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    body_text = Path(result.trace_path).read_text(encoding="utf-8")
    body = json.loads(body_text)
    assert body["run_id"] == result.run_id
    assert isinstance(body["events"], list) and body["events"]

    result_text = json.dumps(result.as_dict(), ensure_ascii=False)
    forbidden = list(BY_ID[claim_id]["expected"].get("forbid_substrings", []))
    forbidden += ["CANARY_SECRET", "CANARY_INTERNAL", BY_ID[claim_id]["ticket"]]
    for needle in forbidden:
        assert needle not in body_text, f"trace leaks {needle!r}"
        assert needle not in result_text, f"result leaks {needle!r}"
