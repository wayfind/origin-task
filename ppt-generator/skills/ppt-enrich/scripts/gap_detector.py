#!/usr/bin/env python3
"""
Gap Detector
分析 skeleton 和上下文，检测内容空缺
"""

import yaml
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import sys

# 添加 ppt-outline 的路径以复用 context_scanner
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ppt-outline' / 'scripts'))
from context_scanner import ContextScanner, ContextSummary


@dataclass
class ContentGap:
    """内容空缺"""
    section_id: str
    section_title: str
    gap_type: str  # cases | stats | content | quotes
    current: int
    required: int
    severity: str  # critical | warning | info
    suggestion: str = ""


@dataclass
class SectionAnalysis:
    """章节分析结果"""
    section_id: str
    title: str
    type: str
    duration: int
    slides_estimate: int
    gaps: List[ContentGap] = field(default_factory=list)
    content_score: float = 0.0  # 0-100
    has_source_doc: bool = False
    source_chars: int = 0
    case_count: int = 0
    data_count: int = 0


class GapDetector:
    """内容空缺检测器"""

    # 内容充足度要求
    REQUIREMENTS = {
        'opening': {'cases': 0, 'stats': 2, 'chars_per_min': 200},
        'content': {'cases': 1, 'stats': 3, 'chars_per_min': 300},
        'case-study': {'cases': 3, 'stats': 2, 'chars_per_min': 250},
        'framework': {'cases': 1, 'stats': 2, 'chars_per_min': 300},
        'closing': {'cases': 0, 'stats': 1, 'chars_per_min': 150},
        'transition': {'cases': 0, 'stats': 0, 'chars_per_min': 50},
    }

    def __init__(self, skeleton_path: str, context_dir: str = None):
        self.skeleton_path = skeleton_path
        self.skeleton = self._load_skeleton()
        self.context = None

        if context_dir:
            scanner = ContextScanner(context_dir)
            self.context = scanner.scan()

    def _load_skeleton(self) -> Dict[str, Any]:
        """加载骨架文件"""
        with open(self.skeleton_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def analyze(self) -> List[SectionAnalysis]:
        """分析所有章节"""
        results = []

        for section in self.skeleton.get('structure', []):
            analysis = self._analyze_section(section)
            results.append(analysis)

        return results

    def _analyze_section(self, section: Dict[str, Any]) -> SectionAnalysis:
        """分析单个章节"""
        section_id = section.get('id', '')
        section_type = section.get('type', 'content')
        duration = section.get('duration', 10)

        # 创建分析结果
        analysis = SectionAnalysis(
            section_id=section_id,
            title=section.get('title', ''),
            type=section_type,
            duration=duration,
            slides_estimate=section.get('slides_estimate', 5)
        )

        # 获取要求
        reqs = self.REQUIREMENTS.get(section_type, self.REQUIREMENTS['content'])

        # 查找匹配的上下文模块
        if self.context:
            for module in self.context.modules:
                if self._match_module(section_id, module.id):
                    analysis.has_source_doc = True
                    analysis.source_chars = module.char_count
                    analysis.case_count = module.case_count
                    analysis.data_count = module.data_count
                    break

        # 检查案例空缺
        if reqs['cases'] > 0:
            if analysis.case_count < reqs['cases']:
                gap = reqs['cases'] - analysis.case_count
                severity = 'critical' if analysis.case_count == 0 else 'warning'
                analysis.gaps.append(ContentGap(
                    section_id=section_id,
                    section_title=analysis.title,
                    gap_type='cases',
                    current=analysis.case_count,
                    required=reqs['cases'],
                    severity=severity,
                    suggestion=f"需要补充 {gap} 个案例"
                ))

        # 检查数据空缺
        if reqs['stats'] > 0:
            if analysis.data_count < reqs['stats']:
                gap = reqs['stats'] - analysis.data_count
                severity = 'warning' if analysis.data_count > 0 else 'critical'
                analysis.gaps.append(ContentGap(
                    section_id=section_id,
                    section_title=analysis.title,
                    gap_type='stats',
                    current=analysis.data_count,
                    required=reqs['stats'],
                    severity=severity,
                    suggestion=f"需要补充 {gap} 个数据点"
                ))

        # 检查内容量
        required_chars = duration * reqs['chars_per_min']
        if analysis.source_chars < required_chars:
            severity = 'critical' if not analysis.has_source_doc else 'warning'
            analysis.gaps.append(ContentGap(
                section_id=section_id,
                section_title=analysis.title,
                gap_type='content',
                current=analysis.source_chars,
                required=required_chars,
                severity=severity,
                suggestion=f"内容不足（当前 {analysis.source_chars} 字，建议 {required_chars} 字）"
            ))

        # 计算内容分数
        analysis.content_score = self._calculate_score(analysis, reqs)

        return analysis

    def _match_module(self, section_id: str, module_id: str) -> bool:
        """匹配章节和模块"""
        # 简单匹配逻辑
        s_clean = section_id.lower().replace('-', '').replace('_', '')
        m_clean = module_id.lower().replace('-', '').replace('_', '')

        return s_clean in m_clean or m_clean in s_clean

    def _calculate_score(self, analysis: SectionAnalysis, reqs: Dict) -> float:
        """计算内容充足度分数"""
        scores = []

        # 案例分数
        if reqs['cases'] > 0:
            case_score = min(100, (analysis.case_count / reqs['cases']) * 100)
            scores.append(case_score)

        # 数据分数
        if reqs['stats'] > 0:
            stat_score = min(100, (analysis.data_count / reqs['stats']) * 100)
            scores.append(stat_score)

        # 内容分数
        required_chars = analysis.duration * reqs['chars_per_min']
        if required_chars > 0:
            char_score = min(100, (analysis.source_chars / required_chars) * 100)
            scores.append(char_score)

        return sum(scores) / len(scores) if scores else 0

    def get_all_gaps(self) -> List[ContentGap]:
        """获取所有空缺"""
        all_gaps = []
        for analysis in self.analyze():
            all_gaps.extend(analysis.gaps)
        return all_gaps

    def get_research_requests(self) -> List[Dict[str, Any]]:
        """生成研究请求"""
        requests = []

        for analysis in self.analyze():
            for gap in analysis.gaps:
                if gap.gap_type == 'cases' and gap.current < gap.required:
                    requests.append({
                        'section_id': gap.section_id,
                        'type': 'case_study',
                        'query': f"{analysis.title}相关企业案例，需包含量化效果",
                        'count': gap.required - gap.current,
                        'priority': 'high' if gap.severity == 'critical' else 'medium'
                    })
                elif gap.gap_type == 'stats' and gap.current < gap.required:
                    requests.append({
                        'section_id': gap.section_id,
                        'type': 'statistics',
                        'query': f"{analysis.title}相关市场数据和趋势统计",
                        'count': 1,
                        'priority': 'medium'
                    })

        return requests

    def get_report(self) -> str:
        """生成报告"""
        analyses = self.analyze()

        lines = [
            "=" * 60,
            "Content Gap Analysis Report",
            "=" * 60,
        ]

        total_gaps = 0
        critical_gaps = 0

        for analysis in analyses:
            status = "✓" if not analysis.gaps else "✗"
            score_bar = "█" * int(analysis.content_score / 10) + "░" * (10 - int(analysis.content_score / 10))

            lines.append(f"\n{status} [{analysis.section_id}] {analysis.title}")
            lines.append(f"   Type: {analysis.type}, Duration: {analysis.duration}min")
            lines.append(f"   Score: [{score_bar}] {analysis.content_score:.0f}%")

            if analysis.has_source_doc:
                lines.append(f"   Source: {analysis.source_chars:,} chars, {analysis.case_count} cases, {analysis.data_count} data")
            else:
                lines.append("   Source: No matching document")

            for gap in analysis.gaps:
                icon = "🔴" if gap.severity == 'critical' else "🟡"
                lines.append(f"   {icon} {gap.gap_type}: {gap.current}/{gap.required} - {gap.suggestion}")
                total_gaps += 1
                if gap.severity == 'critical':
                    critical_gaps += 1

        lines.extend([
            "\n" + "-" * 60,
            f"Summary: {total_gaps} gaps ({critical_gaps} critical)",
            "=" * 60
        ])

        return "\n".join(lines)


# CLI
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='检测内容空缺')
    parser.add_argument('skeleton', help='skeleton.yaml 文件')
    parser.add_argument('-c', '--context', help='上下文目录')
    parser.add_argument('--json', action='store_true', help='JSON 输出')

    args = parser.parse_args()

    detector = GapDetector(args.skeleton, args.context)

    if args.json:
        import json
        analyses = detector.analyze()
        output = [{
            'section_id': a.section_id,
            'title': a.title,
            'score': a.content_score,
            'gaps': [{
                'type': g.gap_type,
                'current': g.current,
                'required': g.required,
                'severity': g.severity
            } for g in a.gaps]
        } for a in analyses]
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print(detector.get_report())
