---
name: ppt
description: |
  PPT generation orchestrator - One-click professional PPTX creation.
  Use when: (1) User wants to generate complete PPT from documents, (2) User provides natural language description for presentation, (3) User needs to convert content to slides.
  Triggers: "生成PPT", "create presentation", "make slides", "PPT", "演示文稿", "幻灯片"
---

# /ppt

> 一键生成专业 PPT 的编排器

---

## 🚀 首次使用初始化（必读）

> **在生成 PPT 之前，必须先确认用户的账号和工具可用性。**

### Step 1: 确认账号能力

**必须使用 AskUserQuestion 工具询问用户：**

```
问题1: 您是否有 ChatGPT Plus/Pro 账号？
  - 是 → 可使用 deep-research 进行深度研究
  - 否 → 仅使用 WebSearch（研究质量较低）

问题2: 您是否有 Gemini API Key（Pro 或以上）？
  - 是 → 可使用 nano-banana-image 生成配图
  - 否 → 跳过配图生成
```

### Step 2: 安装依赖 Skill

根据用户确认，安装对应的 skill：

```bash
# 如果有 ChatGPT Plus，安装 deep-research
# 相对路径: ../../../openai-deep-research (同一个 git 库)
SKILL_BASE="/home/david/prj/origin-task"

# deep-research skill
if [ ! -d "$SKILL_BASE/openai-deep-research" ]; then
    echo "deep-research skill 已在 $SKILL_BASE/openai-deep-research"
fi

# nano-banana-image skill
if [ ! -d "$SKILL_BASE/nano-banana-image" ]; then
    echo "nano-banana-image skill 已在 $SKILL_BASE/nano-banana-image"
fi
```

### Step 3: 配置认证

**ChatGPT Plus 用户：**
```
提示: 请在浏览器中登录 ChatGPT (chat.openai.com)
deep-research 将使用 Playwright 自动化访问
```

**Gemini API 用户：**
```
提示: 请设置环境变量 GEMINI_API_KEY
export GEMINI_API_KEY="your-api-key-here"
```

### Step 4: 记录用户配置

将确认结果保存到 `.pptrc.yaml`：

```yaml
# .pptrc.yaml (自动生成)
capabilities:
  deep_research: true    # 有 ChatGPT Plus
  image_generation: true # 有 Gemini API

auth:
  chatgpt_logged_in: true
  gemini_api_key_set: true
```

### ⚠️ 初始化检查清单

**每次执行 /ppt 时，检查：**

1. [ ] 是否存在 `.pptrc.yaml`？
   - 否 → 执行初始化流程
   - 是 → 读取已保存的配置

2. [ ] deep-research 是否可用？
   - 检查: `python -c "from research.deep_research import DeepResearch"`

3. [ ] nano-banana-image 是否可用？
   - 检查: skill 目录是否存在 + GEMINI_API_KEY 是否设置

**如果任何检查失败，提示用户重新配置！**

---

## 📋 Research Directive 语法（必读）

> **这是 PPT 生成的核心机制：显式声明研究任务，强制执行获取结果。**

### 语法定义

#### 1. skeleton.yaml 中声明研究任务

```yaml
# 在 skeleton.yaml 顶层或章节内声明
research_tasks:
  - id: "r01"                    # 唯一标识符
    query: |                      # 研究提示词（详细描述）
      Tesla TSLA stock performance in 2025:
      - Opening and closing prices
      - Year-over-year change percentage
      - Major events affecting stock price
      - Analyst ratings summary
    skill: "deep-research"        # 使用的 skill
    required: true                # true=必须执行, false=可选
    output_format: |              # 期望的输出格式
      ## 2025年股价表现
      - 年初价格: $XXX
      - 年末价格: $XXX
      - 涨跌幅: +/-XX%
      ### 关键事件
      1. [事件1]
      2. [事件2]
```

#### 2. slide-md 中标记填充位置

```markdown
---
slide:
  id: "02-02"
  layout: two-column
---

# 2025年股价回顾

::: left
<!-- @RESEARCH: r01 -->
此区域将由研究结果 r01 填充
<!-- @/RESEARCH -->
:::

::: right
<!-- @RESEARCH: r02 -->
此区域将由研究结果 r02 填充
<!-- @/RESEARCH -->
:::
```

### ⚠️ AI 执行协议（强制）

**当看到 `research_tasks` 或 `<!-- @RESEARCH: -->` 标记时，必须执行以下步骤：**

#### Step 1: 显式输出研究任务

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 RESEARCH TASK [r01]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Skill: deep-research
Query:
  Tesla TSLA stock performance in 2025:
  - Opening and closing prices
  - Year-over-year change percentage
  ...

