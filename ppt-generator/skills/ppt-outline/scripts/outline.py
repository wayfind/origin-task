#!/usr/bin/env python3
"""
PPT Outline - 主入口脚本
从上下文生成 PPT 骨架结构（skeleton.yaml）
"""

import sys
import argparse
import yaml
from pathlib import Path

from context_scanner import ContextScanner
from skeleton_generator import SkeletonGenerator
from research_extractor import ResearchExtractor


class PPTOutline:
    """PPT 骨架生成器"""

    def __init__(self, context_dir: str = '.', **kwargs):
        self.context_dir = Path(context_dir)
        self.options = {
            'style': 'corporate-light',
            'duration': 30,
            'audience': 'professionals',
            'verbose': False,
            **kwargs
        }
        self.context = None
        self.skeleton = None

    def scan_context(self):
        """扫描上下文"""
        scanner = ContextScanner(str(self.context_dir))
        self.context = scanner.scan()

        if self.options['verbose']:
            print(scanner.get_report())

        return self.context

    def generate(self, title: str = None, **kwargs) -> dict:
        """生成骨架"""
        if not self.context:
            self.scan_context()

        generator = SkeletonGenerator(self.context)

        # 合并配置
        config = {**self.options, **kwargs}
        if title:
            config['title'] = title

        generator.configure(**config)
        self.skeleton = generator.generate_from_context()

        return self.skeleton

    def generate_from_brief(self, brief_path: str) -> dict:
        """从 brief 文件生成"""
        with open(brief_path, 'r', encoding='utf-8') as f:
            brief = yaml.safe_load(f)

        generator = SkeletonGenerator()
        self.skeleton = generator.generate_from_brief(brief)

        return self.skeleton

    def extract_research_needs(self, skeleton_path: str = None) -> list:
        """提取研究需求"""
        if skeleton_path:
            extractor = ResearchExtractor(skeleton_path, self.context)
        elif self.skeleton:
            # 临时保存 skeleton
            temp_path = '/tmp/temp_skeleton.yaml'
            self.save(temp_path)
            extractor = ResearchExtractor(temp_path, self.context)
        else:
            raise ValueError("No skeleton available")

        return extractor.extract()

    def save(self, output_path: str):
        """保存骨架"""
        if not self.skeleton:
            raise ValueError("No skeleton generated. Call generate() first.")

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(self.skeleton, f, allow_unicode=True,
                     default_flow_style=False, sort_keys=False)

        if self.options['verbose']:
            print(f"Saved: {output_path}")

        return output_path


def interactive_mode(outline: PPTOutline):
    """交互式模式"""
    print("\n" + "=" * 50)
    print("📋 PPT 骨架生成向导")
    print("=" * 50 + "\n")

    # 扫描上下文
    print("正在扫描上下文...")
    context = outline.scan_context()

    print(f"\n发现 {len(context.modules)} 个模块, {len(context.cases)} 个案例, {len(context.data_points)} 个数据点\n")

    # 获取标题
    default_title = context.meta.get('title', 'Untitled Presentation')
    title = input(f"演示标题 [{default_title}]: ").strip() or default_title

    # 获取时长
    default_duration = context.meta.get('presentation', {}).get('duration', 30)
    if 'structure' in context.meta:
        default_duration = sum(s.get('duration', 0) for s in context.meta['structure'])
    duration_input = input(f"目标时长（分钟）[{default_duration}]: ").strip()
    duration = int(duration_input) if duration_input else default_duration

    # 获取受众
    print("\n受众类型:")
    print("  1. executives - 高管决策层")
    print("  2. managers - 中层管理")
    print("  3. professionals - 专业人士")
    print("  4. general - 通用受众")
    audience_choice = input("选择 [3]: ").strip() or "3"
    audience_map = {'1': 'executives', '2': 'managers', '3': 'professionals', '4': 'general'}
    audience = audience_map.get(audience_choice, 'professionals')

    # 获取场合
    print("\n演示场合:")
    print("  1. training - 培训")
    print("  2. pitch - 汇报")
    print("  3. conference - 会议演讲")
    print("  4. workshop - 工作坊")
    occasion_choice = input("选择 [3]: ").strip() or "3"
    occasion_map = {'1': 'training', '2': 'pitch', '3': 'conference', '4': 'workshop'}
    occasion = occasion_map.get(occasion_choice, 'conference')

    # 生成骨架
    print("\n正在生成骨架...")
    skeleton = outline.generate(
        title=title,
        duration=duration,
        audience_type=audience,
        occasion=occasion
    )

    # 显示结构
    print("\n生成的结构:")
    for section in skeleton['structure']:
        print(f"  [{section['id']}] {section['title']} ({section['duration']}分钟)")

    # 保存
    output_path = input("\n输出文件 [skeleton.yaml]: ").strip() or "skeleton.yaml"
    outline.save(output_path)

    print(f"\n✓ 骨架已保存到: {output_path}")

    # 提取研究需求
    extract = input("\n是否提取研究需求? [y/N]: ").strip().lower()
    if extract == 'y':
        requests = outline.extract_research_needs()
        print(f"\n发现 {len(requests)} 个研究需求:")
        for req in requests[:5]:
            print(f"  - [{req.priority}] {req.query[:40]}...")
        if len(requests) > 5:
            print(f"  ... 还有 {len(requests) - 5} 个")


def main():
    parser = argparse.ArgumentParser(
        description='从上下文生成 PPT 骨架结构',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                           # 交互式模式
  %(prog)s -c ./docs/ -o skeleton.yaml
  %(prog)s --brief brief.yaml -o skeleton.yaml
        """
    )

    parser.add_argument('-c', '--context', default='.', help='上下文目录')
    parser.add_argument('-o', '--output', default='skeleton.yaml', help='输出文件')
    parser.add_argument('--brief', help='从 brief 文件生成')
    parser.add_argument('-t', '--title', help='演示标题')
    parser.add_argument('-d', '--duration', type=int, default=30, help='目标时长（分钟）')
    parser.add_argument('--style', default='corporate-light', help='样式名称')
    parser.add_argument('--audience', default='professionals', help='受众类型')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互式模式')

    args = parser.parse_args()

    outline = PPTOutline(
        context_dir=args.context,
        style=args.style,
        duration=args.duration,
        audience=args.audience,
        verbose=args.verbose
    )

    # 交互式模式
    if args.interactive or (len(sys.argv) == 1):
        interactive_mode(outline)
        return

    # 从 brief 生成
    if args.brief:
        skeleton = outline.generate_from_brief(args.brief)
    else:
        # 从上下文生成
        title = args.title or "Untitled Presentation"
        skeleton = outline.generate(title=title)

    outline.save(args.output)
    print(f"✓ Saved: {args.output}")

    # 显示结构摘要
    print(f"\nGenerated {len(skeleton['structure'])} sections:")
    for section in skeleton['structure']:
        print(f"  - {section['id']}: {section['title']}")


if __name__ == '__main__':
    main()
