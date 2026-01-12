#!/usr/bin/env python3
"""
Research Extractor
从骨架和上下文中提取研究需求
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path

from context_scanner import ContextScanner, ContextSummary


@dataclass
class ResearchRequest:
    """研究请求"""
    section_id: str
    section_title: str
    type: str  # case_study | statistics | quote | trend | comparison
    query: str
    priority: str  # high | medium | low
    count: int = 1
    constraints: Dict[str, str] = field(default_factory=dict)
    gap_reason: str = ""  # 为什么需要这个研究


class ResearchExtractor:
    """研究需求提取器"""

    # 内容充足度阈值
    MIN_CASES_PER_SECTION = 2
    MIN_DATA_POINTS_PER_SECTION = 3
    MIN_CHARS_PER_SECTION = 1500

    def __init__(self, skeleton_path: str, context: Optional[ContextSummary] = None):
        self.skeleton_path = skeleton_path
        self.context = context
        self.skeleton = self._load_skeleton()
        self.requests: List[ResearchRequest] = []

    def _load_skeleton(self) -> Dict[str, Any]:
        """加载骨架文件"""
        with open(self.skeleton_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def extract(self) -> List[ResearchRequest]:
        """提取所有研究需求"""
        self.requests = []

        # 1. 提取骨架中已标记的研究需求
        self._extract_from_skeleton()

        # 2. 分析上下文缺口，补充研究需求
        if self.context:
            self._analyze_gaps()

        # 3. 去重和优先级排序
        self._deduplicate_and_sort()

        return self.requests

    def _extract_from_skeleton(self):
        """从骨架提取已标记的研究需求"""
        for section in self.skeleton.get('structure', []):
            section_id = section.get('id', '')
            section_title = section.get('title', '')

            for rn in section.get('research_needs', []):
                self.requests.append(ResearchRequest(
                    section_id=section_id,
                    section_title=section_title,
                    type=rn.get('type', 'statistics'),
                    query=rn.get('query', ''),
                    priority=rn.get('priority', 'medium'),
                    count=rn.get('count', 1),
                    constraints=rn.get('constraints', {}),
                    gap_reason='skeleton_marked'
                ))

        # 全局研究需求
        for gr in self.skeleton.get('global_research', []):
            apply_to = gr.get('apply_to', ['*'])
            for section_id in apply_to:
                self.requests.append(ResearchRequest(
                    section_id=section_id,
                    section_title='global',
                    type=gr.get('type', 'statistics'),
                    query=gr.get('query', ''),
                    priority='high',
                    count=1,
                    gap_reason='global_research'
                ))

    def _analyze_gaps(self):
        """分析上下文缺口"""
        # 建立模块映射
        module_map = {m.id: m for m in self.context.modules}

        for section in self.skeleton.get('structure', []):
            section_id = section.get('id', '')
            section_title = section.get('title', '')
            section_type = section.get('type', 'content')

            # 查找对应的模块
            matching_module = None
            for mid, module in module_map.items():
                if mid in section_id or section_id in mid:
                    matching_module = module
                    break

            if not matching_module:
                # 没有对应文档，需要全面研究
                self._add_gap_requests(section_id, section_title, section_type,
                                       has_content=False, case_count=0, data_count=0)
                continue

            # 分析内容充足度
            self._add_gap_requests(
                section_id, section_title, section_type,
                has_content=matching_module.char_count >= self.MIN_CHARS_PER_SECTION,
                case_count=matching_module.case_count,
                data_count=matching_module.data_count
            )

    def _add_gap_requests(self, section_id: str, section_title: str, section_type: str,
                         has_content: bool, case_count: int, data_count: int):
        """根据缺口添加研究需求"""

        # 案例不足
        if section_type in ['case-study', 'content']:
            if case_count < self.MIN_CASES_PER_SECTION:
                needed = self.MIN_CASES_PER_SECTION - case_count
                self.requests.append(ResearchRequest(
                    section_id=section_id,
                    section_title=section_title,
                    type='case_study',
                    query=f"{section_title}相关企业应用案例，需包含量化效果和来源",
                    priority='high' if case_count == 0 else 'medium',
                    count=needed,
                    constraints={'time_range': '2024-2025'},
                    gap_reason=f'case_gap: have {case_count}, need {self.MIN_CASES_PER_SECTION}'
                ))

        # 数据不足
        if data_count < self.MIN_DATA_POINTS_PER_SECTION:
            self.requests.append(ResearchRequest(
                section_id=section_id,
                section_title=section_title,
                type='statistics',
                query=f"{section_title}相关市场数据、趋势统计",
                priority='medium',
                count=1,
                constraints={'source_type': '权威报告'},
                gap_reason=f'data_gap: have {data_count}'
            ))

        # 内容不足
        if not has_content:
            self.requests.append(ResearchRequest(
                section_id=section_id,
                section_title=section_title,
                type='trend',
                query=f"{section_title}领域发展趋势和关键洞察",
                priority='high',
                count=1,
                gap_reason='content_gap: no source document'
            ))

    def _deduplicate_and_sort(self):
        """去重和排序"""
        # 按 (section_id, type, query前20字) 去重
        seen = set()
        unique = []

        for req in self.requests:
            key = (req.section_id, req.type, req.query[:20])
            if key not in seen:
                seen.add(key)
                unique.append(req)

        # 按优先级排序
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        unique.sort(key=lambda r: (priority_order.get(r.priority, 1), r.section_id))

        self.requests = unique

    def to_json(self) -> List[Dict[str, Any]]:
        """转换为 JSON 格式"""
        return [
            {
                'section_id': r.section_id,
                'section_title': r.section_title,
                'type': r.type,
                'query': r.query,
                'priority': r.priority,
                'count': r.count,
                'constraints': r.constraints,
                'gap_reason': r.gap_reason
            }
            for r in self.requests
        ]

    def get_report(self) -> str:
        """生成报告"""
        lines = [
            "=" * 50,
            "Research Requirements Report",
            "=" * 50,
            f"Total requests: {len(self.requests)}",
            f"High priority: {len([r for r in self.requests if r.priority == 'high'])}",
            f"Medium priority: {len([r for r in self.requests if r.priority == 'medium'])}",
            "",
        ]

        current_section = None
        for req in self.requests:
            if req.section_id != current_section:
                current_section = req.section_id
                lines.append(f"\n[{req.section_id}] {req.section_title}")

            priority_mark = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(req.priority, '⚪')
            lines.append(f"  {priority_mark} [{req.type}] {req.query[:50]}...")
            if req.gap_reason:
                lines.append(f"     reason: {req.gap_reason}")

        lines.append("\n" + "=" * 50)
        return "\n".join(lines)

    def save(self, output_path: str):
        """保存研究需求"""
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_json(), f, ensure_ascii=False, indent=2)
        return output_path


# CLI
if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python research_extractor.py <skeleton.yaml> [--context <dir>] [-o output.json]")
        sys.exit(1)

    skeleton_path = sys.argv[1]
    context = None
    output_path = 'research_requests.json'

    if '--context' in sys.argv:
        idx = sys.argv.index('--context')
        context_dir = sys.argv[idx + 1]
        scanner = ContextScanner(context_dir)
        context = scanner.scan()

    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        output_path = sys.argv[idx + 1]

    extractor = ResearchExtractor(skeleton_path, context)
    requests = extractor.extract()

    print(extractor.get_report())
    extractor.save(output_path)
    print(f"\nSaved: {output_path}")
