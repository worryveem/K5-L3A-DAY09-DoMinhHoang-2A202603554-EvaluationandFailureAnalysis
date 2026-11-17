# Báo cáo bằng chứng Lab 09

Các JSON và log trong thư mục này được sinh bằng `python -m lab9.verify` từ `src/`;
không sửa giá trị metric hoặc nội dung rows bằng tay.

| Artifact | Nội dung | Tình trạng |
|---|---|---|
| `baseline_v1.json` | Swarm, eval set v1, 14 item × 5 seed | Đã sinh, chưa commit thay đổi sau M1 |
| `eval_fixed.json` | Đối chứng Core tốt | Gate exit 0 |
| `eval_seeded_regression.json` | Regression Core | Gate exit 1, có pass_rate |
| `baseline_v2.json` | Swarm, eval set v2, 28 item × 5 seed | Đã sinh, chưa commit |
| `v2/eval_slice_regression.json` | Regression trên slice chuyển tiền | Gate chặn money_movement |
| `v2/eval_flaky_regression.json` | Lỗi chập chờn theo seed | Gate chặn pass_hat_5 |
| `v2/principal_scope_evidence.json` | Ba attack xuyên principal bị từ chối | Đối chứng replay PASS |
| `judge_tone_calibration.json` | Calibration tone | PASS floors |
| `judge_helpful_calibration.json` | Calibration helpful | FAIL floors đúng mong đợi |
| `m1_taxonomy_evidence.json` | Bằng chứng và đối chứng taxonomy | Script sinh |
| `verification_summary.json` | 32 bước kiểm tra, code fingerprint, verdict và output | PASS tại máy |
| `verification.log` | Toàn bộ lệnh và output kiểm tra | Có sẵn |
| `requirements-resolved.txt` | Dependency thực tế của lượt kiểm tra | Script sinh |

`.gitignore` cho phép riêng các artifact trên và `eval_pr.json` để chuẩn bị nộp;
vẫn ignore `traps/`, SQLite, trace thô và các output runtime khác.
Không có lệnh stage/commit/push nào được thực hiện ở lượt rà soát này.

Báo cáo đọc chính: [bản bàn giao](../../docs/REVIEW_LAB09.md),
[eval card](../../docs/eval_card.md), [đối chiếu rubric](../../docs/RUBRIC_AUDIT.md).

Đây là kết quả tại máy, chưa phải xác nhận GitHub Actions xanh hoặc điểm của bộ chấm ẩn.
