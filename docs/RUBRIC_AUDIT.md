# Kiểm tra rubric, báo cáo và biểu mẫu gốc

## Kết luận

**Chưa đủ cơ sở xác nhận 100/100.** Bài làm đã triển khai toàn bộ phần local của M0–M7 và qua bộ
kiểm tra công khai, nhưng rubric còn yêu cầu CI thực trên GitHub, đối chiếu anchor và các variant/trap ẩn.
Không cộng số test PASS để suy ra điểm, cũng không tự chấm các mục phụ thuộc bộ chấm chưa có.

Lượt kiểm tra tổng thể `V-20261117-175743`: 32 bước đúng exit code mong đợi,
85 test Lab 09 PASS, scorecard 3/3 và 0 false alarm, 4 trap public bị chặn, A/A Δ=0.
Trong lượt rà soát bổ sung, 85 test Lab 09 được chạy lại và vẫn PASS.

## Core — tối đa 60 điểm

| Tiêu chí | Điểm tối đa | Bằng chứng hiện có | Phần chưa thể xác nhận |
|---|---|---|---|
| M1 Taxonomy + eval set | 12 | 8 FM có trace lỗi, coding sheet, provenance, eval set sạch | 5 anchor cần key giảng viên |
| M2 Calibration | 12 | Tone κ=0.757/P=0.857/R=0.8; helpful bị loại; audit 16 case | Đã có bằng chứng công khai; chưa phải điểm do giảng viên chấm |
| M3 Trajectory | 12 | Hai grader, metric FM-08, detection 100%, false alarm 0% | Đã đạt mốc kiểm tra công khai |
| M4 Bootstrap + gate | 15 | Δ pass_rate −0.2714, CI [−0.5000, −0.0571]; fixed qua, seeded bị chặn; harness có eval | Job eval-gate chưa có trạng thái xanh trên GitHub |
| Eval card + PRD v1.1 | 9 | Đủ số liệu, run ID/SHA, CI, phạm vi và giới hạn | Đủ nội dung local; sinh viên kiểm tra bản bàn giao |

## Advanced — tối đa 25 điểm

| Tiêu chí | Điểm tối đa | Bằng chứng hiện có | Phần chưa thể xác nhận |
|---|---|---|---|
| pass_at_k/pass_hat_k | 5 | Vector công khai và input sai đều qua test | Vector ẩn chưa chạy |
| fm_map + eval set v2 | 6 | 8 cơ chế map FM, 28 item, mỗi FM bị tấn công ≥3 item; 0 problem | Chờ đánh giá chính thức về mapping |
| Spec v2 | 4 | pass_hat_5 blocking min=0.80; money_movement/adversarial blocking | Cấu hình đã kiểm tra tại máy |
| Slice regression | 6 | Public slice bị chặn; có test slice tên mới ngoài starter | Slice regression ẩn chưa chạy |
| FM-08 ẩn | 2 | Diagnostic reply sai tiền bị phát hiện; ledger đúng vẫn bắt lỗi reply | Variant FM-08 ẩn chưa chạy; phạm vi parser đã nêu trong eval card |
| Không báo nhầm | 2 | fixed và honest_refactor được merge | Refactor trung thực ẩn chưa chạy |

## Expert — tối đa 15 điểm

| Tiêu chí | Điểm tối đa | Bằng chứng hiện có | Phần chưa thể xác nhận |
|---|---|---|---|
| Integrity/ratchet | 9 | 4/4 trap public bị chặn bằng INTEGRITY; có test dòng trùng, grader error và relabel slice | 2 trap ẩn chưa chạy |
| Stability và điều kiện kèm theo | 6 | flaky bị chặn; test quiet_override; baseline tự so qua; A/A 15 metric Δ=0; sàn 0.80 | Variant ẩn chưa chạy; điểm còn nhân tỷ lệ trap bị chặn |

## Báo cáo và trường thông tin trong mẫu gốc

Đã rà 25 file Markdown thuộc hồ sơ Git/working tree; loại `.venv`, `.git` và cache runtime khỏi phạm vi.
10 file báo cáo/bằng chứng không còn ô bảng rỗng hoặc placeholder cần điền.
Chỉ điền tên ở trường mà repo gốc có yêu cầu: Gate owner trong `docs/eval_card.md`,
Người xử lý và bảng phê duyệt Product/Eval owner trong `docs/PRD_v1.1.md`.
Repo gốc không có trường MSSV hoặc khối hồ sơ sinh viên trong các tài liệu này, nên không tự thêm.
Đối chiếu mẫu tại commit starter `d1b9471`; ngày phê duyệt chưa có nên ghi đúng trạng thái chưa phê duyệt.

