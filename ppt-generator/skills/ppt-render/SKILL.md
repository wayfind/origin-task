---
name: ppt-render
description: |
  PPT renderer - Convert slide-md files to professional PPTX.
  Use when: (1) User has slide-md files and needs PPTX output, (2) User wants to render presentation with specific theme, (3) User needs final PowerPoint file.
  Triggers: "渲染PPT", "render PPTX", "生成幻灯片", "slide to pptx", "导出PPT"
---

# /ppt-render

> 从 Slide Markdown 文件渲染生成 PPTX 演示文稿

---

## 🎨 渲染能力概览

> **重要**: 此渲染器支持丰富的可视化元素，请充分利用！

| 能力 | 语法 | 效果 |
|------|------|------|
| **图表渲染** | ` ```mermaid ` / `::: chart` | Mermaid 转 PNG 嵌入 |
| **卡片布局** | `::: card` | 三列并排卡片 |
| **双列布局** | `::: left` / `::: right` | 左右对比 |
| **引用样式** | `> 文字\n> — 来源` | 突出显示引用 |
| **数据高亮** | `` `+45%`{.metric} `` | 数值醒目标注 |
| **表格** | Markdown 表格 | 整齐的数据呈现 |

---

## 概述

`/ppt-render` 是 PPT 生成流水线的最终环节，负责将结构化的 Slide Markdown 文件转换为专业的 PPTX 文件。它是一个**纯渲染器**，不负责内容生成或研究——只专注于高质量的视觉输出。

## 定位

```
/ppt-outline → /ppt-enrich → /ppt-render
                                   ↑
                              你在这里
```

| 职责 | 说明 |
|------|------|
| ✅ 做 | 解析 slide-md、应用样式、生成 PPTX |
| ❌ 不做 | 生成内容、调研数据、修改骨架结构 |

## 用法

### 基本用法

```bash
/ppt-render slides/              # 渲染目录下所有 .slide.md
/ppt-render slides/ --theme corporate-light
/ppt-render slides/ -o output.pptx
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `<input>` | slide-md 文件或目录 | 必填 |
| `--theme`, `-t` | 主题名称 | `corporate-light` |
| `--output`, `-o` | 输出 PPTX 路径 | `output.pptx` |
| `--validate` | 仅验证，不生成 | `false` |
| `--verbose`, `-v` | 详细输出 | `false` |

### 示例

```bash
# 渲染单个文件
/ppt-render 01-intro.slide.md -o intro.pptx

# 渲染整个目录，使用 Nano Banana Pro 主题
/ppt-render ./slides/ --theme nano-banana-pro -o presentation.pptx

# 先验证再渲染
/ppt-render ./slides/ --validate && /ppt-render ./slides/ -o final.pptx
```

## 输入格式

### Slide Markdown (.slide.md)

每个 `.slide.md` 文件代表一页幻灯片：

```markdown
---
slide:
  id: "01-03"
  type: content
  layout: bullets
---

# AI变革的四条路径

- **效率革命**：文档/代码/营销自动化
- **创新加速**：产品设计/材料研发
- **决策升级**：战略洞察/智能决策
- **模式重构**：AI原生产品/新商业模式

---notes---

重点强调第一条和第四条。
```

详细规范见：[slide-md-spec.md](../ppt-specs/slide-md-spec.md)

### 文件组织

```
slides/
├── 00-cover.slide.md
├── 01-01-section.slide.md
├── 01-02-content.slide.md
├── 01-03-cases.slide.md
└── ...
```

文件按字母序排序后依次渲染。

## 输出

- **PPTX 文件**：Microsoft PowerPoint 格式，16:9 宽屏
- **演讲者备注**：从 `---notes---` 部分提取
- **元数据**：标题、作者、创建时间

## 支持的主题

| 主题 | 说明 | 背景 |
|------|------|------|
| `corporate-light` | 企业商务风格 | 白色 |
| `nano-banana-pro` | 科技创意风格 | 深蓝 |

自定义主题：将 YAML 文件放入 `themes/custom/` 目录。

## 支持的布局

