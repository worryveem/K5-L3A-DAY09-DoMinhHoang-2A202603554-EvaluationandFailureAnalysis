"""R3 ablation: change only the partition of work among investigators.

Production Shape C uses one investigator to read order and policy. This
experimental variant uses two read-only invocations, one tool apiece. The
runtime executes them sequentially: this experiment cannot measure parallel
speedup. No official source file is modified. Model calls and prompts, tool
availability, seed, corpus, money logic, prices and evaluator stay the same.
"""

from __future__ import annotations

from unittest.mock import patch

from lab8.handoff import make_handoff
from lab8.runtime import run_readonly_investigators
from lab8.shapes import orchestrator
from lab8.trace import Trace


def _split_investigators(conn, budget, handoff, principal_id):
    combined = {"claim_view": {}, "tools": {}}
    for tool in handoff["allowed_tools"]:
        child = make_handoff(
            request_id=handoff["request_id"],
            claim_id=handoff["claim_id"],
            task=handoff["task"],
            facts=handoff["facts"],
            allowed_tools=[tool],
            max_output_tokens=handoff["max_output_tokens"],
        )
        result = run_readonly_investigators(conn, budget, child, principal_id=principal_id)
        combined["claim_view"] = result["claim_view"]
        combined["tools"].update(result["tools"])
    return combined


def run_split_claim(claim_id, *, seed, store_path, crash_at=None):
    def variant_trace(run_id):
        return Trace(run_id.replace("R-orchestrator-", "R-orchestrator_split-", 1))

    # Patches exist only during this sequential experimental run.
    with (
        patch.object(orchestrator, "run_readonly_investigators", _split_investigators),
        patch.object(orchestrator, "Trace", variant_trace),
    ):
        result = orchestrator.run_claim(
            claim_id, seed=seed, store_path=store_path, crash_at=crash_at
        )
    result.shape = "orchestrator_split"
    return result
