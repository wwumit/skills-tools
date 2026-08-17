#!/usr/bin/env python3
"""dependency-scan — 供应链依赖扫描器（skill-compliance 依赖检查专项入口）。

实现与 skill-compliance 的 DEPENDENCY 检查同源（单一实现，规则一处演进）：
本工具是 skill-compliance 依赖检查的独立 CLI 入口——检查逻辑由
skill-compliance 提供（DEP-001 宿主遮蔽 / DEP-002 版本锁定 / DEP-003 高危基线 / DEP-004 peer 完整性），
本工具过滤输出依赖专项结果。

用法: python3 dependency-scan.py --dir <插件目录> [--format json|text]
"""
import argparse
import json
import os
import sys
from pathlib import Path

VERSION = "1.0.0"
COMPLY = Path(__file__).resolve().parent.parent.parent / "skill-compliance" / "scripts"


def scan(target: str) -> dict:
    sys.path.insert(0, str(COMPLY))
    try:
        from comply import ComplianceChecker  # type: ignore
    except ImportError:
        return {"scanner": f"dependency-scan@{VERSION}", "target": target,
                "issues": [{"rule": "DEP-000", "severity": "high",
                            "found": "skill-compliance 不可用（同仓依赖缺失）"}], "score": 0}

    c = ComplianceChecker(str(Path(target).resolve()))
    c.run_all()
    deps = [i for i in c.issues if i["category"] == "DEPENDENCY"]
    sc = c.score()
    score = max(0, 100 - sum({"high": 15, "medium": 5}.get(i["severity"], 0) for i in deps))
    issues = [{"rule": i.get("recommendation", "DEP")[:8].strip() or "DEP",
               "severity": i["severity"], "found": i["found"]} for i in deps]
    return {"scanner": f"dependency-scan@{VERSION}",
            "checker": f"skill-compliance@{json.loads((COMPLY.parent / 'package.json').read_text(encoding='utf-8'))['version']}",
            "target": str(Path(target).resolve()), "issues": issues, "score": score}


def main() -> int:
    parser = argparse.ArgumentParser(description="供应链依赖扫描器（skill-compliance 依赖检查专项入口）")
    parser.add_argument("--dir", "-d", default=".", help="目标插件目录")
    parser.add_argument("--format", "-f", choices=["json", "text"], default="text")
    args = parser.parse_args()
    result = scan(args.dir)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"╔══ Dependency Scan ══ {args.dir}")
        print(f"║ scanner: {result['scanner']} | checker: {result.get('checker','')} | score: {result['score']}/100")
        for i in result["issues"]:
            print(f"║ [{i['severity']}] {i['rule']} {i['found'][:70]}")
        if not result["issues"]:
            print("║ ✅ 未发现依赖供应链问题")
    return 0


if __name__ == "__main__":
    sys.exit(main())
