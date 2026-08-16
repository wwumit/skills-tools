#!/usr/bin/env python3
"""
Skill Compliance Check — 上架合规检查器
============================================
在将 skill 上传至 SkillHub 前，检查是否满足国内监管合规要求。

检查项:
  FINANCE     — 敏感金融用语（荐股、投资建议、保证收益等）
  DISCLAIMER  — 免责声明是否到位
  EXAGGERATION— 极限词、夸大描述
  SECURITY    — 安全红线（subprocess/exec/eval、JSON 合法性等）
  RECOMMENDATIONS — 改进建议

输出:
  - 终端/JSON/report 文件
  - 综合评分 (0-100) 与评估结论 (REJECT / NEEDS_FIX / PASS)

规则来源: rules/skillhub-rules.json
纯 Python 标准库，无外部依赖，无网络请求。
"""

import argparse
import typing
import json
import os
import re
import sys
import importlib.util  # for plugin loading

# ── 免责声明 ────────────────────────────────────────────────────
DISCLAIMER = (
    "免责声明：本工具仅为辅助检查参考，不构成任何形式的合规保证。"
    "最终合规责任由 skill 开发者自行承担。"
)


# ═══════════════════════════════════════════════════════════════
#  检查逻辑
# ═══════════════════════════════════════════════════════════════

