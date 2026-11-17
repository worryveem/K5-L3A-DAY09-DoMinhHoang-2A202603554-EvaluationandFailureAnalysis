# M0 — Thiết lập Lab 09

Lab 09 được tích hợp trong repo cá nhân hiện tại, trên nhánh `starter/d09`.

## Nguồn Lab 08

- Thư mục: `D:\LAB_AI\K5-L3A-Day08-NhomV3-FromWorkflowsToAgents`
- Commit nguồn: `e5d9601a49efe58c9318f241a605a76d0d1c5fa9`
- Chép các file được Git theo dõi trong `src/`, `docs/`, `.github/`, trừ `src/reports/`.
- Giữ nguyên nội dung package `src/lab8/`; giữ các file Lab 09 đã có.
- Bổ sung quy tắc ignore của Lab 08 cho `.env`, `.venv`, cache, SQLite và dữ liệu instructor.

## Chạy trên Windows PowerShell

Từ thư mục gốc repo, tạo môi trường và cài dependency nếu chưa có:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r src/requirements.txt -r src/requirements-lab9.txt
```

Chạy các lệnh lab trong `src/`. Dùng trực tiếp Python của môi trường để không cần đổi ExecutionPolicy:

```powershell
Set-Location src
..\.venv\Scripts\python.exe -m lab9.smoke
..\.venv\Scripts\python.exe -m lab9.evalset --build
..\.venv\Scripts\python.exe -m pytest -q tests/test_lab9_evalset.py
```

M0 đạt khi smoke in `M0 PASS`, build sinh 14 item trong
`src/data/eval/eval_set_v1.jsonl` và 14 nhãn trong `src/data/eval/labels_v1.json`,
cả hai lệnh trả exit 0. Nhãn nằm riêng, không nằm trong item.

`failure_modes` còn rỗng ở M0 theo đúng starter. Lệnh `lab9.evalset --check`
chỉ cần đạt sau khi hoàn thành taxonomy và gắn mã lỗi ở M1.

## Kết quả kiểm tra ngày 17/11/2026

- Python 3.13.7; dependency cài trong `.venv/`.
- `python -m lab9.smoke`: `M0 PASS`, exit 0.
- `python -m lab9.evalset --build`: 14 item, 14 nhãn, exit 0.
- Kiểm tra dữ liệu: claim ID khớp giữa item và nhãn, không có nhãn inline.
- `python -m lab8.smoke`: `lab8.smoke pass`, exit 0.
- `python -m pytest -q tests/test_lab9_evalset.py`: `3 passed`.
- `python -m pip check`: `No broken requirements found`.
- So sánh SHA256: 28/28 file trong `src/lab8/` giống hệt thư mục nguồn.
