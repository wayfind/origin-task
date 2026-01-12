#!/usr/bin/env python3
"""
Config Loader - .pptrc.yaml 配置加载器

支持多级配置合并：
1. 系统默认值
2. 用户主目录 ~/.pptrc.yaml
3. 项目目录 .pptrc.yaml
4. 命令行参数（最高优先级）
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class PPTConfig:
    """PPT 生成配置"""
    # 演示默认值
    theme: str = "corporate-light"
    duration: int = 30
    audience: str = "professionals"
    occasion: str = "conference"
    output_dir: str = "./output"

    # 研究配置
    research_mode: str = "browser"  # browser | mock
    research_cache: bool = True
    research_timeout: int = 2400  # 40 分钟
    research_session: str = "default"

    # 路径配置
    docs_dir: Optional[str] = None
    skeleton_path: Optional[str] = None

    # 图片配置
    generate_images: bool = True
    image_style: str = "nano-banana-pro"

    # 图表配置
    enable_charts: bool = True
    chart_theme: str = "dark"

    # 调试选项
    verbose: bool = False
    dry_run: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'theme': self.theme,
            'duration': self.duration,
            'audience': self.audience,
            'occasion': self.occasion,
            'output_dir': self.output_dir,
            'research': {
                'mode': self.research_mode,
                'cache': self.research_cache,
                'timeout': self.research_timeout,
                'session': self.research_session,
            },
            'paths': {
                'docs_dir': self.docs_dir,
                'skeleton_path': self.skeleton_path,
            },
            'images': {
                'generate': self.generate_images,
                'style': self.image_style,
            },
            'charts': {
                'enable': self.enable_charts,
                'theme': self.chart_theme,
            },
            'verbose': self.verbose,
            'dry_run': self.dry_run,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PPTConfig':
        """从字典创建配置"""
        config = cls()

        # 直接字段
        if 'theme' in data:
            config.theme = data['theme']
        if 'duration' in data:
            config.duration = int(data['duration'])
        if 'audience' in data:
            config.audience = data['audience']
        if 'occasion' in data:
            config.occasion = data['occasion']
        if 'output_dir' in data:
            config.output_dir = data['output_dir']
        if 'verbose' in data:
            config.verbose = bool(data['verbose'])
        if 'dry_run' in data:
            config.dry_run = bool(data['dry_run'])

        # defaults 嵌套（兼容旧格式）
        if defaults := data.get('defaults', {}):
            if 'theme' in defaults:
                config.theme = defaults['theme']
            if 'duration' in defaults:
                config.duration = int(defaults['duration'])
            if 'audience' in defaults:
                config.audience = defaults['audience']
            if 'occasion' in defaults:
                config.occasion = defaults['occasion']
            if 'output_dir' in defaults:
                config.output_dir = defaults['output_dir']

        # research 嵌套
        if research := data.get('research', {}):
            if 'mode' in research:
                config.research_mode = research['mode']
            if 'cache' in research:
                config.research_cache = bool(research['cache'])
            if 'timeout' in research:
                config.research_timeout = int(research['timeout'])
            if 'session' in research:
                config.research_session = research['session']

        # paths 嵌套
        if paths := data.get('paths', {}):
            if 'docs_dir' in paths:
                config.docs_dir = paths['docs_dir']
            if 'skeleton_path' in paths:
                config.skeleton_path = paths['skeleton_path']

        # images 嵌套
        if images := data.get('images', {}):
            if 'generate' in images:
                config.generate_images = bool(images['generate'])
            if 'style' in images:
                config.image_style = images['style']

        # charts 嵌套
        if charts := data.get('charts', {}):
            if 'enable' in charts:
                config.enable_charts = bool(charts['enable'])
            if 'theme' in charts:
                config.chart_theme = charts['theme']

        return config


class ConfigLoader:
    """配置加载器"""

    CONFIG_FILENAMES = ['.pptrc.yaml', '.pptrc.yml', 'pptrc.yaml']

    def __init__(self, work_dir: Path = None):
        self.work_dir = Path(work_dir) if work_dir else Path.cwd()
        self._config: Optional[PPTConfig] = None
        self._sources: List[str] = []

    def load(self, cli_overrides: Dict[str, Any] = None) -> PPTConfig:
        """加载配置（多级合并）

        优先级：命令行 > 项目目录 > 用户主目录 > 系统默认
        """
        self._sources = []

        # 1. 系统默认值
        config = PPTConfig()
        self._sources.append("defaults")

        # 2. 用户主目录配置
        home_config = self._load_from_home()
        if home_config:
            config = self._merge_configs(config, home_config)
            self._sources.append(f"~/{self._found_filename}")

        # 3. 项目目录配置
        project_config = self._load_from_project()
        if project_config:
            config = self._merge_configs(config, project_config)
            self._sources.append(f"./{self._found_filename}")

        # 4. 命令行参数覆盖
        if cli_overrides:
            config = self._apply_overrides(config, cli_overrides)
            self._sources.append("cli")

        self._config = config
        return config

    def get_sources(self) -> List[str]:
        """获取配置来源列表"""
        return self._sources.copy()

    def _load_from_home(self) -> Optional[PPTConfig]:
        """从用户主目录加载配置"""
        home = Path.home()
        return self._load_from_dir(home)

    def _load_from_project(self) -> Optional[PPTConfig]:
        """从项目目录加载配置"""
        return self._load_from_dir(self.work_dir)

    def _load_from_dir(self, directory: Path) -> Optional[PPTConfig]:
        """从指定目录加载配置文件"""
        for filename in self.CONFIG_FILENAMES:
            config_path = directory / filename
            if config_path.exists():
                try:
                    data = yaml.safe_load(config_path.read_text(encoding='utf-8'))
                    if data:
                        self._found_filename = filename
                        return PPTConfig.from_dict(data)
                except Exception as e:
                    print(f"Warning: Failed to load {config_path}: {e}")
        return None

    def _merge_configs(self, base: PPTConfig, override: PPTConfig) -> PPTConfig:
        """合并两个配置对象"""
        # 创建新配置
        merged = PPTConfig()

        # 合并所有字段（override 优先）
        for attr in [
            'theme', 'duration', 'audience', 'occasion', 'output_dir',
            'research_mode', 'research_cache', 'research_timeout', 'research_session',
            'docs_dir', 'skeleton_path',
            'generate_images', 'image_style',
            'enable_charts', 'chart_theme',
            'verbose', 'dry_run'
        ]:
            base_val = getattr(base, attr)
            override_val = getattr(override, attr)

            # 使用 override 值，除非是 None 或默认值
            if override_val is not None and override_val != getattr(PPTConfig(), attr):
                setattr(merged, attr, override_val)
            else:
                setattr(merged, attr, base_val)

        return merged

    def _apply_overrides(self, config: PPTConfig, overrides: Dict[str, Any]) -> PPTConfig:
        """应用命令行覆盖"""
        for key, value in overrides.items():
            if value is None:
                continue

            # 映射命令行参数到配置字段
            mapping = {
                'theme': 'theme',
                'duration': 'duration',
                'audience': 'audience',
                'occasion': 'occasion',
                'output': 'output_dir',
                'output_dir': 'output_dir',
                'docs': 'docs_dir',
                'docs_dir': 'docs_dir',
                'skeleton': 'skeleton_path',
                'verbose': 'verbose',
                'dry_run': 'dry_run',
                'no_images': lambda v: not v,  # 反转
                'no_charts': lambda v: not v,  # 反转
                'research_mode': 'research_mode',
                'mock': lambda v: 'mock' if v else 'browser',
            }

            if key in mapping:
                attr = mapping[key]
                if callable(attr):
                    # 特殊处理
                    if key == 'no_images':
                        config.generate_images = not value
                    elif key == 'no_charts':
                        config.enable_charts = not value
                    elif key == 'mock':
                        config.research_mode = 'mock' if value else 'browser'
                else:
                    setattr(config, attr, value)

        return config

    def save_template(self, path: Path = None) -> Path:
        """保存配置模板文件"""
        if path is None:
            path = self.work_dir / '.pptrc.yaml'

        template = """# PPT Generator 配置文件
