# Slide Markdown Specification v1.0

> 单页幻灯片内容格式规范 - `/ppt-enrich` 的输出，`/ppt-render` 的输入

---

## 1. 概述

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **人类可编辑** | 使用熟悉的 Markdown 语法 |
| **结构化** | YAML Frontmatter 定义元数据 |
| **富语义** | 扩展语法支持演示特有元素 |
| **可追溯** | 保留研究来源和引用 |

### 1.2 文件结构

```
{project}/slides/
├── 00-cover.slide.md           # 封面页
├── 01-01-section-title.slide.md # 章节标题页
├── 01-02-content.slide.md      # 内容页
├── 01-03-cases.slide.md        # 案例页
└── ...
```

### 1.3 命名规范

```
{章节序号}-{页面序号}-{简短描述}.slide.md
```

示例：
- `00-01-cover.slide.md` - 封面
- `01-01-section-intro.slide.md` - 第一章标题
- `02-03-case-manufacturing.slide.md` - 第二章第3页案例

---

## 2. 文件格式

### 2.1 基本结构

```markdown
---
# YAML Frontmatter（必须）
slide:
  id: "01-02"
  type: content
  layout: bullets
---

# 幻灯片标题

正文内容...
```

### 2.2 Frontmatter Schema

```yaml
---
slide:
  # 必填字段
  id: string              # 唯一标识，如 "01-02", "02-case-1"
  type: enum              # cover | section | content | case-study | quote | closing

  # 布局（可选，有默认值）
  layout: enum            # title-only | bullets | two-column | three-cards |
                          # table | quote | image-left | image-right | full-image

  # 来源章节（可选，追溯用）
  source_section: string  # skeleton 中的章节 ID

  # 时长建议（可选）
  duration: integer       # 秒，建议停留时间

  # 演讲者备注开关（可选）
  speaker_notes: boolean  # 是否包含备注，默认 true

  # 动画提示（可选）
  animation: enum         # none | fade | slide-left | build-bullets

# 研究来源（可选，用于追溯）
sources:
  - url: string
    title: string
    date: string          # YYYY-MM-DD
    type: enum            # report | news | official | academic

# 自定义样式覆盖（可选）
style:
  background: string      # 颜色或图片路径
  accent: string          # 强调色覆盖
---
```

---

## 3. 幻灯片类型 (slide.type)

### 3.1 类型说明

| 类型 | 说明 | 推荐布局 | 典型用途 |
|------|------|----------|----------|
| `cover` | 封面页 | `title-only` | PPT 首页 |
| `section` | 章节标题页 | `title-only` | 章节分隔 |
| `content` | 内容页 | `bullets`, `two-column` | 正文讲解 |
| `case-study` | 案例页 | `three-cards`, `two-column` | 案例展示 |
| `quote` | 引用页 | `quote` | 金句、专家言论 |
| `closing` | 结束页 | `title-only`, `bullets` | 总结、Q&A |

### 3.2 布局说明

| 布局 | 说明 | 支持的内容元素 |
|------|------|----------------|
| `title-only` | 仅标题 | 标题 + 副标题 |
| `bullets` | 要点列表 | 标题 + 列表 |
| `two-column` | 双列 | 标题 + 左右内容块 |
| `three-cards` | 三列卡片 | 标题 + 3个卡片 |
| `table` | 表格 | 标题 + 表格 |
| `quote` | 引用 | 引用 + 来源 |
| `image-left` | 左图右文 | 图片 + 文字 |
| `image-right` | 左文右图 | 文字 + 图片 |
| `full-image` | 全屏图 | 背景图 + 叠加文字 |

---

## 4. 内容语法

### 4.1 标题

```markdown
# 主标题（一级标题）

## 副标题（可选）
```

### 4.2 要点列表

```markdown
- 第一个要点
- 第二个要点
- **强调的要点**
- 包含数据的要点 `+30%`
```

### 4.3 双列布局

使用 `:::` 分隔符标记列：

```markdown
::: left
### 左侧标题
- 左侧要点1
- 左侧要点2
:::

::: right
### 右侧标题
- 右侧要点1
- 右侧要点2
:::
```

### 4.4 卡片组

使用 `:::card` 标记卡片：

```markdown
::: card
### 卡片标题
卡片描述文字

`效率提升 30%`{.metric}
:::

::: card
### 第二张卡片
另一段描述

`成本降低 25%`{.metric}
:::
```

### 4.5 表格

标准 Markdown 表格：

```markdown
| 维度 | 传统模式 | AI模式 | 提升 |
|------|----------|--------|------|
| 开发周期 | 6个月 | 2个月 | 3x |
| 人力成本 | 50人 | 15人 | 70% |
```

### 4.6 引用

```markdown
> 未来十年，最稀缺的不是AI技术，而是敢于把核心业务交给AI去重构的企业家勇气和组织能力
>
> — 来源说明
```

### 4.7 图片

```markdown
![图片说明](./images/diagram.png){.center width=80%}
```

### 4.8 数据高亮

行内数据标记：

```markdown
市场规模达到 `$1.5万亿`{.highlight} 美元
效率提升 `+45%`{.metric .positive}
成本增加 `-20%`{.metric .negative}
```

### 4.9 图标/Emoji 提示

```markdown
:bulb: 关键洞察
:warning: 风险提醒
:chart_increasing: 增长趋势
:factory: 制造业
```

---

## 5. 演讲者备注

使用 `---notes---` 分隔符：

