#!/usr/bin/env python3
"""
Skeleton Generator
基于上下文和需求生成 skeleton.yaml 结构
"""

import yaml
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any

from context_scanner import ContextScanner, ContextSummary, Module


@dataclass
class ResearchNeed:
    """研究需求"""
    type: str  # case_study | statistics | quote | trend | comparison
    query: str
    priority: str = "medium"  # high | medium | low
    count: int = 1
    constraints: Dict[str, str] = field(default_factory=dict)


@dataclass
class Section:
    """章节定义"""
    id: str
    title: str
    type: str  # opening | content | case-study | framework | closing | transition
    duration: int = 10
    slides_estimate: int = 5
    content_hints: List[str] = field(default_factory=list)
    research_needs: List[ResearchNeed] = field(default_factory=list)


@dataclass
class SkeletonConfig:
    """骨架配置"""
    title: str
    subtitle: str = ""
    duration: int = 30
    audience_type: str = "professionals"
    audience_size: int = 50
    occasion: str = "conference"
    style: str = "corporate-light"
    author: str = ""


class SkeletonGenerator:
    """骨架生成器"""

    # 章节类型对应的默认时长比例
    DURATION_RATIOS = {
        'opening': 0.12,
        'content': 0.25,
        'case-study': 0.20,
        'framework': 0.20,
        'closing': 0.08,
        'transition': 0.03,
    }

    # 每分钟估计幻灯片数
    SLIDES_PER_MINUTE = 0.8

    def __init__(self, context: Optional[ContextSummary] = None):
        self.context = context
        self.sections: List[Section] = []
        self.config = SkeletonConfig(title="Untitled Presentation")

    def configure(self, **kwargs):
        """配置生成参数"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def generate_from_context(self) -> Dict[str, Any]:
        """从上下文生成骨架"""
        if not self.context:
            raise ValueError("No context provided")

        # 从元数据获取配置
        if self.context.meta:
            self._apply_meta_config(self.context.meta)

        # 生成章节结构
        self.sections = self._generate_sections()

        # 生成研究需求
        self._generate_research_needs()

        return self.to_skeleton()

    def generate_from_brief(self, brief: Dict[str, Any]) -> Dict[str, Any]:
        """从简要配置生成骨架"""
        # 应用配置
        self.configure(
            title=brief.get('title', 'Presentation'),
            subtitle=brief.get('subtitle', ''),
            duration=brief.get('duration', 30),
            audience_type=brief.get('audience', 'professionals'),
            occasion=brief.get('occasion', 'conference'),
            style=brief.get('style', 'corporate-light')
        )

        # 从主题生成章节
        topics = brief.get('topics', [])
        self.sections = self._generate_sections_from_topics(topics)

        return self.to_skeleton()

    def _apply_meta_config(self, meta: Dict[str, Any]):
        """应用元数据配置"""
        if 'title' in meta:
            self.config.title = meta['title']
        if 'subtitle' in meta:
            self.config.subtitle = meta['subtitle']
        if 'author' in meta:
            self.config.author = meta['author']
        if 'audience' in meta:
            aud = meta['audience']
            self.config.audience_type = aud.get('type', 'professionals')
            self.config.audience_size = aud.get('size', 50)
        if 'style' in meta:
            style = meta['style']
            self.config.style = style.get('theme', 'corporate-light')

        # 从 structure 计算时长
        if 'structure' in meta:
            total_duration = sum(s.get('duration', 0) for s in meta['structure'])
            if total_duration > 0:
                self.config.duration = total_duration

    def _generate_sections(self) -> List[Section]:
        """从上下文模块生成章节"""
        sections = []
        total_duration = self.config.duration

        # 添加开场
        sections.append(Section(
            id='00-opening',
            title='开场',
            type='opening',
            duration=int(total_duration * self.DURATION_RATIOS['opening']),
            slides_estimate=5,
            content_hints=['破冰互动', '议程预览']
        ))

        # 从模块生成内容章节
        content_modules = [m for m in self.context.modules if not m.id.startswith('0')]
        if content_modules:
            content_duration = int(total_duration * 0.75)  # 75% 给内容
            per_module = content_duration // len(content_modules)

            for i, module in enumerate(content_modules):
                section_type = self._infer_section_type(module)
                sections.append(Section(
                    id=f'{i+1:02d}-{module.id}',
                    title=module.title,
                    type=section_type,
                    duration=per_module,
                    slides_estimate=int(per_module * self.SLIDES_PER_MINUTE),
                    content_hints=module.headings[:5]
                ))

        # 添加结尾
        sections.append(Section(
            id='99-closing',
            title='总结与行动',
            type='closing',
            duration=int(total_duration * self.DURATION_RATIOS['closing']),
            slides_estimate=4,
            content_hints=['核心要点回顾', '行动建议', 'Q&A']
        ))

        return sections

    def _generate_sections_from_topics(self, topics: List[str]) -> List[Section]:
        """从主题列表生成章节"""
        sections = []
        total_duration = self.config.duration

        # 开场
        sections.append(Section(
            id='00-opening',
            title='开场',
            type='opening',
            duration=int(total_duration * 0.1),
            slides_estimate=3,
            content_hints=['欢迎', '议程']
        ))

        # 主题章节
        if topics:
            content_duration = int(total_duration * 0.8)
            per_topic = content_duration // len(topics)

            for i, topic in enumerate(topics):
                sections.append(Section(
                    id=f'{i+1:02d}-topic',
                    title=topic,
                    type='content',
                    duration=per_topic,
                    slides_estimate=int(per_topic * self.SLIDES_PER_MINUTE),
                    content_hints=[topic]
                ))

        # 结尾
        sections.append(Section(
            id='99-closing',
            title='总结',
            type='closing',
            duration=int(total_duration * 0.1),
            slides_estimate=3,
            content_hints=['回顾', 'Q&A']
        ))

        return sections

    def _infer_section_type(self, module: Module) -> str:
        """推断章节类型"""
        title_lower = module.title.lower()
        id_lower = module.id.lower()

        if any(k in title_lower or k in id_lower for k in ['案例', 'case', '实践']):
            return 'case-study'
        if any(k in title_lower or k in id_lower for k in ['框架', 'model', '模型', '路径']):
            return 'framework'
        if any(k in title_lower or k in id_lower for k in ['开场', 'opening', '认知']):
            return 'opening'
        if any(k in title_lower or k in id_lower for k in ['行动', 'closing', '总结']):
            return 'closing'

        return 'content'

    def _generate_research_needs(self):
        """生成研究需求"""
        if not self.context:
            return

        for section in self.sections:
            needs = []

            # 案例类型章节需要案例
            if section.type == 'case-study':
                # 检查现有案例数
                existing_cases = len([c for c in self.context.cases
                                     if section.id in c.source or section.title in c.source])
                if existing_cases < 3:
                    needs.append(ResearchNeed(
                        type='case_study',
                        query=f"{section.title}相关企业案例，要求有量化效果",
                        priority='high',
                        count=3 - existing_cases,
                        constraints={'region': '中国企业优先', 'time_range': '2024-2025'}
                    ))

            # 内容章节需要数据支撑
            if section.type in ['content', 'framework']:
                needs.append(ResearchNeed(
                    type='statistics',
                    query=f"{section.title}相关市场数据和趋势",
                    priority='medium'
                ))

            section.research_needs = needs

    def to_skeleton(self) -> Dict[str, Any]:
        """转换为 skeleton.yaml 格式"""
        skeleton = {
            'meta': {
                'title': self.config.title,
                'version': '1.0',
                'generated_by': 'ppt-outline',
                'generated_at': datetime.now().isoformat()
            },
            'audience': {
                'type': self.config.audience_type,
                'size': self.config.audience_size
            },
            'presentation': {
                'duration': self.config.duration,
                'occasion': self.config.occasion,
                'style': self.config.style
            },
            'structure': []
        }

        if self.config.subtitle:
            skeleton['meta']['subtitle'] = self.config.subtitle
        if self.config.author:
            skeleton['meta']['author'] = self.config.author

        for section in self.sections:
            s = {
                'id': section.id,
                'title': section.title,
                'type': section.type,
                'duration': section.duration,
                'slides_estimate': section.slides_estimate
            }

            if section.content_hints:
                s['content_hints'] = section.content_hints

            if section.research_needs:
                s['research_needs'] = [
                    {
                        'type': rn.type,
                        'query': rn.query,
                        'priority': rn.priority,
                        'count': rn.count,
                        'constraints': rn.constraints
                    }
                    for rn in section.research_needs
                    if rn.count > 0
                ]

            skeleton['structure'].append(s)

        return skeleton

    def save(self, output_path: str):
        """保存 skeleton.yaml"""
        skeleton = self.to_skeleton()
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(skeleton, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        return output_path


# CLI
if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python skeleton_generator.py <context_dir> [-o output.yaml]")
        print("  python skeleton_generator.py --brief brief.yaml [-o output.yaml]")
        sys.exit(1)

    output_path = 'skeleton.yaml'
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        output_path = sys.argv[idx + 1]

    if '--brief' in sys.argv:
        idx = sys.argv.index('--brief')
        brief_path = sys.argv[idx + 1]
        with open(brief_path, 'r', encoding='utf-8') as f:
            brief = yaml.safe_load(f)
        generator = SkeletonGenerator()
        skeleton = generator.generate_from_brief(brief)
    else:
        context_dir = sys.argv[1]
        scanner = ContextScanner(context_dir)
        context = scanner.scan()
        print(scanner.get_report())
        print()

        generator = SkeletonGenerator(context)
        skeleton = generator.generate_from_context()

    generator.save(output_path)
    print(f"Saved: {output_path}")
