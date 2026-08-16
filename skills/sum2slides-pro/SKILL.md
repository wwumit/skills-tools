---
name: sum2slides-pro
description: |
  将多说话人对话/群聊记录一键转化为结构化 PPT（meeting/brainstorm/retro 模板），纯本地生成 PPTX。
  Use when: 用户需要把群聊、会议记录、AI 对话总结成 PPT 演示文稿。
  触发词：sum2slides, 对话转PPT, 群聊生成PPT, 会议纪要转PPT, pptx, auto-pipeline
disclosure:
  cloud: false
  network: []
  offline_mode: true
  api_keys: []
  jurisdiction: []
  retention: "none"
permissions:
  network: []
  filesystem:
    write: []
  env: []

---

# Sum2Slides Pro — 群聊/对话一键生成PPT

## 概述

Sum2Slides Pro 是一个将多说话人对话内容自动转化为结构化 PPT 演示文稿的技能。它解析群聊记录或人机对话文本，提取关键主题、决策点、待办事项和时间线，然后生成专业的 PPTX 文件。

**一句话：群聊讨论结束 / 跟AI聊完 → 一键出PPT。**

---

## 什么时候使用

适用场景（不限于会议，适合各类讨论→产出）：

### 场景A：群聊讨论 → PPT
用户在飞书群、钉钉群、企业微信群、Discord、Slack 等群里讨论完一件事（周会、需求评审、头脑风暴、复盘），agent可以直接拉取群聊记录，输出结构化的PPT总结。

触发关键词示例：
- "把这个讨论整理成PPT"
- "把群里的讨论总结一下，出个PPT"
- "会议纪要出个演示文稿"
- "把刚才讨论的结论做成PPT发给大家"

### 场景B：人机对话 → PPT
用户跟AI助手（无论哪个模型）进行了一场深度对谈（头脑风暴、方案探讨、学习笔记），agent 可以把对话内容提取要点，输出PPT。

触发关键词示例：
- "把刚才跟AI的对话整理成PPT"
- "把我跟助手聊的方案出个演示文稿"
- "对话总结做成幻灯片"

---

## 工作流程

### Step 1: 获取对话文本

支持以下输入方式：

1. **直接粘贴对话文本** — 带说话人标记（`姓名: 内容`）的纯文本
2. **Markdown 格式** — 带 `## 主题` 标题和 `**姓名**:` 标签的文档
3. **JSON 数组** — `[{speaker, text}]` 结构化数据
4. **文件路径** — 指向本地对话记录文件

### Step 2: 解析对话

`chat-parser.py` 自动检测输入格式并解析：
- 识别所有说话人
- 统计消息数量和对话活跃度
- 自动按话题分段

### Step 3: 提取结构

`topic-extractor.py` 分析对话内容：
- **话题分割** — 把对话按主题自动分段
- **关键点提取** — 每个话题的核心观点
- **决策检测** — 识别达成一致的决议
- **待办提取** — 找出谁负责什么、什么时间完成
- **时间线** — 对话中的关键时间节点

### Step 4: 匹配模板

| 模板 | 适用场景 |
|------|---------|
| `meeting` | 会议讨论、需求评审、项目同步 |
| `brainstorm` | 创意讨论、头脑风暴、方案探索 |
| `retro` | 回顾复盘、Sprint回顾、阶段总结 |
| `default` | 通用场景、日常讨论 |

### Step 5: 生成PPT

`slide-builder.py` 输出包含以下结构的 PPTX：

```
Slide 1: 标题页 — 讨论主题 + 参与者 + 日期
Slide 2: 概览 — 话题数/决策数/待办数/参与人数
Slide 3-N: 每个话题一页 — 关键点 + 引用 + 相关决策
Slide N+1: 决策页 — 所有达成的决议清单
Slide N+2: 待办页 — 负责人 + 任务 + 截止时间
Final: 附录 — 参与人列表 + 对话时长
```

### Step 6: 输出文件

默认导出 `.pptx` 格式，兼容 PowerPoint 和 WPS。

---

## 使用方式

### 方式1：一键全流程（推荐）

```bash
# 群聊记录 → PPT
python3 scripts/auto-pipeline.py --input demo-group-chat.txt --template meeting

# 人机对话 → PPT
python3 scripts/auto-pipeline.py --input demo-ai-conversation.txt --template brainstorm

# 自定义品牌色
python3 scripts/auto-pipeline.py --input chat.txt --brand-color "#1a56db" --output report.pptx
```

