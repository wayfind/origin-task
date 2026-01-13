#!/usr/bin/env python3
"""
Intent Engine Integration - PPT 生成跨会话追踪

将 PPT 生成流程的每个阶段记录到 Intent Engine，
实现跨会话追踪、决策日志和断点恢复。

用法：
1. 作为模块导入：
   from ie_integration import IETracker
   tracker = IETracker("ai-trends-brief")
   tracker.log_milestone("skeleton", "Generated skeleton.yaml with 5 sections")

2. 命令行工具：
   python ie_integration.py status             # 查看当前状态
   python ie_integration.py log milestone MSG  # 记录里程碑
   python ie_integration.py log decision MSG   # 记录决策
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class PPTTask:
    """PPT 生成任务"""
    name: str
    status: str  # todo | doing | done
    spec: Optional[str] = None
    children: Optional[List['PPTTask']] = None


class IETracker:
    """Intent Engine 追踪器"""

    # PPT 生成阶段
    STAGES = [
        ('init', 'Initialize project structure'),
        ('skeleton', 'Generate skeleton.yaml'),
        ('research', 'Execute research tasks'),
        ('layout', 'Analyze and decide layouts'),
        ('images', 'Generate decorative images'),
        ('enrich', 'Create slide-md files'),
        ('render', 'Render final PPTX'),
    ]

    def __init__(self, project_name: str, work_dir: Path = None):
        """
        初始化追踪器

        Args:
            project_name: 项目名称，如 "ai-trends-brief"
            work_dir: 工作目录
        """
        self.project_name = project_name
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self._ie_available = None

    def is_available(self) -> bool:
        """检查 ie 命令是否可用"""
        if self._ie_available is None:
            try:
                result = subprocess.run(
                    ['ie', '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                self._ie_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._ie_available = False
        return self._ie_available

    def status(self) -> Dict[str, Any]:
        """获取当前任务状态"""
        if not self.is_available():
            return {'error': 'ie not available'}

        try:
            result = subprocess.run(
                ['ie', 'status'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'output': result.stdout,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'ie status timeout'}

    def create_ppt_task(self, title: str, duration: int, theme: str) -> bool:
        """创建 PPT 生成任务（跨会话追踪根节点）"""
        if not self.is_available():
            self._log_fallback('create_task', f'PPT: {title}')
            return False

        spec = f"""## Goal
Generate professional PPTX: {title}

## Parameters
- Duration: {duration} minutes
- Theme: {theme}
- Project: {self.project_name}

## Approach
1. Generate skeleton.yaml (structure)
2. Execute research tasks (content)
3. Apply layout decisions (design)
4. Generate decorative images (visual)
5. Create slide-md files (output)
6. Render final PPTX (delivery)
"""

        task_json = json.dumps({
            'tasks': [{
                'name': f'PPT: {title}',
                'status': 'doing',
                'spec': spec,
                'children': [
                    {'name': stage_name, 'status': 'todo'}
                    for _, stage_name in self.STAGES
                ]
            }]
        })

        try:
            result = subprocess.run(
                ['ie', 'plan'],
                input=task_json,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def log_milestone(self, stage: str, message: str) -> bool:
        """
        记录阶段完成的里程碑

        Args:
            stage: 阶段名称 (init, skeleton, research, layout, images, enrich, render)
            message: 里程碑描述
        """
        if not self.is_available():
            self._log_fallback('milestone', f'[{stage}] {message}')
            return False

        milestone_msg = f"""## PPT Stage: {stage.upper()}
Project: {self.project_name}
Time: {datetime.now().isoformat()}

### Completed
{message}
"""

        try:
            result = subprocess.run(
                ['ie', 'log', 'milestone', milestone_msg],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def log_decision(self, topic: str, options: List[str], chosen: str, rationale: str) -> bool:
        """
        记录决策

        Args:
            topic: 决策主题
            options: 可选方案列表
            chosen: 选择的方案
            rationale: 决策理由
        """
        if not self.is_available():
            self._log_fallback('decision', f'[{topic}] {chosen}: {rationale}')
            return False

        options_md = '\n'.join(f'{i+1}. {opt}' for i, opt in enumerate(options))

        decision_msg = f"""## Decision: {topic}
Project: {self.project_name}

### Options
{options_md}

### Chosen
{chosen}

### Rationale
{rationale}
"""

        try:
            result = subprocess.run(
                ['ie', 'log', 'decision', decision_msg],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def log_blocker(self, stage: str, issue: str, suggestion: str = None) -> bool:
        """
        记录阻塞问题

        Args:
            stage: 当前阶段
            issue: 问题描述
            suggestion: 建议解决方案
        """
        if not self.is_available():
            self._log_fallback('blocker', f'[{stage}] {issue}')
            return False

        blocker_msg = f"""## Blocker in {stage.upper()}
Project: {self.project_name}

### Issue
{issue}
"""
        if suggestion:
            blocker_msg += f"""
