---
name: dependency-scan
version: 1.0.0
description: |
  供应链依赖扫描器。扫描 package.json 的依赖声明，检查：DSH 宿主遮蔽（@deepseek-ai/* 进普通 dependencies）、
  版本未锁定（范围符）、已知高危/可疑依赖（内置基线）、宿主包缺 peerDependencies 声明。
  纯本地、无第三方依赖、输出 JSON 报告——发布插件/技能前的供应链自检工具。
  Use when: 用户要在发布插件/技能前检查依赖供应链，或询问依赖安全/版本锁定/宿主遮蔽。
  Trigger: dependency-scan, 依赖扫描, 供应链检查, 依赖安全, 版本锁定, 宿主遮蔽
disclosure:
  cloud: false
  network: []
  offline_mode: true
  api_keys: []
  jurisdiction: ["CN"]
  retention: "none"
permissions:
  network: []
  filesystem:
    write: []
  env: []
disclaimer: 本工具为辅助性参考工具，不构成法律建议；最终发布责任由使用者自行承担。
---

# 🔒 Dependency Scan — 供应链依赖扫描器

## Overview
发布插件/技能前，扫描 package.json 依赖声明的供应链风险。规则：
- **DEP-001** DSH 宿主遮蔽：`@deepseek-ai/*` 宿主接口包进普通 `dependencies`/`bundledDependencies`（遮蔽宿主风险）
- **DEP-002** 版本未锁定：依赖使用 `^/~/>=/*` 范围符（可复现构建需精确锁定）
- **DEP-003** 高危/可疑依赖：内置基线（无维护/已知问题包；完整威胁情报需生态级规则库）
- **DEP-004** peer 完整性：代码引用 `@deepseek-ai/*` 但 peerDependencies 未声明

## Usage
```bash
python3 scripts/dependency-scan.py --dir <插件目录> --format json
```

## 输出（JSON）
```json
{
  "scanner": "dependency-scan@1.0.0",
  "issues": [
    { "rule": "DEP-002", "severity": "medium", "found": "版本未锁定: event-stream@^3.3.6" }
  ],
  "score": 85
}
```

## 实现说明（与 skill-compliance 同源）
- 本工具是 skill-compliance 依赖检查（DEP-001~004）的**独立 CLI 入口**——检查逻辑由 skill-compliance 提供，规则一处演进，避免两套实现
- skill-compliance 是 STANDARD §7/§9 采纳的权威检查器（含 DEP 检查）；dependency-scan 提供依赖专项的独立调用入口
- 纯 Python 标准库，无网络请求，无第三方依赖；不执行代码、不安装依赖，只读 package.json 与入口文件
