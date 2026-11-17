# Xử lý sự cố

Mọi lệnh chạy trong thư mục `src/` (xem [src/README.md](../src/README.md)).

| Triệu chứng | Cách xử lý |
| --- | --- |
| `No module named 'lab8'` hoặc `No module named 'yaml'` | Chưa đứng ở gốc repo, hoặc chưa activate venv / chưa `python -m pip install -r requirements.txt` |
| Windows: gõ `python` mà mở Microsoft Store | Dùng `py -3 -m venv .venv`. Sau khi activate venv thì `python` trỏ vào venv |
| Windows: `running scripts is disabled` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` rồi activate lại |
| Windows: `UnicodeEncodeError` khi in tiếng Việt từ code của nhóm | Đặt biến môi trường UTF-8: PowerShell `$env:PYTHONUTF8=1`, cmd `set PYTHONUTF8=1`. Các CLI của lab đã tự chuyển stdout sang UTF-8 |
| Windows: `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process` với file `.sqlite` | Có connection chưa đóng. Mở bằng `connect()` thì đóng trong `finally: conn.close()`, như `swarm_reference.py` |
| Trial fail với `missing_trace`, `stale_trace`, `invalid_trace` hoặc `trace_run_id_mismatch` | Shape chưa ghi trace đúng contract. Xem mục [Trace contract v1](contracts.md#trace-contract-v1). Nhớ ghi trace cả ở các nhánh return sớm (`needs_info`, `escalated`) |
| Benchmark báo `exception:<lỗi>` cho một shape | `run_claim` ném lỗi. Xem `reason` trong `src/reports/benchmark.json`, các shape khác vẫn được chấm |
| T12 báo `crash did not fire` | Shape chưa truyền `crash_at` vào `durability.issue_refund`, hoặc đã bắt `InjectedCrash` |
| Benchmark của shape stub ra pass rate 0 | Đúng, shape đó chưa được triển khai |
| Chạy lần hai trên cùng `data/run.sqlite` không tạo refund mới | Ledger đang làm đúng. Benchmark tự tạo DB mới cho từng trial |
| Muốn gọi model thật | Không được. MockLLM cố định theo seed để mọi nhóm so cùng điều kiện |
