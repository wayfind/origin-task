---
name: ppt-enrich
description: |
  PPT content enricher - Generate slide content from skeleton with research.
  Use when: (1) User has skeleton.yaml and needs content, (2) User wants to fill in slide details, (3) User needs research to enrich presentation.
  Triggers: "PPT内容", "enrich slides", "填充内容", "slide-md", "内容补充"
---

# /ppt-enrich

> 从 skeleton.yaml 生成完整的 slide-md 内容文件

---

## 📋 Research Directive 执行协议（必读）

> **enrich 阶段的核心任务：解析 research_tasks，执行研究，填充结果。**

### Step 1: 解析 skeleton.yaml 中的研究任务

```yaml
# skeleton.yaml 示例
research_tasks:
  - id: "r01"
    query: "Tesla TSLA stock performance 2025"
    skill: "deep-research"
    required: true
    output_format: |
      - 年初价格: $XXX
      - 年末价格: $XXX
      - 涨跌幅: XX%
```

### Step 2: 显式输出每个研究任务

**必须在执行前输出任务详情：**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 RESEARCH TASK [r01]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skill: deep-research
Required: true

Query:
  Tesla TSLA stock performance 2025

Expected Format:
  - 年初价格: $XXX
  - 年末价格: $XXX
  - 涨跌幅: XX%

Status: ⏳ Executing...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 3: 调用 deep-research skill

```python
# 使用 Task 工具调用研究
Task(
    subagent_type="general-purpose",
    prompt=f"""
    执行研究任务 [{task_id}]:

    使用 openai-deep-research skill 研究：
    {query}

    输出格式：
    {output_format}

    要求：
    1. 必须有数据来源引用
    2. 数据时效性 < 6个月
    3. 具体数字，不要模糊表述
    """,
    description=f"Research: {task_id}"
)
```

### Step 4: 🆕 保存研究结果到文件（P0 强制）

> **⚠️ 关键**: 研究结果必须持久化，渲染器会验证！

**目录结构：**
```bash
output/project-name/
├── skeleton.yaml
├── research_results/        # 🆕 必须创建
│   ├── r01.md              # 研究结果
│   ├── r01.meta.json       # 元数据（推荐）
│   └── ...
└── slides/
```

**保存结果 - 使用 Write 工具：**
```python
# 保存 research_results/{task_id}.md
Write(
    file_path=f"{project_dir}/research_results/{task_id}.md",
    content=f"""# Research Result: {task_id}
Generated: {datetime.now().isoformat()}
Skill: deep-research

---

{research_result}

---

*来源: [sources]*
*研究时间: {date}*
"""
)
```

### Step 5: 填充到 slide-md

从 `research_results/{task_id}.md` 读取后填充：

```markdown
# 2025年股价回顾

<!-- @RESEARCH: r01 -->
- 年初价格: $248.42
- 年末价格: $445.03
- 涨跌幅: +79.1%

*来源: Yahoo Finance, 2025-12*
<!-- @/RESEARCH -->
```

### 🚫 渲染器验证（P0）

> **如果不保存 research_results/，渲染将被阻断！**

```
render.js 验证逻辑：
1. 读取 skeleton.yaml 中的 research_tasks
2. 检查 research_results/ 目录是否存在
3. 检查每个 required: true 的任务是否有对应 .md 文件
4. 任何缺失 → 拒绝渲染，输出错误

绕过方法（不推荐）：
  node render.js ./slides/ --skip-artifact-check
```

### 🚨 强制规则

```
❌ 禁止: 看到 research_tasks 却不执行
❌ 禁止: 不显式输出任务详情就执行
❌ 禁止: 用 WebSearch 代替 deep-research（当可用时）
❌ 禁止: 填充没有来源的数据
❌ 禁止: 使用超过 6 个月的旧数据

✅ 必须: 逐个处理每个 research_task
✅ 必须: 显式输出 "🔍 RESEARCH TASK [id]"
✅ 必须: 调用 Task 工具执行研究
✅ 必须: 在结果中包含来源引用
✅ 必须: 每个阶段完成后输出反思报告
```

---

## 🔄 强制反思协议（P1 必读）

> **每个阶段完成后，必须输出反思报告。**

### 反思输出格式

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 STAGE REFLECTION: RESEARCH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ research_results/ 目录已创建
✅ r01.md 已保存 (1,234 字符)
✅ r02.md 已保存 (987 字符)
⚠️ r01.md 缺少来源引用

⚠️  Warnings:
   - r01.md 缺少来源引用

📌 Next: 补充来源引用，然后生成 slide-md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Research 阶段检查清单

```
- [ ] research_results/ 目录已创建
- [ ] 所有 required: true 的任务都有对应 .md 文件
- [ ] 每个文件内容 > 100 字符
- [ ] 每个文件包含 "来源" 或 "Source" 字样
```

