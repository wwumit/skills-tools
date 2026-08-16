# 披露自测命令块（STANDARD.md §7 可直接引用）

> 机器可读规则集：`docs/disclosure-selfcheck-rules.json`（schema v1，供检查器/CI 消费）
> 自动执行：`skill-compliance` v1.4.0（`scripts/comply.py check --dir <skill>`，JSON 输出含 disclosure 摘要）
> 声明形态：SKILL.md frontmatter `disclosure`（snake_case）与 `permissions`；索引归一化 camelCase（§9）

## 命令块（作者提收录前跑）

```bash
# 7. 披露自查（DISCLOSURE v0.2，§9 字段契约）
# ── 7a. 云端依赖（D1 必填）：有网络调用必须 cloud:true + network 列端点 ──
grep -rE "requests\.(get|post|put|delete)|urllib\.(request|parse)|httpx|aiohttp|https?://" scripts/ 2>/dev/null
#   有输出 → SKILL.md frontmatter 必须有：
#     disclosure: { cloud: true, network: ["<实际端点>"] }
#   无输出 → cloud 应为 false；若 cloud:false 但上面有输出 = mismatch（DISCL-005）

# ── 7b. 凭据处理（D3 必填）：cloud:true 必须声明 api_keys ──
grep -A8 "^disclosure:" SKILL.md | grep -E "api_keys|env:|storage:"
#   预期：api_keys 下列出 env（如 COMPLIANCEHUB_API_KEY）+ storage（如 file-0600）

# ── 7c. 权限声明（D4 必填）：frontmatter 必须有 permissions ──
grep -c "^permissions:" SKILL.md   # 预期 ≥1

# ── 7d. 端点一致性（DISCL-006）：声明端点 vs 代码实际端点 ──
grep -rhoE "https?://[a-zA-Z0-9.-]+" scripts/ 2>/dev/null | sort -u
#   对照 disclosure.network 声明，未声明端点 = 不一致

# ── 7e. 法域/保留（D5/D6 建议）：jurisdiction + retention ──
grep -E "jurisdiction:|retention:" SKILL.md | head -4

# ── 7f. DSH 宿主依赖硬规则（DEP-001）：@deepseek-ai/* 只能在 peerDependencies ──
node -e "const p=require('./package.json');const d={...p.dependencies,...p.bundledDependencies};console.log('宿主包在 dependencies:',Object.keys(d||{}).filter(k=>k.startsWith('@deepseek-ai/')))"
#   预期输出：宿主包在 dependencies: [] （放 peerDependencies / devDependencies）
```

## 判定

| 状态 | 条件 | 市场三态 |
|---|---|---|
| 披露完整 | 7a-7c 全过 + 7d 一致 + 7f 无宿主包 | ✅ 已披露 |
| 缺必填 | 7a/7b/7c 任一不过（D1/D3/D4 缺失） | ⚠️ 缺必填项 |
| 未声明 | 无 disclosure 块但 7a 有网络调用 | ❓ 未声明数据行为 |
