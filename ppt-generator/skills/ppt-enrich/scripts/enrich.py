#!/usr/bin/env python3
"""
PPT Enrich - 主入口脚本
从 skeleton.yaml 生成完整的 slide-md 内容文件

特性：
- 自动检测内容空缺
- Deep Research 集成（可选）
- Nano Banana 图片生成（可选）
"""

import os
import sys
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

from gap_detector import GapDetector
from slidemd_writer import SlideMDWriter, SlideContent

# 添加 ppt-outline 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'ppt-outline' / 'scripts'))
from context_scanner import ContextScanner

# 图片生成器（延迟加载）
_image_manager = None

def get_image_manager(output_dir: Path, theme: str, verbose: bool):
    """延迟加载图片生成器"""
    global _image_manager
    if _image_manager is None:
        try:
            from research.image_generator import ImageGeneratorManager
            _image_manager = ImageGeneratorManager(
                output_dir=output_dir,
                theme=theme,
                verbose=verbose
            )
        except ImportError:
            pass
    return _image_manager


class PPTEnrich:
    """PPT 内容增强器"""

    def __init__(self, skeleton_path: str, context_dir: str = None, **kwargs):
        self.skeleton_path = skeleton_path
        self.context_dir = context_dir
        self.options = {
            'output_dir': './slides',
            'research_mode': 'mock',  # browser | api | mock
            'cache_enabled': True,
            'cache_dir': '.cache/research',
            'generate_images': True,  # 是否生成装饰图片
            'theme': 'nano-banana-pro',  # 图片主题
            'verbose': False,
            **kwargs
        }

        # 加载骨架
        with open(skeleton_path, 'r', encoding='utf-8') as f:
            self.skeleton = yaml.safe_load(f)

        # 加载上下文
        self.context = None
        if context_dir:
            scanner = ContextScanner(context_dir)
            self.context = scanner.scan()

        # 空缺检测器
        self.gap_detector = GapDetector(skeleton_path, context_dir)

        # 研究结果缓存
        self.research_cache = {}

        # 图片路径映射
        self.image_paths = {}

    def detect_gaps(self) -> List[Dict]:
        """检测内容空缺"""
        return self.gap_detector.get_all_gaps()

    def run_research(self, requests: List[Dict] = None):
        """执行研究"""
        if requests is None:
            requests = self.gap_detector.get_research_requests()

        if self.options['verbose']:
            print(f"\nResearch requests: {len(requests)}")

        for req in requests:
            cache_key = self._get_cache_key(req)

            # 检查缓存
            if self.options['cache_enabled']:
                cached = self._load_from_cache(cache_key)
                if cached:
                    if self.options['verbose']:
                        print(f"  [cache] {req['section_id']}: {req['type']}")
                    self.research_cache[req['section_id']] = cached
                    continue

            # 执行研究
            if self.options['verbose']:
                print(f"  [research] {req['section_id']}: {req['query'][:40]}...")

            result = self._execute_research(req)
            self.research_cache[req['section_id']] = result

            # 保存缓存
            if self.options['cache_enabled'] and result:
                self._save_to_cache(cache_key, result)

    def _execute_research(self, request: Dict) -> Dict:
        """执行单个研究请求"""
        mode = self.options['research_mode']

        if mode == 'mock':
            return self._mock_research(request)
        elif mode == 'browser':
            return self._browser_research(request)
        elif mode == 'api':
            return self._api_research(request)
        else:
            return {}

    def _mock_research(self, request: Dict) -> Dict:
        """模拟研究结果"""
        if request['type'] == 'case_study':
            return {
                'type': 'case_study',
                'cases': [
                    {
                        'company': f"示例企业{i+1}",
                        'industry': '行业',
                        'application': f"AI应用场景{i+1}",
                        'metrics': [f"+{20+i*5}%效率提升"],
                        'source': 'Mock Research'
                    }
                    for i in range(request.get('count', 3))
                ]
            }
        elif request['type'] == 'statistics':
            return {
                'type': 'statistics',
                'data': [
                    {'metric': 'AI市场规模', 'value': '$1500亿', 'year': '2024'},
                    {'metric': '年增长率', 'value': '35%', 'year': '2024'}
                ]
            }
        return {}

    def _browser_research(self, request: Dict) -> Dict:
        """通过浏览器执行研究（自动发现并调用 openai-deep-research）"""
        try:
            from research import ResearchRunner
            runner = ResearchRunner(
                headless=True,
                timeout=2400,
                verbose=self.options.get("verbose", False)
            )
            return runner.execute(request)
        except ImportError:
            print("  [browser] research module not found, using mock")
            return self._mock_research(request)
        except Exception as e:
            print(f"  [browser] Research failed: {e}, using mock")
            return self._mock_research(request)

    def _api_research(self, request: Dict) -> Dict:
        """通过 API 执行研究"""
        # TODO: 调用 OpenAI API
        print(f"  [api] Not implemented yet, using mock")
        return self._mock_research(request)

    def _get_cache_key(self, request: Dict) -> str:
        """生成缓存键"""
        key_str = f"{request['section_id']}-{request['type']}-{request['query']}"
        return hashlib.md5(key_str.encode()).hexdigest()[:12]

    def _load_from_cache(self, cache_key: str) -> Optional[Dict]:
        """从缓存加载"""
        cache_path = Path(self.options['cache_dir']) / f"{cache_key}.json"
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                pass
        return None

    def _save_to_cache(self, cache_key: str, data: Dict):
        """保存到缓存"""
        cache_dir = Path(self.options['cache_dir'])
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{cache_key}.json"
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def generate_images(self) -> Dict[str, Path]:
        """生成装饰图片"""
        if not self.options.get('generate_images', True):
            if self.options['verbose']:
                print("Image generation disabled")
            return {}

        output_dir = Path(self.options['output_dir']) / 'images'
        theme = self.options.get('theme', 'nano-banana-pro')
        verbose = self.options.get('verbose', False)

        manager = get_image_manager(output_dir, theme, verbose)
        if manager is None:
            if verbose:
                print("Image generator not available")
            return {}

        if not manager.is_available():
            if verbose:
                status = manager.get_status()
                print(f"Image generation not available: {status}")
                if not status.get('gemini_configured'):
                    print("  Hint: Run 'python generate_image.py --check' to configure Gemini API")
            return {}

        if self.options['verbose']:
            print("\nGenerating images...")

        self.image_paths = manager.generate_for_skeleton(self.skeleton)

        if self.options['verbose']:
            print(f"Generated {len(self.image_paths)} images")

        return self.image_paths

    def generate(self, output_dir: str = None) -> List[str]:
        """生成 slide-md 文件"""
        output_dir = output_dir or self.options['output_dir']
        writer = SlideMDWriter(output_dir)

        slides = []
        slide_num = 0

        # 获取元数据
        meta = self.skeleton.get('meta', {})
        presentation = self.skeleton.get('presentation', {})

        # 1. 封面页
        slide_num += 1
        cover = writer.create_cover_slide(
            title=meta.get('title', 'Presentation'),
            subtitle=meta.get('subtitle', ''),
            extra=f"时长：{presentation.get('duration', 30)}分钟"
        )
        cover.id = f"00-{slide_num:02d}-cover"
        slides.append(cover)

        # 2. 为每个章节生成幻灯片
        for section in self.skeleton.get('structure', []):
            section_slides = self._generate_section_slides(section, writer)
            slides.extend(section_slides)

        # 写入所有幻灯片
        paths = writer.write_slides(slides)

        if self.options['verbose']:
            print(f"\nGenerated {len(paths)} slides in {output_dir}/")

        return paths

    def _generate_section_slides(self, section: Dict, writer: SlideMDWriter) -> List[SlideContent]:
        """为章节生成幻灯片"""
        slides = []
        section_id = section.get('id', '')
        section_type = section.get('type', 'content')
        title = section.get('title', '')

        # 章节标题页（非 opening/closing）
        if section_type not in ['opening', 'closing']:
            section_slide = writer.create_section_slide(
                section_id=section_id,
                title=title,
                number=section_id.split('-')[0] if '-' in section_id else ''
            )
            slides.append(section_slide)

        # 根据类型生成内容页
        if section_type == 'opening':
            slides.extend(self._generate_opening_slides(section, writer))
        elif section_type == 'case-study':
            slides.extend(self._generate_case_slides(section, writer))
        elif section_type == 'closing':
            slides.extend(self._generate_closing_slides(section, writer))
        else:
            slides.extend(self._generate_content_slides(section, writer))

        return slides

    def _generate_opening_slides(self, section: Dict, writer: SlideMDWriter) -> List[SlideContent]:
        """生成开场幻灯片"""
        slides = []
        section_id = section.get('id', '')
        hints = section.get('content_hints', [])

        # 议程页
        if hints:
            agenda = writer.create_bullets_slide(
                slide_id=f"{section_id}-agenda",
                title="课程大纲",
                bullets=hints[:6],
                source_section=section_id
            )
            slides.append(agenda)

        return slides

    def _generate_content_slides(self, section: Dict, writer: SlideMDWriter) -> List[SlideContent]:
        """生成内容幻灯片"""
        slides = []
        section_id = section.get('id', '')
        hints = section.get('content_hints', [])

        # 从 hints 生成要点页
        if hints:
            content = writer.create_bullets_slide(
                slide_id=f"{section_id}-content",
                title=section.get('title', ''),
                bullets=hints,
                source_section=section_id
            )
            slides.append(content)

        # 如果有研究结果，添加数据页
        research = self.research_cache.get(section_id, {})
        if research.get('type') == 'statistics':
            data = research.get('data', [])
            if data:
                bullets = [f"{d['metric']}: {d['value']} ({d.get('year', '')})" for d in data]
                stats = writer.create_bullets_slide(
                    slide_id=f"{section_id}-stats",
                    title=f"{section.get('title', '')} - 关键数据",
                    bullets=bullets,
                    source_section=section_id
                )
                slides.append(stats)

        return slides

    def _generate_case_slides(self, section: Dict, writer: SlideMDWriter) -> List[SlideContent]:
        """生成案例幻灯片"""
        slides = []
        section_id = section.get('id', '')

        # 从研究结果获取案例
        research = self.research_cache.get(section_id, {})
        cases = research.get('cases', [])

        if cases:
            # 每3个案例一页
            for i in range(0, len(cases), 3):
                chunk = cases[i:i+3]
                cards = [
                    {
                        'title': c.get('company', '企业'),
                        'description': c.get('application', ''),
                        'metric': c.get('metrics', [''])[0] if c.get('metrics') else ''
                    }
                    for c in chunk
                ]
                case_slide = writer.create_cards_slide(
                    slide_id=f"{section_id}-cases-{i//3+1}",
                    title=section.get('title', '案例'),
                    cards=cards,
                    source_section=section_id
                )
                slides.append(case_slide)
        else:
            # 没有案例时用占位符
            placeholder = writer.create_bullets_slide(
                slide_id=f"{section_id}-placeholder",
                title=section.get('title', ''),
                bullets=section.get('content_hints', ['待补充案例']),
                source_section=section_id
            )
            slides.append(placeholder)

        return slides

    def _generate_closing_slides(self, section: Dict, writer: SlideMDWriter) -> List[SlideContent]:
        """生成结尾幻灯片"""
        slides = []
        section_id = section.get('id', '')
        hints = section.get('content_hints', [])

        # 总结页
        if hints:
            summary = writer.create_bullets_slide(
                slide_id=f"{section_id}-summary",
                title="核心要点",
                bullets=hints,
                source_section=section_id
            )
            slides.append(summary)

        # 结束引用
        quote = writer.create_quote_slide(
            slide_id=f"{section_id}-quote",
            quote="谢谢！欢迎提问",
            attribution=""
        )
        slides.append(quote)

        return slides


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='从 skeleton.yaml 生成 slide-md 文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s skeleton.yaml                      # 基本用法
  %(prog)s skeleton.yaml -o ./slides          # 指定输出目录
  %(prog)s skeleton.yaml --research-mode browser  # 使用 Deep Research
  %(prog)s skeleton.yaml --no-images          # 跳过图片生成

