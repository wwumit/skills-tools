# Skills Tools

## Skills

| Skill | Description | Version |
|---|---|---|
| `agent-tools` | 智能体开发辅助工具集。Token计数(多模型对比：GPT-4o/GPT-4/ | 1.0.0 |
| `csv-tools` | CSV 工具集 v1.1.0 — 子命令+安全增强。 | 1.1.0 |
| `excel2insights` | 结构化数据（CSV/XLSX/XLS/TSV）分析与可视化工具：自动统计分析、数据质量检查、 | 2.0.0 |
| `excel2insights-pro` | Excel2Insights Pro — 交互式数据分析和可视化仪表板。 | 1.1.0 |
| `expert2skill` | 专家方法沉淀器（meta-skill）— 通过引导式访谈，把一个"具备专业技术/知识但不懂 AI" | 1.0.2 |
| `finance-tools` | 财务分析工具集 v1.1.0。7个子命令覆盖财务分析全流程。 | 1.1.0 |
| `fitness-daily` | 每日健身自律打卡：身体活动/营养与恢复/心理与习惯/纪律底线 四组 15 项清单， | 1.0.0 |
| `study-abroad-assistant` | 美国研究生申请助理（美国 · 理工大类：CS/EE/Data 等）— 引擎增强版专家 skill。 | 1.1.1 |
| `sum2slides-pro` | 将多说话人对话/群聊记录一键转化为结构化 PPT（meeting/brainstorm/retro 模板），纯本地生成 PPTX。 | 1.1.0 |

## Install

```bash
# Install one skill (skills.sh CLI)
npx skills add wwumit/skills-tools --skill <name>

# Install all skills in this repo
npx skills add wwumit/skills-tools --all
```

Skills are also compatible with DeepSeek Harness (DSH): copy the skill directory into
`~/.dsh/skills/` or `<project>/.dsh/skills/` and it is auto-discovered.

## License

MIT