class ComplianceChecker:
    """SkillHub 上架合规检查器"""

    SEVERITY_DEDUCTIONS = {"critical": 30, "high": 15, "medium": 5, "low": 2}
    SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)
        self.skill_name = os.path.basename(self.target_dir)
        self.issues: list[dict] = []
        self.rules_data = self._load_rules()
        self.rules = self.rules_data.get("rules", [])
        self.rule_map = {r["id"]: r for r in self.rules}
        # 从 JSON 中读取评分阈值
        scoring_model = self.rules_data.get("scoring_model", {})
        thresholds = scoring_model.get("conclusion_thresholds", {})
        self.pass_threshold = self._extract_score(
            thresholds.get("PASS", "score >= 70")
        )
        self.needs_fix_threshold = self._extract_score(
            thresholds.get("NEEDS_FIX", "score >= 40")
        )

    @staticmethod
    def _extract_score(threshold_str: str) -> int:
        """从类似 'score >= 70' 的文本中提取数值"""
        m = re.search(r"(\d+)", threshold_str)
        return int(m.group(1)) if m else 70

    def _load_rules(self) -> dict:
        """加载 rules/skillhub-rules.json 规则库"""
        path = os.path.join(
            os.path.dirname(__file__), "..", "rules", "skillhub-rules.json"
        )
        if not os.path.exists(path):
            return {"rules": []}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[WARN] 规则文件加载失败: {e}", file=sys.stderr)
            return {"rules": []}

    # ── 辅助 ────────────────────────────────────────────────

    def _add(
        self,
        category: str,
        severity: str,
        file: str,
        line: int,
        found: str,
        recommendation: str,
        redline: bool = False,
        legal_source: str = "",
        authority_type: str = "law",
        plugin: str = "",
    ):
        entry = {
            "category": category,
            "severity": severity,
            "file": file,
            "line": line,
            "found": found,
            "recommendation": recommendation,
            "redline": redline,
            "legal_source": legal_source,
            "authority_type": authority_type,
        }
        if plugin:
            entry["plugin"] = plugin
        self.issues.append(entry)

    def _read(self, *parts: str) -> list[str]:
        path = os.path.join(self.target_dir, *parts)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()
        except Exception:
            return []

    def _text(self, *parts: str) -> str:
        return "".join(self._read(*parts))

    # ── 通用模式匹配引擎 ───────────────────────────────────

    def _scan_patterns(self, category: str) -> list[dict]:
        """对指定 category 的所有 pattern-based 规则执行扫描。

        返回匹配结果列表，每个结果包含:
          rule_id, category, severity, redline, pattern,
          file, line, found, recommendation, legal_source
        """
        found = []
        cat_rules = [
            r
            for r in self.rules
            if r["category"] == category and r.get("patterns")
        ]

        for rule in cat_rules:
            patterns = rule["patterns"]
            exclude_pats = [
                re.compile(e, re.IGNORECASE)
                for e in rule.get("exclude_patterns", [])
            ]
            severity = rule["severity"]
            redline = rule.get("redline", False)
            legal_source = rule.get("legal_source", "")
            authority_type = rule.get("authority_type", "regulation")
            scan_targets = rule.get("scan_targets", [])
            scan_all = "all" in scan_targets
            scan_docs = "docs" in scan_targets
            scan_scripts = "scripts" in scan_targets

            for pat_str in patterns:
                pat = re.compile(pat_str, re.IGNORECASE)

                # 收集要扫描的文件
                targets: list[str] = []
                if scan_all or scan_docs:
                    targets.extend(["SKILL.md", "README.md", "package.json"])
                if scan_all or scan_scripts:
                    script_dir = os.path.join(self.target_dir, "scripts")
                    if os.path.isdir(script_dir):
                        for f in sorted(os.listdir(script_dir)):
                            if f.endswith(".py"):
                                targets.append(f"scripts/{f}")

                for fname in targets:
                    lines = self._read(fname)
                    for lineno, line in enumerate(lines, 1):
                        m = pat.search(line)
                        if not m:
                            continue
                        # 检查排除模式
                        if any(ep.search(line) for ep in exclude_pats):
                            continue
                        # 自描述文本检查：合规类skill描述自身功能时不是违规
                        self_desc_markers = rule.get("self_describing_markers", [])
                        if self_desc_markers and any(
                            re.search(m, line, re.IGNORECASE) for m in self_desc_markers
                        ):
                            continue
                        desc = rule.get(
                            "description",
                            "请参照相关法律法规修改",
                        )
                        found.append({
                            "rule_id": rule["id"],
                            "category": category,
                            "severity": severity,
                            "redline": redline,
                            "pattern": pat_str,
                            "file": fname,
                            "line": lineno,
                            "found": line.strip()[:80],
                            "recommendation": desc,
                            "legal_source": legal_source,
                            "authority_type": authority_type,
                        })
        return found

    # ── 检查 1：敏感金融用语 ─────────────────────────────────

    def check_finance(self):
        for h in self._scan_patterns("FINANCE"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "law"),
            )

    # ── 检查 2：免责声明 ────────────────────────────────────

    def check_disclaimer(self):
        disc_rules = {
            r["id"]: r for r in self.rules if r["category"] == "DISCLAIMER"
        }
        r_inv = disc_rules.get("DISC-001", {})
        r_legal = disc_rules.get("DISC-002", {})
        r_pos = disc_rules.get("DISC-003", {})

        # 检查独立的 DISCLAIMER.md 文件
        disclaimer_md_text = self._text("DISCLAIMER.md")
        has_disclaimer_file = bool(
            disclaimer_md_text
            and re.search(r"免责|不构成|disclaimer|DISCLAIMER|声明", disclaimer_md_text)
        )

        for fname in ("SKILL.md", "README.md"):
            text = self._text(fname)
            if not text:
                continue

            lines = text.splitlines()
            has_investment = False
            has_legal = False
            position = "none"

            # 检查文档是否引用了 DISCLAIMER.md
            refs_disclaimer_file = bool(
                re.search(r"DISCLAIMER\.md|免责.*文件|见.*免责", text)
            )
            uses_external = has_disclaimer_file and refs_disclaimer_file

            for lineno, l in enumerate(lines, 1):
                if re.search(r"不构成投资建议", l):
                    has_investment = True
                    if lineno <= max(5, len(lines) // 4):
                        position = "early"
                    else:
                        position = "late"
                if re.search(r"不构成法律建议", l):
                    has_legal = True

            # 如果引用了独立的 DISCLAIMER.md，视为已有法律免责
            if uses_external:
                has_legal = True

            # 判断是否需要投资免责（涉及金融/投资内容）
            is_finance = any(
                re.search(p, text, re.IGNORECASE)
                for p in [r"股票", r"投资", r"交易", r"买卖", r"行情"]
            )
            if is_finance:
                if not has_investment:
                    self._add(
                        category="DISCLAIMER",
                        severity=r_inv.get("severity", "high"),
                        file='DISCLAIMER.md' if uses_external else fname,
                        line=1,
                        found="缺少投资免责声明",
                        recommendation=r_inv.get(
                            "description",
                            "请在文档显眼位置添加：「免责声明：本工具仅供学习参考，"
                            "不构成任何投资建议。投资者应当自行承担投资风险。」",
                        ),
                        legal_source=r_inv.get("legal_source", ""),
                        authority_type="regulation",
                    )
                elif position == "late":
                    self._add(
                        category="DISCLAIMER",
                        severity=r_pos.get("severity", "medium"),
                        file=fname,
                        line=1,
                        found="免责声明位置不显眼",
                        recommendation=r_pos.get(
                            "description",
                            "将投资免责声明移到文档开头显眼位置",
                        ),
                        legal_source=r_pos.get("legal_source", ""),
                        authority_type="regulation",
                    )

            # 法律免责声明（仅在不引用 DISCLAIMER.md 时检查）
            if not uses_external and not re.search(r"不构成法律建议", text):
                self._add(
                    category="DISCLAIMER",
                    severity=r_legal.get("severity", "high"),
                    file=fname,
                    line=1,
                    found="缺少法律免责声明",
                    recommendation=r_legal.get(
                        "description",
                        "建议添加「免责声明：本工具不构成法律建议」",
                    ),
                    legal_source=r_legal.get("legal_source", ""),
                    authority_type="regulation",
                )

    # ── 检查 3：极限词/夸大描述 ─────────────────────────────

    def check_exaggeration(self):
        for h in self._scan_patterns("EXAGGERATION"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "law"),
            )

    # ── 检查 4：安全红线 ────────────────────────────────────

    def check_security(self):
        # Pattern-based 安全规则扫描 (SEC-001, SEC-002, SEC-003)
        for h in self._scan_patterns("SECURITY"):
            # 特殊处理：有安全注释的 eval 降级为 medium
            if h.get("pattern") and "eval" in h["pattern"]:
                fname = h["file"]
                lines = self._read(fname)
                if lines and h["line"] >= 2:
                    prev_line = lines[h["line"] - 2]
                    if re.search(
                        r"#\s*安全评估|#\s*safe.*eval|#\s*只允许", prev_line
                    ):
                        h["severity"] = "medium"
                        h["redline"] = False
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "platform_policy"),
            )

        # package.json 合法性
        pkg_lines = self._read("package.json")
        if pkg_lines:
            try:
                json.loads("".join(pkg_lines))
            except json.JSONDecodeError as e:
                self._add(
                    category="SECURITY",
                    severity="high",
                    file="package.json",
                    line=1,
                    found=f"JSON 解析错误: {e}",
                    recommendation="修复 package.json 使其为合法 JSON",
                    authority_type="best_practice",
                )

            # 版本号格式
            pkg_text = "".join(pkg_lines)
            try:
                pkg = json.loads(pkg_text)
                ver = pkg.get("version", "")
                if not re.match(r"^\d+\.\d+\.\d+$", ver):
                    self._add(
                        category="SECURITY",
                        severity="medium",
                        file="package.json",
                        line=1,
                        found=f"版本号格式异常: {ver}",
                        recommendation="使用 semver 格式: x.y.z",
                        authority_type="best_practice",
                    )
            except (json.JSONDecodeError, AttributeError):
                pass

        # SEC-004: 未固定版本依赖
        rule_sec004 = self.rule_map.get("SEC-004", {})
        req_lines = self._read("requirements.txt")
        if req_lines:
            unpinned = [
                l.strip()
                for l in req_lines
                if l.strip()
                and not l.startswith("#")
                and "==" not in l.strip()
            ]
            for u in unpinned[:5]:
                self._add(
                    category="SECURITY",
                    severity=rule_sec004.get("severity", "medium"),
                    file="requirements.txt",
                    line=1,
                    found=f"未固定版本: {u}",
                    recommendation=rule_sec004.get(
                        "description",
                        "请固定依赖版本号，如 numpy==1.24.3",
                    ),
                    legal_source=rule_sec004.get("legal_source", ""),
                    authority_type="platform_policy",
                )


    # ── 检查 5a：数据隐私合规（PRIVACY）──────────────────────────

    def check_privacy(self):
        """基于规则库 PRIVACY 类别的 pattern-based 扫描"""
        for h in self._scan_patterns("PRIVACY"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "law"),
            )

    # ── 检查 5b：监管合规（REGULATORY）─────────────────────────

    def check_regulatory(self):
        """基于规则库 REGULATORY 类别的 pattern-based 扫描"""
        for h in self._scan_patterns("REGULATORY"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "regulation"),
            )

    # ── 检查 5a：供应链安全 ──────────────────────────────────

    def check_supply_chain(self):
        """基于规则库 SUPPLY_CHAIN 类别的 pattern-based 扫描"""
        for h in self._scan_patterns("SUPPLY_CHAIN"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "platform_policy"),
            )

    # ── 检查 5b：MCP 权限 ───────────────────────────────────

    def check_mcp(self):
        """基于规则库 MCP 类别的 pattern-based 扫描"""
        for h in self._scan_patterns("MCP"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "platform_policy"),
            )

    # ── 检查 5c：输出处理 ───────────────────────────────────

    def check_output(self):
        """基于规则库 OUTPUT 类别的 pattern-based 扫描"""
        for h in self._scan_patterns("OUTPUT"):
            self._add(
                category=h["category"],
                severity=h["severity"],
                redline=h["redline"],
                file=h["file"],
                line=h["line"],
                found=h["found"],
                recommendation=h["recommendation"],
                legal_source=h["legal_source"],
                authority_type=h.get("authority_type", "platform_policy"),
            )

    # ── 检查 5d：描述-行为不一致 ────────────────────────────


    def check_description_mismatch(self):
        """ADVISORY 类别 — 检测 skill 文档声明与实际代码行为之间的不一致。
        例如声称 'network: none' 但脚本中包含 requests.get 实际调用。

        特别注意排除合规检查工具自身的代码，这些工具包含网络相关的
        正则表达式模式串 (r"...") 而非实际网络调用。"""
        text = self._text("SKILL.md")
        if not text:
            return

        # 提取声明约束
        declared_network_none = bool(re.search(r'network:\s*none', text))

        # 检查实际代码中的网络调用（排除合规检查工具的模式串定义）
        has_network_code = False
        script_dir = os.path.join(self.target_dir, "scripts")
        if os.path.isdir(script_dir):
            for f in sorted(os.listdir(script_dir)):
                if not f.endswith(".py"):
                    continue
                file_lines = self._read("scripts", f)
                for file_line in file_lines:
                    ls = file_line.strip()
                    # 跳过注释、import、模式串定义、docstring
                    if ls.startswith("#"):
                        continue
                    if re.match(r'^(from|import)\s', ls):
                        continue
                    if re.match(r"^r['\"]", ls):
                        continue
                    # 检测实际网络函数调用（带括号调用）
                    if re.search(r'requests\.(get|post|put|delete)\s*\(', ls, re.IGNORECASE):
                        has_network_code = True
                        break
                    if re.search(r'urllib\.(request|parse)\.urlopen\s*\(', ls, re.IGNORECASE):
                        has_network_code = True
                        break
                    if re.search(r'aiohttp\.(ClientSession|request)\s*\(', ls, re.IGNORECASE):
                        has_network_code = True
                        break

        # 报告不一致
        if declared_network_none and has_network_code:
            self._add(
                category="ADVISORY",
                severity="low",
                file="SKILL.md",
                line=1,
                found="声明 network: none 但脚本包含实际网络请求调用",
                recommendation=(
                    "请确保功能描述与实际行为一致。"
                    "若需要网络功能，应如实声明 network: allowed 并说明用途。"
                ),
                authority_type="platform_policy",
            )

    # ── 检查 5：通用建议 ────────────────────────────────────

    def check_recommendations(self):
        """基于现有 issue 产生改进建议"""
        has_disclaimer = any(
            i["category"] == "DISCLAIMER" for i in self.issues
        )
        has_finance = any(
            i["category"] == "FINANCE" for i in self.issues
        )
        has_exaggeration = any(
            i["category"] == "EXAGGERATION" for i in self.issues
        )
        has_privacy = any(
            i["category"] == "PRIVACY" for i in self.issues
        )
        has_regulatory = any(
            i["category"] == "REGULATORY" for i in self.issues
        )
        has_redline = any(
            i.get("redline", False) for i in self.issues
        )

        if has_finance and not has_disclaimer:
            self._add(
                category="RECOMMENDATIONS",
                severity="high",
                file="SKILL.md",
                line=1,
                found="检测到金融用语但缺少对应免责声明",
                recommendation=(
                    "添加「不构成投资建议」声明后再上传"
                ),
                authority_type="best_practice",
            )

        if has_exaggeration:
            self._add(
                category="RECOMMENDATIONS",
                severity="medium",
                file="SKILL.md",
                line=1,
                found="检测到极限词/夸张用语",
                recommendation=(
                    "参考《广告法》第九条，删除所有绝对化用语"
                ),
                authority_type="best_practice",
            )

        # 文件完整性检查
        rule_rec001 = self.rule_map.get("REC-001", {})
        rule_rec003 = self.rule_map.get("REC-003", {})
        rule_rec002 = self.rule_map.get("REC-002", {})

        readme_lines = self._read("README.md")
        if not readme_lines:
            self._add(
                category="RECOMMENDATIONS",
                severity=rule_rec001.get("severity", "medium"),
                file="README.md",
                line=1,
                found="README.md 文件不存在",
                recommendation=rule_rec001.get(
                    "description", "新增 README.md 说明用法"
                ),
                legal_source=rule_rec001.get("legal_source", ""),
                authority_type="best_practice",
            )
        elif len(readme_lines) < 10:
            self._add(
                category="RECOMMENDATIONS",
                severity=rule_rec003.get("severity", "low"),
                file="README.md",
                line=1,
                found="README.md 内容较少",
                recommendation=rule_rec003.get(
                    "description", "补充详细使用说明和示例"
                ),
                legal_source=rule_rec003.get("legal_source", ""),
                authority_type="best_practice",
            )

        # CHANGELOG 检查 (REC-002)
        if not self._read("CHANGELOG.md"):
            self._add(
                category="RECOMMENDATIONS",
                severity=rule_rec002.get("severity", "low"),
                file="CHANGELOG.md",
                line=1,
                found="CHANGELOG.md 文件不存在",
                recommendation=rule_rec002.get(
                    "description", "新增 CHANGELOG.md 记录版本变更"
                ),
                legal_source=rule_rec002.get("legal_source", ""),
                authority_type="best_practice",
            )

        # requirements.txt 检查 (REC-004)
        rule_rec004 = self.rule_map.get("REC-004", {})
        script_dir = os.path.join(self.target_dir, "scripts")
        has_py = os.path.isdir(script_dir) and any(
            f.endswith(".py") for f in os.listdir(script_dir)
        )
        if has_py and not self._read("requirements.txt"):
            self._add(
                category="RECOMMENDATIONS",
                severity=rule_rec004.get("severity", "low"),
                file="requirements.txt",
                line=1,
                found="检测到 Python 脚本但缺少 requirements.txt",
                recommendation=rule_rec004.get(
                    "description",
                    "添加 requirements.txt 声明外部依赖",
                ),
                legal_source=rule_rec004.get("legal_source", ""),
                authority_type="best_practice",
            )

    # ── 运行所有检查 ────────────────────────────────────────

    def run_all(self):
        self.check_finance()
        self.check_disclaimer()
        self.check_exaggeration()
        self.check_security()
        self.check_privacy()
        self.check_regulatory()
        self.check_supply_chain()
        self.check_mcp()
        self.check_output()
        self.check_description_mismatch()
        self.check_recommendations()
        self.run_plugins()

    # ── 检查 6：Domain Plugins ────────────────────────────────

    def run_plugins(self):
        """发现并执行所有 domain 合规检查插件"""
        plugin_dir = os.path.join(
            os.path.dirname(__file__), "..", "plugins"
        )
        if not os.path.isdir(plugin_dir):
            return

        try:
            # 动态加入 sys.path 以支持 import
            sys.path.insert(0, os.path.dirname(plugin_dir))
            from plugins import discover_plugins
            plugins = discover_plugins()
        except Exception as e:
            print(f"[WARN] 插件系统初始化失败: {e}")
            return

        if not plugins:
            return

        # 在执行前记录当前 issue 数
        before_count = len(self.issues)

        for p in plugins:
            try:
                findings = p.check(self.target_dir, self.issues)
                for f in findings:
                    self._add(
                        category=f["category"],
                        severity=f["severity"],
                        file=f["file"],
                        line=f["line"],
                        found=f.get("found", ""),
                        recommendation=f.get("recommendation", ""),
                        redline=f.get("redline", False),
                        legal_source=f.get("legal_source", ""),
                        authority_type=f.get("authority_type", "regulation"),
                        plugin=f.get("plugin", ""),
                    )
            except Exception as e:
                print(f"[WARN] 插件执行失败: {p.name} -> {e}")

        added = len(self.issues) - before_count
        if added > 0:
            pass  # 插件发现已在问题列表中体现

    # ── 评分 ────────────────────────────────────────────────

    def score(self) -> dict:
        compliance_types = {"law", "regulation", "standard"}
        advisory_types = {"platform_policy", "best_practice"}

        all_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        comp_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        adv_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        redline_count = 0
        adv_redline_count = 0

        for i in self.issues:
            sev = i["severity"]
            atype = i.get("authority_type", "law")
            if sev in all_counts:
                all_counts[sev] += 1
            if i.get("redline"):
                if atype in compliance_types:
                    redline_count += 1
                else:
                    adv_redline_count += 1
            if atype in compliance_types:
                comp_counts[sev] += 1
            elif atype in advisory_types:
                adv_counts[sev] += 1

        total_all = sum(all_counts.values())
        total_comp = sum(comp_counts.values())
        total_adv = sum(adv_counts.values())

        # 合规评分（仅法律/法规/标准）
        comp_penalty = (
            comp_counts["critical"] * 30
            + comp_counts["high"] * 15
            + comp_counts["medium"] * 5
            + comp_counts["low"] * 2
        )
        comp_score = max(0, min(100, 100 - comp_penalty))

        # 合规结论
        if redline_count > 0:
            comp_verdict = "REJECT"
        elif total_comp == 0:
            comp_verdict = "PASS"
        elif comp_score >= self.pass_threshold:
            comp_verdict = "PASS"
        elif comp_score >= self.needs_fix_threshold:
            comp_verdict = "NEEDS_FIX"
        else:
            comp_verdict = "REJECT"

        # 老的评分（全量）作为兼容字段
        all_penalty = (
            all_counts["critical"] * 30
            + all_counts["high"] * 15
            + all_counts["medium"] * 5
            + all_counts["low"] * 2
        )
        all_score = max(0, min(100, 100 - all_penalty))

        return {
            "total_issues": total_all,
            "redlines": redline_count + adv_redline_count,
            "critical": all_counts["critical"],
            "high": all_counts["high"],
            "medium": all_counts["medium"],
            "low": all_counts["low"],
            "score": all_score,
            "verdict": "REJECT" if redline_count > 0
                       and comp_score < self.needs_fix_threshold
                       else "NEEDS_FIX",
            "compliance": {
                "total": total_comp,
                "critical": comp_counts["critical"],
                "high": comp_counts["high"],
                "medium": comp_counts["medium"],
                "low": comp_counts["low"],
                "score": comp_score,
                "verdict": comp_verdict,
                "redlines": redline_count,
            },
            "advisory": {
                "total": total_adv,
                "critical": adv_counts["critical"],
                "high": adv_counts["high"],
                "medium": adv_counts["medium"],
                "low": adv_counts["low"],
                "redlines": adv_redline_count,
            },
        }

    # ── 报告输出 ────────────────────────────────────────────

    def report(
        self,
        fmt: str = "text",
        output_path: typing.Optional[str] = None,
    ) -> str:
        sc = self.score()

        if fmt == "json":
            result = {
                "skill": self.skill_name,
                "directory": self.target_dir,
                "rules_version": self.rules_data.get("version", ""),
                "disclaimer": DISCLAIMER,
                "score": sc,
                "compliance": sc.get("compliance", {}),
                "advisory": sc.get("advisory", {}),
                "issues": self.issues,
                "authority_types": {
                    "law": "法律（全国人大及其常委会通过）",
                    "regulation": "行政法规/管理办法/部门规章",
                    "standard": "国标/行标",
                    "platform_policy": "平台规范（如 SkillHub安全规范）",
                    "best_practice": "最佳实践（建议性）"
                }
            }
            txt = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            lines: list[str] = []
            lines.append(
                f"╔══ SkillHub 合规检查报告 ══ {self.skill_name}"
            )
            lines.append(f"║ 目录：{self.target_dir}")
            lines.append(
                "║ 规则版本: "
                + self.rules_data.get("version", "N/A")
            )
            redline_note = (
                "  🛑 红线=" + str(sc["redlines"])
                if sc["redlines"] > 0
                else ""
            )
            comp = sc.get("compliance", {})
            adv = sc.get("advisory", {})
            lines.append(
                f"║"
            )
            lines.append(
                f"║ 【法律合规】评分：{comp.get('score', 0)}/100  "
                f"|  结论：{comp.get('verdict', 'N/A')}"
            )
            if comp.get("redlines", 0) > 0:
                lines.append(
                    f"║  🛑 红线={comp['redlines']} "
                    + "(一票否决：必须修复)"
                )
            if comp.get("total", 0) > 0:
                lines.append(
                    f"║  法律/法规/标准问题：{comp['total']}"
                    f"  (H:{comp['high']} M:{comp['medium']} L:{comp['low']})"
                )
            if adv.get("total", 0) > 0:
                lines.append(
                    f"║"
                )
                lines.append(
                    f"║ 【平台告警】{adv['total']} 项"
                )
                lines.append(
                    f"║  平台规范/最佳实践问题（不影响合规结论）"
                )
            lines.append(
                f"║"
            )
            lines.append(
                f"║ 问题总数：{sc['total_issues']}"
                f"  (critical={sc['critical']},"
                f" high={sc['high']},"
                f" medium={sc['medium']},"
                f" low={sc['low']})"
            )
            lines.append("╠══ 问题列表 ══")
            if not self.issues:
                lines.append("║  未发现合规问题 ✓")
            else:
                sorted_issues = sorted(
                    self.issues,
                    key=lambda x: self.SEVERITY_ORDER.get(
                        x["severity"], 99
                    ),
                )
                for i, issue in enumerate(sorted_issues, 1):
                    lines.append(
                        f"║ [{issue['severity'].upper():>8}] "
                        f"({issue['category']}) "
                        f"{issue['file']}:{issue['line']}"
                    )
                    lines.append(f"║   → {issue['found']}")
                    lines.append(
                        f"║   建议：{issue['recommendation']}"
                    )
                    if issue.get("legal_source"):
                        lines.append(
                            f"║   依据：{issue['legal_source']}"
                        )
                    if i < len(sorted_issues):
                        lines.append("║  ──────────────────────")
            lines.append("╚" + "═" * 50)
            lines.append("")
            lines.append(DISCLAIMER)
            txt = "\n".join(lines)

        if output_path:
            os.makedirs(
                os.path.dirname(output_path) or ".", exist_ok=True
            )
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(txt)
            print(f"报告已写入: {output_path}")

        return txt


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def cmd_check(args):
    """全面合规检查"""
    checker = ComplianceChecker(args.dir)
    checker.run_all()
    print(checker.report(fmt=args.format, output_path=args.output))


