#!/usr/bin/env python3
"""dependency-scan — 供应链依赖扫描器（独立实现，零依赖，纯标准库）。

功能与 skill-compliance 的 DEPENDENCY 检查**对齐**（DEP-001~004 同规则、同严重级），
但两工具**互不依赖**：本工具独立可跑，不 import skill-compliance。
规则演进时两处同步更新，由 tests/alignment 对齐测试保证一致性。

检查：
  DEP-001 DSH 宿主遮蔽（@deepseek-ai/* 进普通 dependencies）
  DEP-002 版本未锁定（^/~/>=/* 范围符）
  DEP-003 已知高危/可疑依赖（内置基线）
  DEP-004 宿主包缺 peerDependencies 声明

用法: python3 dependency-scan.py --dir <插件目录> [--format json|text]
"""
import argparse
import json
import re
import sys
from pathlib import Path

VERSION = "1.1.0"

# 与 skill-compliance 对齐的高危/可疑依赖基线（同步更新）
SUSPICIOUS_BASELINE = {
    "event-stream", "flatmap-stream", "ua-parser-js", "left-pad", "minimist",
}
SEVERITY_PENALTY = {"high": 15, "medium": 5}


def scan(target: str) -> dict:
    root = Path(target).resolve()
    pkg_path = root / "package.json"
    issues = []
    if not pkg_path.is_file():
        return {"scanner": f"dependency-scan@{VERSION}", "target": str(root),
                "issues": [{"rule": "DEP-000", "severity": "high", "found": "package.json 不存在"}], "score": 0}

    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = {}
    for key in ("dependencies", "bundledDependencies"):
        v = pkg.get(key)
        if isinstance(v, dict):
            deps.update(v)
        elif isinstance(v, list):
            deps.update({d: "" for d in v})
    peer = pkg.get("peerDependencies") if isinstance(pkg.get("peerDependencies"), dict) else {}

    # DEP-001 宿主遮蔽
    host = sorted(k for k in deps if k.startswith("@deepseek-ai/"))
    if host:
        issues.append({"rule": "DEP-001", "severity": "high",
                       "found": f"DSH 宿主包在普通 dependencies: {', '.join(host)}"})

    # DEP-002 版本未锁定
    unlocked = [f"{k}@{v}" for k, v in deps.items() if any(ch in str(v or "") for ch in "^~><*x")]
    if unlocked:
        issues.append({"rule": "DEP-002", "severity": "medium",
                       "found": f"依赖版本未锁定（范围符）: {', '.join(unlocked[:5])}"})

    # DEP-003 高危/可疑基线
    suspicious = sorted(k for k in deps if k in SUSPICIOUS_BASELINE)
    if suspicious:
        issues.append({"rule": "DEP-003", "severity": "high",
                       "found": f"已知高危/可疑依赖（内置基线）: {', '.join(suspicious)}"})

    # DEP-004 peer 完整性
    imported = set()
    for f in ("index.js", "lib/index.js", "src/index.ts", "src/index.js"):
        p = root / f
        if p.is_file():
            for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
                for m in re.finditer(r"@deepseek-ai/[a-z-]+", line):
                    imported.add(m.group(0))
    missing_peer = sorted(n for n in imported if n not in peer)
    if missing_peer:
        issues.append({"rule": "DEP-004", "severity": "medium",
                       "found": f"代码引用宿主包但 peerDependencies 未声明: {', '.join(missing_peer[:5])}"})

    score = max(0, 100 - sum(SEVERITY_PENALTY.get(i["severity"], 0) for i in issues))
    return {"scanner": f"dependency-scan@{VERSION}", "target": str(root), "issues": issues, "score": score}


def main() -> int:
    parser = argparse.ArgumentParser(description="供应链依赖扫描器（独立实现，与 skill-compliance DEP 对齐）")
    parser.add_argument("--dir", "-d", default=".", help="目标插件目录")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text")
    args = parser.parse_args()
    result = scan(args.dir)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"╔══ Dependency Scan ══ {args.dir}")
        print(f"║ scanner: {result['scanner']} | score: {result['score']}/100")
        for i in result["issues"]:
            print(f"║ [{i['severity']}] {i['rule']} {i['found'][:70]}")
        if not result["issues"]:
            print("║ ✅ 未发现依赖供应链问题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
