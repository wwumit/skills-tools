---
name: runtime-probe
version: 1.1.0
description: |
  DSH 插件实机验证引导器。对任意插件目录生成标准验证脚本，在真实 DSH SkillRegistry 中注册插件，
  执行 list()/get() 实测，输出证据契约报告（verifiedBy/verifiedAt/reportUrl/schemaVersion）。
  替代每插件复制 verify-dsh.ts 的做法。需 DSH 开发环境（node_modules 含 tsx/cordis/dsh-skill）。
  Use when: 用户要在发布 DSH 插件前做实机验证，或插件 list/get 异常需要复现。
  Trigger: runtime-probe, 实机验证, smoke-test, verify-dsh, 插件实测, 运行验证
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
disclaimer: 本工具为辅助性参考工具，不构成任何保证；验证结果仅代表当前环境与 catalog 快照。
---

# 🧪 runtime-probe — DSH 插件实机验证引导器

## Overview
对任意 DSH 插件目录：生成标准 verify 脚本（模板）→ 注册插件到真实 SkillRegistry →
`list()`/`get()` 实测 → 输出**证据契约报告**（verifiedBy / verifiedAt / reportUrl / schemaVersion）。
"含实测结果"自证（对齐 dshbase 目录特色），替代逐插件复制 verify-dsh.ts。

## Usage
```bash
# 前置：插件目录已 ln -s DSH 的 node_modules（或 node_modules 含 tsx）
python3 scripts/runtime-probe.py --dir <插件目录> --catalog <catalog URL>
python3 scripts/runtime-probe.py --dir <插件目录> --catalog <URL> --format json
```

## 输出（证据契约 JSON 摘要）
```json
{
  "verifiedBy": "runtime-probe@1.0.0",
  "verifiedAt": "2026-08-17T10:29:52Z",
  "reportUrl": "<catalog URL>",
  "schemaVersion": "probe-v1",
  "plugin": "@wwumit/dsh-office",
  "skillCount": 2,
  "skills": ["excel2insights", "sum2slides-pro"],
  "sample": { "name": "excel2insights", "bytes": 7871, "head": "..." },
  "pass": true
}
```

## 与其他工具的关系
- `bundle-lint`：bundle 结构（"装得进去"）
- **runtime-probe**：实机验证（"装了能用"）
- `skill-compliance` / `dependency-scan` / `malware-scan`：内容/供应链/恶意检查
- CI 模板（dsh-plugin-tools 仓库 `templates/ci/plugin-gate.yml`）把以上全部串成发布门禁
