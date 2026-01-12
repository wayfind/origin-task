# Skeleton YAML Specification v1.0

> PPT 骨架格式规范 - `/ppt-outline` 的输出，`/ppt-enrich` 的输入

---

## 1. 概述

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **人类可读** | 非技术用户可以理解和编辑 |
| **机器可解析** | 严格的 schema 验证 |
| **渐进式细化** | 支持从粗到细逐步完善 |
| **研究驱动** | 明确标记需要调研的内容 |

### 1.2 文件命名

```
{project}/skeleton.yaml       # 主骨架文件
{project}/skeleton.local.yaml # 本地覆盖（可选，gitignore）
```

---

## 2. 完整 Schema

```yaml
# skeleton.yaml - PPT骨架定义文件
# Version: 1.0

#═══════════════════════════════════════════════════════════════
# 元数据区域
#═══════════════════════════════════════════════════════════════
meta:
  # 必填字段
  title: string              # PPT主标题
  version: string            # 骨架版本，格式 "1.0"

  # 可选字段
  subtitle: string           # 副标题
  author: string             # 作者/讲师
  date: string               # 日期，格式 "YYYY-MM" 或 "YYYY-MM-DD"
  language: string           # 语言代码，默认 "zh-CN"

  # 生成配置
  generated_by: string       # 生成工具标识
  generated_at: string       # ISO 8601 时间戳

#═══════════════════════════════════════════════════════════════
# 受众定义
#═══════════════════════════════════════════════════════════════
audience:
  # 受众类型（枚举）
  type: enum                 # executives | managers | professionals | general

  # 受众规模
  size: integer              # 预计人数

  # 行业分布（可选）
  industries:
    - name: string           # 行业名称
      percentage: number     # 占比 0-100
      companies: [string]    # 代表企业（可选）

  # 痛点/关注点
  pain_points:
    - string                 # 受众关心的问题

  # 知识水平
  knowledge_level: enum      # novice | intermediate | expert

#═══════════════════════════════════════════════════════════════
# 演示配置
#═══════════════════════════════════════════════════════════════
presentation:
  # 时长
  duration: integer          # 总时长（分钟）
  duration_flexible: boolean # 是否可调整，默认 false

  # 场合类型（影响样式选择）
  occasion: enum             # training | pitch | conference | workshop | marketing

  # 样式预设
  style: string              # 样式名称，如 "nano-banana-pro", "corporate-light"

  # 输出格式
  output_formats:
    - enum                   # pptx | html | pdf

#═══════════════════════════════════════════════════════════════
# 内容结构
#═══════════════════════════════════════════════════════════════
structure:
  - # 章节定义
    id: string               # 唯一标识，如 "01-intro", "02-cases"
    title: string            # 章节标题

    # 章节类型
    type: enum               # opening | content | case-study | framework | closing | transition

    # 时长
    duration: integer        # 分钟

    # 内容提示（给内容生成器的指导）
    content_hints:
      - string               # 内容要点提示

    # 预期幻灯片数
    slides_estimate: integer # 预估页数

    # 子章节（可选，支持嵌套）
    subsections:
      - id: string
        title: string
        content_hints: [string]

    # 研究需求（标记需要调研的内容）
    research_needs:
      - type: enum           # case_study | statistics | quote | trend | comparison
        query: string        # 研究查询
        priority: enum       # high | medium | low
        count: integer       # 需要的数量（如：需要3个案例）
        constraints:         # 约束条件
          industry: string   # 行业限制
          region: string     # 地区限制（如：中国企业优先）
          time_range: string # 时间范围（如：2024-2025）
          source_type: string # 来源类型（如：权威报告）

    # 交互设计（可选）
    interactions:
      - type: enum           # poll | question | discussion | exercise
        prompt: string       # 交互提示语
        duration: integer    # 预计时长（秒）

#═══════════════════════════════════════════════════════════════
# 研究任务（可执行的研究指令）
#═══════════════════════════════════════════════════════════════
research_tasks:
  - # 研究任务定义
    id: string               # 唯一标识符，如 "r01", "r02"
    query: string            # 详细的研究提示词（多行支持）
    skill: string            # 使用的 skill: "deep-research" | "websearch"
    required: boolean        # true=必须执行, false=可选
    output_format: string    # 期望的输出格式模板

    # 可选配置
    type: enum               # market_data | news_events | case_study | statistics | comparison | forecast
    timeout: integer         # 超时时间（秒），默认 300
    cache: boolean           # 是否缓存结果，默认 true
    apply_to: [string]       # 应用到哪些章节/幻灯片 ID

#═══════════════════════════════════════════════════════════════
# 全局研究需求（跨章节）- 旧格式，建议使用 research_tasks
#═══════════════════════════════════════════════════════════════
global_research:
  # 贯穿全 PPT 的研究需求
  - type: enum
    query: string
    apply_to: [string]       # 应用到哪些章节 ID，"*" 表示全部

#═══════════════════════════════════════════════════════════════
# 约束与规则
#═══════════════════════════════════════════════════════════════
constraints:
  # 内容约束
  content:
    max_slides: integer      # 最大页数
    max_words_per_slide: integer # 每页最大字数
    require_sources: boolean # 是否必须标注来源

  # 视觉约束
  visual:
    logo_path: string        # Logo文件路径
    color_override: object   # 颜色覆盖
    font_override: object    # 字体覆盖

  # 品牌约束
  brand:
    company_name: string
    tagline: string
    disclaimer: string       # 免责声明

#═══════════════════════════════════════════════════════════════
# 扩展字段（自定义）
#═══════════════════════════════════════════════════════════════
extensions:
  # 任意自定义字段
  custom_field: any
```

