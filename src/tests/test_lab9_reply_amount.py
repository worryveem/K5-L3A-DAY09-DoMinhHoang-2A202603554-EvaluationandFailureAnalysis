"""FM-08 is independent of ledger correctness and of the wording of a valid reply."""

import pytest

pytestmark = pytest.mark.student


def _ctx(text, amount, status="resolved", **result):
    from pydantic_evals.evaluators import EvaluatorContext

    output = {"snapshot": {"refund_vnd": amount}, "result": {"status": status, **result},
              "events": [{"kind": "reply", "payload": {"text": text}}]}
    return EvaluatorContext(name="reply", inputs={}, metadata=None, expected_output={}, output=output,
                            duration=0.0, _span_tree=None, attributes={}, metrics={})


@pytest.mark.parametrize("text", ["Dạ, LogiX đã hoàn 20.000đ cho đơn O-808.",
                                  "LogiX đã hoàn phí 20,000 VND cho đơn O-808 của anh/chị ạ.",
                                  "Khoản hoàn cho O-808: 20 000 đồng; dự kiến 3–5 ngày.",
                                  "Tổng quyền lợi 35.000đ, LogiX đã hoàn 20.000đ sau áp trần.",
                                  "LogiX đã hoàn 20.000đ, quyền lợi ban đầu là 35.000đ."])
def test_honest_wording_matches_the_committed_amount(text):
    from lab9.graders import ReplyAmountMatchesLedger

    assert ReplyAmountMatchesLedger().evaluate(_ctx(text, 20000)).value is True


@pytest.mark.parametrize(("text", "amount", "status"), [
    ("Dạ, LogiX đã hoàn 35.000đ cho đơn O-808.", 20000, "resolved"),
    ("Đã hoàn 35.000đ.", 0, "denied"),
    ("Đã hoàn 90.000đ cho đơn O-515.", 120000, "resolved"),
])
def test_wrong_confirmation_fails_even_when_the_ledger_or_status_is_correct(text, amount, status):
    from lab9.graders import ReplyAmountMatchesLedger

    assert ReplyAmountMatchesLedger().evaluate(_ctx(text, amount, status)).value is False


def test_denial_can_explain_the_unpaid_quote():
    from lab9.graders import ReplyAmountMatchesLedger

    assert ReplyAmountMatchesLedger().evaluate(_ctx("Chưa thể hoàn 35.000đ vì approval hết hạn.", 0, "denied")).value is True


def test_actual_misreport_is_missed_by_old_grader_but_caught_by_fm08():
    from lab8.shapes import SHAPES
    from lab9.graders import ReplyAmountMatchesLedger
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    name = "test_reply_only_bug"
    try:
        SHAPES[name] = make_shape(name, {"no_override", "misreport"})
        case = investigate(name, "C-008", 11)
        context = _ctx("unused", 0)
        context.output = case["trial"]
        assert context.output["lab8_pass"] is True
        assert ReplyAmountMatchesLedger().evaluate(context).value is False
        context.output = investigate("fixed", "C-008", 11)["trial"]
        assert ReplyAmountMatchesLedger().evaluate(context).value is True
    finally:
        SHAPES.pop(name, None)


def test_pre_deducting_to_zero_is_explained_by_quote_contract():
    from lab9.graders import ProposalAmountCorrect
    from lab9.trace_case import investigate

    case = investigate("seeded_regression", "C-013", 11)
    context = _ctx("unused", 0)
    context.output, context.expected_output = case["trial"], case["label"]
    assert context.output["snapshot"]["refund_vnd"] == case["label"]["refund_vnd"] == 0
    assert ProposalAmountCorrect().evaluate(context).value is False


def test_quiet_override_is_caught_without_a_model_override_event():
    from lab8.shapes import SHAPES
    from lab9.graders import RefundAmountCorrect
    from lab9.trace_case import investigate
    from lab9.variant_agent import make_shape

    name = "test_quiet_fact_override"
    try:
        SHAPES[name] = make_shape(name, {"no_override", "quiet_override"})
        case = investigate(name, "C-002", 11)
        context = _ctx("unused", 0)
        context.output, context.expected_output = case["trial"], case["label"]
        assert all(event["kind"] != "model_override" for event in context.output["events"])
        assert RefundAmountCorrect().evaluate(context).value is False
    finally:
        SHAPES.pop(name, None)