### Enrich 阶段检查清单

```
- [ ] slides/ 目录已创建
- [ ] 幻灯片数量与 skeleton 中定义一致
- [ ] @RESEARCH 标记区域已填充实际内容（非占位符）
- [ ] 每张幻灯片有标题
```

### 反思后行动

```
❌ 有错误 → 立即修复，重新执行当前步骤
⚠️ 有警告 → 输出警告，评估是否需要修复
✅ 全通过 → 继续下一阶段
```

### 研究质量检查清单

填充内容前，确认：

- [ ] **具体数据**: 有数字、百分比、金额（不是 "约" "大概"）
- [ ] **时效性**: 数据来自最近 6 个月
- [ ] **来源引用**: 每个关键数据标注出处
- [ ] **格式匹配**: 符合 output_format 要求

**不满足 → 重新执行研究！**

---

## 🎨 设计工具箱 (Design Toolkit)

> **重要**: 生成 slide-md 时，**必须**充分利用以下设计工具，确保输出美观大方、专业精致。

### 布局选择决策表

| 内容特征 | 推荐布局 | 原因 |
|----------|----------|------|
| 封面、章节标题、结尾 | `title-only` | 视觉冲击力强，突出主题 |
| 3-5 个要点/观点 | `bullets` | 清晰易读，经典布局 |
| 对比内容、优劣势、AB 测试 | `two-column` | 左右对称，对比鲜明 |
| 多案例、多特性并列 | `three-cards` | 卡片并排，信息独立 |
| 数据密集、多维度比较 | `table` | 行列整齐，信息密集 |
| 名人名言、重点强调 | `quote` | 突出显示，吸引注意 |
| 流程、时间线、层级关系 | `chart` | 可视化强，逻辑清晰 |

### 图表模板选择

| 内容类型 | 图表模板 | 语法 |
|----------|----------|------|
| 步骤、阶段、流程 | `process-flow` | `::: chart template: process-flow` |
| 传统 vs 现代、优劣势 | `comparison` | `::: chart template: comparison` |
| 历史、规划、路线图 | `timeline` | `::: chart template: timeline` |
| 层级、架构、分类 | `pyramid` | `::: chart template: pyramid` |
| 核心+扩展元素 | `circle-group` | `::: chart template: circle-group` |
| 复杂自定义 | Mermaid 代码 | ` ```mermaid ` 块 |

### 配图位置策略

| 幻灯片类型 | 图片位置 | 比例 | 效果 |
|------------|----------|------|------|
| 封面页 | `cover` | 16:9 | 全屏主视觉，冲击力强 |
| 章节标题页 | `section` | 16:9 | 背景装饰，主题突出 |
| 内容页 | `side` | 4:3 | 侧边装饰，增加美感 |
| 结尾页 | `ending` | 16:9 | 感谢装饰，温馨收尾 |

### ⚠️ 内容决策原则（必读）

**生成每张幻灯片前，依次检查：**

1. **有数据？→ 可视化**
   - ❌ 不要：堆砌数字文本
   - ✅ 要：用图表、指标卡片展示

2. **有对比？→ 双列或对比图**
   - ❌ 不要：一段文字描述优劣势
   - ✅ 要：`two-column` 或 `comparison` 图表

3. **有流程？→ 流程图**
   - ❌ 不要：1、2、3 编号列表
   - ✅ 要：`process-flow` 图表

4. **多案例？→ 卡片布局**
   - ❌ 不要：连续段落
   - ✅ 要：`three-cards` 并列展示

5. **有金句？→ Quote 布局**
   - ❌ 不要：混在正文中
   - ✅ 要：单独 `quote` 布局突出

6. **重要页面？→ 配装饰图**
   - 封面、章节页、结尾页都应该有配图
   - 使用 nano-banana-image 生成同色系图片

### 示例：如何决策布局

```
输入内容: "AI转型分三个阶段：快赢期(0-6月)、价值放大期(6-18月)、全面转型期(18月+)"

分析:
- 有"阶段"关键词 → 流程/时间线
- 有时间范围 → 适合 timeline 或 process-flow

决策: 使用 chart 布局 + process-flow 模板

输出:
---
slide:
  layout: chart
---
# AI转型路线图

::: chart
template: process-flow
title: AI转型三阶段
steps:
  - 快赢期 | 0-6月
  - 价值放大 | 6-18月
  - 全面转型 | 18月+
:::
```

---

## 概述

`/ppt-enrich` 是 PPT 生成流水线的内容填充环节，负责将结构骨架转换为具体的幻灯片内容。它会检测内容空缺、调用研究工具补充数据、整合案例，最终输出可直接渲染的 slide-md 文件。

## 定位

```
/ppt-outline → /ppt-enrich → /ppt-render
                    ↑
                你在这里
