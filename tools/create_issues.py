#!/usr/bin/env python3
"""Tạo nhãn, milestone và issue trên GitHub từ tools/backlog.json bằng GitHub CLI (gh).

Mặc định chỉ chạy thử (in ra việc sẽ làm). Thêm --apply để thực hiện thật.
Chạy lại nhiều lần an toàn: nhãn được cập nhật, milestone và issue trùng tên sẽ bị bỏ qua.

Yêu cầu: đã cài gh và đăng nhập (gh auth login).
Dùng:
  python tools/create_issues.py                       # chạy thử
  python tools/create_issues.py --apply               # tạo thật
  python tools/create_issues.py --apply --repo krisaleth/codepath
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "backlog.json"


def gh(args, repo=None, check=True):
    cmd = ["gh"] + args + (["-R", repo] if repo and args[0] in ("label", "issue") else [])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise SystemExit(f"Lỗi khi chạy: {' '.join(cmd[:4])} ...\n{r.stderr.strip()}")
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="thực hiện thật (mặc định chỉ chạy thử)")
    ap.add_argument("--repo", help="owner/name, mặc định lấy từ thư mục git hiện tại")
    args = ap.parse_args()
    data = json.loads(DATA.read_text(encoding="utf-8"))
    repo_path = args.repo or "{owner}/{repo}"

    if not args.apply:
        print("CHẠY THỬ, chưa tạo gì trên GitHub.\n")
        print(f"- {len(data['labels'])} nhãn, {len(data['milestones'])} milestone, {len(data['issues'])} issue")
        for m in data["milestones"]:
            n = sum(1 for i in data["issues"] if i["milestone"] == m["title"])
            print(f"  [{m['title']}] {n} issue")
        print("\nThêm --apply để tạo thật.")
        return 0

    for lb in data["labels"]:
        gh(["label", "create", lb["name"], "--color", lb["color"], "--description", lb["description"], "--force"], args.repo)
    print(f"Đã cập nhật {len(data['labels'])} nhãn")

    existing = json.loads(gh(["api", f"repos/{repo_path}/milestones?state=all&per_page=100"]) or "[]")
    have = {m["title"] for m in existing}
    for m in data["milestones"]:
        if m["title"] in have:
            continue
        gh(["api", f"repos/{repo_path}/milestones", "-f", f"title={m['title']}", "-f", f"description={m['description']}"])
        print("Đã tạo milestone:", m["title"])

    done = {i["title"] for i in json.loads(gh(["issue", "list", "--state", "all", "--limit", "1000", "--json", "title"], args.repo) or "[]")}
    created = skipped = 0
    for it in data["issues"]:
        if it["title"] in done:
            skipped += 1
            continue
        cmd = ["issue", "create", "--title", it["title"], "--body", it["body"], "--milestone", it["milestone"]]
        for lb in it["labels"]:
            cmd += ["--label", lb]
        gh(cmd, args.repo)
        created += 1
        print("Đã tạo:", it["title"])
    print(f"\nXong: tạo {created}, bỏ qua {skipped} issue đã có.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
