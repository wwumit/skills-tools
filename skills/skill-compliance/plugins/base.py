#!/usr/bin/env python3
"""
Plugins — 合规检查插件基类

定义标准插件接口，供 domain 专项检查器继承。
每个 plugin 关注一个特定领域（PIPL/GDPR/CCPA等），
对目标 skill 的文档做深度语义检查，返回标准格式的发现。
"""

import os
import re
import typing


class CompliancePlugin:
    """合规检查插件基类，所有 domain 插件继承此类"""

    @property
    def name(self) -> str:
        return "plugin-name"

    @property
    def display_name(self) -> str:
        """人类可读的插件名称，用于输出"""
        return self.name.replace("_", " ").title()

    @property
    def description(self) -> str:
        return ""

    def check(
        self, target_dir: str, existing_issues: typing.List[dict]
    ) -> typing.List[dict]:
        """
        对目标 skill 的文档做领域专项检查。

        Args:
            target_dir: 被检查 skill 的绝对路径
            existing_issues: 通用扫描已发现的问题

        Returns:
            标准格式的发现列表（与 comply.py issues 格式一致）
        """
        return []

    # ── 工具方法 ────────────────────────────────────────────

    def _read(self, target_dir: str, *parts: str) -> str:
        """读取目标 skill 的文本文件，返回全文"""
        path = os.path.join(target_dir, *parts)
        if not os.path.isfile(path):
            return ""
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    def _lines(self, target_dir: str, *parts: str) -> list:
        """读取目标 skill 的文件，返回行列表"""
        path = os.path.join(target_dir, *parts)
        if not os.path.isfile(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()
        except Exception:
            return []

    def _has(self, text: str, *patterns: str) -> bool:
        """检查文本中是否包含任一种模式"""
        return any(
            re.search(p, text, re.IGNORECASE) for p in patterns
        )

    def _count(self, text: str, patterns: list) -> int:
        """统计文本中匹配到的不重复模式数量"""
        seen = set()
        for p in patterns:
            if re.search(p, text, re.IGNORECASE):
                seen.add(p)
        return len(seen)

    def _finding(
        self,
        category: str = "COMPLIANCE",
        severity: str = "medium",
        file: str = "SKILL.md",
        line: int = 1,
        found: str = "",
        recommendation: str = "",
        redline: bool = False,
        legal_source: str = "",
        authority_type: str = "regulation",
    ) -> dict:
        """构造标准格式的发现"""
        return {
            "category": category,
            "severity": severity,
            "file": file,
            "line": line,
            "found": found,
            "recommendation": recommendation,
            "redline": redline,
            "legal_source": legal_source,
            "authority_type": authority_type,
            "plugin": self.name,
        }
