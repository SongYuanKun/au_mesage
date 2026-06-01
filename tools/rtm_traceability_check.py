#!/usr/bin/env python3
"""校验 RTM 高优需求在 rtm_refs.yml 中具备 Design/Code/Test 引用。"""

from __future__ import annotations

import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
REFS_PATH = ROOT / "docs" / "SRS" / "rtm_refs.yml"

REQUIRED_IDS = frozenset({"FR-AUTH-001", "FR-ADM-001", "SEC-002", "NFR-MNT-001"})


def main() -> int:
    if not REFS_PATH.is_file():
        print(f"缺少 {REFS_PATH}", file=sys.stderr)
        return 1

    data = yaml.safe_load(REFS_PATH.read_text(encoding="utf-8")) or {}
    missing = []
    for req_id in sorted(REQUIRED_IDS):
        entry = data.get(req_id)
        if not entry:
            missing.append(f"{req_id}: 无条目")
            continue
        for field in ("design", "code", "test"):
            val = (entry.get(field) or "").strip()
            if not val or val.upper() == "TBD":
                missing.append(f"{req_id}.{field}")

    if missing:
        print("RTM 追踪校验失败:", file=sys.stderr)
        for line in missing:
            print(f"  - {line}", file=sys.stderr)
        return 1

    print(f"RTM 追踪校验通过（{len(REQUIRED_IDS)} 条高优需求）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
