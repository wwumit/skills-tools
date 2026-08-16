#!/usr/bin/env python3
"""
Finance Plugin — 金融合规专项检查

对目标 skill 的文档做金融合规深度检查。
检查逻辑为关系式判断："你说到了收益，是否也说到了风险？"
不重复通用扫描的关键词匹配，而是评估金融信息披露的完整性。
"""

import re
from .base import CompliancePlugin


class FinanceCompliancePlugin(CompliancePlugin):
    """金融合规专项检查插件"""

    @property
    def name(self) -> str:
        return "finance"

    @property
    def description(self) -> str:
        return "金融合规深度检查：投资声明、风险披露、收益说明"

    # ── 金融内容触发词 ──
    FINANCE_TRIGGERS = [
        "股票", "基金", "证券", "期货", "期权", "债券",
        "交易", "投资", "行情", "K线", "走势", "大盘",
        "涨停", "跌停", "仓位", "持仓", "建仓", "减仓",
        "买入", "卖出", "做多", "做空", "多头", "空头",
        "stock", "fund", "trade", "invest", "portfolio",
        "bullish", "bearish", "long", "short", "position",
    ]

    # ── 必需的三项声明 ──
    REQUIRED_DISCLAIMERS = [
        ("no_advice", [
            "不构成投资建议", "不构成任何投资建议",
            "not investment advice", "not financial advice",
            "for informational purposes only",
        ]),
        ("for_reference", [
            "仅供.*参考", "仅供参考",
            "for reference", "for educational",
        ]),
        ("risk_warning", [
            "风险", "谨慎", "损失", "亏损",
            "risk", "loss", "volatility",
        ]),
    ]

    # ── 收益/回报表述 ──
    RETURN_PATTERNS = [
        "收益率", "回报率", "年化", "涨幅", "盈利",
        "profit", "return", "yield", "gain", "percent",
    ]

    # ── 风险提示用语 ──
    RISK_DISCLAIMERS = [
        "过往.*业绩.*不代表.*未来",
        "past performance.*not.*guarantee",
        "不保证.*收益", "不保证.*盈利",
        "投资有风险", "市场有风险",
        "no guarantee", "may lose",
        "historical.*not.*future",
    ]

    # ── 资质声明 ──
    QUALIFICATION_STATEMENTS = [
        "不持有.*牌照", "不持有.*资质",
        "not.*licensed", "not.*qualified",
        "no.*securities.*license",
        "未经.*批准", "未经.*许可",
        "not.*registered.*advisor",
    ]

    # ── 数据来源声明 ──
    SOURCE_ATTRIBUTIONS = [
        "数据来源", "数据来自", "source",
        "data from", "provided by",
        "API", "公开数据",
    ]

    # ── 教育目的声明 ──
    EDUCATIONAL_STATEMENTS = [
        "仅供.*学习", "仅供学习.*参考",
        "教学目的", "研究目的",
        "for.*educational", "for.*learning",
        "for.*research", "study.*purpose",
    ]

    def _check_pair(self, text: str, trigger_pats: list, 
                    required_pats: list, min_required: int = 1) -> int:
        """检查 trigger 出现时，required 的覆盖次数"""
        triggers_found = [p for p in trigger_pats 
                         if re.search(p, text, re.IGNORECASE)]
        if not triggers_found:
            return -1  # 不适用
        
        required_count = sum(
            1 for p in required_pats 
            if re.search(p, text, re.IGNORECASE)
        )
        return required_count

    def check(self, target_dir: str, existing_issues: list) -> list:
        findings = []
        skill_md = self._read(target_dir, "SKILL.md")
        readme = self._read(target_dir, "README.md")
        combined = skill_md + "\n" + readme

        # 如果不涉及金融内容，跳过
        if not self._has(combined, *self.FINANCE_TRIGGERS):
            return []

        # ── 检查 1：三项必需声明覆盖 ──
        missing_disclaimers = []
        for key, pats in self.REQUIRED_DISCLAIMERS:
            if not self._has(combined, *pats):
                missing_disclaimers.append(key)
        
        if missing_disclaimers:
            labels = {
                "no_advice": "不构成投资建议",
                "for_reference": "仅供参考声明",
                "risk_warning": "风险提示",
            }
            missing_labels = [labels.get(k, k) for k in missing_disclaimers]
            findings.append(self._finding(
                category="FINANCE",
                severity="high",
                file="SKILL.md",
                line=1,
                found=(
                    f"涉及金融投资内容但缺少 {len(missing_disclaimers)}/3 项必需声明："
                    + "、".join(missing_labels)
                ),
                recommendation=(
                    "在显眼位置添加完整的金融免责声明包：\n"
                    "1. \"不构成投资建议\"声明\n"
                    "2. \"仅供学习参考\"声明\n"
                    "3. \"投资有风险\"风险提示"
                ),
                legal_source=(
                    "《证券、期货投资咨询管理暂行办法》第二十四条："
                    "证券投资咨询机构及其投资咨询人员，不得对投资行为作出确定性判断。"
                    "《广告法》第二十五条：招商等有投资回报预期的广告，"
                    "应对可能存在的风险及风险责任承担有合理提示或警示。"
                ),
                authority_type="regulation",
            ))

        # ── 检查 2：收益-风险平衡 ──
        return_cites = sum(
            1 for p in self.RETURN_PATTERNS
            if re.search(p, combined, re.IGNORECASE)
        )
        risk_cites = sum(
            1 for p in self.RISK_DISCLAIMERS
            if re.search(p, combined, re.IGNORECASE)
        )
        if return_cites > 0 and risk_cites == 0:
            findings.append(self._finding(
                category="FINANCE",
                severity="high",
                file="SKILL.md",
                line=1,
                found=(
                    f"提及 {return_cites} 类收益/回报表述，但未提及任何风险提示。"
                    "金融信息的完整披露要求收益与风险同时呈现。"
                ),
                recommendation=(
                    "每次提及收益/回报时同步搭配风险提示，例如：\n"
                    "\"过去收益不代表未来表现，投资有风险。\"\n"
                    "引用《广告法》第25条对风险提示的要求。"
                ),
                legal_source=(
                    "《广告法》第二十五条：招商等有投资回报预期的商品或者服务广告，"
                    "应当对可能存在的风险以及风险责任承担有合理提示或者警示。"
                ),
                authority_type="law",
            ))

        # ── 检查 3：具体投资建议的资质说明 ──
        specific_advice = self._has(
            combined,
            "推荐.*买入", "推荐.*卖出", "目标价",
            "buy.*recommend", "sell.*recommend", "target.*price",
            "买入.*评级", "卖出.*评级",
        )
        if specific_advice:
            has_qual = self._has(combined, *self.QUALIFICATION_STATEMENTS)
            has_educ = self._has(combined, *self.EDUCATIONAL_STATEMENTS)
            
            if not has_qual and not has_educ:
                findings.append(self._finding(
                    category="FINANCE",
                    severity="high",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "包含具体买卖建议/目标价预测，但缺少资质说明或教育目的声明。"
                        "《证券法》第160条要求证券投资咨询业务须经批准。"
                    ),
                    recommendation=(
                        "添加资质说明声明，例如：\n"
                        "\"本工具不持有证券投资咨询牌照，所有分析仅供学习参考，"
                        "不构成买卖建议。\"\n"
                        "如为个人/非持牌机构发布，必须明确说明无牌照资质。"
                    ),
                    legal_source=(
                        "《证券法》（2019年修订，2020年3月1日施行）第一百六十条："
                        "未经国务院证券监督管理机构批准，任何单位和个人"
                        "不得从事证券投资咨询业务。"
                    ),
                    authority_type="law",
                ))

        # ── 检查 4：过往业绩声明 ──
        past_perf = self._has(combined, "历史.*收益", "过往.*业绩",
                              "historical.*return", "past.*performance")
        if past_perf:
            has_past_disclaimer = self._has(combined, *self.RISK_DISCLAIMERS)
            if not has_past_disclaimer:
                findings.append(self._finding(
                    category="FINANCE",
                    severity="medium",
                    file="SKILL.md",
                    line=1,
                    found=(
                        "展示历史业绩/收益数据，但未声明\"过往业绩不代表未来表现\"。"
                    ),
                    recommendation=(
                        "在展示历史数据时同步声明：\n"
                        "\"过往业绩不代表未来表现，投资有风险，入市需谨慎。\""
                    ),
                    legal_source=(
                        "《广告法》第二十五条：招商等有投资回报预期的广告，"
                        "不得利用学术机构、行业协会、专业人士、受益者的名义"
                        "或者形象作推荐、证明。"
                    ),
                    authority_type="law",
                ))

        # ── 检查 5：教育/研究目的声明 ──
        if not self._has(combined, *self.EDUCATIONAL_STATEMENTS):
            findings.append(self._finding(
                category="FINANCE",
                severity="low",
                file="SKILL.md",
                line=1,
                found=(
                    "涉及金融投资内容但缺少教育/研究目的声明。"
                    "建议明确工具的使用场景和限制。"
                ),
                recommendation=(
                    "在文档开头或显眼位置添加：\n"
                    "\"本工具仅供学习和研究参考，不构成任何投资建议。\""
                ),
                legal_source=(
                    "行业最佳实践：金融分析类工具应明确声明其教育/研究目的，"
                    "避免用户误解为专业投资建议。"
                ),
                authority_type="best_practice",
            ))

        return findings
