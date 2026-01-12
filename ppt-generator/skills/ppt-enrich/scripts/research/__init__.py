#!/usr/bin/env python3
"""
Research Integration Module - ppt-enrich 研究集成

提供统一的研究接口，自动发现并使用 openai-deep-research skill，
不可用时优雅降级到 mock 数据。

Usage:
    from research import ResearchRunner

    runner = ResearchRunner(verbose=True)
    result = runner.execute({
        "section_id": "01-cases",
        "type": "case_study",
        "query": "AI manufacturing cases",
        "count": 3
    })
"""

import logging
from typing import Any, Callable, Dict, List, Optional

from .skill_discovery import SkillDiscovery, SkillInfo
from .deep_research_adapter import (
    DeepResearchAdapter,
    DeepResearchManager,
    ResearchResult,
    ResearchProgress,
)
from .markdown_parser import MarkdownParser
from .fallback import FallbackManager, FallbackReason, FallbackResult
from .image_generator import (
    NanoBananaImageAdapter,
    ImageGeneratorManager,
    ImageRequest,
    ImageResult,
)

__all__ = [
    "ResearchRunner",
    "SkillDiscovery",
    "SkillInfo",
    "DeepResearchAdapter",
    "DeepResearchManager",
    "ResearchResult",
    "ResearchProgress",
    "MarkdownParser",
    "FallbackManager",
    "FallbackReason",
    "FallbackResult",
    "NanoBananaImageAdapter",
    "ImageGeneratorManager",
    "ImageRequest",
    "ImageResult",
]

log = logging.getLogger("research")


