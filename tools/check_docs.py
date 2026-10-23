#!/usr/bin/env python3
"""Kiểm tra tính nhất quán của tài liệu trong thư mục docs/.

Lỗi (làm lệnh thất bại):
  - mã FR/BR/NFR/AC được tham chiếu nhưng chưa định nghĩa trong requirements.md
  - ID trùng, hoặc đánh số không liên tục
  - AC thiếu hoặc thừa trong ma trận truy vết (mục 9)
  - phiên bản các tài liệu không đồng nhất
  - use case không có đặc tả hoặc xuất hiện nhiều lần
  - UC được nhắc đến nhưng không có trong danh sách
  - tham chiếu §x.y không tồn tại, liên kết tương đối hoặc tên file .md bị hỏng

Cảnh báo (chỉ làm thất bại khi dùng --strict):
  - FR, BR, AC không được use case nào dẫn tới (trừ các mã trong ALLOW_UNCOVERED)

Dùng: python tools/check_docs.py [--strict]
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
REQ, UC = "requirements.md", "use-case.md"
KINDS = ("FR", "BR", "NFR", "AC")
# Các mã không cần use case dẫn tới (xuyên suốt hoặc thuộc phần bàn giao)
ALLOW_UNCOVERED = {"FR-03", "AC-34", "AC-35"}

ID_RE = re.compile(r"\b(FR|BR|NFR|AC)-(\d{2})(?:\s*[–-]\s*(?:(?:FR|BR|NFR|AC)-)?(\d{2}))?")
errors, warnings = [], []


def read(name):
    return (DOCS / name).read_text(encoding="utf-8")


def refs(text):
    """Trả về tập (loại, số) được nhắc trong text, có mở rộng khoảng như AC-15 – AC-24."""
    out = set()
    for m in ID_RE.finditer(text):
        lo = int(m.group(2))
        hi = int(m.group(3) or lo)
        out.update((m.group(1), n) for n in range(lo, hi + 1))
    return out


def section(text, start, end=None):
    i = text.find(start)
    if i < 0:
        return ""
    j = text.find(end, i + len(start)) if end else -1
    return text[i:j] if j > 0 else text[i:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="coi cảnh báo là lỗi")
    args = ap.parse_args()

    files = sorted(p.name for p in DOCS.glob("*.md"))
    texts = {f: read(f) for f in files}
    if REQ not in texts or UC not in texts:
        print(f"Thiếu {REQ} hoặc {UC} trong docs/", file=sys.stderr)
        return 2
    req, uc = texts[REQ], texts[UC]

    # 1. ID được định nghĩa trong requirements.md
    defined = {k: [] for k in KINDS}
    # Chỉ đếm phần định nghĩa (trước mục 9), vì ma trận truy vết cũng có dòng bắt đầu bằng "| AC-xx |"
    definitions = req.split("## 9.")[0]
    for m in re.finditer(r"^\| (FR|BR|NFR|AC)-(\d{2}) \|", definitions, re.M):
        defined[m.group(1)].append(int(m.group(2)))
    ids = {k: set(v) for k, v in defined.items()}
    for k, v in defined.items():
        dup = sorted({n for n in v if v.count(n) > 1})
        if dup:
            errors.append(f"ID trùng trong {REQ}: " + ", ".join(f"{k}-{n:02d}" for n in dup))
        gaps = [n for n in range(1, max(v) + 1) if n not in set(v)] if v else []
        if gaps:
            errors.append(f"{k} đánh số không liên tục, thiếu: " + ", ".join(f"{k}-{n:02d}" for n in gaps))

    # 2. Ma trận truy vết (mục 9)
    matrix = section(req, "## 9.", "## 10.")
    rows = re.findall(r"^\| (AC-\d{2}) \| (.*?) \| (.*?) \|$", matrix, re.M)
    in_matrix = [int(a[3:]) for a, _, _ in rows]
    miss = sorted(ids["AC"] - set(in_matrix))
    extra = sorted(set(in_matrix) - ids["AC"])
    if miss:
        errors.append("AC thiếu trong ma trận truy vết: " + ", ".join(f"AC-{n:02d}" for n in miss))
    if extra:
        errors.append("AC trong ma trận nhưng chưa định nghĩa: " + ", ".join(f"AC-{n:02d}" for n in extra))
    if len(in_matrix) != len(set(in_matrix)):
        errors.append("Ma trận truy vết có AC lặp dòng")

    # 3. Mã tham chiếu trong mọi tài liệu phải tồn tại
    for f, t in texts.items():
        bad = sorted(f"{k}-{n:02d}" for k, n in refs(t) if n not in ids[k])
        if bad:
            errors.append(f"{f}: tham chiếu mã chưa định nghĩa: {', '.join(bad)}")

    # 4. Phiên bản đồng nhất
    versions = {}
    for f, t in texts.items():
        m = re.search(r"\*\*Phiên bản\*\* \| ([\d.]+)", t)
        if m:
            versions[f] = m.group(1)
    if len(set(versions.values())) > 1:
        errors.append("Phiên bản không đồng nhất: " + ", ".join(f"{f}={v}" for f, v in versions.items()))

    # 5. Use case: danh sách, đặc tả, sơ đồ
    sec3 = section(uc, "## 3.", "## 4.")
    uc_ids = re.findall(r"^\| (UC-\d{2}) \|", sec3, re.M)
    dup = sorted({u for u in uc_ids if uc_ids.count(u) > 1})
    if dup:
        errors.append("UC trùng trong danh sách: " + ", ".join(dup))
    detailed = re.findall(r"^### (UC-\d{2}) —", uc, re.M)
    summary = re.findall(r"^\| (UC-\d{2}) \|", section(uc, "## 5."), re.M)
    for u in uc_ids:
        n = detailed.count(u) + summary.count(u)
        if n != 1:
            errors.append(f"{u} có {n} đặc tả (cần đúng 1, ở mục 4 hoặc mục 5)")
    for u in set(detailed + summary) - set(uc_ids):
        errors.append(f"{u} có đặc tả nhưng không có trong danh sách (mục 3)")
    diagram = set()
    for blk in re.findall(r"```mermaid\n(.*?)```", section(uc, "## 2.", "## 3."), re.S):
        diagram |= {f"UC-{n}" for n in re.findall(r"\bUC(\d{2})\(", blk)}
    if diagram and diagram != set(uc_ids):
        errors.append(
            "Sơ đồ use case lệch danh sách: thiếu trong sơ đồ "
            f"{sorted(set(uc_ids) - diagram)}, thừa {sorted(diagram - set(uc_ids))}"
        )
    for f, t in texts.items():
        bad = sorted(set(re.findall(r"\bUC-\d{2}\b", t)) - set(uc_ids))
        if bad:
            errors.append(f"{f}: nhắc UC không có trong danh sách: {', '.join(bad)}")

    # 6. Tham chiếu §x.y phải trỏ tới mục có thật trong requirements.md
    heads = set(re.findall(r"^#{2,3} (\d+(?:\.\d+)?)\.?\s", req, re.M))
    for f, t in texts.items():
        bad = sorted(set(re.findall(r"§(\d+(?:\.\d+)?)", t)) - heads)
        if bad:
            errors.append(f"{f}: tham chiếu mục không tồn tại: " + ", ".join("§" + b for b in bad))

    # 7. Tên file .md trong dấu `` và liên kết tương đối
    for f, t in texts.items():
        for name in set(re.findall(r"`([\w.-]+\.md)`", t)):
            if not (DOCS / name).exists() and not (ROOT / name).exists():
                errors.append(f"{f}: nhắc tới file không tồn tại: {name}")
        for target in re.findall(r"\]\(([^)\s]+)\)", t):
            if re.match(r"(https?:|mailto:|#)", target):
                continue
            path = target.split("#")[0]
            if path and not (DOCS / path).resolve().exists():
                errors.append(f"{f}: liên kết hỏng: {target}")

    # 8. Độ phủ (cảnh báo)
    used = refs(uc)
    for k in ("FR", "BR", "AC"):
        for n in sorted(ids[k]):
            code = f"{k}-{n:02d}"
            if (k, n) not in used and code not in ALLOW_UNCOVERED:
                warnings.append(f"{code} chưa được use case nào dẫn tới")

    for w in warnings:
        print("CẢNH BÁO:", w)
    for e in errors:
        print("LỖI:", e)
    total = {k: len(ids[k]) for k in KINDS}
    print(
        f"\n{len(files)} tài liệu | " + ", ".join(f"{k}: {v}" for k, v in total.items())
        + f" | UC: {len(uc_ids)} | {len(errors)} lỗi, {len(warnings)} cảnh báo"
    )
    if errors or (args.strict and warnings):
        return 1
    print("Đạt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