### 方式2：分步执行

```bash
# 解析对话
python3 scripts/chat-parser.py --input chat.txt --output parsed.json

# 提取主题
python3 scripts/topic-extractor.py --input parsed.json --output outline.json

# 生成PPT
python3 scripts/slide-builder.py --outline outline.json --template meeting --output summary.pptx
```

### 方式3：Agent 调用

当用户提出"把这段讨论出个PPT"时，agent 应该：
1. 获取用户提供的对话文本（支持粘贴、文件、或从平台拉取）
2. 保存到临时文件
3. 调用 `python3 scripts/auto-pipeline.py --input TEMP_FILE --template [meeting|brainstorm|retro]`
4. 读取生成的 PPTX 文件路径
5. 告知用户文件位置，或直接发送

---

## 场景C：腾讯会议集成（竞赛加分项）

用户从腾讯会议导出AI纪要或转写后，可以通过以下流程生成PPT：

```
# Step 1: 通过 腾讯会议 Skill 获取会议数据
# (agent 调用 腾讯会议 Skill 获取 AI 纪要或转写)

# Step 2: 转换为 Sum2Slides 格式
python3 scripts/tmeet-import.py --transcript meeting_transcript.json --output chat.txt

# Step 3: 一键生成PPT
python3 scripts/auto-pipeline.py --input chat.txt --template meeting
```

**触发词示例**：
- "把今天腾讯会议的讨论整理成PPT"
- "把上周的评审会纪要做成演示文稿"
- "帮我用腾讯会议记录生成一份PPT总结"


## 场景D：个人头脑风暴 → 报告/讲义

用户与AI助手就某一话题进行深度对谈（技术调研、学习讨论、方案策划），可以将对话整理成结构化的讲义、教程或书面报告。

触发关键词示例：
- "把刚才的讨论整理成讲义"
- "把这个话题的探讨写成报告"
- "把对话内容做成教学材料"
- "把我跟AI聊的方案整理成汇报PPT"

## 场景E：讨论结果 → 领导汇报

团队完成讨论或评审后，需要将结论向管理层汇报。直接输入讨论记录，生成层级清晰的汇报PPT。

触发关键词示例：
- "把这次评审结果整理成汇报PPT"
- "把讨论结论做成给领导看的演示文稿"
- "出个汇报版本，精简但要点清晰"

> 输出熟练不受限制（默认最多50页），可以根据内容深度自动扩展。详见 `--max-slides` 参数。

---

## 依赖

```bash
pip install python-pptx PyYAML
```

Python 3.9+ 环境。

---

## 示例

### 示例1：群聊讨论

**输入**（从飞书群复制）：
```
老王: 今天拉个会，讨论Q3产品路线图...
小张: 8%不容易，但留存数据还行...
小李: 技术上两个月能搞定...
```

**输出**：8页PPT → 含话题概览、3个主题页、决策页、待办页

### 示例2：人机对话

**输入**：
```
我: 最近在做AI Agent项目，遇到一个瓶颈...
AI: 说说看，什么瓶颈？
我: Agent在复杂任务中的决策准确率不够高...
```

**输出**：6页PPT → 含问题分析、建议方案、实施步骤

---

## 模板定制

可自定义品牌色和Logo：

```bash
python3 scripts/auto-pipeline.py --input chat.txt --brand-color "#2b6af6" --brand-logo logo.png
```

内置模板列表：
```bash
python3 scripts/template-manager.py --list
```

---

## 合规与安全

- **纯本地处理**：对话文本不会离开用户设备（除非用户主动配置第三方服务）
- **依赖透明**：仅依赖 python-pptx 和 PyYAML 两个开源库
- **见 DISCLAIMER.md**：完整免责声明和版权信息
- **AIGC 标识**：生成的 PPT 属于 AI 辅助内容，根据《生成式人工智能服务管理暂行办法》第十二条，用户在公开使用时应标注“本内容由 AI 辅助生成”或类似标识

---

## 相关链接

- [GitHub 仓库](https://github.com/cqdev-ai/sum2slides-pro)
- [Demo: 群聊样例](assets/demo-group-chat.txt)
- [Demo: 人机对话样例](assets/demo-ai-conversation.txt)
