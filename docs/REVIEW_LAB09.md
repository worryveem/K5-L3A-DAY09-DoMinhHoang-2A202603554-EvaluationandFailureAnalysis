# Bản bàn giao Lab 09 để kiểm tra

M0–M7 đã hoàn thiện và qua kiểm tra tại máy. **Chưa commit/push các thay đổi sau M1** theo yêu cầu;
HEAD vẫn là `edf6d6b`. Không mở PR hoặc tự phê duyệt release.

Kiểm chứng: `V-20261117-175743`, kết thúc `2026-11-17T18:05:42.400481+07:00` (UTC+7).
Code tham chiếu: `edf6d6b` + working tree chưa commit;
SHA256 của code đánh giá, spec, test và workflow Lab 09: `2a676d975a35aab5b541e1f06609d1fde55e3b8f6bcf3028170feba050214975`.
Các số liệu dưới đây được trích bằng `scripts/build_lab9_docs.py` từ report do CLI sinh.


## Các file nên đọc

1. [Eval card](eval_card.md): số liệu v1/v2, paired CI, ngưỡng, A/A và giới hạn.
2. [PRD v1.1](PRD_v1.1.md): yêu cầu đo được, gate, trách nhiệm và trạng thái phê duyệt.
3. [Taxonomy](failure_taxonomy.md), [trace case](trace_case.md), [judge audit](judge_audit.md).
4. [PR description dự thảo](PR_DESCRIPTION.md): output regression, scorecard, A/A và bốn trap exit 1.
5. [Log đầy đủ](../src/reports/verification.log) và [summary JSON](../src/reports/verification_summary.json).
6. [Đối chiếu rubric và biểu mẫu gốc](RUBRIC_AUDIT.md): kết luận về điểm và các việc còn lại.

## Kết quả kiểm tra

- `python -m pytest -q`: 105 passed, 333 deselected in 21.58s
- `python -m pytest -q -m student -o addopts= -k lab9`: 85 passed, 353 deselected in 7.73s
- `python -m pytest -q -m student -o addopts= -k swarm`: 63 passed, 375 deselected in 13.61s

- Eval set v1/v2: 0 problem(s); nhãn tách riêng, v2 có 28 item × 5 seed.
- M3 detection 100%, false alarm 0%; Core cho fixed qua và chặn seeded_regression.
- Advanced scorecard 3/3, 0 false alarm; slice_regression bị chặn ở money_movement;
  flaky_regression bị chặn ở pass_hat_5; cả 4 trap public bị chặn bằng INTEGRITY.
- A/A: Δ=0 cho 15 metric; baseline tự so với nó đều qua.
- Lab 08, public fixtures, variants/traps và test gốc được giữ nguyên.

Các nhóm pytest có thể trùng test; không cộng số passed để suy ra tổng test duy nhất.

## Chạy lại

Từ gốc repo:

```powershell
Set-Location src
..\.venv\Scripts\python.exe -m lab9.verify
..\.venv\Scripts\python.exe scripts/build_lab9_docs.py
```

Script kiểm tra sẽ tái sinh các report và log; không commit hoặc gửi dữ liệu đi.
Các report cần nộp nằm trong `src/reports/`. `.gitignore` đã cho phép riêng các baseline,
report và log bằng chứng được chọn để không bị bỏ sót khi người dùng quyết định nộp.
Các file này vẫn chưa stage/commit; `.venv`, trace thô, SQLite và trap runtime tiếp tục bị ignore.

## Phần chưa thể xác nhận tại máy

- Chưa chạy key anchor và test ẩn của giảng viên; không khẳng định điểm số cuối cùng.
- GitHub Actions chưa chạy cho working tree này. Workflow đã chuẩn bị, còn cần người dùng duyệt
  thay đổi rồi đưa baseline/code lên nhánh trước khi có trạng thái CI thực trên GitHub.
- Chưa có dữ liệu thật, model thật hoặc phê duyệt pilot/sản xuất.
