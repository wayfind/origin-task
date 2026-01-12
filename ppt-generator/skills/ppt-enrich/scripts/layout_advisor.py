#!/usr/bin/env python3
"""
Layout Advisor - 智能布局决策器

根据内容分析推荐最佳布局、图表类型和装饰元素，
确保生成的 PPT 美观大方、专业精致。

设计原则：
- 数据密集型内容 → 使用图表/表格可视化
- 对比类内容 → 双列布局或对比图表
- 流程类内容 → 流程图模板
- 案例/故事 → 卡片布局
- 引用/金句 → Quote 布局 + 装饰图
- 章节开头 → 全屏背景图 + 大标题
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LayoutType(Enum):
    """布局类型"""
    TITLE_ONLY = "title-only"      # 封面/章节标题
    BULLETS = "bullets"            # 要点列表
    TWO_COLUMN = "two-column"      # 双列对比
    THREE_CARDS = "three-cards"    # 三列卡片
    TABLE = "table"                # 表格
    QUOTE = "quote"                # 引用
    CHART = "chart"                # 图表
    IMAGE_LEFT = "image-left"      # 左图右文
    IMAGE_RIGHT = "image-right"    # 左文右图
    FULL_IMAGE = "full-image"      # 全图背景


class ChartType(Enum):
    """图表类型"""
    PROCESS_FLOW = "process-flow"   # 流程图
    COMPARISON = "comparison"       # 对比图
    TIMELINE = "timeline"           # 时间线
    PYRAMID = "pyramid"             # 金字塔
    CIRCLE_GROUP = "circle-group"   # 圆形分组
    MERMAID_CUSTOM = "mermaid"      # 自定义 Mermaid


class ImagePosition(Enum):
    """图片位置"""
    NONE = "none"
    COVER = "cover"           # 封面大图
    SECTION = "section"       # 章节背景
    SIDE = "side"             # 侧边装饰
    BACKGROUND = "background" # 浅色背景
    ICON = "icon"             # 小图标


@dataclass
class LayoutDecision:
    """布局决策结果"""
    layout: LayoutType
    confidence: float = 0.0
    chart_type: Optional[ChartType] = None
    image_position: ImagePosition = ImagePosition.NONE
    design_hints: List[str] = field(default_factory=list)
    rationale: str = ""


@dataclass
class ContentAnalysis:
    """内容分析结果"""
    has_numbers: bool = False          # 包含数字/统计
    has_comparison: bool = False       # 包含对比
    has_steps: bool = False            # 包含步骤/流程
    has_timeline: bool = False         # 包含时间线
    has_cases: bool = False            # 包含案例
    has_quote: bool = False            # 包含引用
    has_hierarchy: bool = False        # 包含层级关系
    bullet_count: int = 0              # 要点数量
    word_count: int = 0                # 字数
    keywords: List[str] = field(default_factory=list)


class LayoutAdvisor:
    """布局顾问"""

    # 对比关键词
    COMPARISON_KEYWORDS = [
        '对比', '比较', 'vs', '与', '相比', '优势', '劣势',
        '传统', '现代', '之前', '之后', 'before', 'after',
        '优点', '缺点', '利弊', '差异', '区别'
    ]

    # 流程关键词
    PROCESS_KEYWORDS = [
        '步骤', '流程', '阶段', '环节', '过程', '方法',
        '第一', '第二', '第三', '首先', '然后', '最后',
        'step', 'phase', 'stage', 'process'
    ]

    # 时间线关键词
    TIMELINE_KEYWORDS = [
        '年', '月', '季度', '历史', '发展', '演变', '趋势',
        '2020', '2021', '2022', '2023', '2024', '2025', '2026',
        '过去', '现在', '未来', '规划', '路线图', 'roadmap'
    ]

    # 层级关键词
    HIERARCHY_KEYWORDS = [
        '层次', '级别', '分类', '架构', '结构', '体系',
        '金字塔', '核心', '基础', '高级', '初级', '中级'
    ]

    # 引用关键词
    QUOTE_KEYWORDS = [
        '说', '认为', '表示', '指出', '强调', '提到',
        '"', '"', '——', '—'
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def analyze_content(self, content: Dict[str, Any]) -> ContentAnalysis:
        """分析内容特征"""
        analysis = ContentAnalysis()

        title = content.get('title', '')
        hints = content.get('content_hints', [])
        focus = content.get('focus', '')
        section_type = content.get('type', '')

        # 合并所有文本
        all_text = f"{title} {focus} {' '.join(hints)}".lower()
        analysis.word_count = len(all_text)
        analysis.bullet_count = len(hints)

        # 检测数字
        analysis.has_numbers = bool(re.search(r'\d+[%$¥亿万]|\d+\.\d+', all_text))

        # 检测对比
        analysis.has_comparison = any(kw in all_text for kw in self.COMPARISON_KEYWORDS)

        # 检测流程
        analysis.has_steps = any(kw in all_text for kw in self.PROCESS_KEYWORDS)

        # 检测时间线
        analysis.has_timeline = any(kw in all_text for kw in self.TIMELINE_KEYWORDS)

        # 检测案例
        analysis.has_cases = section_type == 'case-study' or '案例' in all_text or 'case' in all_text

        # 检测引用
        analysis.has_quote = any(kw in all_text for kw in self.QUOTE_KEYWORDS)

        # 检测层级
        analysis.has_hierarchy = any(kw in all_text for kw in self.HIERARCHY_KEYWORDS)

        # 提取关键词
        for kw_list in [self.COMPARISON_KEYWORDS, self.PROCESS_KEYWORDS,
                        self.TIMELINE_KEYWORDS, self.HIERARCHY_KEYWORDS]:
            for kw in kw_list:
                if kw in all_text:
                    analysis.keywords.append(kw)

        return analysis

    def recommend_layout(self, section: Dict[str, Any]) -> LayoutDecision:
        """为章节推荐最佳布局"""
        section_type = section.get('type', 'content')
        section_id = section.get('id', '')

        # 分析内容
        analysis = self.analyze_content(section)

        # 根据类型和分析结果决策
        decision = self._decide_layout(section_type, analysis, section)

        if self.verbose:
            print(f"[LayoutAdvisor] {section_id}: {decision.layout.value}")
            print(f"  Rationale: {decision.rationale}")
            if decision.chart_type:
                print(f"  Chart: {decision.chart_type.value}")
            if decision.image_position != ImagePosition.NONE:
                print(f"  Image: {decision.image_position.value}")

        return decision

    def _decide_layout(
        self,
        section_type: str,
        analysis: ContentAnalysis,
        section: Dict
    ) -> LayoutDecision:
        """核心决策逻辑"""

        # 1. 开场/结尾 → 全屏标题 + 背景图
        if section_type in ['opening', 'closing']:
            return LayoutDecision(
                layout=LayoutType.TITLE_ONLY,
                confidence=1.0,
                image_position=ImagePosition.COVER if section_type == 'opening' else ImagePosition.SECTION,
                design_hints=[
                    "使用全屏背景图增强视觉冲击",
                    "标题字号放大，居中对齐",
                    "可添加简短副标题"
                ],
                rationale=f"{section_type} 章节适合全屏标题布局"
            )

        # 2. 案例研究 → 卡片布局
        if section_type == 'case-study' or analysis.has_cases:
            return LayoutDecision(
                layout=LayoutType.THREE_CARDS,
                confidence=0.9,
                image_position=ImagePosition.ICON,
                design_hints=[
                    "每个卡片展示一个案例",
                    "突出关键指标（绿色背景）",
                    "控制描述文字简洁"
                ],
                rationale="案例内容适合卡片布局，便于对比展示"
            )

        # 3. 对比内容 → 双列或对比图表
        if analysis.has_comparison:
            if analysis.bullet_count >= 4:
                return LayoutDecision(
                    layout=LayoutType.CHART,
                    chart_type=ChartType.COMPARISON,
                    confidence=0.85,
                    design_hints=[
                        "使用对比图表清晰展示差异",
                        "左右分组，颜色区分",
                        "突出关键差异点"
                    ],
                    rationale="对比内容适合使用对比图表"
                )
            return LayoutDecision(
                layout=LayoutType.TWO_COLUMN,
                confidence=0.8,
                image_position=ImagePosition.SIDE,
                design_hints=[
                    "左右分列对比",
                    "使用不同颜色区分",
                    "可添加侧边装饰图"
                ],
                rationale="对比内容适合双列布局"
            )

        # 4. 流程/步骤 → 流程图
        if analysis.has_steps:
            return LayoutDecision(
                layout=LayoutType.CHART,
                chart_type=ChartType.PROCESS_FLOW,
                confidence=0.9,
                design_hints=[
                    "使用流程图清晰展示步骤",
                    "横向或纵向排列",
                    "每步骤可添加细节说明"
                ],
                rationale="步骤内容适合流程图展示"
            )

        # 5. 时间线 → 时间线图表
        if analysis.has_timeline:
            return LayoutDecision(
                layout=LayoutType.CHART,
                chart_type=ChartType.TIMELINE,
                confidence=0.9,
                design_hints=[
                    "使用时间线清晰展示发展历程",
                    "突出关键节点",
                    "时间从左到右或从上到下"
                ],
                rationale="时间相关内容适合时间线图表"
            )

        # 6. 层级结构 → 金字塔
        if analysis.has_hierarchy:
            return LayoutDecision(
                layout=LayoutType.CHART,
                chart_type=ChartType.PYRAMID,
                confidence=0.85,
                design_hints=[
                    "使用金字塔展示层级关系",
                    "从顶部核心到底部基础",
                    "颜色渐变增强层次感"
                ],
                rationale="层级内容适合金字塔图表"
            )

        # 7. 引用/金句 → Quote 布局
        if analysis.has_quote or section_type == 'quote':
            return LayoutDecision(
                layout=LayoutType.QUOTE,
                confidence=0.9,
                image_position=ImagePosition.BACKGROUND,
                design_hints=[
                    "引用文字放大居中",
                    "添加装饰性引号",
                    "注明出处/作者"
                ],
                rationale="引用内容适合 Quote 布局"
            )

        # 8. 数据密集 → 表格
        if analysis.has_numbers and analysis.bullet_count >= 4:
            return LayoutDecision(
                layout=LayoutType.TABLE,
                confidence=0.75,
                design_hints=[
                    "使用表格整理数据",
                    "表头使用主色调",
                    "数字对齐便于比较"
                ],
                rationale="数据密集内容适合表格展示"
            )

        # 9. 默认 → 要点列表（带装饰）
        return LayoutDecision(
            layout=LayoutType.BULLETS,
            confidence=0.6,
            image_position=ImagePosition.SIDE if analysis.bullet_count <= 4 else ImagePosition.NONE,
            design_hints=[
                "控制每页要点数量（3-5个最佳）",
                "使用项目符号增强可读性",
                "可添加侧边装饰图增加美感"
            ],
            rationale="通用内容使用要点列表布局"
        )

    def generate_design_report(self, skeleton: Dict) -> str:
        """生成设计建议报告"""
        sections = skeleton.get('sections', skeleton.get('structure', []))

        report_lines = [
            "=" * 60,
            "  PPT 设计建议报告",
            "=" * 60,
            "",
            f"共 {len(sections)} 个章节",
            "",
        ]

        layout_counts = {}
        chart_counts = {}
        image_counts = {}

        for section in sections:
            decision = self.recommend_layout(section)

            # 统计
            layout_counts[decision.layout.value] = layout_counts.get(decision.layout.value, 0) + 1
            if decision.chart_type:
                chart_counts[decision.chart_type.value] = chart_counts.get(decision.chart_type.value, 0) + 1
            if decision.image_position != ImagePosition.NONE:
                image_counts[decision.image_position.value] = image_counts.get(decision.image_position.value, 0) + 1

            # 章节详情
            section_id = section.get('id', 'unknown')
            section_title = section.get('title', '')[:30]
            report_lines.append(f"[{section_id}] {section_title}")
            report_lines.append(f"  布局: {decision.layout.value} (confidence: {decision.confidence:.0%})")
            if decision.chart_type:
                report_lines.append(f"  图表: {decision.chart_type.value}")
            if decision.image_position != ImagePosition.NONE:
                report_lines.append(f"  配图: {decision.image_position.value}")
            report_lines.append(f"  理由: {decision.rationale}")
            report_lines.append("")

        # 汇总
        report_lines.append("-" * 60)
        report_lines.append("布局分布:")
        for layout, count in sorted(layout_counts.items(), key=lambda x: -x[1]):
            report_lines.append(f"  {layout}: {count}")

        if chart_counts:
            report_lines.append("\n图表类型:")
            for chart, count in sorted(chart_counts.items(), key=lambda x: -x[1]):
                report_lines.append(f"  {chart}: {count}")

        if image_counts:
            report_lines.append("\n配图位置:")
            for pos, count in sorted(image_counts.items(), key=lambda x: -x[1]):
                report_lines.append(f"  {pos}: {count}")

        report_lines.append("=" * 60)

        return "\n".join(report_lines)

    def apply_decisions_to_skeleton(self, skeleton: Dict) -> Dict:
        """将布局决策应用到骨架"""
        sections = skeleton.get('sections', skeleton.get('structure', []))

        for section in sections:
            decision = self.recommend_layout(section)

            # 添加布局决策
            section['recommended_layout'] = decision.layout.value
            section['layout_confidence'] = decision.confidence
            section['design_hints'] = decision.design_hints

            if decision.chart_type:
                section['recommended_chart'] = decision.chart_type.value

            if decision.image_position != ImagePosition.NONE:
                section['recommended_image_position'] = decision.image_position.value

        return skeleton


def get_design_guidelines() -> str:
    """获取设计指南（供 AI 参考）"""
    return """
