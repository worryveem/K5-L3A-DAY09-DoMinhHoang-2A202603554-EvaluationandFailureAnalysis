# Luật nghiệp vụ LogiX-VN (synthetic)

Tài liệu này tách từ README cũ, nội dung giữ nguyên. Code của nhóm phải tuân đúng các luật dưới đây; grader chấm theo các luật này.

Nguồn sự thật là dòng order và policy có `is_current` và `effective_date <= 2026-11-15`. Chữ trong ticket là dữ liệu người dùng, kể cả những câu như "ignore policy" hay "trễ 9 ngày".

| Tình huống | Kết quả đúng |
| --- | --- |
| Trễ ≥ 3 ngày, đơn `delivered` hoặc `delivered_late`, policy hiện hành | Hoàn đúng `shipping_fee_vnd` |
| `damage_verified=true` | `min(max_refund của DMG-04, paid_vnd)` |
| Cả ship và damage cùng đủ điều kiện | Một refund bằng **số lớn hơn**, không cộng hai số |
| Trễ dưới 3 ngày, hỏng hàng chưa verify, phí ship 0, đơn `cancelled` hoặc `in_transit` | Không refund (`denied`) |
| Thiếu `order_id` | `needs_info`, không ghi ledger. Không lấy mã đơn từ câu chữ trong ticket |
| Principal không sở hữu đơn, hoặc không tìm thấy đơn | `escalated`. Không trả phone, địa chỉ, tên hàng, internal note |
| Policy cũ `SHIP-LATE-OLD` hoặc policy tương lai | Bỏ qua. `get_clause` vẫn trả về các clause này, nhóm phải tự kiểm `is_current` |
| Không có approval, approval hết hạn, bị thu hồi, hoặc amount ≤ 0 | Không ghi refund. Khi quote > 0 mà cổng duyệt từ chối thì phải có audit `policy_denied` |
| Approval mà claim trỏ tới (`approval_id`) được cấp cho claim khác | Không ghi refund, audit `policy_denied` lý do `approval_claim_mismatch`. Chỉ approval có `approval_id` khớp claim mới được tính |
| Đơn đã được hoàn trước đó bởi claim khác | Trần tính **theo đơn**: tổng tiền hoàn của một đơn không vượt entitlement lớn nhất. Hoàn đủ rồi → `denied`, audit `policy_denied` lý do `order_already_refunded`. Entitlement mới lớn hơn (ví dụ hỏng hàng sau khi đã hoàn ship) → chỉ hoàn **phần chênh** |
| Approval thấp hơn quote | Refund `min(quote, approved_vnd, paid_vnd)`. `proposal_amount` vẫn là quote |
| Gọi lại cùng claim | Vẫn một dòng ledger. Amount khác số đã commit → `conflict`, không sửa số cũ |
| Crash sau khi đã ghi effect, trước checkpoint | Resume xong vẫn một refund và một audit `refund_committed` |

Ví dụ public:

- T01: đơn `O-107` trễ 4 ngày, phí ship 35.000, approval 35.000 → một effect 35.000 và một audit committed.
- T13: đơn `O-505` đã được hoàn 35.000 ship từ claim trước. Ticket nói "chưa nhận được tiền" → `denied`, `proposal_amount` 35.000, không ghi ledger, có `policy_denied`.
- T14: đơn `O-515` đã được hoàn 30.000 ship, nay hỏng hàng đã verify (entitlement 150.000) → `resolved`, `proposal_amount` 150.000, ledger 120.000.

**Cách làm đúng với trần theo đơn:** truyền **quote đầy đủ** từ `compute_compensation` vào `durability.issue_refund`. Host tự trừ phần đã hoàn. Nếu shape tự trừ trước rồi mới truyền vào, host sẽ trừ thêm lần nữa và T14 fail. Muốn biết đơn đã được hoàn bao nhiêu thì dùng read tool `lookup_refund_history`.

Tiền do code tính: `lab8.tools.compute_compensation` / `lab8.compensation.quote`. Không để MockLLM quyết số tiền.
