# /ppt-enrich

> 从 skeleton.yaml 生成完整的 slide-md 内容文件

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

## 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `/ppt-outline` | 上游：提供 skeleton.yaml |
| `/ppt-render` | 下游：接收 slide-md，生成 PPTX |
| `/ppt` | 编排器：协调整个流程 |
| `openai-deep-research` | 依赖：执行研究查询 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-01-12 | 初版 |

## 相关文档

- [skeleton-spec.md](../ppt-specs/skeleton-spec.md) - Skeleton YAML 规范
- [slide-md-spec.md](../ppt-specs/slide-md-spec.md) - Slide Markdown 规范