class ResearchRunner:
    """研究执行器 - 主入口类

    编排 skill 发现、执行、解析、降级的完整流程。

    Features:
        - 自动发现 openai-deep-research skill
        - 优先使用 Deep Research，不可用时 fallback 到 mock
        - 将 Markdown 结果转换为结构化 JSON
        - 支持进度回调
    """

    DEFAULT_TIMEOUT = 2400  # 40 分钟
    DEFAULT_SESSION = "default"  # 复用已有的 openai-deep-research session

    def __init__(
        self,
        headless: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        session: str = DEFAULT_SESSION,
        verbose: bool = False,
        progress_callback: Optional[Callable[[ResearchProgress], None]] = None,
        force_mock: bool = False,
    ):
        """初始化研究执行器

        Args:
            headless: 是否使用无头模式（需要先 login）
            timeout: 研究超时时间（秒）
            session: 浏览器 session 名称
            verbose: 是否输出详细日志
            progress_callback: 进度回调函数
            force_mock: 强制使用 mock 模式（跳过 Deep Research）
        """
        self.headless = headless
        self.timeout = timeout
        self.session = session
        self.verbose = verbose
        self.progress_callback = progress_callback
        self.force_mock = force_mock

        # 初始化组件
        self.discovery = SkillDiscovery()
        self.parser = MarkdownParser()
        self.fallback = FallbackManager(verbose=verbose)

        # 延迟初始化适配器
        self._adapter: Optional[DeepResearchAdapter] = None
        self._skill_info: Optional[SkillInfo] = None

        if verbose:
            logging.basicConfig(level=logging.DEBUG)
            log.setLevel(logging.DEBUG)

    def _get_adapter(self) -> Optional[DeepResearchAdapter]:
        """获取 Deep Research 适配器（延迟初始化）"""
        if self.force_mock:
            log.info("Force mock mode enabled, skipping Deep Research")
            return None

        if self._adapter is None:
            self._skill_info = self.discovery.find_skill("openai-deep-research")

            if self._skill_info.available:
                log.info(f"Found openai-deep-research at: {self._skill_info.path}")
                self._adapter = DeepResearchAdapter(
                    skill_info=self._skill_info,
                    headless=self.headless,
                    timeout=self.timeout,
                    session=self.session,
                    verbose=self.verbose,
                    progress_callback=self.progress_callback,
                )
            else:
                log.warning("openai-deep-research not found")
                log.debug(f"Searched paths: {self._skill_info.search_paths_tried}")

        return self._adapter

    def is_deep_research_available(self) -> bool:
        """检查 Deep Research 是否可用"""
        adapter = self._get_adapter()
        if not adapter:
            return False
        checks = adapter.check_prerequisites()
        return checks.get("all_passed", False)

    def get_status(self) -> Dict[str, Any]:
        """获取研究模块状态"""
        adapter = self._get_adapter()

        status = {
            "deep_research_available": False,
            "skill_found": False,
            "has_session": False,
            "playwright_installed": False,
            "mode": "mock",
            "skill_path": None,
        }

        if adapter:
            checks = adapter.check_prerequisites()
            status.update({
                "deep_research_available": checks.get("all_passed", False),
                "skill_found": checks.get("skill_available", False),
                "has_session": checks.get("has_session", False),
                "playwright_installed": checks.get("playwright_installed", False),
                "mode": "browser" if checks.get("all_passed") else "mock",
                "skill_path": str(self._skill_info.path) if self._skill_info else None,
            })

        return status

    def execute(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """执行研究请求

        Args:
            request: 研究请求，包含:
                - section_id: 章节 ID
                - section_title: 章节标题
                - type: 请求类型 (case_study, statistics, trend, quote)
                - query: 查询文本
                - count: 需要的结果数量（可选）
                - constraints: 约束条件（可选）

        Returns:
            结构化的研究结果，格式取决于 request type
        """
        adapter = self._get_adapter()

        # 如果 Deep Research 不可用，直接 fallback
        if adapter is None:
            log.info("Deep Research not available, using mock data")
            result = self.fallback.handle_fallback(
                FallbackReason.SKILL_NOT_FOUND,
                request
            )
            return result.data

        # 检查前置条件
        checks = adapter.check_prerequisites()
        if not checks.get("all_passed", False):
            reason = self._determine_fallback_reason(checks)
            log.warning(f"Prerequisites check failed: {reason}")

            # 特别提示 session 问题
            if reason == FallbackReason.NO_SESSION:
                log.warning("=" * 60)
                log.warning("  首次使用 Deep Research 需要手动登录")
                log.warning("=" * 60)
                log.warning("  请运行以下命令登录您的 ChatGPT 账户：")
                log.warning("  python deep_research_browser.py --login")
                log.warning("")
                log.warning("  登录完成后，cookie 会自动保存，之后可以 headless 运行。")
                log.warning("=" * 60)

            result = self.fallback.handle_fallback(reason, request)
            return result.data

        # 构建查询
        query = self._build_query(request)
        log.info(f"Executing Deep Research query: {query[:100]}...")

        # 执行研究
        research_result = adapter.run_query(query)

        if not research_result.success:
            log.warning(f"Research failed: {research_result.error}")
            reason = FallbackManager.determine_reason(research_result.error or "")
            result = self.fallback.handle_fallback(
                reason, request, research_result.error
            )
            return result.data

        # 解析结果
        try:
            parsed = self.parser.parse(
                research_result.markdown,
                request.get("type", "statistics")
            )
            log.info(f"Successfully parsed research result")
            return parsed

        except Exception as e:
            log.error(f"Failed to parse research result: {e}")
            result = self.fallback.handle_fallback(
                FallbackReason.PARSE_ERROR,
                request,
                str(e)
            )
            return result.data

    def _build_query(self, request: Dict[str, Any]) -> str:
        """构建研究查询"""
        base_query = request.get("query", "")
        req_type = request.get("type", "")
        count = request.get("count", 3)
        constraints = request.get("constraints", {})

        # 根据类型构建详细查询
        if req_type == "case_study":
            query = f"""Research: {base_query}

Please provide {count} detailed case studies with:
- Company/organization name
- Industry sector
- Specific technology/AI application
- Quantitative metrics or outcomes (percentages, dollar amounts, improvements)
- Brief description of the implementation

Requirements:
- Focus on real companies with verifiable information
- Include specific numbers and metrics where available
- Prefer recent cases (2023-2025)
"""
            if constraints.get("region"):
                query += f"- Region preference: {constraints['region']}\n"
            if constraints.get("time_range"):
                query += f"- Time range: {constraints['time_range']}\n"

        elif req_type == "statistics":
            query = f"""Research: {base_query}

Please provide key statistics and market data including:
- Market size figures (in dollars)
- Growth rates (percentages)
- Adoption rates
- Year of the data
- Source references where available

Focus on authoritative sources like Gartner, McKinsey, IDC, etc.
"""

        elif req_type == "trend":
            query = f"""Research: {base_query}

Please provide key trends and insights including:
- Major industry trends
- Emerging technologies
- Market predictions
- Expert opinions

Focus on forward-looking analysis and actionable insights.
"""

        elif req_type == "quote":
            query = f"""Research: {base_query}

Please find relevant quotes from:
- Industry experts
- Company executives
- Research reports
- Thought leaders

Include the author/source and context for each quote.
"""

        else:
            query = base_query

        return query

    def _determine_fallback_reason(self, checks: Dict[str, Any]) -> FallbackReason:
        """根据检查结果确定降级原因"""
        if not checks.get("skill_available"):
            return FallbackReason.SKILL_NOT_FOUND
        if not checks.get("playwright_installed"):
            return FallbackReason.PLAYWRIGHT_MISSING
        if not checks.get("has_session") and self.headless:
            return FallbackReason.NO_SESSION
        return FallbackReason.UNKNOWN

    def execute_batch(
        self,
        requests: List[Dict[str, Any]],
        max_concurrent: int = 1
    ) -> List[Dict[str, Any]]:
        """批量执行研究请求

        注意：Deep Research 本身不支持真正的并发，
        此方法主要用于串行执行多个请求。

        Args:
            requests: 研究请求列表
            max_concurrent: 最大并发数（当前固定为1）

        Returns:
            结果列表
        """
        results = []
        total = len(requests)

        for i, request in enumerate(requests, 1):
            log.info(f"Processing request {i}/{total}: {request.get('section_id', 'unknown')}")
            result = self.execute(request)
            results.append(result)

        return results


# 便捷函数
def check_deep_research() -> Dict[str, Any]:
    """检查 Deep Research 是否可用"""
    runner = ResearchRunner()
    return runner.get_status()


def run_research(
    query: str,
    request_type: str = "statistics",
    timeout: int = 2400,
    verbose: bool = False
) -> Dict[str, Any]:
    """便捷的研究执行函数

    Args:
        query: 研究查询
        request_type: 请求类型
        timeout: 超时时间
        verbose: 详细输出

    Returns:
        结构化的研究结果
    """
    runner = ResearchRunner(timeout=timeout, verbose=verbose)
    return runner.execute({
        "query": query,
        "type": request_type,
        "count": 3
    })


# CLI
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Research Runner CLI")
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("--type", "-t", default="statistics",
                       choices=["case_study", "statistics", "trend", "quote"],
                       help="Request type")
    parser.add_argument("--count", "-n", type=int, default=3, help="Number of results")
    parser.add_argument("--timeout", type=int, default=2400, help="Timeout in seconds")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--mock", action="store_true", help="Force mock mode")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    runner = ResearchRunner(
        timeout=args.timeout,
        verbose=args.verbose,
        force_mock=args.mock
    )

    if args.status:
        status = runner.get_status()
        print("\nResearch Module Status:")
        print(f"  Mode: {status['mode']}")
        print(f"  Deep Research Available: {status['deep_research_available']}")
        print(f"  Skill Found: {status['skill_found']}")
        print(f"  Has Session: {status['has_session']}")
        print(f"  Playwright Installed: {status['playwright_installed']}")
        if status['skill_path']:
            print(f"  Skill Path: {status['skill_path']}")

    elif args.query:
        print(f"\nResearching: {args.query[:50]}...")
        result = runner.execute({
            "query": args.query,
            "type": args.type,
            "count": args.count
        })
        print(f"\nResult:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    else:
        parser.print_help()
