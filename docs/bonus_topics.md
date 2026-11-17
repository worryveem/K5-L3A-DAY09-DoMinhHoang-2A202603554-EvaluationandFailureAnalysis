# Điểm cộng: mở rộng theo nghiên cứu mới

Phần này không bắt buộc. Mỗi nhóm **chọn đúng 1 topic** dưới đây để lấy điểm cộng. Mỗi topic lấy từ một nghiên cứu hoặc kỹ thuật trong bài lý thuyết N8 (số slide ghi kèm). Mục đích là đưa một kết quả nghiên cứu vào LogiX-VN rồi **đo xem nó có đúng trên task của mình không**. Nói lại câu trong paper thì không có điểm.

> Architecture is a hypothesis. Benchmark is the evidence. (slide 67)

> **Đường dẫn trong file này:** mọi lệnh chạy trong thư mục `src/`. Các thư mục `bonus/`, `tests/`, `reports/`, `traces/`, `eval/` ở dưới đều nằm trong `src/`. Riêng `report/team/bonus_report.md` nằm ở gốc repo.

## Luật chung

| Luật | Chi tiết |
| --- | --- |
| Chọn 1 topic | Làm nhiều topic vẫn chỉ chấm topic tốt nhất. Muốn tự đề xuất topic khác (ví dụ MASS, ICLR 2026, slide 49) thì phải được giảng viên duyệt trước 15:30 |
| Tối đa +10 điểm | Cộng vào tổng 100 điểm của lab, tổng tối đa **110**. Điểm tính cho **cả nhóm** |
| Gate trước, bonus sau | Bonus chỉ được tính khi shape nhóm chọn: (1) qua cả 3 must-pass: không refund khi thiếu approval hợp lệ, không lộ `CANARY_SECRET_*`, crash không tạo hơn một refund; (2) đạt pass rate hidden **≥ 0.80** trên 40 × 5 trial (ngưỡng bài chính là 0.75); (3) `python -m pytest -q` vẫn xanh |
| Không sửa thước đo | Không sửa `src/lab8/metrics.py`, `src/lab8/durability.py`, `src/lab8/policy.py`, `src/config/*.yaml`, `src/data/*`. Code bonus để trong thư mục `src/bonus/` (tạo mới, có `__init__.py`). Grader riêng của giảng viên chỉ lấy từ repo nhóm 3 file shape và `src/bonus/`; sửa file khác bị bỏ qua và ghi là tampered |
| Đo cùng điều kiện | Biến thể mới chạy qua `--extra-shape` để dùng cùng claim, seed, giá và evaluator với 4 shape chính (xem bên dưới) |
| Offline | Không gọi model thật, không cần internet hay API key. Chạy được trên Windows, macOS, Linux. Chỉ dùng thư viện chuẩn của Python cộng với `requirements.txt` |
| Nhãn tự viết | Nếu tự tạo claim mới, nhãn phải viết tay theo luật nghiệp vụ trong [business_rules.md](business_rules.md). Không sinh nhãn bằng `compensation.quote`, vì như vậy là dùng chính code đang test để chấm nó |

### Chạy biến thể bonus cạnh 4 shape

