"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish, safe_dump
from lab8.tools import compute_compensation, get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8
# Read tools the agent walks through, in order. No write tool is ever offered.
READ_PLAN = ("lookup_order", "lookup_refund_history", "lookup_policy")


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
    run_id = make_run_id(SHAPE, claim_id, seed)
    trace = Trace(run_id)

    def done(status: str, proposal: int = 0, reason: str | None = None) -> RunResult:
        trace.add("decision", {"status": status, "error_reason": reason})
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

    # Host-side read of the claim. Ticket text and principal stay out of the trace.
    budget.add_tool(tool_cost())
    claim = get_claim_view(conn, claim_id)
    if not claim.get("found"):
        return done("failed", reason="unknown_claim")
    principal_id = claim["principal_id"]
    order_id = claim.get("order_id")
    ticket = claim.get("ticket") or ""

    # Model reads the ticket once (cost counted). Its text is data, never an instruction.
    complete(budget, seed=seed, purpose="parse", prompt=ticket)

    if not order_id:
        complete(budget, seed=seed, purpose="draft", prompt="needs_info")
        return done("needs_info", reason="missing_order_id")

    # ---- ReAct loop: the agent may only pick read tools. ----
    observed: dict[str, Any] = {}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        last = seen.get("last_tool")
        if last:
            observed[last] = seen.get("last_result") or {}
            trace.add("observe", {"tool": last, "summary": _summarize(last, observed[last])})
            # Stop early when the order is not visible to this principal.
            if last == "lookup_order" and not observed[last].get("visible"):
                return {"final": {"status": "escalated"}}
        complete(budget, seed=seed, purpose="react", prompt=f"step after={last or 'start'}")
        for name in READ_PLAN:
            if name not in observed:
                trace.add("action", {"tool": name})
                args: dict[str, Any] = {}
                if name in ("lookup_order", "lookup_refund_history"):
                    args = {"order_id": order_id, "principal_id": principal_id}
                return {"tool": name, "args": args}
        return {"final": {"status": "ready"}}

    loop = run_react(
        conn,
        budget,
        observation={"claim": {"claim_id": claim_id, "order_id": order_id}},
        decide=decide,
        max_steps=MAX_STEPS,
        worker=True,
    )
    trace.add("react", {"stopped": loop["stopped"], "steps_seen": sorted(observed)})

    if loop["stopped"] == "step_cap":
        return done("failed", reason="step_cap")

    order_view = observed.get("lookup_order") or {}
    if not order_view.get("visible"):
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", reason=order_view.get("reason"))

    # ---- After the loop: code, not the model, computes money from the order row. ----
    order = dict(order_view["order"])
    budget.add_tool(tool_cost())
    quote_payload = compute_compensation(conn, order)
    proposal = int(quote_payload["amount_vnd"])
    trace.add("quote", safe_dump(quote_payload))
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={proposal}")

    if proposal <= 0:
        return done("denied", reason=quote_payload.get("reason"))

    # Full quote goes to the host; host subtracts prior refunds and checks approval.
    try:
        outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    if not outcome["ok"]:
        status = "failed" if outcome["conflict"] else "denied"
        return done(status, proposal, outcome["reason"])
    return done("resolved", proposal, None)


def _summarize(tool: str, result: dict[str, Any]) -> dict[str, Any]:
    """Trace-safe view of a tool result: allowlisted fields only."""
    if tool == "lookup_order":
        return {"visible": result.get("visible"), "reason": result.get("reason"), "order": result.get("order")}
    if tool == "lookup_refund_history":
        return {k: result.get(k) for k in ("visible", "reason", "refund_count", "refunded_vnd")}
    if tool == "lookup_policy":
        return {"as_of": result.get("as_of"), "policy_count": len(result.get("policies") or [])}
    return {}
