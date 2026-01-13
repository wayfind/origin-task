#!/usr/bin/env python3
"""
Slide-MD Writer
将内容输出为 slide-md 格式文件
"""

import os
import yaml
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class SlideContent:
    """幻灯片内容"""
    id: str
    type: str  # cover | section | content | case-study | quote | closing
    layout: str
    title: str
    subtitle: str = ""
    elements: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    sources: List[Dict[str, str]] = field(default_factory=list)
    cases: List[Dict[str, Any]] = field(default_factory=list)
    source_section: str = ""


class SlideMDWriter:
    """Slide-MD 输出器"""

    # 类型到默认布局的映射
    DEFAULT_LAYOUTS = {
        'cover': 'title-only',
        'section': 'title-only',
        'content': 'bullets',
        'case-study': 'three-cards',
        'framework': 'bullets',
        'quote': 'quote',
        'closing': 'bullets',
        'transition': 'title-only'
    }

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.slide_counter = 0

    def write_slide(self, slide: SlideContent) -> str:
        """写入单个幻灯片"""
        self.slide_counter += 1

        # 生成文件名
        filename = f"{slide.id}.slide.md"
        filepath = self.output_dir / filename

        # 构建 frontmatter
        frontmatter = {
            'slide': {
                'id': slide.id,
                'type': slide.type,
                'layout': slide.layout or self.DEFAULT_LAYOUTS.get(slide.type, 'bullets')
            }
        }

        if slide.source_section:
            frontmatter['slide']['source_section'] = slide.source_section

        if slide.sources:
            frontmatter['sources'] = slide.sources

        if slide.cases:
            frontmatter['cases'] = slide.cases

        # 构建内容
        content_lines = []

        # 主标题
        content_lines.append(f"# {slide.title}")
        content_lines.append("")

        # 副标题
        if slide.subtitle:
            content_lines.append(f"## {slide.subtitle}")
            content_lines.append("")

        # 内容元素
        for element in slide.elements:
            el_type = element.get('type', 'text')

            if el_type == 'bullets':
                for bullet in element.get('items', []):
                    if isinstance(bullet, dict):
                        text = bullet.get('text', '')
                        metric = bullet.get('metric', '')
                        if metric:
                            text = f"{text} `{metric}`"
                        if bullet.get('bold'):
                            text = f"**{text}**"
                    else:
                        text = str(bullet)
                    content_lines.append(f"- {text}")
                content_lines.append("")

            elif el_type == 'card':
                content_lines.append("::: card")
                content_lines.append(f"### {element.get('title', '')}")
                content_lines.append(element.get('description', ''))
                if element.get('metric'):
                    content_lines.append(f"\n`{element['metric']}`{{.metric}}")
                content_lines.append(":::")
                content_lines.append("")

            elif el_type == 'quote':
                content_lines.append(f"> {element.get('text', '')}")
                if element.get('attribution'):
                    content_lines.append(f">")
                    content_lines.append(f"> — {element['attribution']}")
                content_lines.append("")

            elif el_type == 'table':
                headers = element.get('headers', [])
                rows = element.get('rows', [])
                if headers:
                    content_lines.append("| " + " | ".join(headers) + " |")
                    content_lines.append("|" + "|".join(["---"] * len(headers)) + "|")
                    for row in rows:
                        content_lines.append("| " + " | ".join(str(c) for c in row) + " |")
                    content_lines.append("")

            elif el_type == 'paragraph':
                content_lines.append(element.get('text', ''))
                content_lines.append("")

        # 演讲者备注
        if slide.notes:
            content_lines.append("---notes---")
            content_lines.append("")
            content_lines.append(slide.notes)

        # 组装完整文件
        fm_str = yaml.dump(frontmatter, allow_unicode=True, default_flow_style=False, sort_keys=False)
        full_content = f"---\n{fm_str}---\n\n" + "\n".join(content_lines)

        # 写入文件
        filepath.write_text(full_content, encoding='utf-8')

        return str(filepath)

    def write_slides(self, slides: List[SlideContent]) -> List[str]:
        """写入多个幻灯片"""
        paths = []
        for slide in slides:
            path = self.write_slide(slide)
            paths.append(path)
        return paths

    def create_cover_slide(self, title: str, subtitle: str = "", extra: str = "") -> SlideContent:
        """创建封面幻灯片"""
        slide = SlideContent(
            id="00-01-cover",
            type="cover",
            layout="title-only",
            title=title,
            subtitle=subtitle
        )
        if extra:
            slide.elements.append({'type': 'paragraph', 'text': extra})
        return slide

    def create_section_slide(self, section_id: str, title: str, number: str = "") -> SlideContent:
        """创建章节标题幻灯片"""
        slide = SlideContent(
            id=f"{section_id}-section",
            type="section",
            layout="title-only",
            title=title,
            subtitle=number
        )
        return slide

    def create_bullets_slide(self, slide_id: str, title: str, bullets: List[str],
                            source_section: str = "") -> SlideContent:
        """创建要点列表幻灯片"""
        slide = SlideContent(
            id=slide_id,
            type="content",
            layout="bullets",
            title=title,
            source_section=source_section,
            elements=[{
                'type': 'bullets',
                'items': bullets
            }]
        )
        return slide

    def create_cards_slide(self, slide_id: str, title: str,
                          cards: List[Dict[str, str]], source_section: str = "") -> SlideContent:
        """创建卡片幻灯片"""
        slide = SlideContent(
            id=slide_id,
            type="case-study",
            layout="three-cards",
            title=title,
            source_section=source_section
        )
        for card in cards[:3]:
            slide.elements.append({
                'type': 'card',
                'title': card.get('title', ''),
                'description': card.get('description', ''),
                'metric': card.get('metric', '')
            })
        return slide

    def create_two_column_slide(self, slide_id: str, title: str,
                                left_bullets: List[str], right_bullets: List[str],
                                source_section: str = "",
                                left_title: str = "", right_title: str = "") -> SlideContent:
        """创建双列对比幻灯片"""
        slide = SlideContent(
            id=slide_id,
            type="content",
            layout="two-column",
            title=title,
            source_section=source_section
        )
        slide.elements.append({
            'type': 'column',
            'position': 'left',
            'title': left_title,
            'bullets': left_bullets
        })
        slide.elements.append({
            'type': 'column',
            'position': 'right',
            'title': right_title,
            'bullets': right_bullets
        })
        return slide

    def create_quote_slide(self, slide_id: str, quote: str,
                          attribution: str = "") -> SlideContent:
        """创建引用幻灯片"""
        slide = SlideContent(
            id=slide_id,
            type="quote",
            layout="quote",
            title=quote[:50] + "..." if len(quote) > 50 else quote,
            elements=[{
                'type': 'quote',
                'text': quote,
                'attribution': attribution
            }]
        )
        return slide


