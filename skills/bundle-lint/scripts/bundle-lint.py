#!/usr/bin/env python3
"""
bundle-lint — DSH 插件 bundle 结构一致性校验器
================================================
在发布插件前，校验 bundle 三件套是否自洽，避免被市场/目录收录时打回：

  BND-001  cordis.patch.yml 存在且可解析（含 insert 结构）
  BND-002  package.json 的 dsh 插件配置完整（plugin:true / kind / bundle.patch）
  BND-003  files 清单覆盖 cordis.patch.yml 与入口（发布后 bundle 不丢）
  BND-004  入口文件存在（main 字段指向的文件）
  BND-005  bundle id/name 与 package name 一致（装进去的包名对得上）
  BND-006  结构符合 DSH STANDARD（dsh 声明优先于特征推断）

纯 Python 标准库，无第三方依赖，无网络请求。输出与 skill-compliance 同风格（评分 + 结论 + 问题列表）。
"""

import argparse
import json
import os
import re
import sys


def parse_cordis_patch(path: str) -> list:
    """极简解析 cordis.patch.yml 的 insert 结构（id/name）。零依赖，不做完整 YAML。"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except OSError:
        return None
    inserts = []
    cur = {}
    in_insert = False
    for ln in lines:
        s = ln.strip()
        if s.startswith("#") or not s:
            continue
        if s.startswith("- insert:"):
            if cur:
                inserts.append(cur)
            cur = {"_kind": "insert"}
            in_insert = True
            continue
        if in_insert:
            m = re.match(r"^\s+- id:\s*(.+)$", ln)
            if m:
                cur["id"] = m.group(1).strip().strip("'\"")
                continue
            m = re.match(r"^\s+name:\s*(.+)$", ln)
            if m:
                cur["name"] = m.group(1).strip().strip("'\"")
                continue
            if re.match(r"^\s*- ", ln) and "id" in cur:
                inserts.append(cur)
                cur = {"_kind": "insert"}
                continue
    if cur and "id" in cur:
        inserts.append(cur)
    return inserts


def load_json(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def check(target: str) -> dict:
    issues = []

    def add(rule, severity, found, recommendation):
        issues.append({
            "rule": rule, "severity": severity, "found": found,
            "recommendation": recommendation,
        })

    pkg = load_json(os.path.join(target, "package.json"))
    patch_path = os.path.join(target, "cordis.patch.yml")
    inserts = parse_cordis_patch(patch_path)

    # BND-001 cordis.patch.yml
    if inserts is None:
        add("BND-001", "high", "cordis.patch.yml 缺失或无法解析",
            "发布前提供 cordis.patch.yml（含 - insert: 结构的 bundle 清单）")
    elif not inserts:
        add("BND-001", "medium", "cordis.patch.yml 存在但未解析出 insert 条目",
            "确认 insert 结构：`- insert:` 下含 id/name 条目")
    else:
        for ins in inserts:
            if "id" not in ins or "name" not in ins:
                add("BND-001", "medium",
                    f"insert 条目缺少 id 或 name: {ins}",
                    "每条 insert 需同时提供 id（注册名）与 name（包名）")

    # BND-002 package.json dsh 配置
    if pkg is None:
        add("BND-002", "high", "package.json 缺失",
            "插件必须有 package.json（含 dsh.plugin 配置）")
    else:
        dsh = pkg.get("dsh", {})
        if not dsh.get("plugin"):
            add("BND-002", "high", "package.json 缺少 dsh.plugin: true",
                "按 STANDARD 声明插件身份：`\"dsh\": {\"plugin\": true, ...}`")
        kind = dsh.get("kind")
        if kind not in ("server", "client", "mixed"):
            add("BND-002", "medium", f"dsh.kind 缺失或非常见值: {kind!r}",
                "声明 kind（server/client/mixed），帮助运行时机判定")
        bundle = dsh.get("bundle", {})
        if not bundle.get("patch"):
            add("BND-002", "medium", "dsh.bundle.patch 缺失",
                "声明 bundle 清单路径：`\"bundle\": {\"patch\": \"./cordis.patch.yml\"}`")

    # BND-003 files 覆盖
    if pkg is not None:
        files = pkg.get("files", [])
        if isinstance(files, list) and files:
            missing_files = [f for f in files if not os.path.exists(os.path.join(target, f))]
            for mf in missing_files:
                add("BND-003", "high", f"files 声明但文件缺失: {mf}",
                    "files 清单与实际文件一致（否则 npm 包发布后缺文件）")
            if "cordis.patch.yml" not in files and "cordis.patch.yml" in os.listdir(target):
                add("BND-003", "medium",
                    "cordis.patch.yml 在仓库根但不在 files 清单",
                    "把 cordis.patch.yml 加入 files（否则 npm 发布不含 bundle）")

    # BND-004 入口文件
    if pkg is not None:
        main = pkg.get("main")
        if main and not os.path.exists(os.path.join(target, main)):
            add("BND-004", "high", f"main 入口缺失: {main}",
                "构建产物（lib/index.js 等）需存在；发布前跑 npm run build")
        exports = pkg.get("exports")
        if isinstance(exports, dict):
            for k, v in exports.items():
                if isinstance(v, dict):
                    for sub in v.values():
                        if isinstance(sub, str) and sub.startswith(".") and not os.path.exists(os.path.join(target, sub)):
                            add("BND-004", "medium", f"exports 引用的文件缺失: {sub}",
                                "exports 指向的实际文件需存在")

    # BND-005 bundle id/name 与 package name 一致
    if pkg is not None and inserts:
        pkg_name = pkg.get("name", "")
        for ins in inserts:
            ins_name = ins.get("name", "")
            if ins_name and pkg_name and ins_name != pkg_name:
                add("BND-005", "high",
                    f"bundle name ({ins_name}) 与 package name ({pkg_name}) 不一致",
                    "装进去的包名必须对得上，否则 cordis 解析失败")
            if not ins.get("id"):
                add("BND-005", "medium", "bundle insert 缺少 id", "提供注册 id（如 dsh-<线名>）")

    # BND-007 插件 name 导出与包名一致（防复制遗留：name 导出指向别的插件）
    if pkg is not None:
        pkg_name = pkg.get("name", "")
        if pkg_name.startswith("@"):
            bare = pkg_name.split("/")[1] if "/" in pkg_name else pkg_name
        else:
            bare = pkg_name
        # 在 src/ 下找 name 导出
        import glob
        hits = []
        for f in glob.glob(os.path.join(target, "src", "*.ts")):
            try:
                lines = open(f, encoding="utf-8").read().split("\n")
            except OSError:
                continue
            for i, ln in enumerate(lines, 1):
                m = re.search(r"export\s+const\s+name\s*=\s*['\"]([^'\"]+)['\"]", ln)
                if m:
                    hits.append((f, i, m.group(1)))
        for f, ln, exported in hits:
            if exported != bare:
                add("BND-007", "high",
                    f"插件 name 导出 '{exported}' 与包名 '{bare}' 不一致（{os.path.basename(f)}:{ln}）",
                    "export const name 必须等于插件标识（包名去 scope），防复制遗留导致身份错乱")
        if not hits:
            add("BND-007", "low", "未在 src/ 找到 export const name",
                "标准插件应在入口导出 name（cordis 插件身份）")

    # BND-006 结构合规提示
    if pkg is not None:
        has_topic = pkg.get("keywords", []) or []
        if not any("dsh" in str(k).lower() for k in has_topic):
            add("BND-006", "low", "package.json keywords 缺少 dsh 标识",
                "加 dsh-plugin / deepseek-harness 关键词便于生态发现")

    # 评分
    severity_w = {"high": 20, "medium": 8, "low": 3}
    score = max(0, 100 - sum(severity_w.get(i["severity"], 0) for i in issues))
    conclusion = "PASS" if score >= 90 and not any(i["severity"] == "high" for i in issues) else (
        "NEEDS_FIX" if any(i["severity"] == "high" for i in issues) else "REVIEW"
    )
    return {"score": score, "conclusion": conclusion, "issues": issues}


def main():
    ap = argparse.ArgumentParser(description="DSH 插件 bundle 结构一致性校验器")
    ap.add_argument("--dir", "-d", required=True, help="目标插件目录")
    ap.add_argument("--format", "-f", choices=["text", "json"], default="text")
    args = ap.parse_args()

    if not os.path.isdir(args.dir):
        print(f"错误：目录不存在 {args.dir}", file=sys.stderr)
        sys.exit(1)

    result = check(args.dir)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print("╔══ bundle-lint ══ " + args.dir)
    print(f"║ 评分：{result['score']}/100  |  结论：{result['conclusion']}")
    if not result["issues"]:
        print("║ ✅ bundle 结构一致，未发现问题")
    for i in result["issues"]:
        sev = i["severity"].upper()
        print(f"║ [{sev:>7}] ({i['rule']})")
        print(f"║   → {i['found']}")
        print(f"║   建议：{i['recommendation']}")
    print("╚══════════════════════════════")


if __name__ == "__main__":
    main()
