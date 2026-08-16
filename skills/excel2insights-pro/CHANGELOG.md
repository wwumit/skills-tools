# Excel2Insights Pro — 更新日志

## [1.1.0] - 2026-07-19

### 新增
- **Plotly 交互式图表** — 取代静态 matplotlib/seaborn，支持缩放、悬停、筛选
- **品牌化交互式 HTML 仪表板** — 一键生成自包含的 HTML 仪表板，支持品牌颜色、Logo 定制
- **品牌模板系统** — 通过 `--init-brand` 生成品牌配置文件，支持自定义颜色、字体、Logo
- **完整分析管线** — `auto-pipeline.py` 一键运行：加载 → 分析 → 图表 → 仪表板
- **数据质量面板** — 仪表板内嵌缺失值分析、列类型概览
- **关键洞察** — 自动生成数据洞察标签（positive/warning/error）

### 变更
- 依赖从 matplotlib/seaborn 迁移到 plotly
- `chart-generator.py` 输出 HTML 交互式图表
- 新增 `dashboard-generator.py` — 核心 Pro 功能
- 更新 `auto-pipeline.py` 支持完整的仪表板生成管线
- 版本号从 1.0.0 升级到 1.1.0

### 移除
- 移除 matplotlib/seaborn 依赖
- 移除静态 PNG 图表输出（使用 Plotly HTML 替代）
