#!/usr/bin/env python3
"""
Context Scanner
扫描文档目录，提取结构、案例、数据点等信息
"""

import os
import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class CaseStudy:
    """案例数据"""
    title: str
    company: str = ""
    industry: str = ""
    content: List[str] = field(default_factory=list)
    metrics: List[str] = field(default_factory=list)
    source: str = ""


@dataclass
class DataPoint:
    """数据点"""
    value: str
    context: str
    source: str = ""


@dataclass
class Module:
    """模块/章节"""
    id: str
    title: str
    file_path: str
    char_count: int = 0
    case_count: int = 0
    data_count: int = 0
    headings: List[str] = field(default_factory=list)


@dataclass
class ContextSummary:
    """上下文扫描结果"""
    root_dir: str
    meta: Dict[str, Any] = field(default_factory=dict)
    modules: List[Module] = field(default_factory=list)
    cases: List[CaseStudy] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)
    quotes: List[str] = field(default_factory=list)
    total_chars: int = 0
    file_count: int = 0


class ContextScanner:
    """上下文扫描器"""

    # 文件权重
    FILE_WEIGHTS = {
        '_meta.yaml': 100,
        '课程计划.md': 90,
        'README.md': 85,
    }

    # 数据模式
    DATA_PATTERNS = [
        r'\d+(?:\.\d+)?%',           # 百分比
        r'\d+(?:\.\d+)?倍',           # 倍数
        r'\d+(?:,\d{3})*(?:\.\d+)?[万亿]',  # 万/亿
        r'\$\d+(?:,\d{3})*(?:\.\d+)?[BMK]?',  # 美元
        r'¥\d+(?:,\d{3})*(?:\.\d+)?',  # 人民币
    ]

    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.summary = ContextSummary(root_dir=str(self.root_dir))

    def scan(self) -> ContextSummary:
        """执行扫描"""
        # 1. 扫描元数据
        self._scan_meta()

        # 2. 扫描 Markdown 文件
        self._scan_markdown_files()

        # 3. 扫描调研目录
        self._scan_research_dirs()

        return self.summary

    def _scan_meta(self):
        """扫描元数据文件"""
        meta_path = self.root_dir / '_meta.yaml'
        if meta_path.exists():
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    self.summary.meta = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to parse _meta.yaml: {e}")

    def _scan_markdown_files(self):
        """扫描 Markdown 文件"""
        md_files = sorted(self.root_dir.glob('*.md'))

        for md_file in md_files:
            if md_file.name.startswith('_'):
                continue

            self.summary.file_count += 1

            try:
                content = md_file.read_text(encoding='utf-8')
                self.summary.total_chars += len(content)

                # 解析模块
                module = self._parse_module(md_file, content)
                self.summary.modules.append(module)

                # 提取案例
                cases = self._extract_cases(content, str(md_file))
                self.summary.cases.extend(cases)
                module.case_count = len(cases)

                # 提取数据点
                data_points = self._extract_data_points(content, str(md_file))
                self.summary.data_points.extend(data_points)
                module.data_count = len(data_points)

                # 提取引用
                quotes = self._extract_quotes(content)
                self.summary.quotes.extend(quotes)

            except Exception as e:
                print(f"Warning: Failed to parse {md_file}: {e}")

    def _parse_module(self, file_path: Path, content: str) -> Module:
        """解析模块信息"""
        # 提取模块 ID
        module_id = file_path.stem

        # 提取标题
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else module_id

        # 提取所有标题
        headings = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)

        return Module(
            id=module_id,
            title=title,
            file_path=str(file_path),
            char_count=len(content),
            headings=headings[:10]  # 最多10个
        )

    def _extract_cases(self, content: str, source: str) -> List[CaseStudy]:
        """提取案例"""
        cases = []

        # 模式1: ### 案例: 或 ### Case:
        case_pattern = r'###\s*(?:案例|Case)[:：]\s*(.+?)(?=\n###|\n##|\Z)'
        for match in re.finditer(case_pattern, content, re.DOTALL):
            case_content = match.group(1).strip()
            lines = case_content.split('\n')

            title = lines[0].strip() if lines else ""
            content_lines = [l.strip('- ').strip() for l in lines[1:] if l.strip()]

            # 提取指标
            metrics = []
            for line in content_lines:
                for pattern in self.DATA_PATTERNS:
                    found = re.findall(pattern, line)
                    metrics.extend(found)

            cases.append(CaseStudy(
                title=title,
                content=content_lines[:5],
                metrics=metrics[:3],
                source=source
            ))

        # 模式2: 公司名 + 描述模式
        company_pattern = r'(?:【|「)([^】」]+)(?:】|」)[：:]\s*(.+?)(?=\n[-*]|\n\n|\Z)'
        for match in re.finditer(company_pattern, content, re.DOTALL):
            company = match.group(1).strip()
            desc = match.group(2).strip()

            # 提取指标
            metrics = []
            for pattern in self.DATA_PATTERNS:
                found = re.findall(pattern, desc)
                metrics.extend(found)

            if metrics:  # 只有包含数据的才算案例
                cases.append(CaseStudy(
                    title=company,
                    company=company,
                    content=[desc[:200]],
                    metrics=metrics[:3],
                    source=source
                ))

        return cases

    def _extract_data_points(self, content: str, source: str) -> List[DataPoint]:
        """提取数据点"""
        data_points = []

        for pattern in self.DATA_PATTERNS:
            for match in re.finditer(pattern, content):
                value = match.group()
                # 获取上下文（前后50个字符）
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].replace('\n', ' ').strip()

                data_points.append(DataPoint(
                    value=value,
                    context=context,
                    source=source
                ))

        return data_points

    def _extract_quotes(self, content: str) -> List[str]:
        """提取引用"""
        quotes = []

        # 模式: > "..." 或 > 「...」
        quote_pattern = r'^>\s*["""「](.+?)["""」]'
        for match in re.finditer(quote_pattern, content, re.MULTILINE):
            quote = match.group(1).strip()
            if len(quote) > 10:  # 过滤太短的
                quotes.append(quote)

        return quotes

    def _scan_research_dirs(self):
        """扫描调研目录"""
        for ds_dir in self.root_dir.glob('*-ds'):
            if ds_dir.is_dir():
                # 可以扩展：解析 .docx 文件
                pass

    def get_report(self) -> str:
        """生成扫描报告"""
        lines = [
            "=" * 50,
            "Context Scan Report",
            "=" * 50,
            f"Root: {self.summary.root_dir}",
            f"Files: {self.summary.file_count}",
            f"Total chars: {self.summary.total_chars:,}",
            "",
            "Modules:",
        ]

        for m in self.summary.modules:
            lines.append(f"  - {m.id}: {m.title}")
            lines.append(f"    chars: {m.char_count:,}, cases: {m.case_count}, data: {m.data_count}")

        lines.extend([
            "",
            f"Cases found: {len(self.summary.cases)}",
            f"Data points: {len(self.summary.data_points)}",
            f"Quotes: {len(self.summary.quotes)}",
            "=" * 50,
        ])

        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'root_dir': self.summary.root_dir,
            'meta': self.summary.meta,
            'file_count': self.summary.file_count,
            'total_chars': self.summary.total_chars,
            'modules': [
                {
                    'id': m.id,
                    'title': m.title,
                    'file_path': m.file_path,
                    'char_count': m.char_count,
                    'case_count': m.case_count,
                    'data_count': m.data_count,
                    'headings': m.headings
                }
                for m in self.summary.modules
            ],
            'cases': [
                {
                    'title': c.title,
                    'company': c.company,
                    'content': c.content,
                    'metrics': c.metrics,
                    'source': c.source
                }
                for c in self.summary.cases
            ],
            'data_point_count': len(self.summary.data_points),
            'quote_count': len(self.summary.quotes)
        }


# CLI
if __name__ == '__main__':
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python context_scanner.py <directory> [--json]")
        sys.exit(1)

    scanner = ContextScanner(sys.argv[1])
    summary = scanner.scan()

    if '--json' in sys.argv:
        print(json.dumps(scanner.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(scanner.get_report())
