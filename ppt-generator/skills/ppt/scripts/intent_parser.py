#!/usr/bin/env python3
"""
Intent Parser
从自然语言或上下文识别用户意图
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class PPTIntent:
    """PPT 生成意图"""
    # 输入类型
    input_type: str = "unknown"  # context | natural_language | skeleton | resume

    # 基本参数
    title: str = ""
    duration: int = 30
    audience: str = "professionals"
    occasion: str = "conference"
    theme: str = "corporate-light"

    # 输入源
    context_dir: Optional[str] = None
    skeleton_path: Optional[str] = None
    resume_state: Optional[str] = None
    description: str = ""

    # 内容要求
    topics: List[str] = field(default_factory=list)
    require_cases: bool = False
    require_research: bool = True

    # 输出配置
    output_path: str = "presentation.pptx"

    # 起始阶段
    start_stage: str = "outline"  # outline | enrich | render


class IntentParser:
    """意图解析器"""

    # 时长关键词
    DURATION_PATTERNS = [
        (r'(\d+)\s*分钟', lambda m: int(m.group(1))),
        (r'(\d+)\s*min', lambda m: int(m.group(1))),
        (r'(\d+)\s*小时', lambda m: int(m.group(1)) * 60),
        (r'(\d+)\s*hour', lambda m: int(m.group(1)) * 60),
        (r'半小时', lambda m: 30),
        (r'一小时', lambda m: 60),
        (r'两小时', lambda m: 120),
    ]

    # 受众关键词
    AUDIENCE_KEYWORDS = {
        'executives': ['高管', '决策层', 'CEO', '董事', '总裁', 'executive', 'C-level'],
        'managers': ['经理', '中层', 'manager', '主管'],
        'professionals': ['专业', '技术', 'professional', '工程师', '开发'],
        'general': ['通用', '大众', 'general', '公众'],
    }

    # 场合关键词
    OCCASION_KEYWORDS = {
        'training': ['培训', '教学', 'training', '课程', '研修'],
        'pitch': ['汇报', '提案', 'pitch', '演示', '报告'],
        'conference': ['会议', '演讲', 'conference', '峰会', '论坛'],
        'workshop': ['工作坊', 'workshop', '实操', '练习'],
        'marketing': ['营销', '推广', 'marketing', '宣传'],
    }

    # 主题关键词
    THEME_KEYWORDS = {
        'nano-banana-pro': ['暗色', 'dark', '科技', '炫酷', 'banana'],
        'corporate-light': ['亮色', 'light', '商务', '正式', '企业'],
    }

    def parse(self, input_str: str = None, context_dir: str = None,
              skeleton_path: str = None, resume_state: str = None) -> PPTIntent:
        """解析意图"""
        intent = PPTIntent()

        # 1. 判断输入类型
        if resume_state and os.path.exists(resume_state):
            intent.input_type = "resume"
            intent.resume_state = resume_state
            intent.start_stage = self._get_resume_stage(resume_state)
            return intent

        if skeleton_path and os.path.exists(skeleton_path):
            intent.input_type = "skeleton"
            intent.skeleton_path = skeleton_path
            intent.start_stage = "enrich"
            return intent

        if context_dir and os.path.isdir(context_dir):
            intent.input_type = "context"
            intent.context_dir = context_dir
            # 检查是否有已有骨架
            skeleton = Path(context_dir) / 'skeleton.yaml'
            if skeleton.exists():
                intent.skeleton_path = str(skeleton)
                intent.start_stage = "enrich"
            return intent

        if input_str:
            # 检查是否是目录路径
            if os.path.isdir(input_str):
                intent.input_type = "context"
                intent.context_dir = input_str
                return intent

            # 检查是否是文件路径
            if os.path.isfile(input_str):
                if input_str.endswith('.yaml') or input_str.endswith('.yml'):
                    intent.input_type = "skeleton"
                    intent.skeleton_path = input_str
                    intent.start_stage = "enrich"
                return intent

            # 自然语言描述
            intent.input_type = "natural_language"
            intent.description = input_str
            self._parse_natural_language(intent, input_str)

        return intent

    def _parse_natural_language(self, intent: PPTIntent, text: str):
        """从自然语言解析意图"""
        text_lower = text.lower()

        # 解析时长
        for pattern, extractor in self.DURATION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                intent.duration = extractor(match)
                break

        # 解析受众
        for audience, keywords in self.AUDIENCE_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                intent.audience = audience
                break

        # 解析场合
        for occasion, keywords in self.OCCASION_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                intent.occasion = occasion
                break

        # 解析主题
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                intent.theme = theme
                break

        # 检查是否需要案例
        if any(kw in text_lower for kw in ['案例', 'case', '实例', '例子']):
            intent.require_cases = True

        # 检查是否跳过研究
        if any(kw in text_lower for kw in ['快速', '简单', '不用研究', 'quick']):
            intent.require_research = False

        # 提取主题关键词
        # 简单实现：提取引号内的内容或关键名词
        quoted = re.findall(r'[「」"""](.+?)[「」"""]', text)
        if quoted:
            intent.topics = quoted

        # 尝试生成标题
        if not intent.title:
            # 简单启发式：取前20个字符
            clean_text = re.sub(r'[，。！？,\.!?].*', '', text)
            intent.title = clean_text[:30] if clean_text else "Presentation"

    def _get_resume_stage(self, state_path: str) -> str:
        """从状态文件获取恢复阶段"""
        import json
        try:
            with open(state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
                stage = state.get('stage', 'outline')
                # 返回下一个阶段
                stages = ['outline', 'enrich', 'render']
                idx = stages.index(stage)
                return stages[min(idx + 1, len(stages) - 1)]
        except (json.JSONDecodeError, IOError, OSError, ValueError, KeyError):
            return 'outline'

    def get_summary(self, intent: PPTIntent) -> str:
        """生成意图摘要"""
        lines = [
            "=" * 50,
            "Intent Analysis",
            "=" * 50,
            f"Input type: {intent.input_type}",
            f"Start stage: {intent.start_stage}",
            "",
            "Parameters:",
            f"  Duration: {intent.duration} min",
            f"  Audience: {intent.audience}",
            f"  Occasion: {intent.occasion}",
            f"  Theme: {intent.theme}",
            f"  Research: {'yes' if intent.require_research else 'no'}",
        ]

        if intent.context_dir:
            lines.append(f"  Context: {intent.context_dir}")
        if intent.skeleton_path:
            lines.append(f"  Skeleton: {intent.skeleton_path}")
        if intent.description:
            lines.append(f"  Description: {intent.description[:50]}...")
        if intent.topics:
            lines.append(f"  Topics: {', '.join(intent.topics)}")

        lines.append("=" * 50)
        return "\n".join(lines)


# CLI
if __name__ == '__main__':
    import sys

    parser = IntentParser()

    if len(sys.argv) > 1:
        input_str = sys.argv[1]
        intent = parser.parse(input_str=input_str)
    else:
        # 测试自然语言
        test_inputs = [
            "做一个AI培训的PPT，90分钟，给企业高管",
            "快速做一个产品介绍，30分钟",
            "./docs/",
            "skeleton.yaml"
        ]
        for test in test_inputs:
            print(f"\nInput: {test}")
            intent = parser.parse(input_str=test)
            print(parser.get_summary(intent))
