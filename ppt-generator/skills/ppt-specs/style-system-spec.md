# Style System Specification v1.0

> PPT 样式系统规范 - 所有 /ppt-* skills 共享的视觉配置接口

---

## 1. 概述

### 1.1 设计目标

| 目标 | 说明 |
|------|------|
| **一致性** | 所有 skill 共用同一套样式定义 |
| **可扩展** | 支持自定义主题和覆盖 |
| **解耦** | 内容与样式分离 |
| **可预览** | 样式可独立预览和调试 |

### 1.2 文件结构

```
.claude/skills/ppt-specs/
├── style-system-spec.md       # 本规范文档
└── themes/
    ├── _base.yaml             # 基础样式定义
    ├── corporate-light.yaml   # Corporate Light 主题
    ├── nano-banana-pro.yaml   # Nano Banana Pro 主题
    └── custom/                # 用户自定义主题目录
        └── my-theme.yaml
```

---

## 2. 主题配置文件 Schema

### 2.1 完整 Schema

```yaml
# theme.yaml - 主题配置文件
# 继承自 _base.yaml，可覆盖任意字段

theme:
  # 基本信息
  name: string                # 主题名称，如 "corporate-light"
  display_name: string        # 显示名称，如 "Corporate Light"
  version: string             # 版本号
  description: string         # 主题描述
  author: string              # 作者

  # 基础样式类型
  base: enum                  # light | dark
  mood: enum                  # professional | creative | elegant | bold

#═══════════════════════════════════════════════════════════════
# 色彩系统
#═══════════════════════════════════════════════════════════════
colors:
  # 主色调（必须）
  primary: color              # 主色，用于标题、强调
  secondary: color            # 辅助色，用于副标题
  accent: color               # 点缀色，用于装饰元素

  # 背景色（必须）
  background:
    default: color            # 默认页面背景
    alternate: color          # 交替背景（如卡片）
    section: color            # 章节标题页背景

  # 文字色（必须）
  text:
    primary: color            # 主文字色
    secondary: color          # 次要文字色
    inverse: color            # 反色背景上的文字

  # 语义色（可选，有默认值）
  semantic:
    success: color            # 正向/增长，默认绿色
    warning: color            # 警告/注意，默认橙色
    danger: color             # 负向/风险，默认红色
    info: color               # 信息/中性，默认蓝色

  # 装饰色（可选）
  decorative:
    border: color             # 边框色
    divider: color            # 分隔线色
    shadow: color             # 阴影色

#═══════════════════════════════════════════════════════════════
# 字体系统
#═══════════════════════════════════════════════════════════════
typography:
  # 字体族（必须）
  fonts:
    heading: string           # 标题字体，如 "Microsoft YaHei"
    body: string              # 正文字体
    mono: string              # 等宽字体（用于代码/数据）

  # 字号比例（必须）
  scale:
    cover_title: integer      # 封面标题，如 44
    section_title: integer    # 章节标题，如 36
    slide_title: integer      # 页面标题，如 28
    subtitle: integer         # 副标题，如 20
    body: integer             # 正文，如 18
    caption: integer          # 说明文字，如 14
    footnote: integer         # 脚注，如 12

  # 行高（可选，有默认值）
  line_height:
    tight: number             # 紧凑，如 1.2
    normal: number            # 正常，如 1.5
    loose: number             # 宽松，如 1.8

  # 字重（可选）
  weight:
    normal: integer           # 正常，如 400
    medium: integer           # 中等，如 500
    bold: integer             # 粗体，如 700

#═══════════════════════════════════════════════════════════════
# 布局系统
#═══════════════════════════════════════════════════════════════
layout:
  # 画布
  canvas:
    width: integer            # 宽度，如 10（英寸）
    height: integer           # 高度，如 5.625（16:9）
    aspect_ratio: string      # "16:9" | "4:3" | "16:10"

  # 边距（英寸）
  margins:
    top: number               # 顶部边距
    right: number             # 右侧边距
    bottom: number            # 底部边距
    left: number              # 左侧边距

  # 内边距
  padding:
    card: number              # 卡片内边距
    section: number           # 区块内边距

  # 间距
  spacing:
    xs: number                # 超小，如 0.1
    sm: number                # 小，如 0.2
    md: number                # 中，如 0.4
    lg: number                # 大，如 0.6
    xl: number                # 超大，如 1.0

#═══════════════════════════════════════════════════════════════
# 组件样式
#═══════════════════════════════════════════════════════════════
components:
  # 装饰条
  accent_bar:
    height: number            # 高度
    position: enum            # top | bottom | left | right

  # 卡片
  card:
    border_radius: number     # 圆角
    shadow: boolean           # 是否有阴影
    border_width: number      # 边框宽度

  # 表格
  table:
    header_style: enum        # filled | bordered | minimal
    stripe: boolean           # 斑马纹
    border_width: number      # 边框宽度

  # 列表
  bullets:
    style: enum               # disc | circle | square | dash | arrow
    indent: number            # 缩进
    spacing: number           # 行间距

  # 引用
  quote:
    style: enum               # large-mark | bar-left | minimal
    mark_size: integer        # 引号大小

#═══════════════════════════════════════════════════════════════
# 布局预设
#═══════════════════════════════════════════════════════════════
presets:
  # 封面布局
  cover:
    title_y: number           # 标题 Y 位置
    subtitle_y: number        # 副标题 Y 位置
    has_decoration: boolean   # 是否有装饰元素

  # 章节标题布局
  section:
    number_y: number          # 章节号 Y 位置
    title_y: number           # 标题 Y 位置
    background: enum          # primary | secondary | gradient

  # 内容布局
  content:
    title_height: number      # 标题区域高度
    content_start_y: number   # 内容起始 Y 位置

  # 三列卡片布局
  three_cards:
    card_width: number        # 卡片宽度
    card_height: number       # 卡片高度
    gap: number               # 卡片间距

  # 双列布局
  two_column:
    left_width: number        # 左列宽度比例 0-1
    gap: number               # 列间距
```

