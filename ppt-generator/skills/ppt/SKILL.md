---
name: ppt
description: |
  PPT generation orchestrator - One-click professional PPTX creation.
  Use when: (1) User wants to generate complete PPT from documents, (2) User provides natural language description for presentation, (3) User needs to convert content to slides.
  Triggers: "生成PPT", "create presentation", "make slides", "PPT", "演示文稿", "幻灯片"
---

# /ppt

> 一键生成专业 PPT 的编排器

## 概述

`/ppt` 是 PPT 生成的主入口命令，它编排 `outline → enrich → render` 三阶段流程，将用户的原始需求转化为专业的 PPTX 文件。

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