Expected Output Format:
  ## 2025年股价表现
  - 年初价格: $XXX
  ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

#### Step 2: 调用 Skill 执行研究

```python
# 必须使用 Task 工具调用 deep-research
Task(
    subagent_type="general-purpose",
    prompt="""
    执行研究任务 [r01]:

    使用 openai-deep-research skill 研究以下内容：
    {query}

    输出格式要求：
    {output_format}

    要求：
    1. 数据必须有来源引用
    2. 数据时效性：最近6个月
    3. 包含具体数字，不要模糊表述
    """,
    description="Research: r01"
)
```

#### Step 3: 🆕 保存研究结果到文件（P0 强制）

> **⚠️ 关键改动**: 研究结果必须持久化到文件，渲染器会验证！

```bash
# 目录结构
output/project-name/
├── skeleton.yaml
├── research_results/        # 🆕 必须存在
│   ├── r01.md              # 研究结果内容
│   ├── r01.meta.json       # 元数据（可选但推荐）
│   ├── r02.md
│   └── ...
└── slides/
    └── *.slide.md
```

**保存 research_results/{task_id}.md:**

```markdown
# Research Result: r01
Generated: 2026-01-12T10:30:00Z
Skill: deep-research

---

## 2025年股价表现
- 年初价格: $248.42
- 年末价格: $445.03
- 涨跌幅: +79.1%

### 关键事件
1. Q1: FSD V12 发布，股价上涨 15%
2. Q3: Robotaxi 发布会，股价创新高
3. Q4: 马斯克政治参与引发波动

---

*来源: Yahoo Finance, Reuters*
*研究时间: 2026-01-12*
```

**保存 research_results/{task_id}.meta.json (可选):**

```json
{
  "task_id": "r01",
  "skill": "deep-research",
  "query_hash": "abc123...",
  "executed_at": "2026-01-12T10:30:00Z",
  "duration_seconds": 45,
  "source_count": 5,
  "content_length": 1234
}
```

#### Step 4: 填充结果到 slide-md

从 `research_results/{task_id}.md` 读取内容填充：

```markdown
<!-- @RESEARCH: r01 -->
## 2025年股价表现
- 年初价格: $248.42
- 年末价格: $445.03
- 涨跌幅: +79.1%

### 关键事件
1. Q1: FSD V12 发布，股价上涨 15%
2. Q3: Robotaxi 发布会，股价创新高
3. Q4: 马斯克政治参与引发波动

*来源: Yahoo Finance, Reuters*
<!-- @/RESEARCH -->
```

### 🚫 渲染阻断机制（P0）

> **render.js 会在渲染前验证 research_results/ 目录！**

```
如果 skeleton.yaml 定义了 research_tasks:
  但 research_results/ 目录不存在
  或 必需任务 (required: true) 没有对应的 .md 文件

则渲染器拒绝执行并输出：

╔════════════════════════════════════════════════════════════╗
║          ARTIFACT VALIDATION FAILED                        ║
╚════════════════════════════════════════════════════════════╝

🚫 RENDER BLOCKED: research_results/ 目录不存在

skeleton.yaml 定义了 5 个必需研究任务：
  - [r01] Tesla TSLA stock performance in 2025...
  - [r02] Tesla 2026 bullish catalysts...
  ...

解决方法：
  1. 使用 /ppt-enrich 执行研究任务
  2. 确保每个任务都调用 deep-research skill
  3. 将结果保存为 research_results/{task_id}.md
```

**绕过方法（不推荐）：**
```bash
node render.js ./slides/ --skip-artifact-check
```

### 研究任务类型

| 类型 | 适用场景 | 示例 query |
|------|----------|-----------|
| `market_data` | 股价、财务数据 | "TSLA stock price 2025" |
| `news_events` | 新闻事件分析 | "Tesla major news 2025" |
| `case_study` | 案例研究 | "AI manufacturing cases China 2025" |
| `statistics` | 统计数据 | "Global EV market share 2025" |
| `comparison` | 对比分析 | "Tesla vs BYD sales comparison" |
| `forecast` | 预测分析 | "Tesla stock price forecast 2026" |

### 工具优先级

| 优先级 | 工具 | 使用条件 |
|--------|------|----------|
| 🥇 **1st** | `deep-research` | `required: true` 或 capabilities.deep_research=true |
| 🥈 2nd | `WebSearch` | 仅当 deep-research 不可用时的 fallback |

### ❌ 禁止行为

