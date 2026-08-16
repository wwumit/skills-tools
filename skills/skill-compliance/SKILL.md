---
name: skill-compliance
version: 1.3.1
model: default
description: Skill上架合规检查器（面向国内平台）。在上传前检查skill是否符合国内监管要求，包括金融敏感词、免责声明、安全红线等。
use_when:
  - 准备将skill发布到国内平台（如SkillHub、飞书、钉钉等）前做合规预检
  - 检查skill文档中是否有违反广告法或金融监管的用语
  - 快速扫描脚本中是否有安全红线（subprocess/exec/eval）
  - 批量检查多个skill的合规状况
trigger_keywords:
  - skillhub合规
  - 上架检查
  - 合规预检
  - preflight
  - 金融合规
  - 免责声明
  - 敏感词
  - 广告法
environment: local
network: none
dependencies: none (Python stdlib only)
disclaimer: 本工具仅为辅助检查参考，不构成合规保证。最终合规责任由skill开发者自行承担。
---

# Skill Compliance Check

## 功能

上传 skill 到 SkillHub 前，用本工具做一次快速合规预检：

| 检查项 | 内容 |
|--------|------|
| **FINANCE** | 荐股用语、投资建议、保证收益、需要资质的用语 |
| **DISCLAIMER** | 是否在显眼位置有免责声明（投资/法律类） |
| **EXAGGERATION** | 极限词（最好、第一、全网唯一）、夸大描述 |
| 检查项 | 内容 | 依据类型 |
|--------|------|----------|
| **FINANCE** | 荐股用语、投资建议、保证收益、需要资质的用语 | 法律 |
| **DISCLAIMER** | 投资/法律免责声明是否在显眼位置 | 法律/法规 |
| **EXAGGERATION** | 极限词（最好、第一、全网唯一）、夸大描述 | 法律 |
| **SECURITY** | subprocess/exec/eval 红线、JSON合法性、版本号格式 | 平台规范 |
| **SUPPLY_CHAIN** | 外部脚本获取、代码混淆、未固定版本依赖 | 平台规范 |
| **MCP** | MCP权限最小化、工具权限声明、通配符检测 | 平台规范 |
| **OUTPUT** | 未验证输出注入、跨上下文输出、文件写入安全 | 平台规范 |
| **ADVISORY** | 描述-行为不一致检测（如声明network:none但代码含网络请求） | 建议性 |
| **PRIVACY** | 数据隐私合规（个人信息收集声明、用户同意机制、数据出境合规） | 法律 |
| **REGULATORY** | 专项监管合规（ICP备案、AIGC标识、算法备案、数据安全法、关基保护等）| 法律/法规 |
| **RECOMMENDATIONS** | 基于检测结果给出改进建议 | 最佳实践 |

> 💡 **关于两类评分**: 本工具采用双轨评分机制
> - **法律合规评分**（0-100）：基于法律/法规/标准的评分，影响 PASS/NEEDS_FIX/REJECT 判定
> - **平台告警**（不计分）：基于平台规范/最佳实践的建议性问题，不影响合规结论，但建议关注

## 评分规则

| 扣分 | 等级 |
|------|------|
| -30 / 项 | Critical（安全红线、医疗红线） |
| -15 / 项 | High（隐私合规、金融敏感词、缺免责声明） |
| -5 / 项 | Medium（极限词、JSON问题） |
| -2 / 项 | Low（建议性） |
| **≥70分** | **PASS** — 可上架（无 redline 触发） |
| **40–69分** | **NEEDS_FIX** — 建议修复后再上传 |
| **<40分** | **REJECT** — 强烈不建议上传 |

## 法律免责声明

本工具仅为辅助检查参考，不构成任何形式的合规保证。最终合规责任由 skill 开发者自行承担。
