#!/usr/bin/env python3
"""
PIPL Plugin — 《个人信息保护法》专项合规检查

对目标 skill 的文档做 PIPL 领域专项检查。
每项检查都是关系式判断："你说到了 A，那么是否也说到了 B？"
不同于通用扫描的"关键词 X 出现 = 违规"模式。
"""

from .base import CompliancePlugin


class PIPLCompliancePlugin(CompliancePlugin):
    """《个人信息保护法》专项合规检查插件"""

    @property
    def name(self) -> str:
        return "pipl"

    @property
    def description(self) -> str:
        return "基于《个人信息保护法》的专项合规深度检查"

    # ── PIPL 八大用户权利 ──
    USER_RIGHTS = [
        "知情权", "同意权", "删除权", "更正权",
        "可携带权", "限制处理权", "撤回同意权", "投诉举报权",
        "right to know", "right to consent", "right to delete",
        "right to rectification", "right to portability",
        "right to restriction", "right to withdraw",
        "right to complain",
    ]

    # ── 合法性基础 ──
    LEGAL_BASIS = [
        "同意", "合同", "法定义务", "紧急情况",
        "为公共利益", "为保护个人", "已公开信息",
        "consent", "contract", "legal obligation",
        "vital interest", "public interest", "legitimate interest",
    ]

    # ── 跨境保障措施 ──
    CROSS_BORDER_SAFEGUARDS = [
        "安全评估", "标准合同", "认证", "个人信息保护认证",
        "security assessment", "SCC", "standard contractual",
        "certification", "binding corporate", "BCR",
    ]

    # ── PIPL 核心原则 ──
    PRINCIPLES = [
        "合法", "正当", "必要", "诚信", "公开", "透明",
        "lawful", "fair", "necessary", "good faith",
        "transparent", "open",
    ]

    # ── 敏感信息类型 ──
    SENSITIVE_DATA_TYPES = [
        "生物识别", "金融账户", "行踪轨迹", "健康信息",
        "不满十四周岁", "biometric", "financial", "location",
        "health", "minor", "十四周岁",
    ]

    # ── 敏感信息专项保护措施 ──
    SENSITIVE_SAFEGUARDS = [
        "单独同意", "specific consent", "特别告知",
        "特别保护", "影响评估", "impact assessment",
    ]

    def check(self, target_dir: str, existing_issues: list) -> list:
        findings = []
        skill_md = self._read(target_dir, "SKILL.md")
        readme = self._read(target_dir, "README.md")
        combined = skill_md + "\n" + readme

        # 如果不涉及个人信息/隐私，跳过
        if not self._has(combined, "个人信息", "隐私", "个人数据",
                         "personal data", "personal information"):
            return []

        # ── 检查 1：知情权覆盖度 ──
        rights_count = self._count(combined, self.USER_RIGHTS)
        if rights_count < 3:
            findings.append(self._finding(
                category="PRIVACY",
                severity="medium",
                file="SKILL.md",
                line=1,
                found=(
                    f"提及隐私/个人信息但仅提及 {rights_count}/8 项用户权利。"
                    "PIPL 第44-50条规定了知情权、同意权、删除权、更正权、"
                    "可携带权等8项权利。"
                ),
                recommendation=(
                    "补充至少 3 项 PIPL 用户权利的说明，例如："
                    "知情权（第44条）、同意权/撤回权（第15条）、"
                    "删除权（第47条）、更正权（第46条）"
                ),
                legal_source=(
                    "《个人信息保护法》第四章（第44-50条）："
                    "个人对其个人信息的处理享有知情权、决定权，"
                    "有权限制或者拒绝他人对其个人信息进行处理。"
                ),
                authority_type="law",
            ))

        # ── 检查 2：合法性基础 ──
        if self._has(combined, "收集", "处理", "使用", "存储",
                     "collect", "process", "store"):
            basis_count = self._count(combined, self.LEGAL_BASIS)
            if basis_count < 1:
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "描述了个人信息处理活动，但未提及合法性基础。"
                        "PIPL 第13条要求处理个人信息必须有合法性基础。"
                    ),
                    recommendation=(
                        "补充合法性基础说明，至少包含一种："
                        "取得个人同意（第13条第1项）、"
                        "为订立或履行合同所必需（第2项）、"
                        "为履行法定义务所必需（第3项）等"
                    ),
                    legal_source=(
                        "《个人信息保护法》第十三条：符合下列情形之一的，"
                        "个人信息处理者方可处理个人信息：（一）取得个人的同意；"
                        "（二）为订立、履行个人作为一方当事人的合同所必需……"
                    ),
                    authority_type="law",
                ))

        # ── 检查 3：跨境治理 ──
        if self._has(combined, "跨境", "出境", "cross.?border",
                     "transfer.*overseas", "国际"):
            safeguard_count = self._count(
                combined, self.CROSS_BORDER_SAFEGUARDS
            )
            if safeguard_count < 1:
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及跨境数据流动，但未说明跨境保障措施。"
                    ),
                    recommendation=(
                        "补充跨境数据传输保障措施说明，例如："
                        "通过国家网信部门的安全评估、"
                        "签订标准合同条款(SCC)、"
                        "获得个人信息保护认证"
                    ),
                    legal_source=(
                        "《个人信息保护法》第三十八条：个人信息处理者因业务等需要，"
                        "确需向中华人民共和国境外提供个人信息的，应当具备下列条件之一："
                        "（一）通过国家网信部门组织的安全评估；"
                        "（二）经专业机构进行个人信息保护认证……"
                    ),
                    authority_type="law",
                ))

        # ── 检查 4：核心原则覆盖度 ──
        principle_count = self._count(combined, self.PRINCIPLES)
        if principle_count < 4:
            findings.append(self._finding(
                category="PRIVACY",
                severity="low",
                file="SKILL.md",
                line=1,
                found=(
                    f"仅覆盖 {principle_count}/6 项 PIPL 核心原则。"
                    "PIPL 第5-9条确立了合法、正当、必要、诚信、公开、透明等原则。"
                ),
                recommendation=(
                    "补充 PIPL 核心原则说明：合法（第5条）、"
                    "正当（第5条）、必要（第6条）、"
                    "诚信（第7条）、公开（第7条）、透明（第7条）"
                ),
                legal_source=(
                    "《个人信息保护法》第5-9条："
                    "处理个人信息应当遵循合法、正当、必要和诚信原则，"
                    "应当具有明确、合理的目的，应当遵循公开、透明原则。"
                ),
                authority_type="law",
            ))

        # ── 检查 5：敏感信息专项保护 ──
        if self._has(combined, *self.SENSITIVE_DATA_TYPES):
            if not self._has(combined, *self.SENSITIVE_SAFEGUARDS):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及敏感个人信息，但未说明专项保护措施。"
                    ),
                    recommendation=(
                        "补充敏感个人信息专项保护说明，至少包括："
                        "取得单独同意（第29条）、"
                        "进行个人信息保护影响评估（第55条）"
                    ),
                    legal_source=(
                        "《个人信息保护法》第二十八条：只有在具有特定的目的和"
                        "充分的必要性，并采取严格保护措施的情形下，个人信息处理者"
                        "方可处理敏感个人信息。第二十九条：处理敏感个人信息应当"
                        "取得个人的单独同意。"
                    ),
                    authority_type="law",
                ))

        return findings
