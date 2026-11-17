# Dành cho giảng viên

Học viên không cần đọc file này. Mọi đường dẫn và lệnh dưới đây tính từ thư mục `src/`.

- **Pack hidden không có trong git.** Thư mục `src/eval/instructor/` bị `.gitignore` chặn và chỉ có trên máy soạn bài. Giữ một bản sao ở kho lưu trữ riêng của khóa học, không đẩy lên repo này. Cần tạo lại thì đặt `generate_hidden.py` vào `eval/instructor/`, rồi chạy `python scripts/build_public_fixtures.py` và `python eval/instructor/generate_hidden.py`. Quy trình chi tiết nằm trong `eval/instructor/README_GIANG_VIEN.md`.
- **16:15 phát cho học viên:** chỉ copy `eval/instructor/student_drop/` (claim không nhãn và world state). Không gửi `hidden_labels.json`, `hidden_claims.jsonl` bản đầy đủ, hay `generate_hidden.py`.
- **Chấm chính thức:** chạy bằng grader riêng của giảng viên (repo chấm riêng của giảng viên), không còn nằm trong repo này. Grader nhận bản lab sạch, repo nhóm, pack hidden, danh sách shape, seed và `--extra-shape` cho biến thể bonus. Grader chép nguyên `src` chính thức rồi chỉ phủ lên `src/lab8/shapes/workflow.py`, `single.py`, `orchestrator.py` và `src/bonus/` của nhóm; file khác bị sửa thì bị bỏ qua và ghi vào danh sách tampered. Nhãn không bao giờ đưa vào code học viên, mọi trial (kể cả crash) đều qua leak scan, và bypass tính cả refund ghi dưới claim khác. Crash suite vẫn chạy trong repo này:

  ```text
  python -m lab8.crash_test --count 20 --out reports/crash.json
  ```

  Gate: shape nhóm chọn có pass rate ≥ 0.75 trên 200 trial (≥ 0.80 nếu muốn nhận điểm cộng); `secret_leak_count`, `pii_leak_count`, `approval_bypass_count` bằng 0; crash 20/20. Lưu ý `crash_test` kiểm host và swarm. Crash của shape nhóm được kiểm qua T12 trong ma trận student.
- **Đối chứng mong đợi:** swarm trên hidden ra pass 0.97, pass^5 0.85, chỉ fail ở seed 55. Một workflow đúng ra 1.0 / 1.0.
- **Grader chống ghi lén:** trial fail với lý do `unexpected_ledger_rows` nếu ledger có dòng không thuộc claim đang chấm và không phải refund lịch sử đã seed. Shape không thể ghi tiền dưới claim id khác mà lọt.
- **Chấm bonus:** quy trình 10 phút mỗi nhóm ở cuối `docs/bonus_topics.md`. Biến thể bonus chấm trên hidden bằng cờ `--extra-shape`.
- **Chấm nhiều nhóm:** chạy grader riêng lần lượt cho từng repo nhóm, trỏ `--pack` tới pack của giảng viên bằng đường dẫn tuyệt đối. Shape được chấm cổng hidden lấy từ dòng `- Shape chọn:` trong `report/team/decision_adr.md`. Một shape ném exception chỉ làm fail trial của shape đó, các shape khác vẫn được chấm.
- **CI:** `.github/workflows/ci.yml` (working directory `src/`) chạy smoke, pytest, crash suite và benchmark swarm trên Ubuntu, Windows, macOS × Python 3.11 và 3.13. Push lên GitHub là thấy kết quả trên cả 3 hệ điều hành.
