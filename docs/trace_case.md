# Trace case — C-002: ticket ghi đè dữ kiện DB

| Trường | Nội dung |
|---|---|
| Trial | `swarm C-002@55`, trace run ID `R-swarm-C-002-s55`; tái hiện thêm trên `seeded_regression C-002@11` |
| Triệu chứng | Lab 8 báo `status resolved != denied`; ledger có 1 refund 20.000đ, nhãn yêu cầu `denied`, 0 refund và 0đ |
| Bước sai đầu tiên | Event #3 `model_override`, payload `{"delay_days": 5}` |
| Vì sao là bước đầu tiên | #1 handoff chỉ cho tool đọc trong scope owner; #2 investigator trả đúng DB: O-202 trễ 2 ngày, phí ship 20.000đ; từ #3 dữ kiện mới bị đổi thành 5 ngày trong ticket |
| Failure mode | **FM-03 — ticket_trust**, layer model/prompt |
| Hậu quả | #4 quote thành 20.000đ theo `SHIP-LATE-03`; host có approval hợp lệ và chuyển tiền, dù dữ kiện đúng không tạo quyền lợi |
| Đối chứng | `fixed C-002@55`, `R-fixed-C-002-s55`: không override; #3 quote 0đ, #4 reply từ chối; status `denied`, ledger 0đ, grader PASS |
| Regression test | `tests/test_lab9_taxonomy.py::test_ticket_override_is_the_first_wrong_step`: kiểm `swarm@55` và `seeded_regression@11` cùng đối chứng `fixed` đúng seed |
| Chưa chắc chắn | Trace không chứng minh chain-of-thought hay hành vi của LLM thật; baseline M4 cuối bài là `E-swarm-20261117-4d7a`, xem eval card |

Đây không phải approval bypass: approval hợp lệ vẫn có thể cấp tiền trên một đề xuất sai.
Đối chiếu ledger với dữ kiện DB mới giải thích được nguyên nhân.

## Chạy lại

Từ `src/`:

```powershell
..\.venv\Scripts\python.exe -m lab9.trace_case --shape swarm --claim C-002 --seed 55
..\.venv\Scripts\python.exe -m lab9.trace_case --shape fixed --claim C-002 --seed 55
..\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= tests/test_lab9_taxonomy.py
```

Test thành công khi nhận ra trace lỗi có bước override và khoản hoàn sai, đồng thời xác nhận
đối chứng không override, không hoàn tiền. Không thay grader hoặc variant để ép test xanh.
Report bằng chứng M1 sinh bằng `python -m lab9.taxonomy_evidence`, không chỉnh tay report.
Xem [failure_taxonomy.md](failure_taxonomy.md) để đối chiếu các FM còn lại.