def cmd_disclaimer(args):
    """免责声明检查专项"""
    checker = ComplianceChecker(args.dir)
    checker.check_disclaimer()
    disclaimers = [
        i for i in checker.issues if i["category"] == "DISCLAIMER"
    ]
    if not disclaimers:
        print("✓ 免责声明检查通过，未发现问题。")
        return
    for d in disclaimers:
        sev = d["severity"].upper()
        print(f"[{sev}] {d['file']}:{d['line']}")
        print(f"     问题：{d['found']}")
        print(f"     建议：{d['recommendation']}")
        print()


def cmd_keywords(args):
    """敏感词扫描专项"""
    checker = ComplianceChecker(args.dir)
    checker.check_finance()
    kw = [i for i in checker.issues if i["category"] == "FINANCE"]
    if not kw:
        print("✓ 未发现敏感金融用语。")
        return
    print(f"发现 {len(kw)} 处敏感金融用语：")
    for k in kw:
        sev = k["severity"].upper()
        print(f"  [{sev}] {k['file']}:{k['line']}")
        print(f"        原文：{k['found']}")
        print()


def cmd_summary(args):
    """批量检查多个skill"""
    dirs = args.dirs if args.dirs else []
    if not dirs:
        base = os.path.dirname(os.path.abspath(args.dir))
        print(f"从目录批量扫描: {base}")
        for entry in sorted(os.listdir(base)):
            skill_dir = os.path.join(base, entry)
            if os.path.isdir(skill_dir) and os.path.isfile(
                os.path.join(skill_dir, "package.json")
            ):
                dirs.append(skill_dir)

    results: list[tuple[str, dict, list[dict]]] = []
    for d in dirs:
        checker = ComplianceChecker(d)
        checker.run_all()
        sc = checker.score()
        results.append((checker.skill_name, sc, checker.issues))

    results.sort(key=lambda x: x[1]["score"], reverse=True)

    print(
        f"{'Skill':<30} {'合规分':>6} {'结论':>10} {'告警':>5} {'问题':>5}"
    )
    print("-" * 65)
    for name, sc, _issues in results:
        comp = sc.get("compliance", {})
        adv = sc.get("advisory", {})
        print(
            f"{name:<30} {comp.get('score', 0):>5}  "
            f"{comp.get('verdict', 'N/A'):>10} "
            f"{adv.get('total', 0):>5} "
            f"{sc['total_issues']:>5}"
        )
    print()

    worst = results[-1] if results else None
    if worst and worst[1]["verdict"] != "PASS":
        print(
            f"⚠ 最低分：{worst[0]} ({worst[1]['score']}分) — "
            "建议修复后再上传。"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Skill Compliance Check — 上架合规检查器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  python3 comply.py check --dir ../stock-planner/\n"
            "  python3 comply.py check --dir ../stock-planner/ --json\n"
            "  python3 comply.py check --dir ../stock-planner/ "
            "--output report.json\n"
            "  python3 comply.py disclaimer --dir ../pipl-compliance/\n"
            "  python3 comply.py keywords --dir ../privacy-check/\n"
            "  python3 comply.py summary --dir ../\n"
        ),
    )
    parser.add_argument(
        "--disclaimer",
        action="store_true",
        help="显示免责声明",
    )

    sub = parser.add_subparsers(dest="command", help="子命令")

    # check
    p_check = sub.add_parser(
        "check", help="全面合规检查（默认）"
    )
    p_check.add_argument(
        "--dir", "-d", default=".",
        help="目标 skill 目录 (默认当前目录)",
    )
    p_check.add_argument(
        "--format", "-f", choices=["text", "json"],
        default="text", help="输出格式",
    )
    p_check.add_argument(
        "--output", "-o", default=None,
        help="输出到文件",
    )
    p_check.set_defaults(func=cmd_check)

    # disclaimer
    p_disc = sub.add_parser(
        "disclaimer", help="免责声明检查专项"
    )
    p_disc.add_argument(
        "--dir", "-d", default=".",
        help="目标 skill 目录",
    )
    p_disc.set_defaults(func=cmd_disclaimer)

    # keywords
    p_kw = sub.add_parser(
        "keywords", help="敏感金融用语扫描"
    )
    p_kw.add_argument(
        "--dir", "-d", default=".",
        help="目标 skill 目录",
    )
    p_kw.set_defaults(func=cmd_keywords)

    # summary
    p_sum = sub.add_parser(
        "summary", help="批量检查并输出汇总排名"
    )
    p_sum.add_argument(
        "--dir", "-d", default=".",
        help="包含多个 skill 目录的父级目录",
    )
    p_sum.add_argument(
        "dirs", nargs="*",
        help="或直接指定要检查的目录列表",
    )
    p_sum.set_defaults(func=cmd_summary)

    args = parser.parse_args()

    if args.disclaimer:
        print(DISCLAIMER)
        return

    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
