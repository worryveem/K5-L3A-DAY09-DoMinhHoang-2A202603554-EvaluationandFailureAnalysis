"""Audit report completeness and prepare an honest rubric review; never commit files.

Run from src/: python scripts/audit_lab9_docs.py
"""

import json
from pathlib import Path
import re
import subprocess
import unicodedata

from build_lab9_docs import STUDENT_NAME, clean_document, table

SRC = Path(__file__).resolve().parents[1]
ROOT = SRC.parent
AUDIT = ROOT / "docs/RUBRIC_AUDIT.md"
REPORTS = ["docs/m0_setup.md", "docs/failure_taxonomy.md", "docs/trace_case.md", "docs/judge_audit.md",
           "docs/eval_card.md", "docs/PRD_v1.1.md", "docs/PR_DESCRIPTION.md", "docs/REVIEW_LAB09.md",
           "docs/RUBRIC_AUDIT.md", "src/reports/README.md"]
INDEXES = ["README.md", "SUBMISSION.md", "docs/README.md"]


def main():
    summary = json.loads((SRC / "reports/verification_summary.json").read_text(encoding="utf-8"))
    assert summary["passed"]
    raw = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    paths = {part.decode("utf-8") for part in raw.split(b"\0") if part.endswith(b".md")}
    paths.add("docs/RUBRIC_AUDIT.md")
    identity_errors, empty_cells, placeholders, broken = [], [], [], []
    for relative in REPORTS + INDEXES:
        if relative == "docs/RUBRIC_AUDIT.md":
            continue
        path = ROOT / relative
        text = unicodedata.normalize("NFC", path.read_text(encoding="utf-8"))
        if relative in ("docs/eval_card.md", "docs/PRD_v1.1.md"):
            if STUDENT_NAME not in text:
                identity_errors.append(f"{relative}: original owner/name field is unfilled")
        elif STUDENT_NAME in text:
            identity_errors.append(f"{relative}: personal name added outside an original template field")
        if "student-info:start" in text or re.search(r"^\s*- \*\*(?:Sinh viên|MSSV|Lớp):\*\*", text, re.M):
            identity_errors.append(f"{relative}: unsolicited profile block")
        if relative in REPORTS:
            for number, line in enumerate(text.splitlines(), 1):
                if line.startswith("|") and re.search(r"\|[ \t]*\|", line):
                    empty_cells.append(f"{relative}:{number}")
            if re.search(r"\b(?:TODO|TBD|FIXME)\b|<shape>|<claim>|<MSSV>|MSSV_HoTen", text):
                placeholders.append(relative)
    if identity_errors or empty_cells or placeholders:
        raise SystemExit(f"Report audit failed: identity={identity_errors}, cells={empty_cells}, placeholders={placeholders}")
    for relative in paths:
        path = ROOT / relative
        if not path.exists():
            continue
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                destination = path.parent / target.split("#")[0]
                if not destination.exists() and destination.resolve() != AUDIT.resolve():
                    broken.append((relative, target))
    if broken:
        raise SystemExit(f"Missing local Markdown link targets: {broken}")
    core = [
        ["M1 Taxonomy + eval set", 12, "8 FM có trace lỗi, coding sheet, provenance, eval set sạch", "5 anchor cần key giảng viên"],
        ["M2 Calibration", 12, "Tone κ=0.757/P=0.857/R=0.8; helpful bị loại; audit 16 case", "Đã có bằng chứng công khai; chưa phải điểm do giảng viên chấm"],
        ["M3 Trajectory", 12, "Hai grader, metric FM-08, detection 100%, false alarm 0%", "Đã đạt mốc kiểm tra công khai"],
        ["M4 Bootstrap + gate", 15, "Δ pass_rate −0.2714, CI [−0.5000, −0.0571]; fixed qua, seeded bị chặn; harness có eval", "Job eval-gate chưa có trạng thái xanh trên GitHub"],
        ["Eval card + PRD v1.1", 9, "Đủ số liệu, run ID/SHA, CI, phạm vi và giới hạn", "Đủ nội dung local; sinh viên kiểm tra bản bàn giao"],
    ]
    advanced = [
        ["pass_at_k/pass_hat_k", 5, "Vector công khai và input sai đều qua test", "Vector ẩn chưa chạy"],
        ["fm_map + eval set v2", 6, "8 cơ chế map FM, 28 item, mỗi FM bị tấn công ≥3 item; 0 problem", "Chờ đánh giá chính thức về mapping"],
        ["Spec v2", 4, "pass_hat_5 blocking min=0.80; money_movement/adversarial blocking", "Cấu hình đã kiểm tra tại máy"],
        ["Slice regression", 6, "Public slice bị chặn; có test slice tên mới ngoài starter", "Slice regression ẩn chưa chạy"],
        ["FM-08 ẩn", 2, "Diagnostic reply sai tiền bị phát hiện; ledger đúng vẫn bắt lỗi reply", "Variant FM-08 ẩn chưa chạy; phạm vi parser đã nêu trong eval card"],
        ["Không báo nhầm", 2, "fixed và honest_refactor được merge", "Refactor trung thực ẩn chưa chạy"],
    ]
    expert = [
        ["Integrity/ratchet", 9, "4/4 trap public bị chặn bằng INTEGRITY; có test dòng trùng, grader error và relabel slice", "2 trap ẩn chưa chạy"],
        ["Stability và điều kiện kèm theo", 6, "flaky bị chặn; test quiet_override; baseline tự so qua; A/A 15 metric Δ=0; sàn 0.80", "Variant ẩn chưa chạy; điểm còn nhân tỷ lệ trap bị chặn"],
    ]
    inventory = []
    for relative in sorted(paths):
        if relative in REPORTS:
            category = "Báo cáo/bằng chứng bài làm"
            status = "Đã điền nội dung; thông tin người phụ trách chỉ ở trường mẫu gốc" if relative in ("docs/eval_card.md", "docs/PRD_v1.1.md") else "Đã điền nội dung; không thêm hồ sơ sinh viên"
        elif relative in INDEXES:
            category, status = "Trang bài làm/checklist/mục lục", "Không tự thêm thông tin sinh viên; trạng thái nộp ghi đúng thực tế"
        else:
            category, status = "Đề hoặc tài liệu tham khảo kế thừa", "Không phải mẫu báo cáo cần điền thông tin sinh viên"
        link = "RUBRIC_AUDIT.md" if relative == "docs/RUBRIC_AUDIT.md" else "../" + relative
        inventory.append([f"[{relative}]({link})", category, status])
    content = f"""# Kiểm tra rubric, báo cáo và biểu mẫu gốc

## Kết luận

**Chưa đủ cơ sở xác nhận 100/100.** Bài làm đã triển khai toàn bộ phần local của M0–M7 và qua bộ
kiểm tra công khai, nhưng rubric còn yêu cầu CI thực trên GitHub, đối chiếu anchor và các variant/trap ẩn.
Không cộng số test PASS để suy ra điểm, cũng không tự chấm các mục phụ thuộc bộ chấm chưa có.

Lượt kiểm tra tổng thể `{summary['run_id']}`: {len(summary['steps'])} bước đúng exit code mong đợi,
85 test Lab 09 PASS, scorecard 3/3 và 0 false alarm, 4 trap public bị chặn, A/A Δ=0.
Trong lượt rà soát bổ sung, 85 test Lab 09 được chạy lại và vẫn PASS.

## Core — tối đa 60 điểm

{table(['Tiêu chí', 'Điểm tối đa', 'Bằng chứng hiện có', 'Phần chưa thể xác nhận'], core)}

## Advanced — tối đa 25 điểm

{table(['Tiêu chí', 'Điểm tối đa', 'Bằng chứng hiện có', 'Phần chưa thể xác nhận'], advanced)}

## Expert — tối đa 15 điểm

{table(['Tiêu chí', 'Điểm tối đa', 'Bằng chứng hiện có', 'Phần chưa thể xác nhận'], expert)}

## Báo cáo và trường thông tin trong mẫu gốc

Đã rà {len(paths)} file Markdown thuộc hồ sơ Git/working tree; loại `.venv`, `.git` và cache runtime khỏi phạm vi.
{len(REPORTS)} file báo cáo/bằng chứng không còn ô bảng rỗng hoặc placeholder cần điền.
Chỉ điền tên ở trường mà repo gốc có yêu cầu: Gate owner trong `docs/eval_card.md`,
Người xử lý và bảng phê duyệt Product/Eval owner trong `docs/PRD_v1.1.md`.
Repo gốc không có trường MSSV hoặc khối hồ sơ sinh viên trong các tài liệu này, nên không tự thêm.
Đối chiếu mẫu tại commit starter `d1b9471`; ngày phê duyệt chưa có nên ghi đúng trạng thái chưa phê duyệt.

{table(['File', 'Loại', 'Kết quả rà'], inventory)}

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
"""
    clean = "\n".join(line.rstrip() for line in clean_document(content).strip().splitlines()) + "\n"
    AUDIT.write_text(clean, encoding="utf-8")
    print(f"AUDIT PASS: {len(paths)} Markdown files; original owner fields filled; no unsolicited student profiles")
    print("Score status: public/local checks pass; 100/100 requires GitHub CI and instructor hidden grading")
    print(AUDIT)


if __name__ == "__main__":
    main()
