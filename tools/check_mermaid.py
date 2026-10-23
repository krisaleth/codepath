#!/usr/bin/env python3
"""Render thử mọi khối ```mermaid trong docs/ và README.md để bắt lỗi cú pháp.

Cần mermaid-cli:  npm install -g @mermaid-js/mermaid-cli
Dùng: python tools/check_mermaid.py [--puppeteer-config .github/puppeteer-config.json]
"""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--puppeteer-config", default=str(ROOT / ".github" / "puppeteer-config.json"))
    ap.add_argument("--timeout", type=int, default=120, help="giây cho mỗi sơ đồ")
    args = ap.parse_args()

    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("Không tìm thấy mmdc. Cài bằng: npm install -g @mermaid-js/mermaid-cli", file=sys.stderr)
        return 2

    files = sorted((ROOT / "docs").glob("*.md")) + [ROOT / "README.md"]
    failed = total = 0
    with tempfile.TemporaryDirectory() as tmp:
        for f in files:
            if not f.exists():
                continue
            blocks = re.findall(r"```mermaid\n(.*?)```", f.read_text(encoding="utf-8"), re.S)
            for i, code in enumerate(blocks, 1):
                total += 1
                src = Path(tmp) / f"{f.stem}_{i}.mmd"
                src.write_text(code, encoding="utf-8")
                cmd = [mmdc, "-i", str(src), "-o", str(src.with_suffix(".svg")), "-q"]
                if Path(args.puppeteer_config).exists():
                    cmd += ["-p", args.puppeteer_config]
                try:
                    r = subprocess.run(cmd, capture_output=True, text=True, timeout=args.timeout)
                    ok, msg = r.returncode == 0, (r.stderr or r.stdout).strip()
                except subprocess.TimeoutExpired:
                    ok, msg = False, "quá thời gian"
                print(("OK   " if ok else "LỖI ") + f"{f.relative_to(ROOT)} - sơ đồ {i}")
                if not ok:
                    failed += 1
                    print("     " + msg.replace("\n", "\n     ")[:600])
    print(f"\n{total} sơ đồ, {failed} lỗi")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