```
❌ 看到 research_tasks 却不执行研究
❌ 使用 WebSearch 代替 deep-research（当可用时）
❌ 不显式输出研究任务就直接填充内容
❌ 填充的内容没有来源引用
❌ 使用过时数据（超过6个月）
```

### ✅ 正确流程示例

```
1. 读取 skeleton.yaml
2. 发现 research_tasks: [r01, r02, r03]
3. 输出: "🔍 RESEARCH TASK [r01]..."
4. 调用: Task(subagent_type="general-purpose", prompt="使用 deep-research...")
5. 等待结果
6. 输出: "🔍 RESEARCH TASK [r02]..."
7. 调用: Task(...)
8. ...
9. 生成 slide-md，填充 <!-- @RESEARCH: rXX --> 标记
```

---

## 概述

`/ppt` 是 PPT 生成的主入口命令，它编排 `outline → enrich → render` 三阶段流程，将用户的原始需求转化为专业的 PPTX 文件。

---

## 🎨 设计工具箱 (Design Toolkit)

> **重要**: 生成 PPT 时，请充分利用以下丰富的设计工具，确保输出美观大方、专业精致。

### 可用布局类型

| 布局 | 类型 | 适用场景 | 效果 |
|------|------|----------|------|
| `title-only` | 全屏标题 | 封面、章节页、结尾 | 视觉冲击力强 |
| `bullets` | 要点列表 | 通用内容、3-5 个要点 | 清晰易读 |
| `two-column` | 双列对比 | 对比内容、左右分列 | 结构对称 |
| `three-cards` | 三列卡片 | 案例展示、特性对比 | 并列展示 |
| `table` | 表格 | 数据密集、多维比较 | 信息整齐 |
| `quote` | 引用 | 名人金句、重点强调 | 突出重点 |
| `chart` | 图表 | 流程、时间线、层级 | 可视化强 |

### 可用图表模板

使用 `::: chart` 块或 ` ```mermaid ` 代码块：

| 模板 | 语法示例 | 适用内容 |
|------|----------|----------|
| **流程图** | `template: process-flow` | 步骤、阶段、流程 |
| **对比图** | `template: comparison` | 传统 vs 现代、优劣势 |
| **时间线** | `template: timeline` | 历史、规划、路线图 |
| **金字塔** | `template: pyramid` | 层级、架构、分类 |
| **自定义** | ` ```mermaid ` 代码块 | 复杂自定义图表 |

**图表语法示例:**

```markdown
::: chart
template: process-flow
title: AI实施三阶段
steps:
  - 快赢期 | 0-6月
  - 价值放大 | 6-18月
  - 全面转型 | 18月+
:::
```

### 装饰图片位置

使用 nano-banana-image 生成同色系装饰图：

| 位置 | 适用页面 | 效果 |
|------|----------|------|
| `cover` | 封面页 | 全屏主视觉，增强冲击力 |
| `section` | 章节标题页 | 背景装饰，突出主题 |
| `side` | 内容页 | 侧边装饰，增加美感 |
| `ending` | 结尾页 | 感谢装饰，温馨收尾 |

### 设计决策原则

1. **数据 → 图表**: 有数字就可视化，不堆砌数字
2. **对比 → 双列/图表**: 对比内容必须清晰区分
3. **流程 → 流程图**: 步骤内容用流程图展示
4. **案例 → 卡片**: 多案例并列用卡片布局
5. **引用 → Quote**: 金句单独突出展示
6. **重要页 → 配图**: 封面、章节页配装饰图

### 主题选择

| 主题 | 风格 | 适用场景 |
|------|------|----------|
| `corporate-light` | 浅色正式 | 企业汇报、正式场合 |
| `nano-banana-pro` | 深色科技 | 创意提案、科技演讲 |

---

## 架构

```
                    /ppt（编排器）
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   /ppt-outline    /ppt-enrich      /ppt-render
   (骨架生成)      (内容填充)       (PPTX渲染)
        │                │                │
        ▼                ▼                ▼
   skeleton.yaml    slide-md/*.md     output.pptx
```

## 用法

### 快速开始

```bash
/ppt                              # 交互式生成
/ppt ./docs/                      # 从文档目录生成
/ppt "做一个AI培训的PPT，30分钟"    # 从自然语言生成
```

### 完整参数

```bash
/ppt [input] [options]

Arguments:
  [input]               输入源（目录/文件/描述）

Options:
  -o, --output <path>   输出 PPTX 路径
  -t, --theme <name>    主题 (corporate-light | nano-banana-pro)
  -d, --duration <min>  目标时长（分钟）
  --no-research         跳过研究步骤
  --step <stage>        只执行到指定阶段 (outline | enrich | render)
  --resume <state>      从断点恢复
  -v, --verbose         详细输出
```