# CLI
if __name__ == '__main__':
    import argparse
    import json

    parser = argparse.ArgumentParser(description='生成 slide-md 文件')
    parser.add_argument('-o', '--output', default='./slides', help='输出目录')
    parser.add_argument('--demo', action='store_true', help='生成演示文件')

    args = parser.parse_args()

    writer = SlideMDWriter(args.output)

    if args.demo:
        # 生成演示文件
        slides = [
            writer.create_cover_slide(
                "生成式AI驱动的产业应用",
                "清华经管研修班",
                "时长：90分钟 | 2026年1月"
            ),
            writer.create_section_slide("01", "第一部分", "01"),
            writer.create_bullets_slide(
                "01-02-content",
                "AI变革的四条路径",
                [
                    "**效率革命**：文档/代码/营销自动化",
                    "**创新加速**：产品设计/材料研发",
                    "**决策升级**：战略洞察/智能决策",
                    "**模式重构**：AI原生产品/新商业模式"
                ]
            ),
            writer.create_cards_slide(
                "01-03-cases",
                "制造业AI应用标杆",
                [
                    {'title': '美的集团', 'description': '全流程智能化', 'metric': '效率+30%'},
                    {'title': '隆基绿能', 'description': 'AI视觉质检', 'metric': '良品率99%'},
                    {'title': '宁德时代', 'description': '智能产线调度', 'metric': '产能+25%'}
                ]
            ),
            writer.create_quote_slide(
                "99-01-quote",
                "未来十年，最稀缺的不是AI技术，而是敢于把核心业务交给AI去重构的企业家勇气",
                "课程核心观点"
            )
        ]

        paths = writer.write_slides(slides)
        print(f"Generated {len(paths)} slides in {args.output}/")
        for p in paths:
            print(f"  - {p}")
