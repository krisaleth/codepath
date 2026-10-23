#!/usr/bin/env python3
"""Sinh backlog (issue theo milestone) từ docs/use-case.md và docs/requirements.md.

Đầu ra:
  docs/backlog.md       bảng backlog để đọc
  tools/backlog.json    dữ liệu cho tools/create_issues.py

Dùng:
  python tools/generate_backlog.py          # ghi lại hai file đầu ra
  python tools/generate_backlog.py --check  # báo lỗi nếu hai file đầu ra đã lỗi thời (dùng trong CI)
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REPO_URL = "https://github.com/krisaleth/codepath"
BLOB = f"{REPO_URL}/blob/main/docs"

MILESTONES = [
    ("M0 Tài liệu và thiết lập repo", "Chốt quyết định, ERD, đặc tả API, kế hoạch kiểm thử."),
    ("M1 Lát cắt dọc chấm bài", "Nộp bài, hàng đợi, sandbox, verdict: giảm rủi ro kỹ thuật lớn nhất (UC-09, UC-25, UC-27)."),
    ("M2 Khóa học và học tập", "Tài khoản, khóa học, nội dung, ghi danh, học và kiểm duyệt."),
    ("M3 Đánh giá và quản trị", "QUIZ, bài đánh giá, chấm lại, phục hồi, thống kê, quản trị."),
    ("M4 Kiểm thử, đóng gói, báo cáo", "Kiểm thử tự động, kiểm thử sandbox, dữ liệu mẫu, tài liệu, báo cáo."),
]
M0, M1, M2, M3, M4 = (m[0] for m in MILESTONES)

UC_MILESTONE = {}
for ms, ucs in (
    (M1, (8, 9, 25, 27)),
    (M2, (1, 2, 3, 4, 5, 6, 7, 10, 12, 13, 14, 15, 17, 20, 28)),
    (M3, (11, 16, 18, 19, 21, 22, 23, 24, 26, 29, 30)),
):
    for n in ucs:
        UC_MILESTONE[f"UC-{n:02d}"] = ms

LABELS = {
    "use-case": ("1d76db", "Triển khai một use case"),
    "type:feature": ("0e8a16", "Chức năng mới"),
    "type:docs": ("0075ca", "Tài liệu"),
    "type:infra": ("5319e7", "Hạ tầng, đóng gói, CI"),
    "type:spike": ("fbca04", "Thử nghiệm kỹ thuật có thời hạn"),
    "type:test": ("c2e0c6", "Kiểm thử"),
    "type:decision": ("d4c5f9", "Cần ra quyết định"),
    "type:report": ("bfdadc", "Báo cáo đồ án"),
    "area:public": ("ededed", "Khách và mọi người dùng"),
    "area:learner": ("ededed", "Người học"),
    "area:instructor": ("ededed", "Giảng viên"),
    "area:admin": ("ededed", "Quản trị viên"),
    "area:system": ("ededed", "Thành phần hệ thống"),
}

# Use case có sơ đồ tuần tự hoặc trạng thái đi kèm
EXTRA_LINKS = {
    "UC-09": [("Sơ đồ tuần tự UC-09", "sequence-diagrams.md#2-uc-09--nộp-bài-và-xem-kết-quả-chấm"),
              ("Vòng đời bài nộp", "state-diagrams.md#2-vòng-đời-bài-nộp")],
    "UC-11": [("Sơ đồ tuần tự UC-11", "sequence-diagrams.md#3-uc-11--làm-bài-đánh-giá"),
              ("Vòng đời lần làm bài đánh giá", "state-diagrams.md#3-vòng-đời-lần-làm-bài-đánh-giá")],
    "UC-13": [("Vòng đời khóa học", "state-diagrams.md#1-vòng-đời-khóa-học")],
    "UC-17": [("Vòng đời khóa học", "state-diagrams.md#1-vòng-đời-khóa-học")],
    "UC-19": [("Luồng sự cố và chấm lại", "sequence-diagrams.md#22-luồng-sự-cố-bài-nộp-kẹt-và-chấm-lại")],
    "UC-25": [("Cách xác định verdict", "state-diagrams.md#22-cách-xác-định-verdict-cuối")],
    "UC-26": [("Luồng sự cố và chấm lại", "sequence-diagrams.md#22-luồng-sự-cố-bài-nộp-kẹt-và-chấm-lại")],
}

ID_RE = re.compile(r"\b(FR|BR|NFR|AC)-(\d{2})(?:\s*[–-]\s*(?:(?:FR|BR|NFR|AC)-)?(\d{2}))?")


def ids_in(text):
    out = {}
    for m in ID_RE.finditer(text):
        lo, hi = int(m.group(2)), int(m.group(3) or m.group(2))
        for n in range(lo, hi + 1):
            out.setdefault(m.group(1), set()).add(n)
    return out


def fmt(ids, kind):
    return ", ".join(f"{kind}-{n:02d}" for n in sorted(ids.get(kind, ())))


def slug(heading):
    return re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-")


def areas(actor):
    out = []
    for key, label in (("Khách", "area:public"), ("Mọi người dùng", "area:public"), ("Người học", "area:learner"),
                       ("Giảng viên", "area:instructor"), ("Admin", "area:admin"),
                       ("Hệ thống chấm bài", "area:system"), ("Bộ định thời", "area:system"), ("nội bộ", "area:system")):
        if key in actor and label not in out:
            out.append(label)
    return out or ["area:system"]


def parse():
    uc = (DOCS / "use-case.md").read_text(encoding="utf-8")
    req = (DOCS / "requirements.md").read_text(encoding="utf-8")

    ac_text = dict(re.findall(r"^\| (AC-\d{2}) \| (.*?) \|$", req.split("## 9.")[0], re.M))

    sec3 = uc.split("## 3.")[1].split("## 4.")[0]
    ucs = []
    for m in re.finditer(r"^\| (UC-\d{2}) \| (.*?) \| (.*?) \| (.*?) \|$", sec3, re.M):
        ucs.append({"id": m.group(1), "name": m.group(2), "actor": m.group(3), "fr": m.group(4)})

    # Quy tắc, AC cho từng UC: bảng chi tiết (mục 4) hoặc cột Tham chiếu (mục 5)
    refs_by_uc, heading_by_uc = {}, {}
    sec4 = uc.split("## 4.")[1].split("## 5.")[0]
    parts = re.split(r"^### (UC-\d{2}) — (.*)$", sec4, flags=re.M)
    for i in range(1, len(parts), 3):
        uid, title, body = parts[i], parts[i + 1], parts[i + 2]
        row = re.search(r"\*\*Quy tắc liên quan\*\* \| (.*?) \|", body)
        refs_by_uc[uid] = ids_in(row.group(1)) if row else {}
        heading_by_uc[uid] = f"{uid} — {title.strip()}"
    sec5 = uc.split("## 5.")[1]
    for m in re.finditer(r"^\| (UC-\d{2}) \| .* \| (.*?) \|$", sec5, re.M):
        refs_by_uc[m.group(1)] = ids_in(m.group(2))
    return ucs, ac_text, refs_by_uc, heading_by_uc


def uc_issue(u, ac_text, refs, heading):
    r = dict(refs)
    for k, v in ids_in(u["fr"]).items():
        r.setdefault(k, set()).update(v)
    lines = [
        f"**Use case:** {u['id']} — {u['name']}",
        f"**Tác nhân chính:** {u['actor']}",
    ]
    if r.get("FR"):
        lines.append(f"**Yêu cầu chức năng:** {fmt(r, 'FR')}")
    rules = ", ".join(x for x in (fmt(r, "BR"), fmt(r, "NFR")) if x)
    if rules:
        lines.append(f"**Quy tắc và phi chức năng:** {rules}")
    link = f"{BLOB}/use-case.md"
    if u["id"] in heading:
        link += "#" + slug(heading[u["id"]])
    docs = [f"[Đặc tả {u['id']}]({link})"]
    docs += [f"[{t}]({BLOB}/{p})" for t, p in EXTRA_LINKS.get(u["id"], [])]
    lines.append("**Tài liệu:** " + ", ".join(docs))
    acs = sorted(r.get("AC", ()))
    lines += ["", "## Tiêu chí chấp nhận"]
    lines += [f"- [ ] AC-{n:02d}: {ac_text.get(f'AC-{n:02d}', '')}" for n in acs] or ["- [ ] Hành vi khớp đặc tả use case"]
    lines += ["", "## Định nghĩa hoàn thành",
              "- [ ] Hiện thực đúng luồng chính, luồng thay thế và ngoại lệ trong đặc tả",
              "- [ ] Có kiểm thử cho các tiêu chí chấp nhận ở trên",
              "- [ ] Nếu hành vi khác đặc tả: cập nhật tài liệu và chạy `python tools/check_docs.py`"]
    return {"title": f"{u['id']} — {u['name']}", "milestone": UC_MILESTONE[u["id"]],
            "labels": ["use-case", "type:feature"] + areas(u["actor"]), "body": "\n".join(lines), "ref": u["id"]}


def plain(title, milestone, typ, body, refs="", ref=""):
    text = body.strip()
    if refs:
        text += f"\n\n**Tham chiếu:** {refs}"
    return {"title": title, "milestone": milestone, "labels": [typ], "body": text, "ref": ref}


def infra_issues():
    I = []
    I.append(plain("Chốt giấy phép và chế độ hiển thị repo", M0, "type:decision",
                   "Chọn giấy phép (hoặc để trống nếu là đồ án nộp riêng) và quyết định repo public hay private đến khi nộp báo cáo.\n\n- [ ] Quyết định và ghi vào README\n- [ ] Không đưa file báo cáo `.docx` (có tên, mã sinh viên) vào repo public"))
    I.append(plain("Chốt các câu hỏi mở ở requirements §10 và ghi ADR", M0, "type:decision",
                   "Mỗi câu hỏi mở thành một ADR ngắn trong `docs/adr/`, sau đó cập nhật requirements, use case và changelog.\n\n- [ ] Judge0 hay runner Docker tự xây (ADR-0001, chốt sau spike M1)\n- [ ] Lần làm bài đánh giá bị bỏ dở có tính lượt không\n- [ ] Quay lại sau khi hết hạn nhưng trước lần quét của bộ định thời\n- [ ] Hủy ghi danh khi đang làm bài đánh giá\n- [ ] Giảng viên bị vô hiệu hóa thì khóa học ra sao\n- [ ] Khi gửi duyệt có chạy lại lời giải tham chiếu không\n- [ ] Giảng viên có rút lại yêu cầu duyệt được không\n- [ ] Khóa `ARCHIVED` có khôi phục được không",
                   "requirements.md §10, state-diagrams.md mục 4, sequence-diagrams.md mục 2.3 và 3.4"))
    I.append(plain("Thiết kế ERD", M0, "type:docs",
                   "Mô hình dữ liệu cho toàn bộ hệ thống. Các điểm cần thể hiện:\n\n- [ ] Bản sao câu hỏi và bài tập trong bài đánh giá (BR-20)\n- [ ] Tiến độ gắn với (người học, mục học), không phụ thuộc ghi danh (§3.5)\n- [ ] Bản ghi kết quả chấm lại, có người thực hiện (BR-11)\n- [ ] Kết quả code của bài đánh giá lưu theo lần làm (BR-19)\n- [ ] Ràng buộc duy nhất cho ghi danh, tiến độ và một lần làm `IN_PROGRESS` (NFR-13)\n- [ ] Nơi lưu số lần đưa lại của bài `QUEUED` kẹt (§3.3)",
                   "BR-04, BR-11, BR-19, BR-20, NFR-13, §3.5"))
    I.append(plain("Đặc tả API (OpenAPI)", M0, "type:docs",
                   "Suy ra từ use case và sơ đồ tuần tự; thay các endpoint minh họa bằng endpoint chính thức.\n\n- [ ] Endpoint, quyền, mã lỗi cho từng use case\n- [ ] Định dạng lỗi thống nhất (NFR-15)\n- [ ] Phân trang (NFR-14)",
                   "NFR-14, NFR-15, NFR-16"))
    I.append(plain("Lập kế hoạch kiểm thử theo tiêu chí chấp nhận", M0, "type:docs",
                   "Mỗi AC thành một hoặc vài test; ghi rõ mức kiểm thử (unit, integration, sandbox).\n\n- [ ] Bảng AC → test\n- [ ] Danh sách chuyển trạng thái không hợp lệ cần test từ chối (state-diagrams.md mục 4)",
                   "AC-35, NFR-20"))
    I.append(plain("Dựng khung monorepo và Docker Compose", M1, "type:infra",
                   "Khung chạy được cho API, web, worker, PostgreSQL và Redis.\n\n- [ ] Cấu trúc `apps/` và `packages/`\n- [ ] `docker-compose.yml` cho PostgreSQL, Redis\n- [ ] Migration Prisma đầu tiên\n- [ ] Biến môi trường theo `.env.example`",
                   "NFR-17, NFR-19"))
    I.append(plain("Spike sandbox: chạy Python trong container cô lập", M1, "type:spike",
                   "Thử trong 1–2 ngày để chọn giữa Judge0 và runner Docker tự xây (ADR-0001).\n\n- [ ] Chạy mã Python với giới hạn thời gian và bộ nhớ\n- [ ] Không mạng, không root, hủy container sau khi chạy\n- [ ] Phân biệt được TLE, MLE, lỗi biên dịch, lỗi chạy\n- [ ] Đo thời gian chạy một test\n- [ ] Ghi kết quả vào ADR-0001",
                   "BR-10, NFR-07, §3.6, AC-17, AC-18"))
    I.append(plain("Kiểm thử sandbox với mã độc mẫu", M4, "type:test",
                   "Vòng lặp vô hạn, fork bomb, truy cập mạng, đọc file hệ thống, cấp phát bộ nhớ quá mức, in quá nhiều dữ liệu. Máy chủ vẫn hoạt động bình thường sau mỗi mẫu.",
                   "AC-17, AC-18, NFR-20"))
    I.append(plain("Bộ kiểm thử tự động theo tiêu chí chấp nhận", M4, "type:test",
                   "Unit và integration test chạy bằng một lệnh được tài liệu hóa; gồm verdict của bộ chấm, phân quyền, BR-05, BR-09, BR-12, BR-15.",
                   "AC-35, NFR-20"))
    I.append(plain("Kiểm thử tải: 20 bài nộp đồng thời", M4, "type:test",
                   "Bài nhỏ (tối đa 10 test, mỗi test tối đa 1 giây) có kết quả trong 10 giây ở tải bình thường; API nộp bài phản hồi trong 500 ms.",
                   "NFR-09, NFR-10, AC-21"))
    I.append(plain("Dữ liệu mẫu và chạy hệ thống bằng Docker Compose", M4, "type:infra",
                   "1 admin, 2 giảng viên, 3 người học, danh mục, khóa học ở nhiều trạng thái, ít nhất 5 bài tập code (Python, JS, C++) có test công khai và ẩn, 1 bài đánh giá.",
                   "NFR-19, AC-34"))
    I.append(plain("Tài liệu OpenAPI tại /api/docs và hướng dẫn cài đặt", M4, "type:docs",
                   "Hoàn thiện `/api/docs` và README để cài đặt, demo chỉ bằng hướng dẫn.",
                   "NFR-16, AC-34"))
    I.append(plain("Hoàn thiện báo cáo đồ án", M4, "type:report",
                   "Mở đầu, bốn chương, kết luận, tài liệu tham khảo theo mẫu. Lưu ý: file báo cáo để ngoài repo public.",
                   ""))
    return I


def build():
    ucs, ac_text, refs_by_uc, heading_by_uc = parse()
    missing = [u["id"] for u in ucs if u["id"] not in UC_MILESTONE]
    assert not missing, f"UC chưa gán milestone: {missing}"
    issues = infra_issues() + [uc_issue(u, ac_text, refs_by_uc.get(u["id"], {}), heading_by_uc) for u in ucs]
    order = {m[0]: i for i, m in enumerate(MILESTONES)}
    issues.sort(key=lambda x: (order[x["milestone"]], x["labels"][0] != "type:decision", x["title"]))
    return issues


def render_md(issues):
    out = ["# Backlog", "",
           "> File này được sinh tự động bởi `tools/generate_backlog.py` từ `use-case.md` và `requirements.md`. Không sửa tay: sửa tài liệu nguồn rồi chạy lại công cụ.", "",
           f"Tổng cộng {len(issues)} mục. Tạo issue lên GitHub bằng `python tools/create_issues.py --apply` (mặc định chỉ chạy thử).", ""]
    for name, desc in MILESTONES:
        rows = [i for i in issues if i["milestone"] == name]
        out += [f"## {name}", "", desc, "", "| Mục | Nhãn |", "|---|---|"]
        out += [f"| {i['title']} | {', '.join(l for l in i['labels'] if l != 'use-case')} |" for i in rows]
        out.append("")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="chỉ kiểm tra, không ghi file")
    args = ap.parse_args()
    issues = build()
    data = json.dumps(
        {"milestones": [{"title": t, "description": d} for t, d in MILESTONES],
         "labels": [{"name": n, "color": c, "description": d} for n, (c, d) in LABELS.items()],
         "issues": issues},
        ensure_ascii=False, indent=2) + "\n"
    md = render_md(issues).rstrip("\n") + "\n"
    targets = {DOCS / "backlog.md": md, ROOT / "tools" / "backlog.json": data}
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, c in targets.items() if not p.exists() or p.read_text(encoding="utf-8") != c]
        if stale:
            print("Lỗi thời, hãy chạy lại python tools/generate_backlog.py: " + ", ".join(stale))
            return 1
        print("Backlog đã cập nhật.")
        return 0
    for p, c in targets.items():
        p.write_text(c, encoding="utf-8")
        print("Đã ghi", p.relative_to(ROOT))
    print(f"{len(issues)} mục backlog.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
