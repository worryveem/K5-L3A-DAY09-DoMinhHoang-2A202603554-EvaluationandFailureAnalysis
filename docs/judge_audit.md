# Judge audit — M2

Ngày kiểm tra: 17/11/2026. Backend là **replay**: đọc verdict có sẵn trong CSV, không gọi LLM/API.
Lớp dương là **FAIL**: mục tiêu của judge là tìm lỗi. Tính trên nguyên bản nhãn public,
chưa thay nhãn hoặc verdict nào sau audit.

## Kết quả calibration

| Tiêu chí | n | κ | Precision | Recall | Floors κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | PASS cả ba | Dùng cho tone trong phạm vi dữ liệu replay đã kiểm |
| helpful | 100 | 0.375 | 1.000 | 0.300 | FAIL κ và Recall | Loại khỏi gate |

| Tiêu chí | TP | FP | FN | TN | Tỉ lệ FAIL judge quan sát | Tỉ lệ FAIL sau Rogan–Gladen |
|---|---:|---:|---:|---:|---:|---:|
| tone_ok | 24 | 4 | 6 | 66 | 0.280 | 0.300 |
| helpful | 9 | 0 | 21 | 70 | 0.090 | 0.300 |

TP là người FAIL/judge FAIL, FP là người PASS/judge FAIL, FN là người FAIL/judge PASS,
TN là cả hai PASS. Mọi số đo được tính trước khi làm tròn; chỉ giá trị hiển thị làm tròn 3 chữ số.
Một judge có Precision thực 0.7996 vẫn phải FAIL sàn 0.8 dù hiển thị thành 0.800.

Rogan–Gladen dùng `(p_obs + specificity - 1) / (sensitivity + specificity - 1)`, clip về [0, 1].
Tone có sensitivity=24/30=0.8, specificity=66/70; helpful có sensitivity=9/30=0.3,
specificity=70/70=1. Cả hai khôi phục tỉ lệ lỗi 30% của chính tập calibration.
Đây không phải bằng chứng judge helpful đã tốt: hiệu chỉnh prevalence không sửa 21 verdict bị bỏ sót,
và ước lượng sensitivity/specificity từ cùng tập dữ liệu chưa kiểm chứng trên held-out.

## Audit các bất đồng

Bảng dưới là phân tích của trợ lý dựa trên reply, nhãn và note trong CSV public, chưa phải lượt
adjudication độc lập của người dùng. Số tiền ledger của các case HL lấy từ **note của CSV**;
CSV không cung cấp ledger/ticket gốc để xác minh lại. Không gán các order này sang claim Lab 08
chỉ vì trùng mã đơn.

| # | Case / tiêu chí | Judge nói | Người nói | Ai đúng theo bằng chứng hiện có? | Cơ sở và hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | H-008 / tone | PASS | FAIL | Người, theo rubric CS trong note | “Em… nha… anh check” quá suồng sã. Quy định xưng hô và từ kết câu bằng ví dụ PASS/FAIL; thân thiện không tự đồng nghĩa phù hợp. |
| 2 | H-017 / tone | PASS | FAIL | Người theo note; tuổi khách cần metadata | “Bạn ơi… nha” không phù hợp ngữ cảnh khách lớn tuổi nêu trong note. Cấp context xưng hô hoặc dùng cách gọi chuẩn “anh/chị”; không tự suy tuổi từ reply. |
| 3 | H-029 / tone | PASS | FAIL | Người | “Không cần nhắn thêm” mang giọng ra lệnh. Chấm toàn câu, không cộng điểm chỉ vì có “Dạ, vui lòng”; thêm ví dụ mở đầu lịch sự nhưng phần sau gây áp lực. |
| 4 | H-042 / tone | FAIL | PASS | Người | Câu ngắn vẫn lịch sự và đủ ý. Không bắt buộc xin lỗi trong mọi reply; đánh giá mức phù hợp theo ngữ cảnh. |
| 5 | H-051 / tone | FAIL | PASS | Người theo chính sách CS trong note | “Refund” được LogiX cho phép. Thêm danh sách thuật ngữ cho phép; không đánh FAIL chỉ vì một từ tiếng Anh. |
| 6 | H-063 / tone | PASS | FAIL | Người theo rubric dataset | “Sẽ hoàn thêm” là cam kết ngoài kết quả hệ thống. Nêu rõ cấm hứa không có bằng chứng; tách kiểm factual/tiền bằng code khỏi phần lịch sự. |
| 7 | H-070 / tone | PASS | FAIL | Người theo ngữ cảnh khiếu nại | Emoji cười không phù hợp khi thông báo xử lý khiếu nại. Ghi rõ nhóm emoji và ngữ cảnh bị cấm thay vì chỉ chấm từ xưng hô. |
| 8 | H-081 / tone | FAIL | PASS | Theo note: judge đúng, nhãn người sai; chưa xác minh độc lập | Note nói người đọc nhầm ticket, nhưng không có ticket gốc. Đưa vào danh sách adjudication; kiểm lại tiêu chí tone so với helpful/factual, xin nhãn người thứ hai trước khi đổi nhãn. |
| 9 | H-088 / tone | FAIL | PASS | Người theo mức dung sai trong note | Lặp “Dạ” do lỗi gõ không đủ để kết luận bất lịch sự. Cho phép lỗi gõ nhỏ không đổi nghĩa/tone; tách lỗi trình bày khỏi lỗi nghiêm trọng. |
| 10 | H-094 / tone | PASS | FAIL | Người theo yêu cầu tiếng Việt trong dataset | Reply mất dấu gần như toàn bộ. Ghi rõ yêu cầu ngôn ngữ của kênh CS và ví dụ lỗi diện rộng; không tự áp quy tắc này cho mọi sản phẩm khác. |
| 11 | HL-015 / helpful | PASS | FAIL | Người theo note ledger | Reply nói 55.000đ, note ghi ledger 40.000đ. Chặn bằng phép so reply–ledger của FM-08; câu ngắn gọn không bù được sai tiền. |
| 12 | HL-016 / helpful | PASS | FAIL | Người theo note ledger | Reply nói 55.000đ, ledger 35.000đ dù xin lỗi dài. Thêm cặp ví dụ cùng lỗi, một câu ngắn và một câu dài; cả hai đều FAIL. |
| 13 | HL-020 / helpful | PASS | FAIL | Người theo note ledger | Reply nói 90.000đ, ledger 120.000đ. Kiểm cả báo cao lẫn báo thấp bằng số nguyên VND, không chấm mức “có vẻ hợp lý”. |
| 14 | HL-028 / helpful | PASS | FAIL | Người theo note ledger | Reply 50.000đ, ledger 35.000đ; lời xin lỗi bị lặp. Kiểm facts trước, không dùng độ dài hoặc số lần xin lỗi làm bằng chứng hữu ích. |
| 15 | HL-035 / helpful | PASS | FAIL | Người theo note ledger | Reply 50.000đ, ledger 35.000đ. Không cho lời cảm ơn/lời mời ủng hộ bù cho lỗi tiền; route phép kiểm tiền sang code. |
| 16 | HL-047 / helpful | PASS | FAIL | Người theo rubric xưng hô | “Ok bạn… nhé” không đạt chuẩn CS của dataset. Đánh tone riêng, không lấy việc có nhắc trạng thái đơn làm PASS cho toàn bộ helpful. |