# PPT 设计工具指南

## 可用布局类型

| 布局 | 用途 | 何时使用 |
|------|------|----------|
| title-only | 封面/章节页 | 开场、章节标题、结尾 |
| bullets | 要点列表 | 通用内容、3-5个要点 |
| two-column | 双列对比 | 对比内容、左右分列 |
| three-cards | 三列卡片 | 案例展示、特性对比 |
| table | 表格 | 数据密集、多维比较 |
| quote | 引用 | 名人金句、重点强调 |
| chart | 图表 | 流程、时间线、层级 |

## 可用图表模板

| 模板 | 语法 | 适用场景 |
|------|------|----------|
| process-flow | ::: chart + template: process-flow | 步骤、流程、阶段 |
| comparison | ::: chart + template: comparison | 对比、优劣势 |
| timeline | ::: chart + template: timeline | 历史、规划、路线图 |
| pyramid | ::: chart + template: pyramid | 层级、架构、分类 |
| mermaid | ```mermaid 代码块 | 自定义复杂图表 |

## 图片装饰位置

| 位置 | 用途 | 推荐场景 |
|------|------|----------|
| cover | 封面大图 | 开场页、主视觉 |
| section | 章节背景 | 章节标题页 |
| side | 侧边装饰 | 内容页辅助 |
| background | 浅色背景 | 需要增加层次感 |

## 设计原则

1. **一页一主题**: 每页只传达一个核心观点
2. **数据可视化**: 有数据就用图表，不要堆砌数字
3. **对比清晰化**: 对比内容必须用双列或对比图
4. **流程步骤化**: 步骤内容必须用流程图
5. **适度装饰**: 重要页面配装饰图，但不喧宾夺主
6. **配色一致**: 使用主题色系，保持视觉统一
"""


# CLI
if __name__ == "__main__":
    import sys
    import yaml

    if len(sys.argv) < 2:
        print("Usage: python layout_advisor.py <skeleton.yaml>")
        print("\nDesign Guidelines:")
        print(get_design_guidelines())
        sys.exit(0)

    skeleton_path = sys.argv[1]
    with open(skeleton_path, 'r', encoding='utf-8') as f:
        skeleton = yaml.safe_load(f)

    advisor = LayoutAdvisor(verbose=True)
    report = advisor.generate_design_report(skeleton)
    print(report)
