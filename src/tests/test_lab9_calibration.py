"""M2 checks for label alignment, undefined calibration and threshold boundaries."""

import csv
from pathlib import Path

import pytest

pytestmark = pytest.mark.student


@pytest.mark.parametrize(("human", "judge"), [([], []), (["FAIL"], []), (["UNKNOWN"], ["PASS"])])
def test_confusion_rejects_unusable_labels(human, judge):
    from lab9 import stats

    with pytest.raises(ValueError):
        stats.confusion(human, judge)


def test_no_detected_failures_is_not_perfect_precision():
    from lab9 import stats

    assert stats.precision_recall(["FAIL", "PASS"], ["PASS", "PASS"]) == (0.0, 0.0)
    assert stats.cohen_kappa(["FAIL", "PASS"], ["PASS", "PASS"]) == 0.0
    assert stats.cohen_kappa(["FAIL", "PASS"], ["PASS", "FAIL"]) == -1.0


@pytest.mark.parametrize("rates", [(0.2, 0.5, 0.5), (0.2, 0.2, 0.2), (float("nan"), 0.8, 0.9),
                                  (0.2, 1.1, 0.9), (-0.1, 0.8, 0.9)])
def test_rogan_gladen_rejects_unidentifiable_or_invalid_rates(rates):
    from lab9 import stats

    with pytest.raises(ValueError):
        stats.rogan_gladen(*rates)


def test_rogan_gladen_upper_clip():
    from lab9 import stats

    assert stats.rogan_gladen(0.95, 0.8, 0.9) == 1.0


def _write_labels(path, pairs):
    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=["item_id", "reply", "human", "judge"])
        writer.writeheader()
        for index, (human, judge) in enumerate(pairs):
            writer.writerow({"item_id": str(index), "reply": "replay", "human": human, "judge": judge})


def test_constant_judge_fails_without_a_crash(tmp_path):
    from lab9.judge import calibrate

    path = tmp_path / "constant.csv"
    _write_labels(path, [("PASS", "PASS")] * 5)
    result = calibrate(path)
    assert result["passed"] is False
    assert result["kappa"] is None
    assert result["corrected_fail_rate"] is None
    assert {"kappa", "rogan_gladen"} <= result["calibration_errors"].keys()


def test_display_rounding_does_not_approve_a_judge(tmp_path):
    from lab9.judge import calibrate

    path = tmp_path / "near_floor.csv"
    _write_labels(path, [("FAIL", "FAIL")] * 1999 + [("PASS", "FAIL")] * 501
                  + [("PASS", "PASS")] * 2499)
    result = calibrate(path)
    assert result["precision"] == 0.8  # actual P=1999/2500=0.7996
    assert result["recall"] >= 0.7 and result["kappa"] >= 0.6
    assert result["passed"] is False


def test_helpful_replay_is_rejected_for_missed_failures():
    from lab9.judge import calibrate

    result = calibrate(Path("data/eval/judge_helpful_public.csv"))
    assert result["confusion"] == {"tp": 9, "fp": 0, "fn": 21, "tn": 70}
    assert result["precision"] == 1.0
    assert result["recall"] == 0.3
    assert result["kappa"] == 0.375
    assert result["passed"] is False