```

| 职责 | 说明 |
|------|------|
| ✅ 做 | 内容空缺检测、调用研究、生成 slide-md |
| ❌ 不做 | 修改骨架结构、渲染 PPTX |

## 用法

### 基本用法

```bash
/ppt-enrich skeleton.yaml              # 从骨架生成 slide-md
/ppt-enrich skeleton.yaml -o slides/   # 指定输出目录
/ppt-enrich skeleton.yaml --no-research # 跳过研究，仅生成框架
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<skeleton>` | 输入的 skeleton.yaml 文件 | 必填 |
| `--output`, `-o` | 输出目录 | `./slides/` |
| `--context`, `-c` | 上下文目录（补充内容来源） | - |
| `--no-research` | 跳过研究步骤 | `false` |
| `--research-mode` | 研究模式 (browser/api/mock) | `browser` |
| `--cache` | 启用研究缓存 | `true` |
| `--verbose`, `-v` | 详细输出 | `false` |

## 工作流程

### Step 1: 加载骨架

```yaml
# 读取 skeleton.yaml
structure:
  - id: "01-cases"
    title: "行业案例"
    type: case-study
    research_needs:
      - type: case_study
        query: "制造业AI案例"
        count: 3
```

### Step 2: 内容空缺检测

分析每个章节的内容充足度：

```
[01-cases] 行业案例
  ✗ Cases: 0/3 (need 3 more)
  ✗ Stats: 0/2 (need 2 more)
  ✓ Content: 1,200 chars
```

### Step 3: 执行研究（可选）

调用 deep-research 补充内容：

```
Researching: 制造业AI案例...
  → Found 3 cases from OpenAI Deep Research
  → Cached to: .cache/research/01-cases-abc123.json
```

### Step 4: 生成 slide-md

为每个章节生成幻灯片文件：

```
slides/
├── 00-01-cover.slide.md
├── 01-01-section.slide.md
├── 01-02-content.slide.md
├── 01-03-cases.slide.md
└── ...
```

## 输入格式

符合 [skeleton-spec.md](../ppt-specs/skeleton-spec.md) 规范的 YAML 文件。

## 输出格式

符合 [slide-md-spec.md](../ppt-specs/slide-md-spec.md) 规范的 Markdown 文件。

### 示例输出

```markdown
---
slide:
  id: "01-03"
  type: case-study
  layout: three-cards
  source_section: "01-cases"

sources:
  - url: "https://..."
    title: "来源报告"
    date: "2025-01"
---

# 制造业AI应用标杆

::: card
### 美的集团
智能供应链优化

`效率+30%`{.metric}
:::

::: card
### 宁德时代
AI质检系统

`良品率99%`{.metric}
:::
```

## 研究集成

### 支持的研究模式

| 模式 | 说明 | 要求 |
|------|------|------|
| `browser` | 通过浏览器自动化调用 ChatGPT | ChatGPT Plus 账号 |
| `api` | 通过 OpenAI API 调用 | OPENAI_API_KEY |
| `mock` | 使用模拟数据 | 无（测试用） |

### 研究请求格式

```json
{
  "section_id": "01-cases",
  "type": "case_study",
  "query": "Find 3 AI manufacturing cases with ROI metrics (2024-2025)",
  "constraints": {
    "region": "China preferred",
    "time_range": "2024-2025"
  }
}
```

### 研究结果缓存

- 缓存目录：`.cache/research/`
- 缓存有效期：7 天
- 缓存键：`{section_id}-{query_hash}.json`

## 内容生成规则

### 幻灯片数量估算

| 章节类型 | 每分钟幻灯片 | 说明 |
|----------|-------------|------|
| opening | 0.5 | 氛围为主 |
| content | 0.8 | 信息密度适中 |
| case-study | 0.6 | 案例需要展开 |
| framework | 0.7 | 图表为主 |
| closing | 0.4 | 简洁有力 |

### 内容来源优先级

1. 上下文文档（`--context`）
2. skeleton 中的 `content_hints`
3. 研究结果
4. 模板占位符

## 文件结构

```
.claude/skills/ppt-enrich/
├── SKILL.md                    # 本文档
├── scripts/
│   ├── enrich.py               # 主入口脚本
│   ├── gap_detector.py         # 内容空缺检测
│   ├── layout_advisor.py       # 🆕 布局决策顾问
│   ├── research/               # 研究模块
│   │   ├── __init__.py
│   │   ├── deep_research.py    # Deep Research 集成
│   │   ├── skill_discovery.py  # Skill 发现
│   │   └── image_generator.py  # 🆕 配图生成器
│   ├── research_runner.py      # 研究执行器
│   ├── content_merger.py       # 内容整合器
│   └── slidemd_writer.py       # slide-md 输出
└── templates/
    ├── cover.slide.md          # 封面模板
    ├── section.slide.md        # 章节模板
    ├── bullets.slide.md        # 要点模板
    ├── cards.slide.md          # 卡片模板
    └── quote.slide.md          # 引用模板