| File | Loại | Kết quả rà |
|---|---|---|
| [CHECKPOINTS.md](../CHECKPOINTS.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [README.md](../README.md) | Trang bài làm/checklist/mục lục | Không tự thêm thông tin sinh viên; trạng thái nộp ghi đúng thực tế |
| [RUBRIC.md](../RUBRIC.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [SUBMISSION.md](../SUBMISSION.md) | Trang bài làm/checklist/mục lục | Không tự thêm thông tin sinh viên; trạng thái nộp ghi đúng thực tế |
| [docs/PRD_v1.1.md](../docs/PRD_v1.1.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; thông tin người phụ trách chỉ ở trường mẫu gốc |
| [docs/PR_DESCRIPTION.md](../docs/PR_DESCRIPTION.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/README.md](../docs/README.md) | Trang bài làm/checklist/mục lục | Không tự thêm thông tin sinh viên; trạng thái nộp ghi đúng thực tế |
| [docs/REVIEW_LAB09.md](../docs/REVIEW_LAB09.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/RUBRIC_AUDIT.md](RUBRIC_AUDIT.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/architecture.md](../docs/architecture.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/bonus_topics.md](../docs/bonus_topics.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/business_rules.md](../docs/business_rules.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/contracts.md](../docs/contracts.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/eval_card.md](../docs/eval_card.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; thông tin người phụ trách chỉ ở trường mẫu gốc |
| [docs/failure_taxonomy.md](../docs/failure_taxonomy.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/instructor.md](../docs/instructor.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/judge_audit.md](../docs/judge_audit.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/m0_setup.md](../docs/m0_setup.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/metrics.md](../docs/metrics.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [docs/trace_case.md](../docs/trace_case.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |
| [docs/troubleshooting.md](../docs/troubleshooting.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [src/README.md](../src/README.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [src/eval/README.md](../src/eval/README.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [src/grader_audit/README.md](../src/grader_audit/README.md) | Đề hoặc tài liệu tham khảo kế thừa | Không phải mẫu báo cáo cần điền thông tin sinh viên |
| [src/reports/README.md](../src/reports/README.md) | Báo cáo/bằng chứng bài làm | Đã điền nội dung; không thêm hồ sơ sinh viên |

Các ký hiệu đường dẫn mẫu và chỉ dẫn viết bài trong tài liệu gốc của giảng viên được giữ làm ví dụ,
không thay bằng dữ liệu giả và không coi là báo cáo sinh viên bị bỏ sót.

Các trạng thái “chờ kiểm tra”, “chưa phê duyệt pilot/sản xuất”, “chưa chạy bộ chấm ẩn” là trạng thái
thực tế. Chúng không phải phần bị quên điền; không ký phê duyệt release hoặc tự ghi ngày duyệt.

## Các thiếu sót đã sửa trong lượt rà soát

1. Gỡ các khối tên/MSSV/lớp tự thêm ngoài mẫu; generator chỉ điền tên tại các trường người phụ trách của mẫu gốc.
2. Cập nhật checklist [SUBMISSION.md](../SUBMISSION.md): đánh dấu phần đã có bằng chứng, giữ mở đúng các tác vụ GitHub/ẩn.
3. Sửa link kế thừa sang TEAM/RULES/group report của Lab 08 không tồn tại trong repo Lab 09.
4. Bổ sung [README báo cáo](../src/reports/README.md) và allowlist Git cho baseline/report cần nộp;
   không stage/commit, vẫn ignore trace thô, SQLite, trap runtime và môi trường Python.
5. Sửa phạm vi chọn test của job Lab 08 thành `swarm and not lab9`:
   job chỉ cài dependency Lab 08, còn toàn bộ test Lab 09 chạy trong job riêng.
   Đã kiểm bằng môi trường Lab 08 không cài pydantic-evals: 62 test swarm PASS.
6. Cập nhật các ghi chú lịch sử M0/M1/M2 để phân biệt kết quả từng mốc và trạng thái đã hoàn thiện cuối bài.

## Việc còn cần để chốt bài nộp/điểm

- Đưa code và artifact cần nộp lên nhánh GitHub, mở PR và có hai job `eval-gate`, `eval-gate-v2` xanh.
  Đây là việc còn lại theo yêu cầu nộp, hiện chưa làm vì sinh viên yêu cầu không commit.
- Giảng viên đối chiếu 5 anchor và chạy bộ chấm ẩn; sau đó mới xác nhận điểm 100 hoặc phần bị trừ.
- Bảo đảm commit/PR đúng hạn của lớp; báo cáo local không tự chứng minh đã nộp trước deadline.

Không có yêu cầu Lab 09 bắt buộc `TEAM.md`, báo cáo nhóm/cá nhân theo mẫu Lab 08 hoặc thêm báo cáo bonus
Inspect AI/DeepEval. Bonus tối đa +5 là tùy chọn, không phải điều kiện bắt buộc để đạt trần 100 của rubric chính.
Không cần dữ liệu người dùng thật hoặc chữ ký duyệt sản xuất để hoàn thành bài mô phỏng này.

Nguồn đối chiếu: [rubric gốc](../RUBRIC.md), [checkpoints](../CHECKPOINTS.md),
[eval card](eval_card.md), [summary kiểm chứng](../src/reports/verification_summary.json).