Biến thể là một hàm có cùng chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult`. Đăng ký nó khi chạy, không sửa `src/lab8/shapes/__init__.py`. Lệnh chạy trong thư mục `src/`:

```bash
python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json
```

Lệnh trên chạy y hệt trên PowerShell, cmd và bash. Có thể lặp `--extra-shape` cho nhiều biến thể. Giảng viên dùng cùng cờ này trong grader riêng (repo chấm riêng của giảng viên) để chấm biến thể trên bộ hidden.

## Thang điểm chung (áp dụng cho mọi topic)

| Mức | Điểm | Cần có |
| --- | --- | --- |
| Chạy được | +3 | Code trong `bonus/`, ít nhất 2 test mới trong `tests/test_bonus_*.py`, một lệnh tái lập kết quả copy-paste được |
| Đo công bằng | +4 | So với baseline trên cùng claim × seed, số liệu lấy từ file `reports/bonus_*.json` do script sinh ra (không chép tay), báo đủ pass rate, pass^5, variance, cost/success và safety counts |
| Phân tích có giới hạn | +3 | Nêu CLAIM và BOUNDARY của nguồn. Nói rõ kết quả trên LogiX ủng hộ hay bác bỏ hypothesis, vì sao, và điều kiện nào thì kết luận đảo ngược. MockLLM là giới hạn bắt buộc phải nêu |

Nộp `report/team/bonus_report.md`, tối đa 2 trang, theo khung ở cuối file này.

---

## B1 · Investigator song song và critical path

**Nguồn:** Google Research 2026, *Towards a Science of Scaling Agent Systems*. Slide 15 (Parallelization), 24 (Graph scheduling), 33 (Latency model), 41.

**Claim của nguồn:** multi-agent chỉ có lợi khi task chia song song được. Với task tuần tự, các biến thể multi-agent trong nghiên cứu giảm 39–70%.

**Việc cần làm**

1. Viết `bonus/orchestrator_parallel.py`. Chạy song song các investigator đọc độc lập bằng `concurrent.futures.ThreadPoolExecutor`. Mỗi thread mở **connection SQLite riêng**, vì connection không được dùng chung giữa các thread. Join theo thứ tự cố định để kết quả không phụ thuộc thread nào xong trước. Chỉ có một writer.
2. MockLLM không đo latency, nên tự viết mô hình latency mô phỏng: file `bonus/latency.yaml` ghi ms cho từng tool và từng lần gọi model, có jitter cố định theo seed. Tính critical path từ DAG phụ thuộc, **không dùng `time.sleep`**.
3. So sánh orchestrator tuần tự với bản song song: critical path mean/p95, pass rate, cost/success.

**Câu phải trả lời:** bước quote phụ thuộc vào order, vậy phần nào của claims flow thực sự song song được? Speedup đo được có khớp với dự đoán của Amdahl (slide 33) không?

**Bằng chứng tối thiểu:** bảng critical path tuần tự so với song song. Pass rate và ledger không đổi. Test chứng minh kết quả giống nhau bất kể thứ tự thread hoàn thành.

## B2 · Gắn nhãn lỗi theo MAST

**Nguồn:** MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* Slide 35, 45.

**Claim của nguồn:** 14 failure mode chia làm 3 nhóm: system design, inter-agent misalignment, task verification. Taxonomy được xây bằng human annotation, κ = 0,88.

**Việc cần làm**

1. Viết `bonus/mast_tag.py`. Script đọc `reports/benchmark.json` và các file trong `traces/`, rồi gán mỗi trial fail vào một nhóm MAST (và failure mode nếu xác định được) bằng luật rõ ràng, có ghi lý do.
2. Tạo ít nhất 3 biến thể hỏng có chủ đích để kiểm tra tagger, ví dụ: handoff làm rơi `delay_days`, worker dùng clause hết hiệu lực, orchestrator bỏ bước kiểm approval rồi bị host chặn.
3. Gán nhãn tay ít nhất 15 trial fail, rồi so với tagger: báo agreement hoặc Cohen's κ (tự tính bằng thư viện chuẩn).

**Câu phải trả lời:** lỗi seed 55 của swarm thuộc nhóm nào? Mitigation nào trong slide 35 sửa đúng nhóm lỗi đó?

**Bằng chứng tối thiểu:** `reports/bonus_mast.json`, bảng số lỗi theo shape × nhóm MAST, độ khớp giữa tagger và nhãn tay.

## B3 · Verifier/aggregator chống khuếch đại lỗi

**Nguồn:** Google Research 2026, error amplification. Agent độc lập khuếch đại lỗi tới 17,2×, orchestration tập trung còn 4,4×. Slide 17 (Evaluator–optimizer), 22 (Reflection), 42.

**Việc cần làm**

1. Viết `bonus/swarm_verified.py`: giữ nguyên swarm, thêm một bước **verifier bằng code** trước khi ghi. Verifier đối chiếu mọi dữ kiện dùng để quote (`delay_days`, `status`, `damage_verified`) với order có cấu trúc. Nếu lệch thì quote lại từ dữ liệu có cấu trúc, tối đa 1 vòng sửa, và ghi sự kiện `verifier_override` vào trace.
2. Thêm ít nhất 8 claim đối kháng tự viết vào `bonus/cases.jsonl` và `bonus/world.json`, nhãn viết tay. Ví dụ: ticket nói quá, nói thiếu, nói dối hỏng hàng, nhiều con số trong một câu.
3. So sánh swarm với swarm_verified, rồi với workflow, trên public và trên bộ case tự viết.

**Câu phải trả lời:** verifier đưa swarm về gần workflow tới đâu, với cost/success bao nhiêu? Nếu verifier đã thay cả phần quyết định thì swarm còn giữ lại giá trị gì?

**Bằng chứng tối thiểu:** bảng pass rate, pass^5, variance, cost/success của 3 shape. Số lần verifier can thiệp. Một trace minh họa.

## B4 · Baseline công bằng, ablation và thống kê

**Nguồn:** EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* (slide 44, 59). AgentArch, AACL 2026 (slide 43).

**Claim của nguồn:** "efficiency gain" có thể đến từ cách thiết kế benchmark. Có lúc random pruning vẫn giữ được hiệu năng. Phải so với single-agent và baseline đơn giản, giữ cố định runtime, model và tool.

**Việc cần làm**

1. Dựng 2 baseline: rules-only (không gọi model) và "swarm pruned" (bỏ ngẫu nhiên các lần gọi peer/parse, theo seed).
2. Ablation trên shape nhóm chọn: mỗi lần bỏ một thành phần (draft model call, investigator, bước kiểm tra) và đo lại.
3. Viết `bonus/stats.py` chỉ dùng thư viện chuẩn: tính bootstrap 95% CI cho pass rate (resample theo claim), và kiểm định cặp McNemar hoặc sign test giữa hai shape trên cùng cặp (claim, seed).

**Câu phải trả lời:** chênh lệch giữa shape nhóm chọn và swarm có ý nghĩa thống kê không? Thành phần nào bỏ đi mà metric không đổi?

**Bằng chứng tối thiểu:** `reports/bonus_ablation.json`, bảng có CI, p-value, và kết luận không vượt quá dữ liệu.

## B5 · Provider idempotency và reconciliation

**Nguồn:** DBOS, *Durable Workflows and Steps* (slide 36–37). Pseudo-code slide 37: "Crash giữa ledger và provider vẫn cần cơ chế recovery."

**Việc cần làm**

1. Viết `bonus/provider.py`: một payment provider giả lập, lưu trong bảng SQLite riêng, **dedupe theo idempotency key**. Thêm một chế độ provider không dedupe để làm phản ví dụ.
2. Viết luồng hai pha `reserve → provider.refund(key) → confirm` cạnh host, **không sửa** `src/lab8/durability.py`. Thêm các điểm crash mới: `after_reserve_before_provider`, `after_provider_before_confirm`, `after_confirm_before_audit`.
3. Viết job `reconcile()` để giải quyết các reservation đang treo bằng cách hỏi lại provider.

**Câu phải trả lời:** ở crash window nào thì ledger dedupe một mình không đủ? Provider không hỗ trợ idempotency thì reconciliation cứu được tới đâu?

**Bằng chứng tối thiểu:** suite crash mới, ít nhất 10 kịch bản, kịch bản nào cũng kết thúc với đúng 1 charge ở provider và đúng 1 dòng ledger. Phản ví dụ cho thấy provider không dedupe sẽ charge 2 lần.

## B6 · Investigator từ xa theo kiểu A2A

**Nguồn:** A2A v1.0 (slide 58), ProtocolBench, ICML 2026 (slide 28, 48). Theo ProtocolBench, chỉ đổi protocol đã làm completion time chênh tới 36,5% trong một scenario.

**Việc cần làm**

1. Viết `bonus/a2a_investigator.py`. Investigator thành một "remote agent" có Agent Card (JSON: name, skills, auth scheme, phiên bản contract) và envelope message gồm `task_id`, `correlation_id`, `request_id`. Vòng đời task: `submitted → working → completed | failed`.
2. Transport viết in-process, có fault injection cố định theo seed: drop, duplicate, delay, reorder. Ai muốn thì làm thêm bản HTTP localhost bằng `http.server` của thư viện chuẩn, vẫn phải chạy offline được trên Windows.
3. Orchestrator retry theo `request_id`: message trùng không được tạo 2 kết quả. Handoff `handoff.v1` vẫn sanitize khi qua ranh giới, không gửi secret qua transport.

**Câu phải trả lời:** với LogiX, khi nào A2A đáng dùng hơn function call trong cùng process? Xét ranh giới deploy, trust, ai sở hữu agent.

**Bằng chứng tối thiểu:** bảng success rate và message overhead (số message, số byte) ở fault rate 0%, 10%, 30%, so với function call. 0 secret leak qua ranh giới. Test cho message trùng và message mất.

## B7 · Kiểm toán grader

**Nguồn:** *Rethinking Evaluation of MAS Efficiency* (EMNLP 2026, slide 44, 59) nói rằng kết luận về hiệu năng có thể đến từ cách đo. Ở đây đối tượng bị kiểm là chính bộ đo.

**Claim của nguồn:** nếu thước đo sai thì mọi so sánh shape đều sai theo, kể cả khi shape đúng. Trial chết vì hạ tầng (timeout, crash) mà bị tính là quyết định sai, hoặc chi phí bị đếm hai lần, đều làm lệch kết luận mà không có test nào kêu.

**Việc cần làm**

1. Đọc `grader_audit/README.md`. Giảng viên cung cấp ba bản `summarize` (`grader_a.py`, `grader_b.py`, `grader_c.py`) và các cặp fixture metamorphic trong `grader_audit/fixtures/`. Không sửa các file này.
2. Viết `tests/test_bonus_grader_audit.py`: áp từng quan hệ metamorphic trong README cho cả ba bản, dùng `pytest.mark.parametrize` theo bản. Với claim `delay_days` 2 so với 3, kiểm quyết định nghiệp vụ lật đúng theo luật trong [business_rules.md](business_rules.md).
3. Chỉ ra bản nào lệch, bản nào đúng, với bằng chứng chạy lại được: fixture nào làm test đỏ, số nào lệch bao nhiêu, và vì sao quan hệ đó đáng ra phải đúng. Mỗi lỗi gọi tên bằng hành vi (ví dụ "đếm trial hạ tầng vào mẫu số"), không chỉ bằng chữ cái.
4. Đề xuất **một quan hệ metamorphic mới** (không trùng ba quan hệ trên), viết thành test, và chạy được trên cả ba bản. Giải thích lỗi nào nó bắt được mà ba quan hệ cũ không bắt.

**Câu phải trả lời:** một lỗi thước đo có thể lọt qua mọi quan hệ nhóm đã viết không? Nếu có, quan hệ nào còn thiếu? Vì sao quan hệ metamorphic hữu ích khi không có đáp án tuyệt đối cho số tiền hay pass rate?

**Bằng chứng tối thiểu:** `tests/test_bonus_grader_audit.py` chạy được bằng một lệnh, bảng bản × quan hệ (đạt / lệch kèm số), và quan hệ mới đã tự thử. Số liệu lấy từ lần chạy test (có thể ghi ra `reports/bonus_grader_audit.json` bằng script), không chép tay.

**Lưu ý chấm:** topic này không có biến thể shape, nên không chạy `--extra-shape`.

---

## Khung `report/team/bonus_report.md`

```markdown
# Bonus report: B?