Các thay đổi rubric trên là đề xuất cho phiên bản judge/rubric tiếp theo, không giả định CSV replay
sẽ đổi verdict khi sửa văn bản này. H-081 được ghi nhận để rà nhãn, **chưa sửa CSV public**;
đổi nhãn hoặc rubric phải tăng phiên bản và chạy lại calibration.

## Quyết định sử dụng

- **tone_ok dùng được trong phạm vi calibration này:** κ=0.757, P=0.857, R=0.8 đạt floors;
  vẫn có 6 FN và 4 FP so với nhãn public, cần duy trì audit và kiểm nhãn đáng ngờ.
- **helpful không được dùng làm gate:** Precision 1.0 chỉ cho biết 9 lần judge báo lỗi đều đúng;
  judge bỏ sót 21/30 lỗi, tức 70% lỗi thực tế trong tập nhãn. κ=0.375 và R=0.3 không đạt sàn.
  Accuracy 79% hoặc việc hiệu chỉnh tỉ lệ lỗi về 30% không thay thế các điều kiện này.
- Tiền, approval và ledger luôn chấm bằng code. Tone PASS không chứng minh đã hoàn tiền đúng;
  helpful FAIL không phải lý do để hạ floors cho judge.
- Kappa không xác định (`p_e=1`) phải FAIL calibration, lưu `null` kèm lý do.
  Rogan–Gladen không xác định hoặc không đủ tín hiệu (`sensitivity + specificity <= 1`)
  cũng lưu `null`, không biến thành một ước lượng lỗi bằng 0.

## Tái lập và bằng chứng

Chạy từ `src/`:

```powershell
..\.venv\Scripts\python.exe -m lab9.judge --csv data/eval/judge_tone_public.csv --audit 10 --out reports/judge_tone_calibration.json
..\.venv\Scripts\python.exe -m lab9.judge --csv data/eval/judge_helpful_public.csv --audit 5 --out reports/judge_helpful_calibration.json
..\.venv\Scripts\python.exe -m pytest -q -m student -o addopts= tests/test_lab9_stats.py tests/test_lab9_calibration.py -k 'not paired_bootstrap'
```

Lệnh tone trả **exit 0**. Lệnh helpful trả **exit 1**, là kết quả bị loại đúng mong đợi.
Report JSON do CLI sinh, không sửa tay:
[tone](../src/reports/judge_tone_calibration.json), [helpful](../src/reports/judge_helpful_calibration.json).
Kết quả riêng M2: **17 passed, 2 deselected**. Ở lượt kiểm tra cuối bài, cả test paired bootstrap M4 đã chạy và PASS trong nhóm **85 test Lab 09**.

Giới hạn: 100 dòng/tiêu chí đều là public replay; không gọi model thật, không có dữ liệu người dùng mới,
không phải held-out độc lập. Chưa coi các đề xuất sửa rubric hoặc nhãn là đã được kiểm chứng lại.
Các thay đổi M2 được giữ ở working tree theo yêu cầu, chưa commit.
