# Nộp bài (hạn 23:59 cùng ngày)
PR từ `starter/d09` → `main` của repo nhóm. Chấm commit cuối trước 23:59; commit sau hạn không tính.

## Core (nên xong trước 17:00)
- [x] `src/lab9/{stats,graders,evalset}.py` đã hoàn thành M1–M4
- [x] `src/data/eval/eval_set_v1.jsonl` có `failure_modes`, `labels_v1.json` tách riêng
- [x] `docs/failure_taxonomy.md`, `docs/trace_case.md` (1 case + regression test), `docs/judge_audit.md`, `docs/eval_card.md`, `docs/PRD_v1.1.md`
- [x] `src/reports/baseline_v1.json`, `eval_fixed.json`, `eval_seeded_regression.json` có sẵn tại máy, sinh bằng script
- [x] `src/harness_map.yaml` có section `eval`
- [x] Output gate exit 1 của `seeded_regression` có trong [PR description dự thảo](docs/PR_DESCRIPTION.md)
- [ ] Mở PR và xác nhận job `eval-gate` xanh trên GitHub

## Advanced / Expert (tới 23:59)
- [x] `config/fm_map.yaml`, `config/metric_spec_v2.yaml` (slices, `pass_hat_5`, metric FM-08), `stats.pass_at_k/pass_hat_k`, `gate.slice_check`, `gate.integrity_check`
- [x] `src/data/eval/eval_set_v2.jsonl` + `labels_v2.json`, sinh bằng `evalset --v2 --build`
- [x] `src/reports/baseline_v2.json` đã sinh bằng script
- [x] PR description dự thảo có output `lab9.mutation` (scorecard + `--aa`) và 4 dòng `exit 1` của trap
- [x] `docs/eval_card.md` có v2, ngưỡng A/A, slice và giới hạn cỡ mẫu
- [ ] Xác nhận job `eval-gate-v2` xanh trên GitHub
- [ ] Giảng viên đối chiếu 5 anchor và chạy variant/trap ẩn để xác nhận điểm cuối cùng

## Tình trạng lưu bài và điểm

- [x] `.gitignore` đã cho phép riêng các baseline/report bằng chứng cần nộp; runtime nhạy cảm vẫn bị chặn.
- [x] Đưa thay đổi sau M1 và các artifact cần nộp lên nhánh GitHub trước hạn (chưa thực hiện theo yêu cầu không commit).

Các mục chưa hoàn thành ở trên không được tự đánh dấu đạt hoặc coi là đã có 100/100.
Phê duyệt sản xuất, dữ liệu thật và bonus chuyển grader sang Inspect AI/DeepEval không phải yêu cầu bắt buộc để đạt tối đa 100 điểm của rubric chính.
# Nộp bài (hạn 23:59 cùng ngày)