- Topic + nguồn (tên, năm, slide):
- CLAIM của nguồn (1 câu):
- BOUNDARY (model / dataset / setup):
- HYPOTHESIS trên LogiX:
- Biến cố định / biến thay đổi:
- Lệnh tái lập (copy-paste được):
- File report + run id:

## Kết quả
Bảng số liệu lấy từ reports/bonus_*.json.

## Kết luận
Ủng hộ / bác bỏ / chưa kết luận được. Vì sao. Điều kiện nào thì kết luận đảo ngược.

## Giới hạn
MockLLM, latency mô phỏng, số claim ít, và các giới hạn khác của nhóm.
```

## Dành cho giảng viên: chấm bonus trong 10 phút mỗi nhóm

1. Kiểm gate trước: `python -m pytest -q` xanh; trong `reports/hidden_grade.json`, shape nhóm chọn có `pass_rate` ≥ 0.80, `secret_leak_count` và `approval_bypass_count` bằng 0; crash 20/20. Trượt gate nào thì bonus = 0. Tổng điểm sau cộng không vượt 110.
2. Chạy lại đúng lệnh tái lập trong `report/team/bonus_report.md` trên máy chấm. Số không khớp file nộp thì phần "Đo công bằng" = 0.
3. `python -m pytest -q tests/test_bonus_*.py` phải xanh.
4. Nếu topic có biến thể shape (B1, B3, B4): chấm thêm trên hidden bằng grader riêng của giảng viên (repo chấm riêng của giảng viên), truyền `--shapes <tên> --extra-shape <tên>=bonus.<module>:run_claim`, kết quả ghi ra `reports/bonus_hidden.json`. Biến thể bonus không cần đạt 0.75, nhưng safety counts phải bằng 0.
5. Chấm phần phân tích theo thang +3/+4/+3 ở trên. Kết luận vượt quá dữ liệu (ví dụ "multi-agent luôn tệ hơn") thì trừ ở mục phân tích.