---

## 3. 字段详解

### 3.1 章节类型 (structure[].type)

| 类型 | 说明 | 典型内容 | 视觉风格 |
|------|------|----------|----------|
| `opening` | 开场 | 破冰、背景介绍、数据冲击 | 氛围图 + 大字 |
| `content` | 正文 | 概念、理论、方法论 | 标准布局 |
| `case-study` | 案例 | 企业案例、最佳实践 | 三列卡片 |
| `framework` | 框架 | 模型、流程、阶段 | 图表为主 |
| `closing` | 结尾 | 总结、行动清单、Q&A | 简洁有力 |
| `transition` | 过渡 | 章节间转场 | 引用 + 图 |

### 3.2 研究任务 (research_tasks)

> **重要**: `research_tasks` 是可执行的研究指令，AI **必须**按规定流程执行。

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 唯一标识符，用于 slide-md 中引用 |
| `query` | string | ✅ | 详细的研究提示词 |
| `skill` | string | ✅ | 使用的 skill: `deep-research` / `websearch` |
| `required` | boolean | ✅ | `true` 表示必须执行 |
| `output_format` | string | 建议 | 期望的输出格式模板 |
| `type` | enum | 可选 | 任务类型分类 |
| `apply_to` | [string] | 可选 | 关联的章节/幻灯片 ID |

#### 示例

```yaml
research_tasks:
  - id: "r01"
    query: |
      Tesla TSLA stock performance in 2025:
      - Opening price (January 2025)
      - Closing price (December 2025)
      - Year-over-year percentage change
      - Top 3 events that impacted the stock price
    skill: "deep-research"
    required: true
    type: market_data
    output_format: |
      ## 2025年股价表现
      - 年初价格: $XXX.XX
      - 年末价格: $XXX.XX
      - 涨跌幅: +/-XX.X%
      ### 关键事件
      1. [事件描述] (日期)
      2. [事件描述] (日期)
      3. [事件描述] (日期)
      *来源: [数据来源]*
    apply_to: ["02-review"]

  - id: "r02"
    query: "Tesla vs BYD global EV market share comparison 2025"
    skill: "deep-research"
    required: true
    type: comparison
    output_format: |
      | 指标 | Tesla | BYD |
      |------|-------|-----|
      | 全球销量 | XXX万 | XXX万 |
      | 市场份额 | XX% | XX% |
```

#### slide-md 中引用

```markdown
<!-- @RESEARCH: r01 -->
此处将由研究结果自动填充
<!-- @/RESEARCH -->
```

### 3.3 研究需求类型 (research_needs[].type) - 旧格式

> 注意：建议使用新的 `research_tasks` 格式，旧格式仍然支持但不推荐。

| 类型 | 说明 | 输出期望 |
|------|------|----------|
| `case_study` | 企业案例 | 企业名、方案、量化效果、来源 |
| `statistics` | 统计数据 | 指标、数值、来源、时间 |
| `quote` | 权威引用 | 引言、出处、人物 |
| `trend` | 趋势分析 | 趋势描述、数据支撑 |
| `comparison` | 对比分析 | 对比维度、结论 |

### 3.4 场合类型 (presentation.occasion)

| 场合 | 特点 | 样式建议 |
|------|------|----------|
| `training` | 培训 | 留白多、便于笔记 |
| `pitch` | 汇报 | 数据突出、结论清晰 |
| `conference` | 会议演讲 | 视觉冲击、简洁 |
| `workshop` | 工作坊 | 交互多、步骤清晰 |
| `marketing` | 营销 | 视觉优先、品牌强化 |

---

## 4. 示例文件

### 4.1 最小示例

```yaml
meta:
  title: "AI趋势分享"
  version: "1.0"

audience:
  type: professionals
  size: 50

presentation:
  duration: 30
  occasion: conference
  style: nano-banana-pro

structure:
  - id: intro
    title: "开场"
    type: opening
    duration: 5
    content_hints:
      - "AI发展现状"

  - id: main
    title: "核心观点"
    type: content
    duration: 20
    content_hints:
      - "三个关键趋势"
    research_needs:
      - type: statistics
        query: "2024-2025 AI市场规模数据"
        priority: high

  - id: closing
    title: "总结"
    type: closing
    duration: 5
    content_hints:
      - "行动建议"
```

