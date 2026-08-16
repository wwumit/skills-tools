> ⚠️ **免责声明**：本工具为辅助性参考工具，**不构成投资建议，不构成法律建议**。市场有风险，投资需谨慎；据此操作，风险自担。正式合规意见请咨询具备资质的律师。最终决策与责任由使用者自行承担。
> **仅供学习研究参考**；> **仅供参考，不构成任何操作依据**；市场有风险，投资需谨慎，据此操作风险自担。

# Sum2Slides Pro 📽️ — 群聊 / 对话一键生成PPT

> **让讨论不白费 —— 群聊/头脑风暴/会议 → 共识+分歧+行动计划，一键出PPT**

Sum2Slides Pro 是一个将多人群聊讨论或人机对话自动转化为结构化PPT演示文稿的工具。适合飞书群、钉钉群、企业微信群、Slack等团队协作场景，以及个人与AI助手的深度对谈场景。

---

## 核心场景

| 场景 | 说明 | 示例 |
|------|------|------|
| 🏢 **群聊讨论** | 飞书/钉钉/企微群讨论完出PPT | 周会、需求评审、头脑风暴 |
| 🤖 **人机对话** | 跟AI深度对谈后生成报告/讲义 | 方案探讨、技术调研、学习笔记 |
| 📊 **会议导入** | 腾讯会议AI纪要/转写 → PPT（竞赛加分） | 评审会总结、周会纪要 |
| 📋 **领导汇报** | 讨论结论输出精简汇报 | 项目评审汇报、决策报告 |
| 📚 **讲义教程** | 头脑风暴内容整理成教学材料 | 技术教程、培训讲义、研究报告 |

---

## 快速上手

### 安装依赖

```bash
pip install python-pptx PyYAML
```

### 用法1：群聊记录 → PPT

```bash
python3 scripts/auto-pipeline.py --input assets/demo-group-chat.txt --template meeting
```

### 用法2：人机对话 → PPT

```bash
python3 scripts/auto-pipeline.py --input assets/demo-ai-conversation.txt --template brainstorm
```

### 用法3：从腾讯会议导入

```bash
# 1. 获取腾讯会议AI纪要/转写（通过 腾讯会议 Skill）

# 2. 转换成 Sum2Slides 格式
python3 scripts/tmeet-import.py --transcript transcript.json --output chat.txt

# 3. 生成PPT
python3 scripts/auto-pipeline.py --input chat.txt --template meeting
```

### 用法4：自定义品牌

```bash
python3 scripts/auto-pipeline.py --input chat.txt --brand-color "#1a56db" --brand-logo logo.png --output report.pptx
```

---

## 生成PPT结构

```
Slide 1: 标题页 — 讨论主题 + 参与者 + 日期
Slide 2: 概览 — 话题数 / 决策数 / 待办数 / 参与人数
Slide 3-N: 每个话题一页 — 关键点 + 引用 + 决策
Slide N+1: 决策页 — 所有决议清单
Slide N+2: 待办页 — 负责人 + 任务 + 截止时间
Final: 附录 — 参与人、对话时长
```

---

## 内置模板

| 模板 | 适用场景 | 配色 |
|------|---------|------|
| `meeting` | 会议讨论、需求评审 | 深蓝/白 |
| `brainstorm` | 创意讨论、头脑风暴 | 多彩 |
| `retro` | 回顾复盘、阶段总结 | 墨绿/白 |
| `default` | 通用场景 | 蓝灰/白 |

---

## 脚本说明

| 脚本 | 功能 | 用法 |
|------|------|------|
| `auto-pipeline.py` | 一键全流程 | `--input FILE [--template NAME] [--output PATH]` |
| `chat-parser.py` | 对话解析 | `--input FILE [--format auto\|text\|markdown\|json]` |
| `topic-extractor.py` | 话题提取 | `--input PARSED_JSON [--output OUTLINE_JSON]` |
| `slide-builder.py` | PPT生成 | `--outline JSON [--template NAME] [--output PATH]` |
| `template-manager.py` | 模板管理 | `--list \| --show NAME` |

### 分步使用

```bash
# Step 1: 解析对话
python3 scripts/chat-parser.py --input input.txt --output parsed.json

# Step 2: 提取主题
python3 scripts/topic-extractor.py --input parsed.json --output outline.json

# Step 3: 生成PPT
python3 scripts/slide-builder.py --outline outline.json --template meeting --output output.pptx
```

---

## 输入格式支持

### 纯文本（自动识别说话人）

```
老王: 今天讨论Q3产品路线图
小张: 我觉得应该聚焦用户增长
老王: 同意，社交裂变是个方向
```

### Markdown

```markdown
## Q3路线图讨论

**老王**: 今天讨论Q3产品路线图
- 活跃用户增长率从5%提升到8%

**小张**: 我觉得应该聚焦用户增长
- 当前次日留存42%
```

### JSON

```json
[
  {"speaker": "老王", "text": "今天讨论Q3产品路线图"},
  {"speaker": "小张", "text": "我觉得应该聚焦用户增长"}
]
```

---

## 输出格式

- **PPTX**：标准PowerPoint格式，兼容WPS Office
- 自动排版：标题、概览、话题、决策、待办、附录页面
- 支持品牌色 + Logo 自定义

---

## 示例效果

### 群聊讨论 → 5页PPT

```
📋 输入: 群聊讨论Q3产品路线图（19条消息，3人）
📑 输出:
  Slide 1:  产品路线图讨论 — 老王/小张/小李
  Slide 2:  概览 — 7项决策，2项待办，3位参与者
  Slide 3:  讨论话题详情
  Slide 4:  决策汇总（7项决议）
  Slide 5:  待办事项（含负责人）
```

### 人机对话 → 5页PPT

```
📋 输入: 与AI讨论Agent决策优化（18轮对话）
📑 输出:
  Slide 1:  AI Agent决策优化探讨
  Slide 2:  概览 — 4项决策，1项待办
  Slide 3:  核心讨论：Agent批判性思维
  Slide 4:  决策汇总
  Slide 5:  后续行动
```

> 实际输出页数取决于输入内容的信息密度和话题数量。更多话题 = 更多幻灯片。

---

## 依赖

```
python-pptx>=1.0.0     # PPTX生成
PyYAML>=6.0            # 配置解析
```

Python 3.9+，无其他系统依赖。

---

## 安全说明

- ✅ **纯本地运行**：所有对话数据处理均在用户设备本地完成
- ✅ **无网络请求**：默认不向任何外部服务器发送数据
- ✅ **依赖透明**：仅依赖两个知名开源库（python-pptx, PyYAML）
- ⚠️ 品牌Logo和颜色自定义完全本地，不上传

---

## 免责声明

见 [DISCLAIMER.md](DISCLAIMER.md)

---

## 版权信息

© 2026 ChengQian（成乾）· cqdev-ai  
GitHub: https://github.com/cqdev-ai/sum2slides-pro
