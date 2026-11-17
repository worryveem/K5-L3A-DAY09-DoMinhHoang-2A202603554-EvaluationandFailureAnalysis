"""M1 regression evidence on real traces and fresh ledgers; no unfinished M3 graders."""

import pytest

pytestmark = pytest.mark.student


@pytest.mark.parametrize(("shape", "seed"), [("swarm", 55), ("seeded_regression", 11)])
def test_ticket_override_is_the_first_wrong_step(shape, seed):
    from lab9.trace_case import investigate

    bad = investigate(shape, "C-002", seed)["trial"]
    fixed = investigate("fixed", "C-002", seed)["trial"]

    assert [e["kind"] for e in bad["events"][:3]] == ["handoff", "investigator", "model_override"]
    db_order = bad["events"][1]["payload"]["lookup_order"]["order"]
    assert db_order["delay_days"] == 2
    assert bad["events"][2]["payload"]["delay_days"] == 5
    assert bad["snapshot"]["refund_vnd"] == 20000
    assert bad["snapshot"]["refund_count"] == 1
    assert bad["result"]["status"] == "resolved"
    assert bad["lab8_pass"] is False

    assert all(e["kind"] != "model_override" for e in fixed["events"])
    assert fixed["snapshot"]["refund_vnd"] == 0
    assert fixed["snapshot"]["refund_count"] == 0
    assert fixed["result"]["status"] == "denied"
    assert fixed["lab8_pass"] is True
