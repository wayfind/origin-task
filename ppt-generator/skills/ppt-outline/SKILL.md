# /ppt-outline

> 从上下文生成 PPT 骨架结构（skeleton.yaml）

## 概述

`/ppt-outline` 是 PPT 生成流水线的入口，负责分析输入上下文（文档、对话、需求描述），通过对话式交互澄清需求，生成结构化的 PPT 骨架文件。它是一个**结构生成器**，不负责内容填充——只专注于定义"讲什么"和"怎么组织"。

## 定位

```
/ppt-outline → /ppt-enrich → /ppt-render
     ↑
 你在这里
```

| 职责 | 说明 |
|------|------|
| ✅ 做 | 扫描上下文、澄清需求、生成骨架、标记研究需求 |
| ❌ 不做 | 内容填充、调研执行、幻灯片渲染 |

## 用法

### 交互模式（推荐）

```bash
/ppt-outline                    # 交互式生成骨架
/ppt-outline --context ./docs/  # 指定上下文目录
```

### 批处理模式

```bash
/ppt-outline --batch brief.yaml -o skeleton.yaml
```

### 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--context`, `-c` | 上下文目录或文件 | 当前目录 |
| `--output`, `-o` | 输出 skeleton.yaml 路径 | `skeleton.yaml` |
| `--batch` | 批处理模式，从 brief 文件生成 | - |
| `--style` | 预设样式 | `corporate-light` |
| `--duration` | 目标时长（分钟） | 30 |
| `--audience` | 受众类型 | `professionals` |
| `--verbose`, `-v` | 详细输出 | `false` |

## 工作流程

### Step 1: 上下文扫描

自动扫描指定目录，识别：
- Markdown 文档 (`.md`)
- 元数据文件 (`_meta.yaml`)
- 已有骨架 (`skeleton.yaml`)
- 研究结果 (`*-ds/` 目录)

```
Context Analysis:
  Documents: 6 files, 45,230 chars
  Modules: 4 detected
  Cases: 12 found
  Data points: 45 found
```

### Step 2: 需求澄清（交互式）

通过对话澄清关键信息：

```
📋 PPT 骨架生成向导

Q1: 演示的主要目标是什么？
    [ ] 培训教学
    [ ] 项目汇报
    [x] 会议演讲
    [ ] 产品推介

Q2: 目标时长？
    → 90 分钟

Q3: 受众是谁？
    → 企业决策层（董事长/CEO）

Q4: 有哪些必须涵盖的主题？
    → AI趋势、行业案例、落地框架
```

### Step 3: 骨架生成

基于上下文和需求，生成结构化骨架：

```yaml
meta:
  title: "生成式AI驱动的产业应用与企业转型"
  version: "1.0"

audience:
  type: executives
  size: 30

presentation:
  duration: 90
  occasion: training
  style: corporate-light

structure:
  - id: "00-opening"
    title: "AI大势判断与破冰互动"
    type: opening
    duration: 12
    ...
```

### Step 4: 研究需求标记

自动识别需要调研补充的内容：

```yaml
research_needs:
  - type: case_study
    query: "制造业AI应用案例，要求有ROI数据"
    priority: high
    count: 3
  - type: statistics
    query: "2024-2025 AI市场规模数据"
    priority: medium
```

## 输入格式

### 上下文目录结构

```
docs/
├── _meta.yaml              # 元数据（可选）
├── 课程计划.md             # 总览文档
├── 01-模块一.md            # 内容文档
├── 02-模块二.md
└── 01-模块一-ds/           # 调研目录
    └── research.docx
```

### Brief 文件（批处理模式）

```yaml
# brief.yaml
title: "AI培训课程"
duration: 60
audience: managers
topics:
  - "AI基础概念"
  - "行业应用案例"
  - "实施路径"
style: corporate-light
```

## 输出格式

生成符合 [skeleton-spec.md](../ppt-specs/skeleton-spec.md) 规范的 YAML 文件。

## 上下文扫描规则

### 文档权重

| 文件模式 | 权重 | 说明 |
|----------|------|------|
| `_meta.yaml` | 最高 | 元数据定义 |
| `课程计划.md`, `README.md` | 高 | 总览文档 |
| `0*.md` | 中高 | 开场/结束模块 |
| `*.md` | 中 | 内容模块 |
| `*-ds/*.docx` | 中 | 调研结果 |

### 内容识别

| 模式 | 识别为 |
|------|--------|
| `## 案例:`, `### Case:` | 案例 |
| 数字 + `%`, `倍`, `万`, `亿` | 数据点 |
| `> "..."` | 引用 |
| 表格 | 对比/框架 |

## 研究需求推断

根据内容缺口自动生成研究需求：

| 缺口类型 | 生成的研究需求 |
|----------|----------------|
| 案例不足 | `type: case_study` |
| 数据过时 | `type: statistics` |
| 缺少权威引用 | `type: quote` |
| 趋势描述模糊 | `type: trend` |

## 文件结构

```
.claude/skills/ppt-outline/
├── SKILL.md                    # 本文档
├── scripts/
│   ├── outline.py              # 主入口脚本
│   ├── context_scanner.py      # 上下文扫描器
│   ├── skeleton_generator.py   # 骨架生成器
│   └── research_extractor.py   # 研究需求提取器
└── templates/
    └── skeleton_template.yaml  # 骨架模板
```

## 依赖

- Python >= 3.9
- PyYAML
- python-docx（可选，用于读取 .docx）

## API（编程使用）

```python
from outline import PPTOutline

outline = PPTOutline(
    context_dir='./docs/',
    style='corporate-light',
    duration=90
)

# 扫描上下文
context = outline.scan_context()

# 生成骨架
skeleton = outline.generate(
    title="AI培训课程",
    audience="executives"
)

# 保存
outline.save('skeleton.yaml')
```

## 与其他 Skill 的关系

| Skill | 关系 |
|-------|------|
| `/ppt-enrich` | 下游：接收 skeleton，生成 slide-md |
| `/ppt-render` | 下下游：接收 slide-md，生成 PPTX |
| `/ppt` | 编排器：协调整个流程 |

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-01-12 | 初版 |

## 相关文档

- [skeleton-spec.md](../ppt-specs/skeleton-spec.md) - Skeleton YAML 规范
- [slide-md-spec.md](../ppt-specs/slide-md-spec.md) - Slide Markdown 规范
