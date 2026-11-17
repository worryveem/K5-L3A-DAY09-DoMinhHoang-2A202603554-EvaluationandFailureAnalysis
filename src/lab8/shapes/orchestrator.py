"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import json
import sqlite3

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.mock_llm import complete
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace


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
        # Close on normal returns AND InjectedCrash, including on Windows.
        conn.close()


def _run(
    conn: sqlite3.Connection,
    claim_id: str,
    *,
    seed: int,
    crash_at: str | None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("orchestrator", claim_id, seed))

    def conclude(
        status: str,
        proposal_amount: int = 0,
        error_reason: str | None = None,
    ) -> RunResult:
        # Only structured decisions reach the drafting model, never the ticket.
        complete(
            budget,
            seed=seed,
            purpose="draft",
            prompt=json.dumps({"status": status, "proposal_amount": proposal_amount}),
        )
        trace.add("decision", {"status": status, "reason": error_reason})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    # get_claim_view omits parent secrets, but its ticket is still untrusted text.
    # Do not put that view, the ticket, or any raw row into a trace or handoff.
    trace.add("claim_lookup", {"found": bool(claim["found"])})
    if not claim["found"]:
        return conclude("failed", error_reason="unknown_claim")
    if not claim.get("order_id"):
        return conclude("needs_info", error_reason="missing_order_id")

    handoff = make_handoff(
        request_id=f"REQ-{claim_id}",
        claim_id=claim_id,
        task="check_order_and_current_policy",
        facts={},
        allowed_tools=["lookup_order", "lookup_policy"],
    )
    trace.add("handoff", handoff)
    # The model may acknowledge the plan; it cannot change the tool allowlist,
    # structured order facts, quote, approval, or the refund writer.
    complete(
        budget,
        seed=seed,
        purpose="plan",
        prompt=json.dumps(handoff, ensure_ascii=False, sort_keys=True),
    )
    investigation = run_readonly_investigators(
        conn, budget, handoff, principal_id=claim["principal_id"]
    )
    order_view = investigation["tools"].get("lookup_order") or {}
    policy_view = investigation["tools"].get("lookup_policy") or {}
    trace.add(
        "investigator",
        {
            "order_visible": bool(order_view.get("visible")),
            "policy_count": len(policy_view.get("policies") or []),
        },
    )
    if not order_view.get("visible"):
        return conclude("escalated", error_reason=order_view.get("reason"))

    # Money comes from code and the scoped order, not a number in the ticket.
    budget.add_tool(tool_cost())
    quote = compute_compensation(conn, order_view["order"])
    proposal = int(quote["amount_vnd"])
    trace.add("quote", {"amount_vnd": proposal, "reason": quote["reason"]})
    if proposal <= 0:
        return conclude("denied", error_reason=quote["reason"])

    # Keep the full entitlement. The host owns approval and the per-order cap,
    # including subtracting earlier refunds and recording policy_denied.
    trace.add("refund_request", {"proposal_amount": proposal})
    trace.write()
    # Flush before the crash window. Do not catch or suppress InjectedCrash.
    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    trace.add("refund_outcome", {"ok": outcome["ok"], "reason": outcome["reason"]})
    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return conclude(status, proposal, outcome["reason"])
    return conclude("resolved", proposal)
