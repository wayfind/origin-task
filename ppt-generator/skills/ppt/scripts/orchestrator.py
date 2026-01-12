#!/usr/bin/env python3
"""
PPT Orchestrator
编排 outline → enrich → render 流程

特性：
- 交互式向导：检测缺失信息时引导用户输入
- 配置文件：支持 .pptrc.yaml 多级配置
- 断点恢复：从 .ppt-state.json 恢复
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
from wizard import InteractiveWizard, run_wizard
from config_loader import ConfigLoader, PPTConfig, load_config

# Skills 路径
SKILLS_ROOT = Path(__file__).parent.parent.parent
OUTLINE_SCRIPT = SKILLS_ROOT / 'ppt-outline' / 'scripts' / 'outline.py'
ENRICH_SCRIPT = SKILLS_ROOT / 'ppt-enrich' / 'scripts' / 'enrich.py'
RENDER_SCRIPT = SKILLS_ROOT / 'ppt-render' / 'scripts' / 'render.js'


class PPTOrchestrator:
    """PPT 生成编排器"""

    STAGES = ['outline', 'enrich', 'render']

    def __init__(self, verbose: bool = False, work_dir: Path = None):
        self.verbose = verbose
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self.intent_parser = IntentParser()
        self.config_loader = ConfigLoader(self.work_dir)
        self.config: Optional[PPTConfig] = None
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
            audience: str = None, occasion: str = None,
            no_research: bool = False, no_images: bool = False,
            step: str = None, interactive: bool = True) -> str:
        """执行完整流程

        Args:
            input_str: 输入字符串（目录/文件/描述）
            context_dir: 文档目录
            skeleton_path: 骨架文件路径
            resume_state: 恢复状态文件
            output: 输出文件
            theme: 主题
            duration: 时长
            audience: 受众类型
            occasion: 演示场合
            no_research: 跳过研究
            no_images: 跳过图片生成
            step: 执行到指定阶段
            interactive: 是否启用交互式向导
        """

        # 0. 加载配置文件
        cli_overrides = {
            'output': output,
            'theme': theme,
            'duration': duration,
            'audience': audience,
            'occasion': occasion,
            'no_images': no_images,
            'mock': no_research,
            'verbose': self.verbose,
        }
        self.config = self.config_loader.load(cli_overrides)

        if self.verbose:
            sources = self.config_loader.get_sources()
            self._log(f"Configuration loaded from: {', '.join(sources)}")

        # 1. 如果无输入且启用交互，运行向导
        wizard_params = None
        if interactive and not input_str and not context_dir and not skeleton_path and not resume_state:
            wizard_params = self._run_wizard()
            if wizard_params:
                # 应用向导收集的参数
                if wizard_params.get('context_dir'):
                    context_dir = wizard_params['context_dir']
                if wizard_params.get('skeleton_path'):
                    skeleton_path = wizard_params['skeleton_path']
                if wizard_params.get('title'):
                    input_str = wizard_params['title']
                if wizard_params.get('duration') and not duration:
                    duration = wizard_params['duration']
                if wizard_params.get('audience') and not audience:
                    audience = wizard_params['audience']
                if wizard_params.get('occasion') and not occasion:
                    occasion = wizard_params['occasion']
                if wizard_params.get('theme') and not theme:
                    theme = wizard_params['theme']

        # 2. 解析意图
        intent = self.intent_parser.parse(
            input_str=input_str,
            context_dir=context_dir,
            skeleton_path=skeleton_path,
            resume_state=resume_state
        )

        # 3. 应用配置和覆盖参数
        # 优先级: 命令行/向导 > 配置文件 > 默认值
        if output:
            intent.output_path = output
        elif self.config.output_dir:
            intent.output_path = str(Path(self.config.output_dir) / 'presentation.pptx')

        if theme:
            intent.theme = theme
        elif self.config.theme:
            intent.theme = self.config.theme

        if duration:
            intent.duration = duration
        elif self.config.duration:
            intent.duration = self.config.duration

        if audience:
            intent.audience = audience
        elif self.config.audience:
            intent.audience = self.config.audience

        if no_research or self.config.research_mode == 'mock':
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
            '--research-mode', 'api' if intent.require_research else 'mock'
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

    def _run_wizard(self) -> Optional[Dict[str, Any]]:
        """运行交互式向导"""
        self._log("\n" + "=" * 55)
        self._log("  PPT 生成向导")
        self._log("=" * 55)

        wizard = InteractiveWizard(
            work_dir=self.work_dir,
            config=self.config.to_dict() if self.config else {}
        )
        wizard.detect_context()

        if wizard.needs_interaction():
            return wizard.run_interactive()
        else:
            # 不需要交互，返回检测到的参数
            ctx = wizard.context
            self._log("\n自动检测到完整上下文，跳过向导。")
            return {
                'title': ctx.detected_title,
                'duration': ctx.detected_duration or 30,
                'context_dir': str(ctx.detected_docs_dir) if ctx.detected_docs_dir else None,
                'skeleton_path': str(ctx.detected_skeleton) if ctx.detected_skeleton else None,
            }

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
  %(prog)s                             # 启动交互式向导
  %(prog)s ./docs/                     # 从文档目录生成
  %(prog)s ./docs/ -o my.pptx          # 指定输出文件
  %(prog)s "AI培训，60分钟"             # 从自然语言生成
  %(prog)s --resume .ppt-state.json    # 从断点恢复
  %(prog)s --init-config               # 生成配置文件模板

主题:
  corporate-light    企业浅色（正式场合）
  nano-banana-pro    Nano Banana Pro（创意/科技）

受众:
  executives         高管决策层
  managers           中层管理
  professionals      专业人士（默认）
  general            通用受众

场合:
  training           培训
  pitch              汇报/提案
  conference         会议演讲（默认）
  workshop           工作坊
        """
    )

    parser.add_argument('input', nargs='?', help='输入（目录/文件/描述）')
    parser.add_argument('-o', '--output', help='输出文件')
    parser.add_argument('-t', '--theme', help='主题 (corporate-light, nano-banana-pro)')
    parser.add_argument('-d', '--duration', type=int, help='时长（分钟）')
    parser.add_argument('-a', '--audience', help='受众类型')
    parser.add_argument('--occasion', help='演示场合')
    parser.add_argument('--no-research', action='store_true', help='跳过研究')
    parser.add_argument('--no-images', action='store_true', help='跳过图片生成')
    parser.add_argument('--no-interactive', action='store_true', help='禁用交互式向导')
    parser.add_argument('--step', choices=['outline', 'enrich', 'render'], help='执行到指定阶段')
    parser.add_argument('--resume', help='从状态文件恢复')
    parser.add_argument('--init-config', action='store_true', help='生成 .pptrc.yaml 配置模板')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    # 生成配置模板
    if args.init_config:
        loader = ConfigLoader()
        path = loader.save_template()
        print(f"✓ Configuration template saved to: {path}")
        print("  Edit the file to customize your defaults.")
        return

    orchestrator = PPTOrchestrator(verbose=args.verbose)

    try:
        output = orchestrator.run(
            input_str=args.input,
            output=args.output,
            theme=args.theme,
            duration=args.duration,
            audience=args.audience,
            occasion=args.occasion,
            no_research=args.no_research,
            no_images=args.no_images,
            step=args.step,
            resume_state=args.resume,
            interactive=not args.no_interactive
        )
        print(f"\n✓ Generated: {output}")
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
