#!/usr/bin/env python3
"""
PPT Orchestrator
编排 outline → enrich → render 流程
"""

import os
import sys
import json
import yaml
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from intent_parser import IntentParser, PPTIntent

# Skills 路径
SKILLS_ROOT = Path(__file__).parent.parent.parent
OUTLINE_SCRIPT = SKILLS_ROOT / 'ppt-outline' / 'scripts' / 'outline.py'
ENRICH_SCRIPT = SKILLS_ROOT / 'ppt-enrich' / 'scripts' / 'enrich.py'
RENDER_SCRIPT = SKILLS_ROOT / 'ppt-render' / 'scripts' / 'render.js'


class PPTOrchestrator:
    """PPT 生成编排器"""

    STAGES = ['outline', 'enrich', 'render']

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.intent_parser = IntentParser()
        self.state = {
            'stage': None,
            'skeleton_path': None,
            'slides_dir': None,
            'output_path': None,
            'options': {},
            'timestamp': None
        }

    def run(self, input_str: str = None, context_dir: str = None,
            skeleton_path: str = None, resume_state: str = None,
            output: str = None, theme: str = None, duration: int = None,
            no_research: bool = False, step: str = None) -> str:
        """执行完整流程"""

        # 1. 解析意图
        intent = self.intent_parser.parse(
            input_str=input_str,
            context_dir=context_dir,
            skeleton_path=skeleton_path,
            resume_state=resume_state
        )

        # 覆盖参数
        if output:
            intent.output_path = output
        if theme:
            intent.theme = theme
        if duration:
            intent.duration = duration
        if no_research:
            intent.require_research = False

        if self.verbose:
            print(self.intent_parser.get_summary(intent))

        # 2. 确定执行阶段
        start_idx = self.STAGES.index(intent.start_stage)
        end_idx = self.STAGES.index(step) if step else len(self.STAGES) - 1

        # 3. 设置工作目录
        work_dir = Path(intent.context_dir or '.').resolve()
        self.state['options'] = {
            'theme': intent.theme,
            'duration': intent.duration,
            'audience': intent.audience,
            'require_research': intent.require_research
        }

        # 4. 执行各阶段
        skeleton_path = intent.skeleton_path
        slides_dir = work_dir / 'slides'
        output_path = work_dir / intent.output_path

        for i in range(start_idx, end_idx + 1):
            stage = self.STAGES[i]
            self._log(f"\n{'='*50}")
            self._log(f"Stage {i+1}/{end_idx+1}: {stage.upper()}")
            self._log('='*50)

            try:
                if stage == 'outline':
                    skeleton_path = self._run_outline(intent, work_dir)
                elif stage == 'enrich':
                    slides_dir = self._run_enrich(skeleton_path, intent, work_dir)
                elif stage == 'render':
                    output_path = self._run_render(slides_dir, intent, work_dir)

                # 更新状态
                self.state['stage'] = stage
                self.state['skeleton_path'] = str(skeleton_path) if skeleton_path else None
                self.state['slides_dir'] = str(slides_dir) if slides_dir else None
                self.state['output_path'] = str(output_path) if output_path else None
                self.state['timestamp'] = datetime.now().isoformat()

                # 保存状态
                self._save_state(work_dir / '.ppt-state.json')

            except Exception as e:
                self._log(f"Error in {stage}: {e}")
                self._save_state(work_dir / '.ppt-state.json')
                raise

        self._log(f"\n✓ Done! Output: {output_path}")
        return str(output_path)

    def _run_outline(self, intent: PPTIntent, work_dir: Path) -> Path:
        """执行 outline 阶段"""
        skeleton_path = work_dir / 'skeleton.yaml'

        cmd = [
            'python3', str(OUTLINE_SCRIPT),
            '-c', str(intent.context_dir or work_dir),
            '-o', str(skeleton_path),
            '-d', str(intent.duration),
            '--style', intent.theme,
            '--audience', intent.audience
        ]

        if intent.title:
            cmd.extend(['-t', intent.title])

        self._log(f"Running: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self._log(f"stdout: {result.stdout}")
            self._log(f"stderr: {result.stderr}")
            raise RuntimeError(f"Outline failed: {result.stderr}")

        if self.verbose:
            self._log(result.stdout)

        return skeleton_path

    def _run_enrich(self, skeleton_path: Path, intent: PPTIntent, work_dir: Path) -> Path:
        """执行 enrich 阶段"""
        slides_dir = work_dir / 'slides'

        cmd = [
            'python3', str(ENRICH_SCRIPT),
            str(skeleton_path),
            '-o', str(slides_dir),
            '-c', str(intent.context_dir or work_dir),
            '--research-mode', 'mock' if not intent.require_research else 'mock'  # TODO: support browser/api
        ]

        if self.verbose:
            cmd.append('-v')

        self._log(f"Running: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self._log(f"stdout: {result.stdout}")
            self._log(f"stderr: {result.stderr}")
            raise RuntimeError(f"Enrich failed: {result.stderr}")

        if self.verbose:
            self._log(result.stdout)

        return slides_dir

    def _run_render(self, slides_dir: Path, intent: PPTIntent, work_dir: Path) -> Path:
        """执行 render 阶段"""
        output_path = work_dir / intent.output_path

        cmd = [
            'node', str(RENDER_SCRIPT),
            str(slides_dir),
            '-o', str(output_path),
            '-t', intent.theme
        ]

        if self.verbose:
            cmd.append('-v')

        self._log(f"Running: {' '.join(cmd[:5])}...")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            self._log(f"stdout: {result.stdout}")
            self._log(f"stderr: {result.stderr}")
            raise RuntimeError(f"Render failed: {result.stderr}")

        if self.verbose:
            self._log(result.stdout)

        return output_path

    def _save_state(self, path: Path):
        """保存状态"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, ensure_ascii=False, indent=2)

    def _load_state(self, path: Path) -> Dict[str, Any]:
        """加载状态"""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _log(self, message: str):
        """输出日志"""
        print(message)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='PPT 生成编排器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s ./docs/                     # 从文档目录生成
  %(prog)s ./docs/ -o my.pptx          # 指定输出文件
  %(prog)s "AI培训，60分钟"             # 从自然语言生成
  %(prog)s --resume .ppt-state.json    # 从断点恢复
        """
    )

    parser.add_argument('input', nargs='?', help='输入（目录/文件/描述）')
    parser.add_argument('-o', '--output', default='presentation.pptx', help='输出文件')
    parser.add_argument('-t', '--theme', default='corporate-light', help='主题')
    parser.add_argument('-d', '--duration', type=int, help='时长（分钟）')
    parser.add_argument('--no-research', action='store_true', help='跳过研究')
    parser.add_argument('--step', choices=['outline', 'enrich', 'render'], help='执行到指定阶段')
    parser.add_argument('--resume', help='从状态文件恢复')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    orchestrator = PPTOrchestrator(verbose=args.verbose)

    try:
        output = orchestrator.run(
            input_str=args.input,
            output=args.output,
            theme=args.theme,
            duration=args.duration,
            no_research=args.no_research,
            step=args.step,
            resume_state=args.resume
        )
        print(f"\n✓ Generated: {output}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
