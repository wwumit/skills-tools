#!/usr/bin/env python3
"""
GDPR Plugin — GDPR (General Data Protection Regulation) 专项合规检查

对目标 skill 的文档做 GDPR 领域专项检查。
检查逻辑为关系式判断："你说到了数据处理，是否也说到了数据主体权利？"
"""

from .base import CompliancePlugin


class GDPRCompliancePlugin(CompliancePlugin):
    """GDPR 专项合规检查插件"""

    @property
    def name(self) -> str:
        return "gdpr"

    @property
    def description(self) -> str:
        return "基于 GDPR 的专项合规深度检查"

    # ── GDPR 6 大合法性基础 ──
    LAWFUL_BASES = [
        "consent", "contract", "legal obligation",
        "vital interests", "public task", "legitimate interests",
        "同意", "合同", "法定义务", "重大利益",
        "公共利益", "合法利益",
    ]

    # ── GDPR 8 大数据主体权利 ──
    DATA_SUBJECT_RIGHTS = [
        "right to be informed", "right of access",
        "right to rectification", "right to erasure",
        "right to restrict", "right to data portability",
        "right to object", "automated decision",
        "被遗忘权", "删除权", "更正权", "访问权",
        "知情权", "可携带权", "限制处理", "反对权",
        "自动化决策",
    ]

    # ── 跨境传输保障措施 ──
    TRANSFER_SAFEGUARDS = [
        "adequacy decision", "SCC", "standard contractual",
        "binding corporate rules", "BCR",
        "充分性认定", "标准合同条款", "有约束力的公司规则",
        "code of conduct", "certification",
    ]

    # ── 高风险处理场景 ──
    HIGH_RISK_KEYWORDS = [
        "automated", "profiling", "sensitive", "biometric",
        "genetic", "health", "criminal", "large scale",
        "monitoring", "children",
        "自动化", "画像", "敏感", "生物识别",
        "基因", "健康", "大规模", "监控",
    ]

    # ── DPIA 关键词 ──
    DPIA_KEYWORDS = [
        "impact assessment", "DPIA", "data protection impact",
        "风险评估", "影响评估",
    ]

    # ── DPO 关键词 ──
    DPO_KEYWORDS = [
        "data protection officer", "DPO",
        "数据保护官",
    ]

    def check(self, target_dir: str, existing_issues: list) -> list:
        findings = []
        skill_md = self._read(target_dir, "SKILL.md")
        readme = self._read(target_dir, "README.md")
        combined = skill_md + "\n" + readme

        # 只对明确引用 GDPR/欧盟法域的 Skill 进行专项检查
        if not self._has(combined,
                         "GDPR", "General Data Protection",
                         "EU data", "European Union",
                         "欧盟", "gdpr"):
            return []

        # ── 检查 1：合法性基础覆盖 ──
        if self._has(combined, "process", "collect", "store",
                     "处理", "收集", "存储"):
            basis_count = self._count(combined, self.LAWFUL_BASES)
            if basis_count < 1:
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "涉及个人数据处理但未提及 GDPR 合法性基础。"
                        "GDPR 第6条要求处理个人数据必须基于至少一项合法性基础。"
                    ),
                    recommendation=(
                        "补充 GDPR 合法性基础说明，至少包含一种："
                        "consent（同意）、contract（合同）、"
                        "legal obligation（法定义务）、"
                        "legitimate interests（合法利益）等"
                    ),
                    legal_source=(
                        "GDPR Article 6 (Lawfulness of processing): "
                        "Processing shall be lawful only if and to the extent "
                        "that at least one of the following applies: "
                        "(a) consent; (b) contract; (c) legal obligation; "
                        "(d) vital interests; (e) public task; "
                        "(f) legitimate interests."
                    ),
                    authority_type="law",
                ))

        # ── 检查 2：数据主体权利覆盖 ──
        rights_count = self._count(combined, self.DATA_SUBJECT_RIGHTS)
        if rights_count < 4:
            findings.append(self._finding(
                category="PRIVACY",
                severity="medium",
                file="SKILL.md",
                line=1,
                found=(
                    f"提及个人数据处理但仅覆盖 {rights_count}/8 项数据主体权利。"
                    "GDPR 第15-22条规定了8项数据主体权利。"
                ),
                recommendation=(
                    "补充至少 4 项 GDPR 数据主体权利说明，例如："
                    "right to be informed（知情权）、right of access（访问权）、"
                    "right to erasure（被遗忘权）、right to data portability（可携带权）"
                ),
                legal_source=(
                    "GDPR Chapter III (Articles 15-22): "
                    "Right of access, right to rectification, "
                    "right to erasure ('right to be forgotten'), "
                    "right to restrict processing, "
                    "right to data portability, right to object, "
                    "and rights related to automated decision-making."
                ),
                authority_type="law",
            ))

        # ── 检查 3：跨境传输保障 ──
        if self._has(combined, "cross.?border", "transfer.*third",
                     "international", "跨境", "向.*境外", "转移给第三人"):
            safeguard_count = self._count(combined, self.TRANSFER_SAFEGUARDS)
            if safeguard_count < 1:
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及跨境数据转移，但未说明 GDPR 第44-49条要求的保障措施。"
                    ),
                    recommendation=(
                        "补充跨境传输保障措施说明：adequacy decision（充分性认定）、"
                        "SCC（标准合同条款）、BCR（有约束力的公司规则）"
                    ),
                    legal_source=(
                        "GDPR Chapter V (Articles 44-49): "
                        "Transfers of personal data to third countries or "
                        "international organisations shall only take place if "
                        "adequate safeguards are in place, including "
                        "adequacy decisions, SCCs, or BCRs."
                    ),
                    authority_type="law",
                ))

        # ── 检查 4：DPIA（数据保护影响评估）──
        if self._has(combined, *self.HIGH_RISK_KEYWORDS):
            if not self._has(combined, *self.DPIA_KEYWORDS):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及高风险处理场景（自动化决策/大规模监控/敏感数据），"
                        "但未提及 DPIA（数据保护影响评估）。"
                    ),
                    recommendation=(
                        "补充 DPIA 说明。GDPR 第35条要求在可能对自然人的权利和自由"
                        "产生高风险的处理前进行数据保护影响评估。"
                    ),
                    legal_source=(
                        "GDPR Article 35 (Data protection impact assessment): "
                        "Where a type of processing is likely to result in high "
                        "risk to the rights and freedoms of natural persons, "
                        "the controller shall carry out a DPIA."
                    ),
                    authority_type="law",
                ))

        # ── 检查 5：DPO（数据保护官）──
        if self._has(combined, *self.HIGH_RISK_KEYWORDS):
            if not self._has(combined, *self.DPO_KEYWORDS):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="medium",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及高风险处理场景，但未提及 DPO（数据保护官）。"
                        "GDPR 第37条要求特定情况下的组织指定 DPO。"
                    ),
                    recommendation=(
                        "补充 DPO 说明。GDPR 第37条要求以下组织指定 DPO："
                        "公共机构、从事大规模监控的组织、"
                        "大规模处理敏感数据的组织。"
                    ),
                    legal_source=(
                        "GDPR Article 37 (Designation of the data protection "
                        "officer): The controller and the processor shall "
                        "designate a DPO where the core activities consist of "
                        "processing operations which require regular and "
                        "systematic monitoring of data subjects on a large scale."
                    ),
                    authority_type="law",
                ))

        return findings
