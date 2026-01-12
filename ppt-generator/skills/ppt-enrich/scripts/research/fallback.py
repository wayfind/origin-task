#!/usr/bin/env python3
"""
Fallback Manager - 研究降级策略

当 deep research 不可用时，提供优雅的降级方案。
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

log = logging.getLogger("research.fallback")


class FallbackReason(Enum):
    """降级原因"""
    SKILL_NOT_FOUND = "openai-deep-research skill not found"
    NO_SESSION = "No valid browser session (run --login first)"
    PLAYWRIGHT_MISSING = "playwright not installed"
    TIMEOUT = "Research timeout exceeded"
    NETWORK_ERROR = "Network error during research"
    PARSE_ERROR = "Failed to parse research results"
    PROCESS_ERROR = "Research process failed"
    UNKNOWN = "Unknown error"


@dataclass
class FallbackResult:
    """降级结果"""
    reason: FallbackReason
    data: Dict[str, Any]
    warning: str
    suggestion: str


class FallbackManager:
    """降级管理器"""

    # 降级建议
    SUGGESTIONS = {
        FallbackReason.SKILL_NOT_FOUND: (
            "Install openai-deep-research skill from intent-engine plugin"
        ),
        FallbackReason.NO_SESSION: (
            "首次使用需要手动登录 ChatGPT 以保存 cookie。\n"
            "请运行: python deep_research_browser.py --login\n"
            "在浏览器中登录您的 ChatGPT 账户，完成后会自动保存 session。"
        ),
        FallbackReason.PLAYWRIGHT_MISSING: (
            "Run: pip install playwright && playwright install chromium"
        ),
        FallbackReason.TIMEOUT: (
            "Try a more specific query or increase timeout"
        ),
        FallbackReason.NETWORK_ERROR: (
            "Check network connection and ChatGPT availability"
        ),
        FallbackReason.PARSE_ERROR: (
            "Research completed but result format was unexpected"
        ),
        FallbackReason.PROCESS_ERROR: (
            "Check logs for detailed error information"
        ),
        FallbackReason.UNKNOWN: (
            "Check logs for detailed error information"
        ),
    }

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if verbose:
            log.setLevel(logging.DEBUG)

    def handle_fallback(
        self,
        reason: FallbackReason,
        original_request: Dict[str, Any],
        error_detail: Optional[str] = None
    ) -> FallbackResult:
        """处理降级，返回 mock 数据"""
        warning = self._build_warning(reason, error_detail)
        suggestion = self.SUGGESTIONS.get(reason, "")

        # 记录警告
        log.warning(f"[Fallback] {reason.value}")
        if error_detail:
            log.warning(f"  Detail: {error_detail}")
        log.warning(f"  Suggestion: {suggestion}")
        log.warning("  Using mock data instead")

        # 生成 mock 数据
        mock_data = self._generate_mock_data(original_request)

        return FallbackResult(
            reason=reason,
            data=mock_data,
            warning=warning,
            suggestion=suggestion
        )

    def _build_warning(
        self,
        reason: FallbackReason,
        error_detail: Optional[str]
    ) -> str:
        """构建警告消息"""
        warning = f"[Research Fallback] {reason.value}"
        if error_detail:
            warning += f": {error_detail}"
        return warning

    def _generate_mock_data(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """生成 mock 数据"""
        request_type = request.get("type", "statistics")
        section_title = request.get("section_title", "")
        count = request.get("count", 3)

        if request_type == "case_study":
            return self._mock_case_study(section_title, count)
        elif request_type == "statistics":
            return self._mock_statistics(section_title)
        elif request_type == "trend":
            return self._mock_trend(section_title)
        elif request_type == "quote":
            return self._mock_quote(section_title)
        else:
            return {"type": request_type, "data": [], "_mock": True}

    def _mock_case_study(self, title: str, count: int) -> Dict[str, Any]:
        """生成 mock 案例数据"""
        cases = []
        industries = ["科技", "制造", "金融", "医疗", "零售"]
        applications = ["智能客服", "预测分析", "流程自动化", "质量检测", "个性化推荐"]

        for i in range(min(count, 5)):
            cases.append({
                "company": f"示例企业{i+1}",
                "industry": industries[i % len(industries)],
                "application": f"{title}相关的{applications[i % len(applications)]}",
                "metrics": [f"+{20 + i * 5}% 效率提升", f"-{15 + i * 3}% 成本降低"],
                "source": "[Mock Data - 请使用 Deep Research 获取真实案例]"
            })

        return {
            "type": "case_study",
            "cases": cases,
            "_mock": True,
            "_warning": "This is mock data. Enable browser research for real results."
        }

    def _mock_statistics(self, title: str) -> Dict[str, Any]:
        """生成 mock 统计数据"""
        return {
            "type": "statistics",
            "data": [
                {"metric": f"{title}市场规模", "value": "$XXX亿", "year": "2025"},
                {"metric": "年增长率", "value": "XX%", "year": "2025"},
                {"metric": "企业采用率", "value": "XX%", "year": "2025"},
            ],
            "_mock": True,
            "_warning": "This is mock data. Enable browser research for real statistics."
        }

    def _mock_trend(self, title: str) -> Dict[str, Any]:
        """生成 mock 趋势数据"""
        return {
            "type": "trend",
            "trends": [
                f"{title}领域正在快速发展",
                "企业加速数字化转型",
                "AI 应用场景持续扩展",
            ],
            "_mock": True,
            "_warning": "This is mock data. Enable browser research for real trends."
        }

    def _mock_quote(self, title: str) -> Dict[str, Any]:
        """生成 mock 引用数据"""
        return {
            "type": "quote",
            "quotes": [
                {
                    "text": f"关于{title}的精彩观点",
                    "author": "行业专家",
                    "source": "[Mock Data]"
                }
            ],
            "_mock": True,
            "_warning": "This is mock data. Enable browser research for real quotes."
        }

    @staticmethod
    def determine_reason(error: str) -> FallbackReason:
        """从错误信息推断降级原因"""
        error_lower = error.lower()

        if "not found" in error_lower or "not installed" in error_lower:
            return FallbackReason.SKILL_NOT_FOUND
        elif "session" in error_lower or "login" in error_lower:
            return FallbackReason.NO_SESSION
        elif "playwright" in error_lower or "chromium" in error_lower:
            return FallbackReason.PLAYWRIGHT_MISSING
        elif "timeout" in error_lower:
            return FallbackReason.TIMEOUT
        elif "network" in error_lower or "connection" in error_lower:
            return FallbackReason.NETWORK_ERROR
        elif "parse" in error_lower or "json" in error_lower:
            return FallbackReason.PARSE_ERROR
        elif "process" in error_lower or "subprocess" in error_lower:
            return FallbackReason.PROCESS_ERROR
        else:
            return FallbackReason.UNKNOWN


# CLI 测试
if __name__ == "__main__":
    manager = FallbackManager(verbose=True)

    test_request = {
        "section_id": "01-cases",
        "section_title": "AI应用",
        "type": "case_study",
        "query": "AI manufacturing cases",
        "count": 3
    }

    result = manager.handle_fallback(
        FallbackReason.SKILL_NOT_FOUND,
        test_request
    )

    print(f"\nFallback Result:")
    print(f"  Reason: {result.reason}")
    print(f"  Warning: {result.warning}")
    print(f"  Suggestion: {result.suggestion}")
    print(f"  Data: {result.data}")
