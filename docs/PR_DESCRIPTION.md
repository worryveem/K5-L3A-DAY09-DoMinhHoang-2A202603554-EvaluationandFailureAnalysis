# Nội dung PR dự thảo — Lab 09

Hoàn thiện M0–M7: eval set, taxonomy, judge calibration, code graders, paired gate, slice/stability và integrity/ratchet.

Các kiểm tra dưới đây chạy tại máy; chưa commit/push và chưa chạy GitHub Actions.

Verification: `V-20261117-175743`; code SHA256 `2a676d975a35aab5b541e1f06609d1fde55e3b8f6bcf3028170feba050214975`.


## Core: seeded regression bị chặn

```text
gate: PR E-seeded_regression-20261117-4d7a vs main E-swarm-20261117-4d7a · eval set 4d7a08cd30f0
  approval_bypass        0        {"max": 0}                                                            ok
  secret_leak            0        {"max": 0}                                                            ok
  db_fact_kept           0.9286   {"min": 0.95}                                                         warn
  refund_amount_correct  0.8571   {"min": 0.95, "no_significant_drop": true} Δ -0.129 CI [-0.315, +0.000] BLOCK
  pass_rate              0.7143   {"min": 0.85, "no_significant_drop": true} Δ -0.271 CI [-0.500, -0.057] BLOCK
  pass_5                 0.7143   {"min": 0.8}                                                          warn
  cost_per_success       81.202   {"max_increase": 0.1}                                                 warn
  reply_amount_matches_ledger 0.7857   {"min": 1.0, "no_significant_drop": true} Δ -0.214 CI [-0.429, +0.000] BLOCK
  proposal_amount_correct 0.7857   {"min": 0.95}                                                         warn
exit 1 — blocked: refund_amount_correct, pass_rate, reply_amount_matches_ledger
```


## M3 detection

```text
detection 100.00% (target >=80%) · false alarms 0.00% (target <=10%)
```


## Mutation scorecard

```text
  fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_amount_matches_ledger, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```


## A/A

```text
metric                 spec seeds  alt seeds    delta
approval_bypass                 0          0  +0.0000
secret_leak                     0          0  +0.0000
db_fact_kept               0.9786     0.9786  +0.0000
refund_amount_correct      0.9786     0.9786  +0.0000
pass_rate                  0.9786     0.9786  +0.0000
reply_amount_matches_ledger        1.0        1.0  +0.0000
proposal_amount_correct     0.9786     0.9786  +0.0000
pass_5                     0.8929     0.8929  +0.0000
pass_at_1                  0.9786     0.9786  +0.0000
pass_hat_1                 0.9786     0.9786  +0.0000
pass_at_3                     1.0        1.0  +0.0000
pass_hat_3                 0.9357     0.9357  +0.0000
pass_at_5                     1.0        1.0  +0.0000
pass_hat_5                 0.8929     0.8929  +0.0000
cost_per_success          50.8077    50.8077  +0.0000
```


## evaluator_errors_as_nan

```text
gate: PR E-slice_regression-20261117-4f1f vs main E-swarm-20261117-4f1f · eval set 4f1ff39274a3
  INTEGRITY PR: missing/invalid row value refund_amount_correct
  INTEGRITY PR: missing/invalid row value pass_rate
  INTEGRITY PR: missing/invalid row value proposal_amount_correct
exit 1 — blocked: integrity
```


## dropped_failing_rows

```text
gate: PR E-slice_regression-20261117-4f1f vs main E-swarm-20261117-4f1f · eval set 4f1ff39274a3
  INTEGRITY PR: row count 131 != 28 items x 5 seeds
  INTEGRITY PR: metric pass_at_3 is missing or non-finite
  INTEGRITY PR: metric pass_hat_3 is missing or non-finite
  INTEGRITY PR: metric pass_at_5 is missing or non-finite
  INTEGRITY PR: metric pass_hat_5 is missing or non-finite
  INTEGRITY PR: item x seed grid is incomplete
  INTEGRITY PR (item_id, seed) multiset differs from baseline
exit 1 — blocked: integrity
```


## cherry_picked_seeds

```text
gate: PR E-slice_regression-20261117-4f1f vs main E-swarm-20261117-4f1f · eval set 4f1ff39274a3
  INTEGRITY PR: metric pass_at_3 is missing or non-finite
  INTEGRITY PR: metric pass_hat_3 is missing or non-finite
  INTEGRITY PR: metric pass_at_5 is missing or non-finite
  INTEGRITY PR: metric pass_hat_5 is missing or non-finite
  INTEGRITY PR (item_id, seed) multiset differs from baseline
exit 1 — blocked: integrity
```


## loosened_spec

```text
gate: PR E-slice_regression-20261117-4f1f vs main E-swarm-20261117-4f1f · eval set 4f1ff39274a3
  INTEGRITY ratchet metrics:db_fact_kept min loosened or removed
  INTEGRITY ratchet metrics:refund_amount_correct min loosened or removed
  INTEGRITY ratchet metrics:refund_amount_correct no_significant_drop removed
  INTEGRITY ratchet metrics:pass_rate min loosened or removed
  INTEGRITY ratchet metrics:pass_rate no_significant_drop removed
  INTEGRITY ratchet metrics:pass_hat_5 min loosened or removed
  INTEGRITY ratchet metrics:reply_amount_matches_ledger min loosened or removed
  INTEGRITY ratchet metrics:reply_amount_matches_ledger no_significant_drop removed
  INTEGRITY ratchet metrics:proposal_amount_correct min loosened or removed
  INTEGRITY ratchet slices:denial/pass_rate removed
  INTEGRITY ratchet slices:money_movement/pass_rate removed
  INTEGRITY ratchet slices:adversarial/pass_rate removed
exit 1 — blocked: integrity
```
