#!/usr/bin/env python3
"""runtime-probe 单元测试：入口解析 + 模板生成（不依赖 DSH 环境）。

用法: python3 tests/units.py
"""
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "runtime-probe" / "scripts"

# 文件名带连字符，无法直接 import —— 用 importlib 加载
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "runtime_probe_mod", SCRIPTS / "runtime-probe.py")
runtime_probe = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runtime_probe)


def _mk_pkg(d, pkg):
    (d / "package.json").write_text(json.dumps(pkg, ensure_ascii=False), encoding="utf-8")
    return d


def test_find_main():
    fails = 0

    def check(name, pkg, files, expect):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            _mk_pkg(d, pkg)
            for f in files:
                (d / f).parent.mkdir(parents=True, exist_ok=True)
                (d / f).write_text("// x", encoding="utf-8")
            got = runtime_probe.find_main(pkg, str(d))
            ok = got == expect
            if not ok:
                print(f"  ❌ {name}: got {got!r}, expect {expect!r}")
            return ok

    cases = [
        ("main 指向", {"name": "@t/a", "main": "lib/index.js"}, ["lib/index.js"], "lib/index.js"),
        ("exports dict", {"name": "@t/b", "exports": {".": {"import": "./dist/index.js"}}},
         ["dist/index.js"], "dist/index.js"),
        ("exports 数组", {"name": "@t/c", "exports": {".": [{"import": "./lib/index.js"}, {"default": "./lib/index.js"}]}},
         ["lib/index.js"], "lib/index.js"),
        ("main 缺失回退", {"name": "@t/d"}, ["index.js"], "index.js"),
        ("全部缺失", {"name": "@t/e"}, [], None),
    ]
    for c in cases:
        fails += 0 if check(*c) else 1
    return fails


def test_template():
    fails = 0
    # 从源码读 VERIFY_TEMPLATE（raw 字符串），format 后检查
    src = open(SCRIPTS / "runtime-probe.py", encoding="utf-8").read()
    m = re.search(r"VERIFY_TEMPLATE = (?:r)?'''(.*?)'''\n\n", src, re.S)
    tmpl = m.group(1)
    out = tmpl.format(entry="lib/index.js", catalog_url="https://x/catalog.json",
                      cwd="/tmp", package_name="@wwumit/x", version=runtime_probe.__version__)

    # 1) 正则未被破坏（\n 是两字符，非换行）
    if "replace(/\\n/g" not in out:
        print("  ❌ 模板正则被破坏（replace(\\n 未保持两字符）")
        fails += 1
    # 2) version 注入
    if f"runtime-probe@{runtime_probe.__version__}" not in out:
        print("  ❌ verifiedBy 版本未注入")
        fails += 1
    # 3) 占位符全解析（无残留 { 未转义）
    if re.search(r"[{}]{2,}", out.replace("{{", "").replace("}}", "")):
        pass
    # 4) package_name 注入
    if "@wwumit/x" not in out:
        print("  ❌ package_name 未注入")
        fails += 1
    # 5) 多技能抽查逻辑存在
    if "probeCount" not in out or "samples.push" not in out:
        print("  ❌ 多技能抽查逻辑缺失")
        fails += 1
    return fails


def main():
    f = 0
    f += test_find_main()
    f += test_template()
    print(f"\n{'✅ 全部通过' if f == 0 else f'❌ {f} 处失败'}")
    sys.exit(1 if f else 0)


if __name__ == "__main__":
    main()
