#!/usr/bin/env python3
"""
Markdown Parser - 将 Deep Research 的 Markdown 输出转换为结构化 JSON

支持提取：
- case_study: 企业案例（公司名、行业、应用、指标）
- statistics: 统计数据（指标、数值、年份）
- trend: 趋势洞察
- quote: 引用
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ParsedCase:
    """解析后的案例"""
    company: str
    industry: str = ""
    application: str = ""
    metrics: List[str] = field(default_factory=list)
    description: str = ""
    source: str = "Deep Research"


@dataclass
class ParsedStatistic:
    """解析后的统计数据"""
    metric: str
    value: str
    year: str = ""
    source: str = ""


class MarkdownParser:
    """Markdown 解析器"""

    # 标题模式
    HEADING_PATTERN = re.compile(r'^#{1,4}\s+(.+)$', re.MULTILINE)

    # 案例模式
    CASE_PATTERNS = [
        # ## Company Name 或 ### Company Name
        re.compile(r'^#{2,3}\s+(?:\d+\.\s*)?(.+?)(?:\s*[-–—:：]|$)', re.MULTILINE),
        # **Company Name** - description
        re.compile(r'\*\*([^*]+)\*\*\s*[-–—:：]\s*(.+)', re.MULTILINE),
        # - **Company**: description
        re.compile(r'[-•]\s*\*\*([^*]+)\*\*[：:]\s*(.+)', re.MULTILINE),
        # 1. Company Name: description
        re.compile(r'^\d+\.\s+([^:：\n]+)[：:]\s*(.+)', re.MULTILINE),
    ]

    # 指标模式
    METRIC_PATTERNS = [
        re.compile(r'(\d+(?:\.\d+)?)\s*%'),  # 百分比
        re.compile(r'\$\s*(\d+(?:\.\d+)?)\s*([BMKbmk](?:illion)?)?'),  # 金额
        re.compile(r'(\d+(?:\.\d+)?)\s*[xX倍]'),  # 倍数
        re.compile(r'[+\-]\s*(\d+(?:\.\d+)?)\s*%'),  # 增减百分比
        re.compile(r'(\d{4})年?'),  # 年份
    ]

    # 统计数据模式
    STAT_PATTERNS = [
        # Market size: $150B (2024)
        re.compile(r'(.+?)[：:]\s*\$?\s*([\d,.]+\s*[BMK%]?)\s*(?:\((\d{4})\))?'),
        # $150 billion in 2024
        re.compile(r'\$?\s*([\d,.]+)\s*(billion|million|B|M|K)?\s*(?:in\s+)?(\d{4})?'),
        # 35% growth rate
        re.compile(r'([\d,.]+)\s*%\s*(.+?)(?:\((\d{4})\))?'),
    ]

    # 行业关键词
    INDUSTRIES = [
        "科技", "技术", "Technology", "Tech",
        "制造", "制造业", "Manufacturing",
        "金融", "银行", "Finance", "Banking", "FinTech",
        "医疗", "健康", "Healthcare", "Medical",
        "零售", "电商", "Retail", "E-commerce",
        "教育", "Education",
        "汽车", "Automotive",
        "能源", "Energy",
        "物流", "Logistics",
        "通信", "Telecom",
    ]

    def __init__(self):
        self.industry_pattern = re.compile(
            r'\b(' + '|'.join(self.INDUSTRIES) + r')\b',
            re.IGNORECASE
        )

    def parse(self, markdown: str, request_type: str) -> Dict[str, Any]:
        """解析 Markdown，返回结构化数据"""
        if not markdown or not markdown.strip():
            return {"type": request_type, "data": [], "_empty": True}

        if request_type == "case_study":
            return self._extract_cases(markdown)
        elif request_type == "statistics":
            return self._extract_statistics(markdown)
        elif request_type == "trend":
            return self._extract_trends(markdown)
        elif request_type == "quote":
            return self._extract_quotes(markdown)
        else:
            # 通用提取
            return self._extract_generic(markdown, request_type)

    def _extract_cases(self, markdown: str) -> Dict[str, Any]:
        """提取案例"""
        cases: List[Dict[str, Any]] = []
        sections = self._split_sections(markdown)

        for section in sections:
            case = self._parse_case_section(section)
            if case and case.company:
                cases.append({
                    "company": case.company,
                    "industry": case.industry,
                    "application": case.application,
                    "metrics": case.metrics,
                    "source": case.source
                })

        # 如果没有找到结构化案例，尝试从列表项提取
        if not cases:
            cases = self._extract_cases_from_list(markdown)

        return {
            "type": "case_study",
            "cases": cases,
            "_parsed": True
        }

    def _split_sections(self, markdown: str) -> List[str]:
        """按标题分割文档"""
        sections = []
        current = []
        lines = markdown.split('\n')

        for line in lines:
            if re.match(r'^#{2,3}\s+', line) and current:
                sections.append('\n'.join(current))
                current = [line]
            else:
                current.append(line)

        if current:
            sections.append('\n'.join(current))

        return sections

    def _parse_case_section(self, section: str) -> Optional[ParsedCase]:
        """解析单个案例章节"""
        lines = section.strip().split('\n')
        if not lines:
            return None

        # 提取标题（公司名）
        title_match = re.match(r'^#{2,3}\s+(?:\d+\.\s*)?(.+?)(?:\s*[-–—].*)?$', lines[0])
        if not title_match:
            return None

        company = title_match.group(1).strip()
        if not company or len(company) < 2:
            return None

        # 跳过通用标题
        skip_titles = ['summary', 'overview', 'conclusion', 'introduction',
                      '总结', '概述', '结论', '引言', 'key findings', 'case study',
                      'case studies', 'examples', 'references']
        if company.lower() in skip_titles:
            return None

        case = ParsedCase(company=company)

        # 提取内容
        content = '\n'.join(lines[1:])

        # 提取行业
        industry_match = self.industry_pattern.search(content)
        if industry_match:
            case.industry = industry_match.group(1)

        # 提取指标
        case.metrics = self._extract_metrics(content)

        # 提取应用描述（第一段非空内容）
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                case.application = line[:200]  # 限制长度
                break

        return case

    def _extract_cases_from_list(self, markdown: str) -> List[Dict[str, Any]]:
        """从列表项提取案例"""
        cases = []

        for pattern in self.CASE_PATTERNS:
            matches = pattern.findall(markdown)
            for match in matches:
                if isinstance(match, tuple):
                    company = match[0].strip()
                    description = match[1].strip() if len(match) > 1 else ""
                else:
                    company = match.strip()
                    description = ""

                # 过滤无效公司名
                if not company or len(company) < 2:
                    continue
                if company.lower() in ['the', 'a', 'an', 'this', 'that']:
                    continue

                metrics = self._extract_metrics(description)

                cases.append({
                    "company": company,
                    "industry": "",
                    "application": description[:200] if description else "",
                    "metrics": metrics,
                    "source": "Deep Research"
                })

        # 去重
        seen = set()
        unique_cases = []
        for case in cases:
            key = case["company"].lower()
            if key not in seen:
                seen.add(key)
                unique_cases.append(case)

        return unique_cases[:10]  # 最多返回10个

    def _extract_metrics(self, text: str) -> List[str]:
        """提取指标"""
        metrics = []

        # 百分比
        for match in re.finditer(r'[+\-]?\s*(\d+(?:\.\d+)?)\s*%', text):
            full = match.group(0).strip()
            metrics.append(full)

        # 金额
        for match in re.finditer(r'\$\s*(\d+(?:\.\d+)?)\s*([BMK](?:illion)?)?', text):
            full = match.group(0).strip()
            metrics.append(full)

        # 倍数
        for match in re.finditer(r'(\d+(?:\.\d+)?)\s*[xX倍]', text):
            full = match.group(0).strip()
            metrics.append(full)

        return list(set(metrics))[:5]  # 去重，最多5个

    def _extract_statistics(self, markdown: str) -> Dict[str, Any]:
        """提取统计数据"""
        stats: List[Dict[str, Any]] = []

        # 按行扫描
        for line in markdown.split('\n'):
            line = line.strip()
            if not line:
                continue

            # 尝试各种模式
            stat = self._parse_stat_line(line)
            if stat:
                stats.append({
                    "metric": stat.metric,
                    "value": stat.value,
                    "year": stat.year,
                    "source": stat.source
                })

        # 去重
        seen = set()
        unique_stats = []
        for stat in stats:
            key = f"{stat['metric']}:{stat['value']}"
            if key not in seen:
                seen.add(key)
                unique_stats.append(stat)

        return {
            "type": "statistics",
            "data": unique_stats[:15],  # 最多15个
            "_parsed": True
        }

    def _parse_stat_line(self, line: str) -> Optional[ParsedStatistic]:
        """解析单行统计数据"""
        # 模式1: Metric: Value (Year)
        match = re.search(r'([^:：]+)[：:]\s*\$?\s*([\d,.]+\s*(?:billion|million|B|M|K|%)?)\s*(?:\((\d{4})\))?', line, re.IGNORECASE)
        if match:
            return ParsedStatistic(
                metric=match.group(1).strip(),
                value=match.group(2).strip(),
                year=match.group(3) or ""
            )

        # 模式2: $XXX billion market
        match = re.search(r'\$\s*([\d,.]+)\s*(billion|million|B|M)?\s+(.+?)(?:market|size|value)?', line, re.IGNORECASE)
        if match:
            value = match.group(1)
            unit = match.group(2) or ""
            context = match.group(3).strip()
            return ParsedStatistic(
                metric=context or "Market Size",
                value=f"${value}{unit}"
            )

        # 模式3: XX% of something
        match = re.search(r'([\d,.]+)\s*%\s+(?:of\s+)?(.+)', line, re.IGNORECASE)
        if match:
            return ParsedStatistic(
                metric=match.group(2).strip()[:50],
                value=f"{match.group(1)}%"
            )

        return None

    def _extract_trends(self, markdown: str) -> Dict[str, Any]:
        """提取趋势"""
        trends = []

        # 提取列表项
        for match in re.finditer(r'^[-•*]\s+(.+)$', markdown, re.MULTILINE):
            trend = match.group(1).strip()
            if len(trend) > 20:  # 过滤太短的项
                trends.append(trend)

        # 如果没有列表项，提取段落
        if not trends:
            paragraphs = re.split(r'\n\n+', markdown)
            for p in paragraphs:
                p = p.strip()
                if p and not p.startswith('#') and len(p) > 50:
                    trends.append(p[:300])

        return {
            "type": "trend",
            "trends": trends[:10],
            "_parsed": True
        }

    def _extract_quotes(self, markdown: str) -> Dict[str, Any]:
        """提取引用"""
        quotes = []

        # 模式1: > quote
        for match in re.finditer(r'^>\s*(.+)$', markdown, re.MULTILINE):
            quotes.append({
                "text": match.group(1).strip(),
                "author": "",
                "source": "Deep Research"
            })

        # 模式2: "quote" - Author
        for match in re.finditer(r'"([^"]+)"\s*[-–—]\s*(.+)', markdown):
            quotes.append({
                "text": match.group(1).strip(),
                "author": match.group(2).strip(),
                "source": "Deep Research"
            })

        return {
            "type": "quote",
            "quotes": quotes[:5],
            "_parsed": True
        }

    def _extract_generic(self, markdown: str, request_type: str) -> Dict[str, Any]:
        """通用提取"""
        # 提取所有列表项
        items = []
        for match in re.finditer(r'^[-•*]\s+(.+)$', markdown, re.MULTILINE):
            items.append(match.group(1).strip())

        # 提取所有标题
        headings = []
        for match in self.HEADING_PATTERN.finditer(markdown):
            headings.append(match.group(1).strip())

        return {
            "type": request_type,
            "items": items[:20],
            "headings": headings[:10],
            "_parsed": True,
            "_generic": True
        }


# CLI 测试
if __name__ == "__main__":
    parser = MarkdownParser()

    test_markdown = """
# Deep Research: AI Manufacturing Cases

## Tesla

Tesla has implemented AI-powered quality control systems achieving +30% defect detection improvement.

Industry: Automotive, Manufacturing
Metrics: 30% improvement, $50M savings

## Siemens

Siemens Digital Industries uses predictive maintenance AI across 200+ factories.

- 25% reduction in downtime
- $100M annual savings
- 15% efficiency improvement

## Key Statistics

- AI market size: $150 billion (2024)
- Manufacturing AI adoption: 35%
- Expected growth rate: 28% CAGR
"""

    print("=== Case Study Extraction ===")
    result = parser.parse(test_markdown, "case_study")
    for case in result.get("cases", []):
        print(f"\n{case['company']}:")
        print(f"  Industry: {case['industry']}")
        print(f"  Application: {case['application'][:50]}...")
        print(f"  Metrics: {case['metrics']}")

    print("\n=== Statistics Extraction ===")
    result = parser.parse(test_markdown, "statistics")
    for stat in result.get("data", []):
        print(f"  {stat['metric']}: {stat['value']}")
