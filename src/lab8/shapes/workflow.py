"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

SHAPE = "workflow"

# Only these order fields go into the trace. The order row also carries phone,
# address, item name and internal note; those never leave lookup_order here.
_TRACE_ORDER_FIELDS = ("order_id", "status", "delay_days", "shipping_fee_vnd", "damage_verified")


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id(SHAPE, claim_id, seed))

    def done(status: str, proposal: int = 0, reason: str | None = None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal), "reason": reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )

    # 1. Claim through the allowlisted view (no parent_secret). The ticket is
    #    user data: it is never parsed for amounts, delays or order ids.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim["found"]:
        trace.add("claim", {"claim_id": claim_id, "found": False})
        return done("failed", reason="unknown_claim")
    order_id = claim.get("order_id")
    trace.add("claim", {"claim_id": claim_id, "found": True, "has_order_id": bool(order_id)})

    # 2. Missing order id -> ask for it. No ledger write.
    if not order_id:
        return done("needs_info", reason="missing_order_id")

    # 3. Order must exist and belong to the claimant's principal.
    budget.add_tool(tool_cost())
    order_view = lookup_order(conn, order_id, claim["principal_id"])
    if not order_view.get("visible"):
        trace.add("order", {"visible": False, "reason": order_view.get("reason")})
        return done("escalated", reason=order_view.get("reason"))
    order: dict[str, Any] = order_view["order"]
    trace.add("order", {"visible": True, **{k: order.get(k) for k in _TRACE_ORDER_FIELDS}})

    # 4. Money is computed by code from the order row and current policies only.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order)
    proposal = int(quote["amount_vnd"])
    trace.add("quote", safe_dump(quote))

    # 5. Nothing owed -> deny without touching the host.
    if proposal <= 0:
        return done("denied", reason=quote.get("reason"))

    # 6. Full quote to the host. The host checks approval, the per-order cap and
    #    idempotency, and subtracts what earlier claims already got.
    #    InjectedCrash must propagate (crash suite / T12).
    budget.add_tool(tool_cost())
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    trace.add(
        "issue_refund",
        {"ok": bool(outcome["ok"]), "reason": outcome["reason"], "conflict": bool(outcome["conflict"])},
    )

    # 7. Host refused: conflict -> failed, otherwise denied (host wrote policy_denied).
    if not outcome["ok"]:
        return done("failed" if outcome["conflict"] else "denied", proposal, outcome["reason"])

    # 8. Committed (or idempotent replay of the same amount).
    return done("resolved", proposal)
