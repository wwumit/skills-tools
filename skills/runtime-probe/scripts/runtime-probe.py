#!/usr/bin/env python3
"""
runtime-probe — DSH 插件实机验证引导器
========================================
对任意 DSH 插件目录：生成标准 verify 脚本 → 在真实 DSH SkillRegistry 里注册插件
→ list()/get() 实测 → 输出证据契约报告（verifiedBy/verifiedAt/reportUrl/schemaVersion）。
替代"每插件复制一份 verify-dsh.ts"的做法——本工具是通用引导器。

依赖：DSH 开发环境（node_modules 含 tsx/@deepseek-ai/cordis/@deepseek-ai/dsh-skill）。
纯 Python 标准库；无网络请求（DSH 环境本地运行）。
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys

__version__ = "1.1.0"

VERIFY_TEMPLATE = r'''/**
 * 由 runtime-probe 生成的 DSH 实机验证脚本（通用模板）。
 * 注册目标插件 → ctx.skills.list()/get() 实测 → 输出证据契约 JSON。
 */
import {{ Context }} from '@deepseek-ai/cordis'
import SkillRegistry from '@deepseek-ai/dsh-skill'
import * as target from '{entry}'

const CATALOG_URL = '{catalog_url}'

async function main(): Promise<void> {{
  const ctx = new Context()
  await ctx.plugin(SkillRegistry)

  // 注册目标插件（cordis 标准：ctx.plugin(plugin, config)）
  await ctx.plugin(target as any, {{ catalogUrl: CATALOG_URL }})

  const cwd = '{cwd}'
  const skills = await ctx.skills.list({{ cwd }})
  const names = skills.map((s: any) => s.name)

  const samples: {{ name: string; bytes: number; head: string }}[] = []
  const probeCount = Math.min(names.length, 3)
  for (const nm of names.slice(0, probeCount)) {{
    try {{
      const one = await ctx.skills.get(nm, {{ cwd }})
      if (one) {{
        samples.push({{ name: nm, bytes: one.content.length, head: one.content.slice(0, 80).replace(/\n/g, ' ') }})
      }}
    }} catch {{
      // 单技能 get 失败不中断整体
    }}
  }}


  const report = {{
    verifiedBy: 'runtime-probe@{version}',
    verifiedAt: new Date().toISOString(),
    reportUrl: CATALOG_URL,
    schemaVersion: 'probe-v1',
    plugin: '{package_name}',
    skillCount: names.length,
    skills: names,
    samples,
    pass: samples.length > 0,
  }}
  console.log('RUNTIME_PROBE_RESULT:' + JSON.stringify(report))
  if (!report.pass) process.exitCode = 1
}}

main().catch((err) => {{
  console.error('❌ runtime-probe 失败:', err)
  process.exit(1)
}})
'''


def find_main(pkg: dict, target: str) -> str:
    """解析插件入口（main / exports["."].default / 常见路径）"""
    for key in ("main",):
        v = pkg.get(key)
        if v and os.path.exists(os.path.join(target, v)):
            return v
    def _iter_paths(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for sub in v.values():
                yield from _iter_paths(sub)
        elif isinstance(v, list):
            for item in v:
                yield from _iter_paths(item)

    exp = pkg.get("exports")
    if isinstance(exp, dict):
        for cand in _iter_paths(exp.get(".")):
            if isinstance(cand, str) and cand.startswith(".") and os.path.exists(os.path.join(target, cand)):
                return cand.lstrip("./") if cand.startswith("./") else cand
    for cand in ("lib/index.js", "dist/index.js", "index.js"):
        if os.path.exists(os.path.join(target, cand)):
            return cand
    return None


def ensure_tsx_available(target: str, harness: str) -> str:
    """定位 tsx 可执行文件；缺则提示链接 DSH node_modules。"""
    tsx = os.path.join(target, "node_modules", ".bin", "tsx")
    if not os.path.exists(tsx):
        tsx = os.path.join(harness, "node_modules", ".bin", "tsx")
    if not os.path.exists(tsx):
        return None
    return tsx


def probe(target: str, catalog_url: str, harness: str) -> dict:
    pkg_path = os.path.join(target, "package.json")
    if not os.path.exists(pkg_path):
        raise SystemExit(f"错误：{target}/package.json 不存在")
    with open(pkg_path, encoding="utf-8") as f:
        pkg = json.load(f)

    entry = find_main(pkg, target)
    if not entry:
        raise SystemExit(f"错误：无法定位插件入口（main/exports），{pkg.get('name', target)}")

    if not entry.startswith(('.', '/')) and not entry.startswith('file:'):
        entry = './' + entry

    tsx = ensure_tsx_available(target, harness)
    if not tsx:
        raise SystemExit(
            f"错误：找不到 tsx。请先准备 DSH 环境：\n"
            f"  cd {target} && ln -s {harness}/node_modules node_modules"
        )

    script = VERIFY_TEMPLATE.format(
        entry=entry,
        catalog_url=catalog_url,
        cwd=os.path.abspath(target),
        package_name=pkg.get("name", ""),
        version=__version__,
    )
    probe_path = os.path.join(target, "runtime-probe.mts")
    with open(probe_path, "w", encoding="utf-8") as f:
        f.write(script)

    tsconfig = os.path.join(harness, "tsconfig.json")
    cmd = [tsx, "--tsconfig", tsconfig, probe_path]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    marker = "RUNTIME_PROBE_RESULT:"
    report = None
    for line in proc.stdout.splitlines():
        if marker in line:
            try:
                report = json.loads(line.split(marker, 1)[1])
            except Exception:
                report = None
    if report is None:
        report = {
            "pass": False,
            "verifiedBy": "runtime-probe@1.0.0",
            "verifiedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "schemaVersion": "probe-v1",
            "error": (proc.stdout + proc.stderr)[-500:],
        }
    return report


def main():
    ap = argparse.ArgumentParser(description="DSH 插件实机验证引导器")
    ap.add_argument("--dir", "-d", required=True, help="目标插件目录")
    ap.add_argument("--catalog", "-c", required=True, help="插件的 catalog JSON URL")
    ap.add_argument("--harness", default="/Users/wuwei/deepseek-harness",
                    help="DeepSeek Harness 仓库路径（含 node_modules）")
    ap.add_argument("--format", "-f", choices=["text", "json"], default="text")
    ap.add_argument("--keep", action="store_true", help="保留生成的 runtime-probe.mts（默认运行后清理）")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        raise SystemExit(f"错误：目录不存在 {args.dir}")

    report = probe(args.dir, args.catalog, args.harness)
    probe_file = os.path.join(args.dir, "runtime-probe.mts")
    if not args.keep and os.path.exists(probe_file):
        os.remove(probe_file)

    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("╔══ runtime-probe ══ " + args.dir)
        ok = "✅ PASS" if report.get("pass") else "❌ FAIL"
        print(f"║ 结论：{ok} | 插件：{report.get('plugin', '?')}")
        print(f"║ 技能数：{report.get('skillCount', 0)}")
        if report.get("skills"):
            print(f"║ 技能：{', '.join(report['skills'][:12])}")
        if report.get("sample"):
            s = report["sample"]
            print(f"║ 抽查：get('{s['name']}') → {s['bytes']} 字节 | {s['head'][:50]}")
        if report.get("error"):
            print(f"║ 错误：{report['error'][:200]}")
        print(f"║ 证据：verifiedBy={report.get('verifiedBy')} verifiedAt={report.get('verifiedAt')}")
        print("╚════════════════════════════════════")
    sys.exit(0 if report.get("pass") else 1)


if __name__ == "__main__":
    main()
