"""Gate behavior on unseen slices, corrupted reports, and legitimate reordered reports."""

import copy

import pytest

pytestmark = pytest.mark.student


def _fixture():
    rows = [{"item_id": f"Q-{item}", "seed": seed, "pass_rate": True,
             "slices": ["priority_customers"] if item < 2 else []}
            for item in range(4) for seed in (11, 22)]
    report = {"manifest": {"eval_set_sha": "test", "items": 4, "seeds": [11, 22]},
              "metrics": {"pass_rate": 1.0}, "rows": rows, "evaluator_failures": []}
    spec = {"eval_set_version": "v2", "metrics": [
        {"id": "pass_rate", "kind": "capability", "blocking": True,
         "threshold": {"min": 0.5, "no_significant_drop": True}}],
        "slices": [{"name": "priority_customers", "metric": "pass_rate", "min": 0.95,
                    "no_significant_drop": True, "blocking": True}]}
    return report, spec


@pytest.mark.parametrize("trap", ["duplicate", "grader_error", "missing_value", "non_finite_row", "summary_only",
                                  "slice_relabel", "seed_swap", "missing_metric", "bad_manifest", "bad_row"])
def test_integrity_rejects_structural_corruption(trap):
    from lab9.gate import check

    base, spec = _fixture()
    pr = copy.deepcopy(base)
    if trap == "duplicate":
        pr["rows"][-1] = copy.deepcopy(pr["rows"][0])
    elif trap == "grader_error":
        pr["evaluator_failures"] = ["crash on an otherwise green report"]
    elif trap == "missing_value":
        pr["rows"][0]["pass_rate"] = None
    elif trap == "non_finite_row":
        pr["rows"][0]["pass_rate"] = float("inf")
    elif trap == "summary_only":
        pr["rows"][0]["pass_rate"] = False
    elif trap == "slice_relabel":
        for row in pr["rows"]:
            row["slices"] = []
    elif trap == "seed_swap":
        pr["rows"][0]["seed"] = 99
    elif trap == "missing_metric":
        pr["metrics"] = {}
    elif trap == "bad_manifest":
        pr["manifest"] = ["untrusted"]
    else:
        pr["rows"][0] = None
    blocked, lines = check(pr, base, spec)
    assert blocked == ["integrity"]
    assert any("INTEGRITY" in line for line in lines)


@pytest.mark.parametrize("change", ["drop_metric", "remove_blocking", "remove_ci", "lower_floor",
                                    "drop_slice", "remove_slice_ci", "slice_nonblocking"])
def test_ratchet_covers_metrics_and_slices(change):
    from lab9.gate import integrity_check

    base, spec = _fixture()
    pr_spec = copy.deepcopy(spec)
    if change == "drop_metric":
        pr_spec["metrics"] = []
    elif change == "remove_blocking":
        pr_spec["metrics"][0]["blocking"] = False
    elif change == "remove_ci":
        pr_spec["metrics"][0]["threshold"].pop("no_significant_drop")
    elif change == "lower_floor":
        pr_spec["metrics"][0]["threshold"]["min"] = 0.1
    elif change == "drop_slice":
        pr_spec["slices"] = []
    elif change == "remove_slice_ci":
        pr_spec["slices"][0].pop("no_significant_drop")
    else:
        pr_spec["slices"][0]["blocking"] = False
    assert integrity_check(base, base, pr_spec, spec)


def test_unseen_slice_is_gated_without_a_hardcoded_name():
    from lab9.gate import check

    base, spec = _fixture()
    pr = copy.deepcopy(base)
    pr["rows"][0]["pass_rate"] = False
    pr["metrics"]["pass_rate"] = 0.875
    blocked, _ = check(pr, base, spec)
    assert "slice:priority_customers/pass_rate" in blocked
    assert "pass_rate" not in blocked  # global paired CI touches zero; slice floor catches it.


def test_honest_reorder_and_tightening_are_accepted():
    from lab9.gate import check

    base, spec = _fixture()
    pr = copy.deepcopy(base)
    pr["rows"].reverse()
    pr["manifest"]["seeds"].reverse()
    tightened = copy.deepcopy(spec)
    tightened["metrics"][0]["threshold"]["min"] = 0.9
    assert check(pr, base, tightened, spec)[0] == []


@pytest.mark.parametrize("fn_name", ["pass_at_k", "pass_hat_k"])
@pytest.mark.parametrize("args", [(0, 0, 1), (-1, 0, 1), (5, -1, 1), (5, 6, 1),
                                  (5, 2, 0), (3, 1, 4), (5.0, 2, 1), (True, 0, 1)])
def test_both_pass_estimators_reject_invalid_sampling(fn_name, args):
    from lab9 import stats

    with pytest.raises(ValueError):
        getattr(stats, fn_name)(*args)
