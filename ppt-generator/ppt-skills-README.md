# PPT Skills 架构

> 模块化 PPT 生成系统 - 从文档到专业 PPTX 的三阶段流水线

## 概述

本系统将单一的 PPT 生成器拆分为四个可组合的专业 skill：

```
                    /ppt（编排器）
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   /ppt-outline    /ppt-enrich      /ppt-render
   (骨架生成)      (内容填充)       (PPTX渲染)
        │                │                │
        ▼                ▼                ▼
   skeleton.yaml    slides/*.md     output.pptx
```

## Skills 清单

| Skill | 语言 | 功能 | 输入 | 输出 |
|-------|------|------|------|------|
| `/ppt` | Python | 编排器 | 文档/描述 | PPTX |
| `/ppt-outline` | Python | 骨架生成 | 文档/对话 | skeleton.yaml |
| `/ppt-enrich` | Python | 内容填充 | skeleton.yaml | slide-md |
| `/ppt-render` | Node.js | PPTX 渲染 | slide-md | PPTX |

## 快速开始

### 一键生成

```bash
/ppt ./docs/ -o presentation.pptx
```

### 分阶段执行

```bash
# 1. 生成骨架
/ppt-outline --context ./docs/ -o skeleton.yaml

# 2. 填充内容
/ppt-enrich skeleton.yaml -o slides/

# 3. 渲染 PPTX
/ppt-render slides/ -o presentation.pptx
```

### 自然语言

```bash
/ppt "给企业高管做一个AI转型培训，90分钟"
```

## 中间格式

### skeleton.yaml

```yaml
meta:
  title: PPT 标题
  duration: 90

structure:
  - id: 01-intro
    title: 开场
    type: opening
    slides_estimate: 5
    content_hints:
      - 破冰互动
      - 议程预览
```

详见：[ppt-specs/skeleton-spec.md](ppt-specs/skeleton-spec.md)

### slide-md

```markdown
---
slide:
  id: 01-intro-cover
  type: cover
  layout: center
---

# 标题

副标题内容
```

详见：[ppt-specs/slide-md-spec.md](ppt-specs/slide-md-spec.md)

## 主题

| 主题 | 风格 | 用途 |
|------|------|------|
| `corporate-light` | 白底专业 | 商务演示（默认） |
| `nano-banana-pro` | 暗色科技 | 科技感演示 |

```bash
/ppt ./docs/ --theme nano-banana-pro -o dark.pptx
```

## 目录结构

```
.claude/skills/
├── ppt/                    # 编排器
│   ├── SKILL.md
│   └── scripts/
│       ├── orchestrator.py
│       └── intent_parser.py
├── ppt-outline/            # 骨架生成
│   ├── SKILL.md
│   └── scripts/
│       ├── outline.py
│       ├── context_scanner.py
│       ├── skeleton_generator.py
│       └── research_extractor.py
├── ppt-enrich/             # 内容填充
│   ├── SKILL.md
│   └── scripts/
│       ├── enrich.py
│       ├── gap_detector.py
│       └── slidemd_writer.py
├── ppt-render/             # PPTX 渲染
│   ├── SKILL.md
│   ├── package.json
│   └── scripts/
│       ├── render.js
│       ├── slide-parser.js
│       ├── pptx-renderer.js
│       └── theme-loader.js
├── ppt-specs/              # 格式规范
│   ├── skeleton-spec.md
│   ├── slide-md-spec.md
│   ├── style-system-spec.md
│   └── skeleton.schema.json
└── _deprecated-ppt-generator/  # 已废弃的旧版
```

## 迁移指南

### 从旧 ppt-generator 迁移

旧版 `/ppt init` + `/ppt begin` 已废弃。迁移步骤：

1. **更新命令**
   ```bash
   # 旧版
   /ppt init my-project
   /ppt begin

   # 新版
   /ppt ./my-project/context/ -o output.pptx
   ```

2. **保留上下文目录**
   - 旧版 `context/` 目录可直接作为新版输入
   - 无需修改文档格式

3. **主题兼容**
   - `nano-banana-pro` 主题完全兼容
   - `corporate-light` 为新增主题

### 断点续传

```bash
# 执行到某阶段
/ppt ./docs/ --step enrich
# 生成 .ppt-state.json

# 从断点继续
/ppt --resume .ppt-state.json
```

## 依赖安装

```bash
# Python 依赖
pip install pyyaml

# Node.js 依赖（ppt-render）
cd .claude/skills/ppt-render && npm install
```

## 设计原则

1. **Unix 哲学** - 每个 skill 做好一件事
2. **人类可读** - 中间格式均为标准 YAML/Markdown
3. **可组合** - 每个 skill 可独立使用或组合
4. **可恢复** - 支持断点续传和手动干预
5. **渐进增强** - 从简单到复杂，按需添加功能

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.0.0 | 2026-01-12 | 架构重构：拆分为 4 个 skill |
| 1.0.0 | 2026-01-11 | 初版单体 ppt-generator |

## 相关文档

- [/ppt SKILL.md](ppt/SKILL.md) - 编排器文档
- [/ppt-outline SKILL.md](ppt-outline/SKILL.md) - 骨架生成文档
- [/ppt-enrich SKILL.md](ppt-enrich/SKILL.md) - 内容填充文档
- [/ppt-render SKILL.md](ppt-render/SKILL.md) - 渲染器文档