主题:
  nano-banana-pro   Nano Banana Pro 风格（深色科技感）
  corporate-light   企业浅色风格
        """
    )

    parser.add_argument('skeleton', help='skeleton.yaml 文件')
    parser.add_argument('-o', '--output', default='./slides', help='输出目录')
    parser.add_argument('-c', '--context', help='上下文目录')
    parser.add_argument('--no-research', action='store_true', help='跳过研究')
    parser.add_argument('--research-mode', choices=['browser', 'api', 'mock'],
                       default='mock', help='研究模式')
    parser.add_argument('--no-images', action='store_true', help='跳过图片生成')
    parser.add_argument('--theme', default='nano-banana-pro',
                       choices=['nano-banana-pro', 'corporate-light'],
                       help='图片主题风格')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    enricher = PPTEnrich(
        skeleton_path=args.skeleton,
        context_dir=args.context,
        output_dir=args.output,
        research_mode=args.research_mode,
        generate_images=not args.no_images,
        theme=args.theme,
        verbose=args.verbose
    )

    # 检测空缺
    print("Analyzing content gaps...")
    print(enricher.gap_detector.get_report())

    # 执行研究
    if not args.no_research:
        print("\nRunning research...")
        enricher.run_research()

    # 生成图片
    if not args.no_images:
        enricher.generate_images()

    # 生成 slide-md
    print("\nGenerating slides...")
    paths = enricher.generate(args.output)

    print(f"\n✓ Generated {len(paths)} slides in {args.output}/")
    if enricher.image_paths:
        print(f"✓ Generated {len(enricher.image_paths)} images in {args.output}/images/")


if __name__ == '__main__':
    main()