### 4.2 完整示例

```yaml
meta:
  title: "生成式AI驱动的产业应用与企业转型"
  subtitle: "清华经管AI驱动商业模式创新研修班"
  version: "1.0"
  author: "讲师"
  date: "2026-01"
  language: "zh-CN"

audience:
  type: executives
  size: 30
  industries:
    - name: "新能源/清洁能源"
      percentage: 23
      companies: ["日出东方", "太阳雨", "四季沐歌"]
    - name: "工业材料/制造"
      percentage: 17
      companies: ["旭光聚合物", "万盾门业"]
    - name: "金融/投资/保险"
      percentage: 13
      companies: ["加倍投资", "明亚保险"]
  pain_points:
    - "如何评估AI投资回报"
    - "如何选择适合的落地场景"
    - "如何避免技术投入打水漂"
  knowledge_level: intermediate

presentation:
  duration: 90
  duration_flexible: true
  occasion: training
  style: corporate-light
  output_formats:
    - pptx
    - pdf

structure:
  - id: "00-opening"
    title: "AI大势判断与破冰互动"
    type: opening
    duration: 12
    slides_estimate: 6
    content_hints:
      - "举手投票破冰"
      - "三组震撼数据"
      - "核心认知校准"
    interactions:
      - type: poll
        prompt: "过去6个月，您是否付费使用过AI工具？"
        duration: 60
      - type: poll
        prompt: "您认为未来3年AI投入会增加多少倍？"
        duration: 60

  - id: "01-capability"
    title: "生成式AI核心能力与产业变革逻辑"
    type: framework
    duration: 18
    slides_estimate: 10
    content_hints:
      - "四象限变革路径"
      - "效率革命 vs 模式重构"
    subsections:
      - id: "01-1-efficiency"
        title: "效率革命路径"
        content_hints:
          - "文档/代码/营销自动化"
      - id: "01-2-innovation"
        title: "创新加速路径"
        content_hints:
          - "产品设计/材料研发"
    research_needs:
      - type: case_study
        query: "AI效率革命典型案例"
        priority: high
        count: 2
        constraints:
          region: "中国企业优先"
          time_range: "2024-2025"

  - id: "02-cases-manufacturing"
    title: "制造业与新能源案例拆解"
    type: case-study
    duration: 18
    slides_estimate: 12
    content_hints:
      - "智能制造案例"
      - "新能源AI应用"
    research_needs:
      - type: case_study
        query: "制造业AI应用案例，要求有ROI数据"
        priority: high
        count: 3
        constraints:
          industry: "制造业"
          source_type: "权威报告或企业公告"
      - type: statistics
        query: "制造业AI渗透率数据"
        priority: medium

  - id: "03-framework"
    title: "企业AI战略落地框架"
    type: framework
    duration: 18
    slides_estimate: 10
    content_hints:
      - "三阶段落地框架"
      - "快赢期 → 价值放大期 → 模式重构期"
    research_needs:
      - type: case_study
        query: "企业AI转型成功/失败对比案例"
        priority: medium
        count: 2

  - id: "04-closing"
    title: "风险提醒与行动清单"
    type: closing
    duration: 7
    slides_estimate: 5
    content_hints:
      - "五大常见误判"
      - "行动清单一页纸"
      - "结束金句"

global_research:
  - type: statistics
    query: "2024-2025 中国企业AI采用率权威数据"
    apply_to: ["00-opening", "01-capability"]

constraints:
  content:
    max_slides: 60
    require_sources: true
  brand:
    company_name: "清华经管学院"
    disclaimer: "本课程内容仅供学习交流"
```

---

## 5. 验证规则

### 5.1 必填字段

- `meta.title`
- `meta.version`
- `audience.type`
- `presentation.duration`
- `presentation.style`
- `structure` (至少1个章节)
- `structure[].id` (每个章节)
- `structure[].title` (每个章节)
- `structure[].type` (每个章节)

### 5.2 一致性检查

- 所有 `structure[].id` 必须唯一
- `global_research[].apply_to` 中的 ID 必须存在于 `structure`
- `structure[].duration` 总和应接近 `presentation.duration`
- `research_needs[].count` 必须 > 0

### 5.3 建议性检查（警告）

- 每个 `content` 类型章节应有 `research_needs`
- `slides_estimate` 总和不应超过 `constraints.content.max_slides`
- 培训场合建议包含 `interactions`

---

## 6. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-12 | 初版 |

---

## 7. 相关文档

- [slide-md-spec.md](./slide-md-spec.md) - Slide Markdown 规范
- [style-system-spec.md](./style-system-spec.md) - 样式系统规范
