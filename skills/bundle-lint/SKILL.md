---
name: bundle-lint
version: 1.0.0
description: |
  DSH 插件 bundle 结构一致性校验器。校验 cordis.patch.yml、package.json 的 dsh 插件配置、
  files 清单、入口文件与 bundle id/name 一致性——发布前自检，避免被市场/目录收录时打回。
  纯本地、零依赖、输出 JSON 报告（BND-001~006）。
  Use when: 用户要在发布 DSH 插件前检查 bundle 结构，或插件被收录/安装时报 bundle 相关错误。
  Trigger: bundle-lint, bundle检查, bundle校验, cordis.patch, 插件结构检查, 发布前检查
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

# 📦 bundle-lint — DSH 插件 bundle 结构校验器

## Overview
发布 DSH 插件前，校验 bundle 三件套（cordis.patch.yml / package.json dsh 配置 / 入口）是否自洽。规则：
- **BND-001** cordis.patch.yml 存在且可解析（insert 结构完整）
- **BND-002** package.json dsh 插件配置完整（plugin:true / kind / bundle.patch）
- **BND-003** files 清单覆盖 cordis.patch.yml 与入口（npm 发布后 bundle 不丢）
- **BND-004** 入口文件存在（main / exports 指向的文件）
- **BND-005** bundle id/name 与 package name 一致（装进去的包名对得上）
- **BND-006** 结构符合 DSH STANDARD（关键词标识便于生态发现）

## Usage
```bash
python3 scripts/bundle-lint.py --dir <插件目录> --format text   # 终端报告
python3 scripts/bundle-lint.py --dir <插件目录> --format json   # JSON 报告
```

## 输出（JSON 摘要）
```json
{
  "score": 100,
  "conclusion": "PASS",
  "issues": [
    { "rule": "BND-001", "severity": "high", "found": "...", "recommendation": "..." }
  ]
}
```

## 与其他工具的关系
- `skill-compliance`：内容合规（披露/免责/红线）
- `dependency-scan`：依赖供应链
- `malware-scan`：恶意代码
- **bundle-lint**：bundle 结构（"装得进去"的前置检查）