### Suggested Resolution
{suggestion}
"""

        try:
            result = subprocess.run(
                ['ie', 'log', 'blocker', blocker_msg],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def log_note(self, stage: str, note: str) -> bool:
        """记录笔记"""
        if not self.is_available():
            self._log_fallback('note', f'[{stage}] {note}')
            return False

        note_msg = f"""## Note: {stage}
Project: {self.project_name}

{note}
"""

        try:
            result = subprocess.run(
                ['ie', 'log', 'note', note_msg],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def complete_stage(self, stage: str) -> bool:
        """标记阶段完成"""
        if not self.is_available():
            self._log_fallback('complete', f'Stage {stage} completed')
            return False

        # 找到对应的阶段名称
        stage_name = None
        for s, name in self.STAGES:
            if s == stage:
                stage_name = name
                break

        if not stage_name:
            return False

        task_json = json.dumps({
            'tasks': [{
                'name': stage_name,
                'status': 'done'
            }]
        })

        try:
            result = subprocess.run(
                ['ie', 'plan'],
                input=task_json,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            return False

    def search(self, query: str) -> Dict[str, Any]:
        """搜索历史"""
        if not self.is_available():
            return {'error': 'ie not available'}

        try:
            result = subprocess.run(
                ['ie', 'search', query],
                capture_output=True,
                text=True,
                timeout=10
            )
            return {
                'output': result.stdout,
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {'error': 'ie search timeout'}

    def _log_fallback(self, log_type: str, message: str):
        """当 ie 不可用时的后备日志"""
        fallback_file = self.work_dir / '.ppt-ie-fallback.log'
        timestamp = datetime.now().isoformat()

        with open(fallback_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] [{log_type.upper()}] {message}\n")

    def get_fallback_log(self) -> str:
        """读取后备日志"""
        fallback_file = self.work_dir / '.ppt-ie-fallback.log'
        if fallback_file.exists():
            return fallback_file.read_text(encoding='utf-8')
        return ""


def print_stage_guide():
    """打印阶段集成指南"""
    print("""
╔════════════════════════════════════════════════════════════╗
║         PPT Generator × Intent Engine 集成指南             ║
╚════════════════════════════════════════════════════════════╝

📋 何时记录里程碑 (milestone):
   - skeleton.yaml 生成完成
   - 所有研究任务完成
   - 布局决策应用完成
   - 配图生成完成
   - slide-md 文件创建完成
   - PPTX 渲染完成

📝 何时记录决策 (decision):
   - 选择主题 (corporate-light vs nano-banana-pro)
   - 选择布局方案
   - 选择图表类型
   - 是否跳过某个研究任务

⚠️ 何时记录阻塞 (blocker):
   - 研究 API 不可用
   - 图片生成失败
   - 渲染错误

💡 何时记录笔记 (note):
   - 发现的有趣数据
   - 内容调整建议
   - 后续改进想法

示例用法:
  from ie_integration import IETracker

  tracker = IETracker("my-presentation", Path("./output"))

  # 创建任务
  tracker.create_ppt_task("AI Trends 2026", 30, "nano-banana-pro")

  # 记录阶段完成
  tracker.log_milestone("skeleton", "Generated 5 sections, 12 slides")

  # 记录决策
  tracker.log_decision(
      "Layout for section 02",
      ["bullets", "three-cards", "chart"],
      "three-cards",
      "Content has 3 AI trends, perfect for card layout"
  )

  # 完成阶段
  tracker.complete_stage("skeleton")
""")


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description='PPT Generator Intent Engine Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # status
    status_parser = subparsers.add_parser('status', help='Get current task status')

    # log
    log_parser = subparsers.add_parser('log', help='Log event')
    log_parser.add_argument('type', choices=['milestone', 'decision', 'blocker', 'note'])
    log_parser.add_argument('message', help='Log message')
    log_parser.add_argument('--stage', default='general', help='Stage name')

    # search
    search_parser = subparsers.add_parser('search', help='Search history')
    search_parser.add_argument('query', help='Search query')

    # guide
    guide_parser = subparsers.add_parser('guide', help='Show integration guide')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    tracker = IETracker('ppt-project', Path.cwd())

    if args.command == 'status':
        result = tracker.status()
        if 'error' in result:
            print(f"⚠️ {result['error']}")
            fallback = tracker.get_fallback_log()
            if fallback:
                print("\n📋 Fallback log:")
                print(fallback)
        else:
            print(result['output'])

    elif args.command == 'log':
        if args.type == 'milestone':
            success = tracker.log_milestone(args.stage, args.message)
        elif args.type == 'decision':
            success = tracker.log_decision(args.stage, [], args.message, 'CLI input')
        elif args.type == 'blocker':
            success = tracker.log_blocker(args.stage, args.message)
        elif args.type == 'note':
            success = tracker.log_note(args.stage, args.message)

        if success:
            print(f"✅ Logged {args.type}")
        else:
            print(f"⚠️ ie unavailable, logged to fallback file")

    elif args.command == 'search':
        result = tracker.search(args.query)
        if 'error' in result:
            print(f"⚠️ {result['error']}")
        else:
            print(result['output'])

    elif args.command == 'guide':
        print_stage_guide()


if __name__ == '__main__':
    main()
