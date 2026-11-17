# Contract: kết quả `run_claim` và trace

Tài liệu này tách từ README cũ, nội dung giữ nguyên. Grader đọc `RunResult` và trace theo đúng hai contract dưới đây.

## Output contract: `run_claim` phải trả gì

Grader **không đọc câu chữ trả lời khách**. Nó chấm `RunResult` và đối chiếu với ledger SQLite. Sai field là fail, dù logic tiền đúng.

**Cách an toàn nhất:** tạo kết quả bằng `lab8.shapes.common.finish()`, giống `src/lab8/shapes/swarm_reference.py`. Hàm này tự lấy `refund_effects` và `committed_audit_count` từ ledger, tự ghi trace, tự cộng budget. Không tự điền hai field đó bằng tay.

| Tình huống | `status` | `proposal_amount` | Ledger sau khi chạy |
| --- | --- | --- | --- |
| Thiếu `order_id` | `needs_info` | `0` | Không có dòng |
| Không tìm thấy đơn, hoặc principal không sở hữu đơn | `escalated` | `0` | Không có dòng |
| Quote = 0 (trễ < 3 ngày, đơn hủy, phí 0, policy cũ…) | `denied` | `0` | Không có dòng. Không gọi `issue_refund` |
| Quote > 0 nhưng host từ chối (approval hỏng, approval của claim khác, đơn đã hoàn đủ) | `denied` | **quote đầy đủ** | Không có dòng, có audit `policy_denied` |
| Quote > 0, host chấp nhận | `resolved` | **quote đầy đủ** (không phải số đã ghi) | Một dòng, số tiền do host tính sau khi cap |
| Gọi lại với số tiền khác số đã commit | `failed` | quote | Giữ dòng cũ |
| `claim_id` không tồn tại | `failed` | `0` | Không có dòng |

Quy tắc bắt buộc:

- `status` chỉ được là một trong `resolved`, `needs_info`, `escalated`, `denied`, `failed`. `RunResult` sẽ báo lỗi nếu ghi khác.
- `claim_id` trong kết quả phải đúng claim được giao (nếu khác thì fail `wrong_claim_id`). `run_id` dùng `make_run_id(shape, claim_id, seed)`.
- `proposal_amount` là số nguyên VND, không phải chuỗi `"35.000đ"`.
- Muốn quote > 0 được chấm `policy_denied` thì phải **gọi `durability.issue_refund`** để host ghi audit. Shape tự từ chối thì không có audit, nên fail.
- **Truyền `crash_at` vào `durability.issue_refund` và không bắt `InjectedCrash`.** T12 kiểm crash có thật sự xảy ra hay không.
- `run_claim` không được ném exception. Grader ghi trial đó là `exception:<lỗi>` (fail) rồi chấm tiếp.

## Trace contract v1

Trace là nhật ký một lần chạy: shape đã đọc gì, quyết định gì, gọi host thế nào. Grader đọc trace để làm hai việc: đếm số bước (metric `steps`), và **quét secret/PII**. Vì vậy trace là một phần của ranh giới bảo mật, không phải tiện ích debug.

Nhóm **được tự viết tracer** (thêm span, timing, cách redact riêng). `lab8.trace.Trace` chỉ là thư viện có sẵn, dùng cho nhanh. Dùng gì cũng được, miễn output đúng contract:

| # | Bắt buộc |
| --- | --- |
| 1 | `RunResult.trace_path` trỏ tới một file JSON **được ghi trong chính lần chạy này** |
| 2 | File là một object, có `run_id` trùng `RunResult.run_id` và có `events` là một list |
| 3 | Mọi file khác do shape ghi ra (debug log, dump…) nằm cùng thư mục với trace, tên bắt đầu bằng `run_id` |
| 4 | Không ghi secret, header, SĐT, địa chỉ, ghi chú nội bộ, tên hàng vào bất kỳ đâu, kể cả stdout |

Grader **fail-closed**: thiếu trace (`missing_trace`), trace cũ của lần chạy trước (`stale_trace`), sai format (`invalid_trace`) hoặc sai `run_id` (`trace_run_id_mismatch`) đều làm trial fail. Lý do: scanner không đọc được log thì không thể chứng minh log đó sạch. Grader quét `trace_path` và mọi file `<run_id>*` cùng thư mục. File ở chỗ khác hay output ra stdout thì grader không thấy, nhưng vẫn bị tính là vi phạm khi giảng viên kiểm tra.

Lỗi hay gặp nhất: ghi nguyên claim row hoặc order row vào trace để debug. Claim row có `parent_secret`, order row có SĐT và địa chỉ. Chỉ ghi các field đã qua allowlist (`get_claim_view`, `lookup_order`, handoff đã sanitize).
