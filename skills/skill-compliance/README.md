# Skill Compliance Check

**SkillHub 上架合规检查器** — 在将 skill 上传至 SkillHub 前，快速检查是否满足国内监管合规要求。

## 为什么需要这个工具

SkillHub 面向国内用户，上架 skill 需要满足《广告法》《证券法》《网络安全法》等法规要求：

- **金融类 skill**：不能荐股、不能承诺收益、不能无资质给出投资建议
- **合规类 skill**：不能代替律师给出法律意见
- **所有 skill**：不能使用极限词（"最好"、"第一"）、不能使用 subprocess/exec/eval
- **必须声明**：在显眼位置添加免责声明

这些规则经常变化且容易被忽略。本工具帮你一次性扫描所有常见问题。

## 安装

```bash
# 无需安装，纯 Python 标准库
cd skill-compliance
python3 scripts/comply.py --help
```

## 使用示例

### 全面检查单个 skill

```bash
python3 scripts/comply.py check --dir ../stock-planner/
```

输出示例：

```
╔══ SkillHub 合规检查报告 ══ stock-planner
║ 目录：/Users/.../stock-planner
║ 评分：65/100  |  结论：NEEDS_FIX
║ 问题数：4  (critical=1, high=2, medium=1, low=0)
╠══ 问题列表 ══
║ [CRITICAL] (SECURITY) scripts/planner.py:45
║    → import subprocess
║   建议：删除或替换为安全的替代方案...
║  ──────────────────────
║ [   HIGH] (FINANCE) SKILL.md:12
║    → 推荐买入XX股票
║   建议：删除或替换为中性用语...
╚══════════════════════════════════════
```

### JSON 格式输出

```bash
python3 scripts/comply.py check --dir ../pipl-compliance/ --json --output report.json
```

### 免责声明专项

```bash
python3 scripts/comply.py disclaimer --dir ../pipl-compliance/
```

### 敏感词专项

```bash
python3 scripts/comply.py keywords --dir ../stock-planner/
```

### 批量检查多个 skill

```bash
# 自动扫描 ../ 下的所有 skill
python3 scripts/comply.py summary --dir ../
```

## 检查项详表

| 类别 | 检查内容 | 严重级别 |
|------|---------|----------|
| FINANCE | 荐股推荐、目标价、保证收益、需资质的金融用语 | high / medium / low |
| DISCLAIMER | 投资、法律免责声明是否存在及位置 | high / medium |
| EXAGGERATION | 极限词（最好、第一）、夸大描述、对比表述 | medium |
| SECURITY | subprocess/exec/eval/JSON 合法性/版本号格式 | critical / high / medium |
| RECOMMENDATIONS | 综合改进建议 | high / medium / low |

## 评分标准

| 分值区间 | 结论 | 含义 |
|----------|------|------|
| 80–100 | PASS | 可上架 |
| 50–79 | NEEDS_FIX | 建议修复后再上传 |
| 0–49 | REJECT | 强烈不建议上传 |

## 兼容性

- Python 3.8+
- 纯标准库，零外部依赖
- 跨平台（macOS / Linux / Windows）
- 无网络请求，所有检查在本地完成

## 法律免责声明

本工具仅为辅助检查参考，不构成任何形式的合规保证，不构成法律建议。最终合规责任由 skill 开发者自行承担。涉及具体合规问题时，请咨询专业律师。
