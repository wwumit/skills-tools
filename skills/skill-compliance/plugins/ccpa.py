#!/usr/bin/env python3
"""
CCPA Plugin — CCPA/CPRA (California Consumer Privacy Act) 专项合规检查

对目标 skill 的文档做 CCPA 领域专项检查。
检查逻辑为关系式判断："你说到了消费者数据，是否也说到了消费者的权利？"
"""

from .base import CompliancePlugin


class CCPACompliancePlugin(CompliancePlugin):
    """CCPA/CPRA 专项合规检查插件"""

    @property
    def name(self) -> str:
        return "ccpa"

    @property
    def description(self) -> str:
        return "基于 CCPA/CPRA 的专项合规深度检查"

    # ── CCPA 核心消费者权利 ──
    CONSUMER_RIGHTS = [
        "right to know", "right to delete",
        "right to opt.?out", "right to non.discrimination",
        "知情权", "删除权", "退出权", "选择退出",
        "不受歧视", "opt.?out of sale",
    ]

    # ── CCPA 管辖门槛 ──
    COVERAGE_CRITERIA = [
        "annual.*revenue", "25 million", "100,000",
        "50%", "sell.*personal information",
        "年收入", "2500万", "10万",
    ]

    # ── 出售/共享数据相关 ──
    SALE_KEYWORDS = [
        "sell", "sale", "share.*third.?party",
        "monetary.*consideration", "valuable.*consideration",
        "出售", "共享.*第三方", "对价",
    ]

    # ── 敏感个人信息（CPRA 扩展） ──
    SENSITIVE_INFO_CPRA = [
        "social security", "driver.?s license",
        "financial account", "geolocation",
        "biometric", "health", "union",
        "racial", "ethnic", "sexual orientation",
        "公民身份号码", "驾照", "金融账户",
        "地理位置", "生物识别", "健康信息",
    ]

    # ── 服务提供商约定 ──
    SERVICE_PROVIDER = [
        "service provider", "contractor", "third.?party",
        "business purpose", "service provider agreement",
        "服务提供商", "承包商", "业务目的",
    ]

    def check(self, target_dir: str, existing_issues: list) -> list:
        findings = []
        skill_md = self._read(target_dir, "SKILL.md")
        readme = self._read(target_dir, "README.md")
        combined = skill_md + "\n" + readme

        # 如果不涉及消费者数据 / CCPA，跳过
        if not self._has(combined, "CCPA", "CPRA", "California",
                         "consumer.*data", "personal information",
                         "消费者", "加州"):
            return []

        # ── 检查 1：消费者权利覆盖 ──
        rights_count = self._count(combined, self.CONSUMER_RIGHTS)
        if rights_count < 3:
            findings.append(self._finding(
                category="PRIVACY",
                severity="medium",
                file="SKILL.md",
                line=1,
                found=(
                    f"提及 CCPA/消费者数据但仅覆盖 {rights_count}/4 项核心消费者权利。"
                    "CCPA 赋予消费者知情权、删除权、选择退出销售权、不受歧视权。"
                ),
                recommendation=(
                    "补充至少 3 项 CCPA 消费者权利说明："
                    "right to know（知情权）、right to delete（删除权）、"
                    "right to opt-out of sale（选择退出权）、"
                    "right to non-discrimination（不受歧视权）"
                ),
                legal_source=(
                    "California Consumer Privacy Act (CCPA) as amended by CPRA: "
                    "Sections 1798.100-1798.125 grant consumers the right to know, "
                    "right to delete, right to opt-out of sale/sharing, "
                    "and right to non-discrimination."
                ),
                authority_type="law",
            ))

        # ── 检查 2：业务目的声明 ──
        if self._has(combined, "collect", "collect",
                     "收集", "采集") and \
           not self._has(combined, "business purpose",
                         "业务目的", "商业目的"):
            findings.append(self._finding(
                category="PRIVACY",
                severity="high",
                file="SKILL.md",
                line=1,
                found=(
                    "提及消费者数据收集，但未说明业务目的。"
                    "CCPA 要求收集个人信息时告知收集目的和用途。"
                ),
                recommendation=(
                    "补充业务目的声明。CCPA 要求明确说明收集个人信息的"
                    "业务目的（business purpose），并限于为实现该目的所必需的范围。"
                ),
                legal_source=(
                    "CCPA Section 1798.100(b): A business shall, at or before "
                    "the point of collection, inform consumers as to the "
                    "categories of personal information to be collected and "
                    "the purposes for which the categories of personal "
                    "information shall be used."
                ),
                authority_type="law",
            ))

        # ── 检查 3：Opt-Out 机制（若涉及数据出售/共享）──
        if self._has(combined, *self.SALE_KEYWORDS):
            if not self._has(combined, "opt.?out", "do not sell",
                             "选择退出", "不出售", "Don't sell"):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及数据出售/共享行为，但未说明 opt-out 机制。"
                        "CCPA 要求提供清晰的 opt-out 路径。"
                    ),
                    recommendation=(
                        "补充 opt-out 机制说明：在主页提供'Do Not Sell My "
                        "Personal Information'链接，确保消费者可以随时"
                        "选择退出个人信息的出售/共享。"
                    ),
                    legal_source=(
                        "CCPA Section 1798.120: A consumer shall have the right, "
                        "at any time, to direct a business that sells personal "
                        "information about the consumer to third parties not to "
                        "sell the consumer's personal information."
                    ),
                    authority_type="law",
                ))

        # ── 检查 4：不受歧视权 ──
        if self._has(combined, *self.CONSUMER_RIGHTS):
            if not self._has(combined, "non.discrimination",
                             "不受歧视", "差别待遇", "不同价格"):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="low",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及消费者权利但未说明不受歧视权。"
                        "CCPA 禁止企业因消费者行使隐私权利而歧视对待。"
                    ),
                    recommendation=(
                        "补充不受歧视权说明：企业不得因消费者行使 CCPA 权利"
                        "而拒绝提供服务、收取不同价格或提供不同质量的服务。"
                    ),
                    legal_source=(
                        "CCPA Section 1798.125: A business shall not discriminate "
                        "against a consumer because the consumer exercised any of "
                        "the consumer's rights under this title."
                    ),
                    authority_type="law",
                ))

        # ── 检查 5：敏感个人信息（CPRA 扩展）──
        if self._has(combined, *self.SENSITIVE_INFO_CPRA):
            if not self._has(combined, "limited use", "specify.?purpose",
                             "限制使用", "特定目的", "敏感个人信息"):
                findings.append(self._finding(
                    category="PRIVACY",
                    severity="medium",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "提及敏感个人信息类型，但未说明 CPRA 的敏感信息限制使用要求。"
                        "CPRA 新增了敏感个人信息的特别保护（right to limit use）。"
                    ),
                    recommendation=(
                        "补充 CPRA 敏感个人信息保护说明：消费者有权限制企业"
                        "对敏感个人信息的使用和披露，仅限于为提供服务所必需的范围。"
                    ),
                    legal_source=(
                        "CPRA Section 1798.121: A consumer shall have the right "
                        "to limit a business's use and disclosure of sensitive "
                        "personal information to that use which is necessary "
                        "to perform the services."
                    ),
                    authority_type="law",
                ))

        return findings
