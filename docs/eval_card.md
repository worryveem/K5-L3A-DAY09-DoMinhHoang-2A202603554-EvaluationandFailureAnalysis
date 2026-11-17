# Eval card — LogiX-VN refund agent

Kiểm chứng: `V-20261117-175743`, kết thúc `2026-11-17T18:05:42.400481+07:00` (UTC+7).
Code tham chiếu: `edf6d6b` + working tree chưa commit;
SHA256 của code đánh giá, spec, test và workflow Lab 09: `2a676d975a35aab5b541e1f06609d1fde55e3b8f6bcf3028170feba050214975`.
Các số liệu dưới đây được trích bằng `scripts/build_lab9_docs.py` từ report do CLI sinh.


## Core: eval set v1

- Baseline: `E-swarm-20261117-4d7a`; nguồn `swarm`, 14 item × 5 seed.
- Đối chứng tốt: `E-fixed-20261117-4d7a`; regression: `E-seeded_regression-20261117-4d7a`.
- Eval set SHA: `4d7a08cd30f0`; labels SHA: `8ec43bda7384`.
- Metric spec `1.1`; seeds `[11, 22, 33, 44, 55]`; MockLLM offline.
- Baseline được sinh từ working tree đã hoàn thiện, chưa được đưa lên main được bảo vệ.

| Metric | Baseline swarm | Fixed | Seeded regression |
|---|---|---|---|
| approval_bypass | 0 | 0 | 0 |
| secret_leak | 0 | 0 | 0 |
| db_fact_kept | 0.9857 | 1.0000 | 0.9286 |
| refund_amount_correct | 0.9857 | 1.0000 | 0.8571 |
| pass_rate | 0.9857 | 1.0000 | 0.7143 |
| pass_5 | 0.9286 | 1.0000 | 0.7143 |
| cost_per_success | 49.5670 | 48.7157 | 81.2020 |
| reply_amount_matches_ledger | 1.0000 | 1.0000 | 0.7857 |
| proposal_amount_correct | 0.9857 | 1.0000 | 0.7857 |

Paired bootstrap lấy **trung bình từng item qua 5 seed**, rồi resample cùng chỉ số item;
không coi 70 trial là 70 quan sát độc lập. Percentile CI 95%, 1.000 resample, RNG 2027.
Δ = candidate − baseline; CI có upper bound < 0 thì chặn metric có `no_significant_drop`.

| Metric | Fixed: Δ [CI 95%] | Seeded: Δ [CI 95%] |
|---|---|---|
| pass_rate | +0.0143 [+0.0000, +0.0429] | -0.2714 [-0.5000, -0.0571] |
| refund_amount_correct | +0.0143 [+0.0000, +0.0429] | -0.1286 [-0.3146, +0.0000] |
| reply_amount_matches_ledger | +0.0000 [+0.0000, +0.0000] | -0.2143 [-0.4286, +0.0000] |

- Baseline tự so với nó và PR swarm: exit 0; `fixed`: exit 0; `seeded_regression`: exit 1, có `pass_rate` trong lý do chặn.
- M3: detection 100.00% (target >=80%) · false alarms 0.00% (target <=10%)
- `ProposalAmountCorrect` giải thích lỗi trừ trước về 0 ở C-013, dù ledger 0đ vẫn đúng; tránh chỉ nhìn số tiền cuối.
- Metric FM-08 `reply_amount_matches_ledger`: sàn 1.0, blocking, đối chiếu số tiền đã xác nhận với ledger.
- `swarm` cũ không ghi event reply: metric FM-08 coi đó là không quan sát được và không báo mismatch;
  điểm 1.0 của baseline không chứng minh reply của shape này đúng. Variant có reply được kiểm trực tiếp.
- Tiền được hỗ trợ khi ghi `đ`, `đồng`, `₫`, `VND`/`VNĐ` với dấu phân nhóm phổ biến;
  chữ số tiền bằng lời hoặc đơn vị viết tắt chưa có trong corpus cần mở rộng parser và eval set trước pilot thật.
- Trace case: [C-002](trace_case.md), bước #3 đổi DB trễ 2 ngày thành ticket 5 ngày.

## Judge và phạm vi pilot

- Tone: κ=0.757, P=0.857, R=0.8, đạt floors trên 100 replay.
- Helpful: κ=0.375, P=1.0, R=0.3; loại khỏi gate vì bỏ sót 21/30 lỗi.
- [Judge audit](judge_audit.md) có 16 bất đồng; H-081 cần adjudication, chưa sửa nhãn public.
- Pilot hiện tại chỉ là mô phỏng offline: một claim/một đơn, trễ giao hàng hoặc hỏng hàng đã xác minh,
  approval hợp lệ và trần theo đơn do host áp dụng. Chưa chạy người dùng thật hoặc chuyển tiền thật.
- **Gate owner:** Đỗ Minh Hoàng — phụ trách eval; gate exit 1 thì kiểm integrity trước,
  sau đó đọc metric/slice và trace, sửa lỗi rồi chạy lại. Chưa có phê duyệt sản xuất.

## Advanced / Expert: eval set v2