---

## 3. 预置主题

### 3.1 Corporate Light

适用场景：企业培训、正式汇报、学术演讲

```yaml
theme:
  name: corporate-light
  display_name: "Corporate Light"
  base: light
  mood: professional

colors:
  primary: "#1E3A5F"          # 深蓝
  secondary: "#2C5282"        # 蓝色
  accent: "#3182CE"           # 亮蓝

  background:
    default: "#FFFFFF"
    alternate: "#F7FAFC"
    section: "#1E3A5F"

  text:
    primary: "#1A202C"
    secondary: "#4A5568"
    inverse: "#FFFFFF"

  semantic:
    success: "#38A169"
    warning: "#D69E2E"
    danger: "#E53E3E"
    info: "#3182CE"

  decorative:
    border: "#E2E8F0"
    divider: "#CBD5E0"

typography:
  fonts:
    heading: "Microsoft YaHei"
    body: "Microsoft YaHei"
    mono: "Consolas"

  scale:
    cover_title: 44
    section_title: 36
    slide_title: 24
    subtitle: 20
    body: 18
    caption: 14
    footnote: 12

layout:
  canvas:
    aspect_ratio: "16:9"

  margins:
    top: 0.5
    right: 0.5
    bottom: 0.5
    left: 0.5

components:
  accent_bar:
    height: 0.15
    position: top

  card:
    border_radius: 0.05
    shadow: false
    border_width: 1

  table:
    header_style: filled
    stripe: true

  bullets:
    style: disc
    indent: 0.3
    spacing: 0.15

  quote:
    style: large-mark
    mark_size: 120
```

### 3.2 Nano Banana Pro

适用场景：创意演示、产品发布、科技主题

```yaml
theme:
  name: nano-banana-pro
  display_name: "Nano Banana Pro"
  base: dark
  mood: bold

colors:
  primary: "#F4C430"          # Banana Gold
  secondary: "#00D9C0"        # Teal
  accent: "#F4C430"           # Gold

  background:
    default: "#1C2833"        # Deep Navy
    alternate: "#232F3E"
    section: "#1C2833"

  text:
    primary: "#FFFFFF"
    secondary: "#AAB7B8"
    inverse: "#1C2833"

  semantic:
    success: "#27AE60"
    warning: "#F39C12"
    danger: "#E74C3C"
    info: "#3498DB"

  decorative:
    border: "#2C3E50"
    divider: "#34495E"

typography:
  fonts:
    heading: "Microsoft YaHei"
    body: "Microsoft YaHei"
    mono: "Fira Code"

  scale:
    cover_title: 48
    section_title: 40
    slide_title: 28
    subtitle: 22
    body: 18
    caption: 14
    footnote: 12

layout:
  canvas:
    aspect_ratio: "16:9"

  margins:
    top: 0.6
    right: 0.6
    bottom: 0.6
    left: 0.6

components:
  accent_bar:
    height: 0.1
    position: top

  card:
    border_radius: 0.1
    shadow: true
    border_width: 0

  table:
    header_style: filled
    stripe: false

  bullets:
    style: arrow
    indent: 0.4
    spacing: 0.2

  quote:
    style: bar-left
    mark_size: 100
```