| 布局 | 说明 | 适用类型 |
|------|------|----------|
| `title-only` | 仅标题 | cover, section |
| `bullets` | 要点列表 | content |
| `two-column` | 双列 | content |
| `three-cards` | 三列卡片 | case-study |
| `table` | 表格 | content |
| `quote` | 引用 | quote |
| `chart` | 图表（Mermaid） | content, framework |

## 内容语法

### 基础元素

```markdown
# 主标题
## 副标题

- 普通列表项
- **加粗项**
- 带数据项 `+30%`

> 引用文字
> — 来源
```

### 双列布局

```markdown
::: left
### 左侧
- 要点1
- 要点2
:::

::: right
### 右侧
- 要点A
- 要点B
:::
```

### 卡片组

```markdown
::: card
### 卡片标题
描述文字
`关键指标`{.metric}
:::
```

### 数据高亮

```markdown
增长 `+45%`{.metric .positive}
下降 `-20%`{.metric .negative}
```

### 图表（Mermaid）

支持两种方式嵌入图表：

#### 方式一：Mermaid 代码块

```markdown
---
slide:
  layout: chart
---
# 流程图

```mermaid
flowchart LR
    A[开始] --> B[处理] --> C[结束]
```
```

#### 方式二：预定义图表模板

```markdown
---
slide:
  layout: chart
---
# AI实施三阶段

::: chart
template: process-flow
title: 实施路线图
steps:
  - 快赢期 | 0-6月
  - 价值放大 | 6-18月
  - 全面转型 | 18月+
:::
```

#### 可用图表模板

| 模板 | 参数 | 适用场景 |
|------|------|----------|
| `process-flow` | `steps: [{label, detail}]` | 流程、阶段 |
| `comparison` | `left: {title, items}, right: {...}` | 对比 |
| `timeline` | `events: [{year, title}]` | 时间线 |
| `pyramid` | `levels: [{label}]` | 层级 |
| `circle-group` | `center, items: [string]` | 核心+扩展 |

## 错误处理

| 错误类型 | 行为 |
|----------|------|
| YAML 解析失败 | 跳过该文件，警告 |
| 缺少必填字段 | 跳过该文件，警告 |
| 未知布局 | 回退到 `bullets` |
| 未知主题 | 回退到 `corporate-light` |

## 文件结构

```
.claude/skills/ppt-render/
├── SKILL.md                    # 本文档
├── scripts/
│   ├── render.js               # 主渲染脚本
│   ├── slide-parser.js         # Slide-MD 解析器
│   ├── pptx-renderer.js        # PPTX 渲染引擎
│   ├── chart-renderer.js       # 🆕 Mermaid 图表渲染
│   └── theme-loader.js         # 主题加载器
└── themes/
    ├── corporate-light.yaml    # 预置主题
    ├── nano-banana-pro.yaml
    └── custom/                 # 自定义主题
```

## 依赖

- Node.js >= 16
- pptxgenjs >= 3.12
- yaml >= 2.0
- @mermaid-js/mermaid-cli (可选，图表渲染需要)

安装依赖：

```bash
cd .claude/skills/ppt-render && npm install

# 图表渲染需要安装 mermaid-cli
npm install -g @mermaid-js/mermaid-cli
```

## API（编程使用）

```javascript
const { PPTRenderer } = require('./scripts/render');

const renderer = new PPTRenderer({
    theme: 'corporate-light',
    verbose: true
});

// 渲染目录
await renderer.renderDirectory('./slides/', 'output.pptx');

// 渲染单个文件
await renderer.renderFile('./cover.slide.md', 'cover.pptx');
```

## 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `/ppt-outline` | 上游：生成 skeleton.yaml |
| `/ppt-enrich` | 上游：生成 slide-md 文件 |
| `/ppt` | 编排器：协调整个流程 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.1.0 | 2026-01-12 | 添加 Mermaid 图表支持和预定义模板 |
| 1.0.0 | 2026-01-12 | 初版 |

## 相关文档

- [slide-md-spec.md](../ppt-specs/slide-md-spec.md) - Slide Markdown 规范
- [style-system-spec.md](../ppt-specs/style-system-spec.md) - 样式系统规范