- Baseline `E-swarm-20261117-4f1f`: 28 item (14 public + 14 adversarial) × 5 seed = 140 trial.
- Eval set SHA `4f1ff39274a3`; labels SHA `a86f90a9d694`;
  spec `2.1`; nhãn tách khỏi item; mọi FM bị tấn công có ít nhất 3 item trong v2.
- A/A: cùng swarm, seed gốc `[11, 22, 33, 44, 55]`, seed mới `[66, 77, 88, 99, 110]`;
  Δ của cả 15 metric được in đều bằng 0. Hai tập đều có một seed chia hết cho 5,
  nên kích hoạt cùng lỗi ticket-trust cố định; đây không phải ước lượng đủ cho nhiễu LLM thật.
- Sàn `pass_hat_5` = 0.80, thấp hơn A/A baseline 0.8929,
  khoảng cách 0.0929 so với dải nhiễu quan sát bằng 0.
  Sàn money_movement=0.95 áp yêu cầu chất lượng cao cho chuyển tiền; adversarial=0.90 và denial=0.90.
  Các ngưỡng được cố định trước scorecard, không nới để làm xanh variant.

| Slice / pass_rate | Sàn | Baseline | Slice regression | Flaky regression | Slice regression: Δ [CI] |
|---|---|---|---|---|---|
| denial | 0.9 | 0.9455 | 1.0000 | 0.9273 | +0.0545 [+0.0182, +0.1091] |
| money_movement | 0.95 | 1.0000 | 0.8500 | 0.8667 | -0.1500 [-0.3000, +0.0000] |
| adversarial | 0.9 | 0.9714 | 0.9143 | 0.9286 | -0.0571 [-0.1857, +0.0571] |

- `slice_regression`: pass_rate toàn tập 0.9357, vẫn trên sàn toàn cục 0.85;
  paired Δ/CI toàn tập -0.0429 [-0.1214, +0.0286]; slice tiền phát hiện phần giảm bị trung bình che.
- `flaky_regression`: pass_rate 0.9143, `pass_hat_5` 0.5714 < 0.80.
  Trong lượt này paired gate toàn cục cũng có thể chặn; không khẳng định chỉ pass_hat_5 phát hiện được nó.
- `pass@k = 1 − C(n−c,k)/C(n,k)` đo ít nhất một lần thành công;
  `pass^k = C(c,k)/C(n,k)` đo tất cả k lần thành công, không được đánh đồng hai đại lượng.
- Bug phụ thuộc `seed % 3 == 0` trong demo kích hoạt một trong năm seed đang dùng;
  việc bắt được demo này không chứng minh có thể phát hiện ổn định mọi lỗi hiếm hoặc một tỷ lệ lỗi 1/3 trên model thật với chỉ 5 seed.

```text
fixed                expect merge got merge ok
  honest_refactor      expect merge got merge ok
  seeded_regression    expect block got block ok          refund_amount_correct, pass_rate, pass_hat_5, reply_amount_matches_ledger, slice:denial/pass_rate, slice:money_movement/pass_rate, slice:adversarial/pass_rate
  slice_regression     expect block got block ok          slice:money_movement/pass_rate
  flaky_regression     expect block got block ok          pass_rate, pass_hat_5, slice:money_movement/pass_rate
mutation score 3/3 · false alarms 0
```

## Integrity, ratchet và giới hạn

- Bốn trap public đều exit 1 với lý do INTEGRITY: NaN/None, bỏ dòng fail, chọn seed đẹp, nới spec.
- Có test bổ sung cho dòng trùng, evaluator_failures trên report xanh, đổi slice, sửa summary khác rows,
  metric bị thiếu, dữ liệu không hữu hạn, slice chưa từng đặt tên trong starter và lỗi override không để lại event.
- Ratchet so với spec lấy từ Git base: không hạ min, tăng max/max_increase, bỏ metric/slice,
  bỏ blocking/no_significant_drop hay thay grader trên cùng eval-set version.
- Kiểm cấu trúc và tái tính summary không chứng thực được report giả mạo toàn bộ rows một cách nhất quán;
  cần runner CI được bảo vệ và provenance đáng tin. Baseline/spec phải được duyệt trước khi phát hành.
- Chưa chạy key anchor, variant/trap ẩn của giảng viên. Không suy ra điểm 100 chỉ từ test public.
- Nguồn mô phỏng nhỏ, judge replay public, CI có thể rộng; không suy ra chất lượng LLM thật, chi phí API hoặc latency thật.
- Đổi corpus/nhãn/nguồn dữ liệu: tăng eval_set_version, sinh baseline mới; đổi metric/rubric: tăng phiên bản tương ứng;
  cùng eval-set version chỉ siết ngưỡng, không nới ngưỡng.

## Kiểm tra cuối bài

- `python -m pytest -q`: 105 passed, 333 deselected in 21.58s
- `python -m pytest -q -m student -o addopts= -k lab9`: 85 passed, 353 deselected in 7.73s
- `python -m pytest -q -m student -o addopts= -k swarm`: 63 passed, 375 deselected in 13.61s

Log: [verification.log](../src/reports/verification.log);
summary: [verification_summary.json](../src/reports/verification_summary.json);
[nội dung PR dự thảo](PR_DESCRIPTION.md).
Các kết quả trên là local Windows, chưa phải GitHub Actions xanh; chưa commit/push theo yêu cầu.