---

## 4. 主题继承与覆盖

### 4.1 继承机制

所有主题隐式继承 `_base.yaml`：

```yaml
# _base.yaml - 所有主题的基础配置
theme:
  version: "1.0"

colors:
  semantic:
    success: "#22C55E"
    warning: "#F59E0B"
    danger: "#EF4444"
    info: "#3B82F6"

typography:
  line_height:
    tight: 1.2
    normal: 1.5
    loose: 1.8

  weight:
    normal: 400
    medium: 500
    bold: 700

layout:
  spacing:
    xs: 0.1
    sm: 0.2
    md: 0.4
    lg: 0.6
    xl: 1.0
```

### 4.2 自定义覆盖

用户可在项目中创建覆盖文件：

```yaml
# custom/my-company.yaml
extends: corporate-light      # 继承自 corporate-light

theme:
  name: my-company
  display_name: "我的公司主题"

colors:
  primary: "#0066CC"          # 覆盖主色为公司蓝
  accent: "#FF6600"           # 覆盖强调色为公司橙

components:
  card:
    border_radius: 0.2        # 更大的圆角
```

---

## 5. 样式 API 接口

### 5.1 解析器接口

```typescript
interface ThemeResolver {
  // 加载主题配置
  load(themeName: string): Theme;

  // 合并覆盖配置
  merge(base: Theme, override: Partial<Theme>): Theme;

  // 获取颜色值
  getColor(theme: Theme, path: string): string;
  // 例：getColor(theme, "semantic.success") => "#38A169"

  // 获取字号
  getFontSize(theme: Theme, level: string): number;
  // 例：getFontSize(theme, "slide_title") => 24

  // 获取布局值
  getLayout(theme: Theme, path: string): number;
  // 例：getLayout(theme, "margins.top") => 0.5
}
```

### 5.2 渲染器接口

```typescript
interface StyleRenderer {
  // 应用背景色
  applyBackground(slide: Slide, type: 'default' | 'alternate' | 'section'): void;

  // 应用文字样式
  applyTextStyle(
    element: TextElement,
    level: 'title' | 'subtitle' | 'body' | 'caption',
    emphasis?: 'normal' | 'strong' | 'muted'
  ): void;

  // 应用卡片样式
  applyCardStyle(shape: Shape): void;

  // 应用表格样式
  applyTableStyle(table: Table): void;
}
```

---

## 6. 颜色格式

支持的颜色格式：

| 格式 | 示例 | 说明 |
|------|------|------|
| HEX | `#1E3A5F` | 6位十六进制 |
| HEX短 | `#1E3` | 3位十六进制 |
| RGB | `rgb(30, 58, 95)` | RGB函数 |
| RGBA | `rgba(30, 58, 95, 0.8)` | 带透明度 |
| 命名 | `transparent` | 透明 |

**注意**：pptxgenjs 只接受无 `#` 前缀的 HEX，解析器需要自动转换。

---

## 7. 验证规则

### 7.1 必填字段

- `theme.name`
- `theme.base`
- `colors.primary`
- `colors.secondary`
- `colors.background.default`
- `colors.text.primary`
- `typography.fonts.heading`
- `typography.fonts.body`

### 7.2 值范围检查

- 颜色值必须是有效格式
- 字号必须 > 0
- 边距/间距必须 >= 0
- 比例值必须在 0-1 范围内

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0 | 2026-01-12 | 初版 |

---

## 9. 相关文档

- [skeleton-spec.md](./skeleton-spec.md) - Skeleton YAML 规范
- [slide-md-spec.md](./slide-md-spec.md) - Slide Markdown 规范