```markdown
---
slide:
  id: "02-01"
  type: content
---

# 内容标题

- 要点1
- 要点2

---notes---

这里是演讲者备注内容：
- 这一页大约讲 2 分钟
- 可以举一个客户的真实例子
- 如果时间紧张可以跳过第三个要点
```

---

## 6. 研究结果嵌入

### 6.1 来源追溯

在 frontmatter 中声明来源：

```yaml
---
slide:
  id: "02-03"
  type: case-study

sources:
  - url: "https://example.com/report.pdf"
    title: "2024年制造业AI白皮书"
    date: "2024-06"
    type: report
  - url: "https://news.example.com/article"
    title: "某企业AI转型案例"
    date: "2024-12-15"
    type: news
---
```

### 6.2 行内引用

使用 `[^1]` 标记引用：

```markdown
根据麦肯锡报告[^1]，制造业AI渗透率已达 `35%`{.metric}。

[^1]: McKinsey Global Institute, "AI in Manufacturing 2024"
```

### 6.3 案例结构化数据

对于案例页，使用结构化格式：

```markdown
---
slide:
  id: "02-case-01"
  type: case-study
  layout: three-cards

cases:
  - company: "美的集团"
    industry: "制造业"
    application: "智能供应链优化"
    metrics:
      - label: "库存周转"
        value: "+40%"
      - label: "交付准时率"
        value: "98.5%"
    source: "2024年报"
---

# 制造业AI应用案例
```

---

## 7. 完整示例

### 7.1 封面页

```markdown
---
slide:
  id: "00-cover"
  type: cover
  layout: title-only
---

# 生成式AI驱动的产业应用与企业转型

## 清华经管AI驱动商业模式创新研修班

时长：90分钟 | 2026年1月
```

### 7.2 内容页 - 要点列表

```markdown
---
slide:
  id: "01-03"
  type: content
  layout: bullets
  source_section: "01-capability"

sources:
  - url: "https://www.idc.com/..."
    title: "IDC AI Spending Report 2025"
    date: "2025-01"
    type: report
---

# AI变革的四条路径

- **效率革命**：文档/代码/营销自动化 `成本-40%`{.metric}
- **创新加速**：产品设计/材料研发迭代周期缩短
- **决策升级**：战略洞察/智能决策支持
- **模式重构**：AI原生产品/新商业模式

---notes---

重点强调第一条和第四条。
第一条是大部分企业的起点，第四条是终极目标。
```

### 7.3 案例页 - 三列卡片

```markdown
---
slide:
  id: "02-04"
  type: case-study
  layout: three-cards
  source_section: "02-cases-manufacturing"

cases:
  - company: "美的集团"
    industry: "制造业"
    application: "全流程智能化"
    metrics:
      - label: "效率提升"
        value: "+30%"
  - company: "隆基绿能"
    industry: "新能源"
    application: "AI质检"
    metrics:
      - label: "良品率"
        value: "99.2%"
  - company: "宁德时代"
    industry: "电池"
    application: "产线优化"
    metrics:
      - label: "产能提升"
        value: "+25%"
---

# 制造业AI应用标杆

::: card
### 美的集团
全流程智能化改造，覆盖研发、生产、供应链

`效率提升 30%`{.metric}
:::

::: card
### 隆基绿能
AI视觉质检系统替代人工巡检

`良品率 99.2%`{.metric}
:::

::: card
### 宁德时代
智能产线调度与工艺优化

`产能提升 25%`{.metric}
:::
```

### 7.4 引用页

```markdown
---
slide:
  id: "04-05"
  type: quote
  layout: quote
---

> 未来十年，最稀缺的不是AI技术，而是敢于把核心业务交给AI去重构的企业家勇气和组织能力

— 课程核心观点

---notes---

这是全课的核心金句，放慢语速，让学员记住。
```

### 7.5 表格页

```markdown
---
slide:
  id: "03-02"
  type: content
  layout: table
  source_section: "03-framework"
---

# 企业AI落地三阶段框架

| 阶段 | 时长 | 目标 | 关键行动 |
|------|------|------|----------|
| 快赢期 | 0-6月 | 建立信心 | 选2-3个场景试点 |
| 价值放大期 | 6-18月 | 规模复制 | 建立AI中台 |
| 模式重构期 | 18月+ | 战略升级 | 业务流程再造 |

---notes---

每个阶段的时间是弹性的，取决于企业规模和行业特点。
```

---

## 8. 验证规则

### 8.1 必填字段

- `slide.id` - 必须唯一
- `slide.type` - 必须是有效枚举值
- 至少包含一级标题 `# `

### 8.2 格式检查

- Frontmatter 必须是有效 YAML
- `:::` 块必须正确闭合
- 表格必须有表头

### 8.3 建议性检查

- `case-study` 类型建议包含 `cases` 结构化数据
- 包含数据的页面建议声明 `sources`
- 演讲者备注建议包含时长提示

---

## 9. 与其他规范的关系

```
skeleton.yaml          slide-md files           pptx output
(结构定义)    ─────►   (内容填充)    ─────►    (最终渲染)
     │                      │                       │
     │                      │                       │
     ▼                      ▼                       ▼
/ppt-outline          /ppt-enrich              /ppt-render
```

- **skeleton.yaml** 定义章节结构和研究需求
- **slide-md** 填充具体内容，每页一个文件
- **ppt-render** 读取 slide-md 生成最终 PPTX

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-12 | 初版 |

---

## 11. 相关文档

- [skeleton-spec.md](./skeleton-spec.md) - Skeleton YAML 规范
- [style-system-spec.md](./style-system-spec.md) - 样式系统规范