```

## 依赖

- Python >= 3.9
- PyYAML
- Jinja2（模板渲染）

可选：
- playwright（browser 研究模式）
- openai（api 研究模式）

## API（编程使用）

### 基础用法

```python
from enrich import PPTEnrich

enricher = PPTEnrich(
    skeleton_path='skeleton.yaml',
    context_dir='./docs/',
    research_mode='browser'
)

# 检测空缺
gaps = enricher.detect_gaps()

# 执行研究
enricher.run_research()

# 生成 slide-md
enricher.generate(output_dir='./slides/')
```

### 布局顾问 API

```python
from layout_advisor import LayoutAdvisor, get_design_guidelines

# 获取设计指南（供 LLM 参考）
guidelines = get_design_guidelines()
print(guidelines)  # 返回完整的设计决策参考文档

# 分析内容并推荐布局
advisor = LayoutAdvisor()

content = """
AI转型分三个阶段：
1. 快赢期（0-6月）：试点项目
2. 价值放大期（6-18月）：规模化
3. 全面转型期（18月+）：文化变革
"""

decision = advisor.recommend_layout(
    content=content,
    slide_type='content',  # cover/section/content/ending
    hints={'prefer_visual': True}
)

print(f"推荐布局: {decision.layout}")        # → LayoutType.CHART
print(f"图表类型: {decision.chart_type}")    # → ChartType.PROCESS_FLOW
print(f"配图位置: {decision.image_position}") # → None (内容页可选)
print(f"推荐理由: {decision.rationale}")     # → "内容包含流程/阶段描述..."
```

### 配图生成 API

```python
from research.image_generator import ImageGeneratorManager, ImageRequest

# 初始化管理器
img_manager = ImageGeneratorManager(
    output_dir=Path('./images'),
    theme='nano-banana-pro'
)

# 检查 nano-banana-image 是否可用
if img_manager.is_available():
    # 为骨架批量生成配图
    skeleton = {...}  # skeleton.yaml 内容
    image_paths = img_manager.generate_for_skeleton(skeleton)
    # → {'cover': Path('./images/cover.png'), '01': Path('./images/01-section.png'), ...}

    # 单张图片生成
    request = ImageRequest(
        prompt="AI technology abstract visualization",
        position='cover',
        aspect_ratio='16:9',
        style_hints=['tech', 'futuristic', 'dark theme']
    )
    result = img_manager.adapter.generate_image(request, Path('./images/custom.png'))
```

## 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `/ppt-outline` | 上游：提供 skeleton.yaml |
| `/ppt-render` | 下游：接收 slide-md，生成 PPTX |
| `/ppt` | 编排器：协调整个流程 |
| `openai-deep-research` | 依赖：执行研究查询 |
| `nano-banana-image` | 依赖：生成同色系装饰图 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.2.0 | 2026-01-13 | P2: 布局预决策强制集成 |
| 1.1.0 | 2026-01-12 | 添加 Layout Advisor 和配图生成 |
| 1.0.0 | 2026-01-12 | 初版 |

---

## 📐 布局预决策（P2 强制）

> **在生成 slide-md 之前，必须先调用 LayoutAdvisor 分析内容并决定布局。**

### 执行流程

```
1. 加载 skeleton.yaml
2. 运行 gap_detector 检测空缺
3. 执行 research 获取数据
4. 🆕 调用 layout_advisor.apply_layout_decisions() ← 预决策
5. 生成 slide-md 文件
```

### 预决策输出

**enrich.py 现在会自动输出：**

```
Applying layout decisions...
[LayoutAdvisor] 02-01: three-cards
  Rationale: 案例内容适合卡片布局，便于对比展示
[LayoutAdvisor] 03-01: chart
  Chart: timeline
  Rationale: 时间相关内容适合时间线图表

  Applied 5 layout decisions
```

### 布局使用方式

```python
# enrich.py 中已集成
enricher = PPTEnrich(skeleton_path, ...)

# 自动在 generate() 前调用
enricher.apply_layout_decisions()

# 生成时会使用布局决策
enricher.generate()
```

### 验证布局决策

预决策会在 skeleton 中添加 `_layout_decision` 字段：

```yaml
slides:
  - id: "02-01"
    type: content
    _layout_decision:
      layout: three-cards
      confidence: 0.9
      rationale: "..."
```

## 相关文档

- [skeleton-spec.md](../ppt-specs/skeleton-spec.md) - Skeleton YAML 规范
- [slide-md-spec.md](../ppt-specs/slide-md-spec.md) - Slide Markdown 规范
