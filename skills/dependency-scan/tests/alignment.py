#!/usr/bin/env python3
"""对齐测试：dependency-scan 与 skill-compliance 的 DEPENDENCY 检查对同一用例输出一致。

保证两工具功能对齐（DEP-001~004 同规则、同严重级），互不依赖。
规则演进后跑本测试：两处实现对同一 package.json 用例的 DEP 判定必须一致。

用法: python3 tests/alignment.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]  # skills-tools（tests→dependency-scan→skills→skills-tools）
SCAN = ROOT / "skills" / "dependency-scan" / "scripts" / "dependency-scan.py"

# 用例：4 个 DEP 场景
CASES = {
    "host_shadowing": {"package.json": {"name": "x", "dependencies": {"@deepseek-ai/dsh-tools": "^1.0.0"}},
                       "index.js": "import {x} from '@deepseek-ai/dsh-tools'\n"},
    "version_unlocked": {"package.json": {"name": "x", "dependencies": {"normal-pkg": "^2.0.0", "other": ">=1.0.0"}}},
    "suspicious_dep": {"package.json": {"name": "x", "dependencies": {"event-stream": "^3.3.6"}}},
    "clean": {"package.json": {"name": "x", "dependencies": {}, "peerDependencies": {}},
              "index.js": "console.log('hi')\n"},
}


def _rule_from_found(found):
    """从 found 文本识别 DEP 规则（两工具对齐的判定特征；DEP-004 先判避免与宿主包混淆）。"""
    if "peerDependencies" in found:
        return "DEP-004"
    if "宿主包" in found:
        return "DEP-001"
    if "版本未锁定" in found:
        return "DEP-002"
    if "高危" in found or "可疑" in found:
        return "DEP-003"
    return "DEP-UNKNOWN"


def scan_skill_compliance(dirpath):
    sys.path.insert(0, str(ROOT / "skills" / "skill-compliance" / "scripts"))
    from comply import ComplianceChecker
    c = ComplianceChecker(str(dirpath))
    c.run_all()
    return sorted((_rule_from_found(i["found"]), i["severity"]) for i in c.issues if i["category"] == "DEPENDENCY")


def scan_dependency_scan(dirpath):
    r = subprocess.run([sys.executable, str(SCAN), "--dir", str(dirpath), "--format", "json"],
                       capture_output=True, text=True)
    out = json.loads(r.stdout)
    return sorted((i["rule"], i["severity"]) for i in out["issues"])


def main() -> int:
    failures = 0
    for name, files in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            for fname, content in files.items():
                Path(tmp, fname).write_text(json.dumps(content) if fname == "package.json" else content, encoding="utf-8")
            try:
                sc = scan_skill_compliance(tmp)
            except Exception as e:
                print(f"❌ {name}: skill-compliance 失败 {e}")
                failures += 1
                continue
            ds = scan_dependency_scan(tmp)
            # 对齐判定：规则数 + 严重级一致（rule id 前缀对齐）
            if sc == ds:
                print(f"✅ {name}: 一致 ({ds})")
            else:
                print(f"❌ {name}: 不一致\n    skill-compliance: {sc}\n    dependency-scan:   {ds}")
                failures += 1
    print(f"\n{'✅ 对齐通过' if failures == 0 else f'❌ {failures} 个用例不一致'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
