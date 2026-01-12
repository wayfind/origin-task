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

## ⛔ 研究工具选择规则（必读）

> **STOP! 在进行任何数据研究之前，必须阅读此规则。**

### 工具优先级

| 优先级 | 工具 | 何时使用 | 能力 |
|--------|------|----------|------|
| 🥇 **1st** | `openai-deep-research` | **需要深度数据时必须使用** | 浏览器自动化、多轮搜索、登录网站、结构化输出 |
| 🥈 2nd | `WebFetch` | 已知具体 URL | 单页面抓取 |
| 🥉 3rd | `WebSearch` | 仅快速验证事实 | 简单搜索，结果浅层 |

### ⚠️ 强制规则

**当 skeleton.yaml 中存在 `research_needs` 时：**

```
❌ 禁止: 直接使用 WebSearch 获取数据
✅ 必须: 调用 openai-deep-research skill 执行深度研究
```

**调用方式：**

```python
# 方式1: 通过 Task agent 调用 deep-research
Task(
    subagent_type="general-purpose",
    prompt="使用 openai-deep-research skill 研究: {query}"
)

# 方式2: 直接调用研究脚本
python ppt-enrich/scripts/research/deep_research.py \
    --query "{query}" \
    --output research_results.json
```

### 为什么不用 WebSearch？

| WebSearch | deep-research |
|-----------|---------------|
| 返回 10 条摘要 | 返回完整分析报告 |
| 无法进入付费墙 | 可用浏览器登录 |
| 单轮搜索 | 多轮迭代研究 |
| 无来源验证 | 结构化引用来源 |

**记住：PPT 需要的是深度洞察，不是搜索结果拼凑！**

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