# 优先级: 命令行参数 > 项目目录 > 用户主目录 > 默认值

# 演示默认值
defaults:
  theme: corporate-light      # 主题: corporate-light | nano-banana-pro
  duration: 30                # 目标时长（分钟）
  audience: professionals     # 受众: executives | managers | professionals | general
  occasion: conference        # 场合: training | pitch | conference | workshop
  output_dir: ./output        # 输出目录

# 研究配置
research:
  mode: browser               # 研究模式: browser | mock
  cache: true                 # 是否缓存研究结果
  timeout: 2400               # 超时时间（秒，默认40分钟）
  session: default            # 浏览器 session 名称

# 路径配置
paths:
  docs_dir: ./docs            # 文档目录
  # skeleton_path: ./skeleton.yaml  # 已有骨架路径

# 图片配置
images:
  generate: true              # 是否生成装饰图片
  style: nano-banana-pro      # 图片风格

# 图表配置
charts:
  enable: true                # 是否启用图表
  theme: dark                 # 图表主题

# 调试选项
# verbose: false
# dry_run: false
"""
        path.write_text(template, encoding='utf-8')
        return path


def load_config(work_dir: Path = None, cli_args: Dict = None) -> PPTConfig:
    """便捷函数：加载配置"""
    loader = ConfigLoader(work_dir)
    return loader.load(cli_args)


def get_config_template() -> str:
    """获取配置文件模板内容"""
    loader = ConfigLoader()
    import io
    buf = io.StringIO()
    # 返回模板字符串
    return """# PPT Generator 配置文件
defaults:
  theme: corporate-light
  duration: 30
  audience: professionals
  output_dir: ./output

research:
  mode: browser
  cache: true

paths:
  docs_dir: ./docs
"""


# CLI 测试
if __name__ == '__main__':
    import json
    import sys

    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    loader = ConfigLoader(work_dir)
    config = loader.load()

    print("Configuration loaded from:", loader.get_sources())
    print("\nConfiguration:")
    print(json.dumps(config.to_dict(), ensure_ascii=False, indent=2))

    # 测试保存模板
    if '--save-template' in sys.argv:
        template_path = loader.save_template()
        print(f"\nTemplate saved to: {template_path}")