## 工作模式

### 模式 1: 交互式（默认）

```bash
/ppt

📋 PPT 生成向导
━━━━━━━━━━━━━━━

检测到上下文:
  - docs/ 目录: 7 个文档, 35,604 字
  - 已有骨架: skeleton.yaml

请选择操作:
  1. 从现有文档生成 PPT
  2. 从骨架继续（跳过 outline）
  3. 重新开始

选择 [1]: _
```

### 模式 2: 批处理

```bash
# 从文档目录一键生成
/ppt ./docs/ -o presentation.pptx

# 指定主题和时长
/ppt ./docs/ --theme nano-banana-pro -d 60 -o dark-theme.pptx
```

### 模式 3: 自然语言

```bash
/ppt "给企业高管做一个AI转型的培训，90分钟，需要案例"

# 系统会:
# 1. 解析意图 → 识别为 training, executives, 90min
# 2. 生成骨架 → skeleton.yaml
# 3. 执行研究 → 补充案例和数据
# 4. 生成内容 → slide-md 文件
# 5. 渲染输出 → presentation.pptx
```

## 流程阶段

### Stage 1: Outline（骨架生成）

```
Input:  上下文 / 自然语言描述
Output: skeleton.yaml
Tool:   /ppt-outline
```

生成结构化骨架，定义章节、时长、研究需求。

### Stage 2: Enrich（内容填充）

```
Input:  skeleton.yaml + 上下文
Output: slides/*.slide.md
Tool:   /ppt-enrich
```

检测内容空缺，执行研究，生成每页幻灯片的 Markdown。

### Stage 3: Render（渲染输出）

```
Input:  slides/*.slide.md
Output: presentation.pptx
Tool:   /ppt-render
```

将 slide-md 文件渲染为最终 PPTX。

## 断点续传

支持从任意阶段恢复：

```bash
# 保存状态
/ppt ./docs/ --step enrich
# → 生成 .ppt-state.json

# 从断点恢复
/ppt --resume .ppt-state.json
# → 从 render 阶段继续
```

状态文件结构：
```json
{
  "stage": "enrich",
  "skeleton_path": "skeleton.yaml",
  "slides_dir": "slides/",
  "options": {...},
  "timestamp": "2026-01-12T10:00:00Z"
}
```

## 错误恢复

| 错误类型 | 处理策略 |
|----------|----------|
| 骨架验证失败 | 提示修复，不继续 |
| 研究超时 | 跳过该项，继续生成 |
| 渲染失败 | 保存 slide-md，提示手动渲染 |

## 输出

### 默认输出结构

```
project/
├── skeleton.yaml           # 骨架文件
├── slides/                 # slide-md 文件
│   ├── 00-01-cover.slide.md
│   ├── 01-01-section.slide.md
│   └── ...
├── presentation.pptx       # 最终 PPT
└── .ppt-state.json        # 状态文件（可选）
```

### 清理选项

```bash
/ppt ./docs/ --clean        # 生成后删除中间文件
```

## 配置

### 项目配置 (.pptrc.yaml)

```yaml
# .pptrc.yaml
defaults:
  theme: corporate-light
  duration: 30
  audience: professionals

research:
  mode: browser           # browser | api | mock
  cache: true
  timeout: 300            # 秒

output:
  dir: ./output
  clean_intermediate: false
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `OPENAI_API_KEY` | OpenAI API 密钥（api 研究模式） |
| `PPT_THEME` | 默认主题 |
| `PPT_OUTPUT_DIR` | 默认输出目录 |

## 文件结构

```
.claude/skills/ppt/
├── SKILL.md                # 本文档
├── scripts/
│   ├── orchestrator.py     # 主编排脚本
│   ├── intent_parser.py    # 意图解析器
│   └── state_manager.py    # 状态管理器
└── templates/
    └── .pptrc.yaml         # 配置模板
```

## 依赖的 Skills

| Skill | 用途 |
|-------|------|
| `/ppt-outline` | 生成骨架 |
| `/ppt-enrich` | 内容填充 |
| `/ppt-render` | PPTX 渲染 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-01-12 | 初版 |

## 快速示例

```bash
# 最简单的用法
/ppt ./docs/ -o my-presentation.pptx

# 完整流程
/ppt ./docs/ \
  --theme corporate-light \
  --duration 60 \
  -o presentation.pptx \
  -v
```
