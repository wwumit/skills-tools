#!/usr/bin/env python3
"""bundle-lint 边界用例集：正例 + 各盲区反例。

用法: python3 tests/cases.py
构造临时插件目录 → 跑 bundle-lint → 断言结论/规则命中。
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BLINT = ROOT / "skills" / "bundle-lint" / "scripts" / "bundle-lint.py"


def _mk(base: Path, name: str, pkg: dict, patch=None, src_files=None):
    d = base / name
    d.mkdir(exist_ok=True)
    (d / "package.json").write_text(json.dumps(pkg, ensure_ascii=False, indent=2), encoding="utf-8")
    if patch is not None:
        (d / "cordis.patch.yml").write_text(patch, encoding="utf-8")
    for f, content in (src_files or {}).items():
        fp = d / f
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
    return d


def _run(target: Path):
    r = subprocess.run([sys.executable, str(BLINT), "--dir", str(target), "--format", "json"],
                       capture_output=True, text=True)
    return json.loads(r.stdout)


GOOD_PKG = {
    "name": "@wwumit/good",
    "main": "lib/index.js",
    "files": ["cordis.patch.yml", "lib"],
    "keywords": ["dsh-plugin"],
    "dsh": {"plugin": True, "kind": "server", "bundle": {"patch": "./cordis.patch.yml"}},
}
GOOD_PATCH = "- insert:\n    - id: good\n      name: '@wwumit/good'\n"

CASES = [
    ("good", dict(
        pkg=GOOD_PKG, patch=GOOD_PATCH,
        src_files={"lib/index.js": "// built\n", "src/index.ts": "export const name = 'good'\n"},
        expect_pass=True, expect_rules=[],
    )),
    ("missing_bundle_patch", dict(
        pkg=dict(GOOD_PKG, dsh={"plugin": True, "kind": "server",
                                 "bundle": {"patch": "./nope.yml"}}),
        patch=GOOD_PATCH, src_files={"lib/index.js": "// x\n"},
        expect_pass=False, expect_rules=["BND-002"],
    )),
    ("exports_array", dict(
        pkg={"name": "@wwumit/e", "exports": {".": [{"import": "./lib/index.js"}, {"default": "./lib/index.js"}]}},
        patch=None, src_files={},
        expect_pass=False, expect_rules=["BND-004"],
    )),
    ("name_mismatch_src", dict(
        pkg=dict(GOOD_PKG, name="@wwumit/good"),
        patch=GOOD_PATCH,
        src_files={"src/sub/index.ts": "export const name = 'wrong-name'\n", "lib/index.js": "// x\n"},
        expect_pass=False, expect_rules=["BND-007"],
    )),
    ("name_mismatch_root", dict(
        pkg={"name": "@wwumit/r", "main": "index.js"},
        patch=None,
        src_files={"index.ts": "export const name = 'r-wrong'\n"},
        expect_pass=False, expect_rules=["BND-007"],  # 根入口的 name 导出不一致（验证 root 扫描命中）
    )),
]


def main():
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        fails = 0
        for name, c in CASES:
            d = _mk(base, name, c["pkg"], c.get("patch"), c.get("src_files"))
            r = _run(d)
            got_rules = {i["rule"] for i in r["issues"]}
            ok_pass = (r["conclusion"] == "PASS") == c["expect_pass"]
            ok_rules = all(rule in got_rules for rule in c["expect_rules"])
            status = "✅" if (ok_pass and ok_rules) else "❌"
            if status == "❌":
                fails += 1
            print(f"{status} {name}: score={r['score']} conclusion={r['conclusion']} "
                  f"rules={sorted(got_rules)} (expect {c['expect_rules']})")
        print(f"\n{len(CASES) - fails}/{len(CASES)} 通过")
        sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
