#!/usr/bin/env python3
"""
Skill Discovery - 运行时发现 Claude Code skills

扫描 marketplace → plugin.json → skill 路径，查找目标 skill。
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class SkillInfo:
    """Skill 信息"""
    name: str
    path: Optional[Path] = None
    available: bool = False
    script_path: Optional[Path] = None
    has_session: bool = False
    search_paths_tried: List[str] = field(default_factory=list)


class SkillDiscovery:
    """Skill 发现器"""

    # 搜索路径优先级（从高到低）
    DEFAULT_SEARCH_PATHS = [
        # 1. 源码路径（开发环境）
        Path("/mnt/d/prj/origin-task"),
        # 2. WSL 路径（如果在 WSL 中）
        Path("/home/david/prj/origin-task"),
        # 3. 插件缓存
        Path.home() / ".claude/plugins/cache/origin-task",
        # 4. Marketplace
        Path.home() / ".claude/plugins/marketplaces/origin-task",
    ]

    # openai-deep-research 的相对路径
    DEEP_RESEARCH_RELATIVE_PATH = "intent-engine/skills/openai-deep-research"
    DEEP_RESEARCH_SCRIPT = "deep_research_browser.py"

    # nano-banana-image 的相对路径
    NANO_BANANA_RELATIVE_PATH = "nano-banana-image/skills/nano-banana-image"
    NANO_BANANA_SCRIPT = "scripts/generate_image.py"

    def __init__(self, search_paths: Optional[List[Path]] = None):
        self.search_paths = search_paths or self.DEFAULT_SEARCH_PATHS

    def find_skill(self, name: str) -> SkillInfo:
        """查找指定 skill"""
        info = SkillInfo(name=name)

        if name == "openai-deep-research":
            return self._find_deep_research(info)
        elif name == "nano-banana-image":
            return self._find_nano_banana_image(info)

        # 通用 skill 发现（未来扩展）
        return self._find_generic_skill(name, info)

    def _find_deep_research(self, info: SkillInfo) -> SkillInfo:
        """查找 openai-deep-research skill"""
        for search_path in self.search_paths:
            info.search_paths_tried.append(str(search_path))

            # 直接路径
            skill_path = search_path / self.DEEP_RESEARCH_RELATIVE_PATH
            if skill_path.exists():
                script_path = skill_path / self.DEEP_RESEARCH_SCRIPT
                if script_path.exists():
                    info.path = skill_path
                    info.script_path = script_path
                    info.available = True
                    info.has_session = self._check_session(skill_path)
                    return info

            # 检查缓存目录（可能有版本号）
            cache_pattern = search_path / "intent-engine"
            if cache_pattern.exists():
                for version_dir in cache_pattern.iterdir():
                    if version_dir.is_dir():
                        skill_path = version_dir / "skills/openai-deep-research"
                        if skill_path.exists():
                            script_path = skill_path / self.DEEP_RESEARCH_SCRIPT
                            if script_path.exists():
                                info.path = skill_path
                                info.script_path = script_path
                                info.available = True
                                info.has_session = self._check_session(skill_path)
                                return info

        return info

    def _find_nano_banana_image(self, info: SkillInfo) -> SkillInfo:
        """查找 nano-banana-image skill"""
        for search_path in self.search_paths:
            info.search_paths_tried.append(str(search_path))

            # 直接路径
            skill_path = search_path / self.NANO_BANANA_RELATIVE_PATH
            if skill_path.exists():
                script_path = skill_path / self.NANO_BANANA_SCRIPT
                if script_path.exists():
                    info.path = skill_path
                    info.script_path = script_path
                    info.available = True
                    return info

            # 检查缓存目录（可能有版本号）
            cache_pattern = search_path / "nano-banana-image"
            if cache_pattern.exists():
                for version_dir in cache_pattern.iterdir():
                    if version_dir.is_dir():
                        skill_path = version_dir / "skills/nano-banana-image"
                        if skill_path.exists():
                            script_path = skill_path / self.NANO_BANANA_SCRIPT
                            if script_path.exists():
                                info.path = skill_path
                                info.script_path = script_path
                                info.available = True
                                return info

        return info

    def _find_generic_skill(self, name: str, info: SkillInfo) -> SkillInfo:
        """通用 skill 发现"""
        for search_path in self.search_paths:
            info.search_paths_tried.append(str(search_path))

            # 扫描 marketplace.json
            marketplace_path = search_path / ".claude-plugin/marketplace.json"
            if marketplace_path.exists():
                try:
                    data = json.loads(marketplace_path.read_text())
                    for plugin in data.get("plugins", []):
                        plugin_source = plugin.get("source", "")
                        plugin_path = search_path / plugin_source
                        skill_path = self._find_skill_in_plugin(plugin_path, name)
                        if skill_path:
                            info.path = skill_path
                            info.available = True
                            return info
                except (json.JSONDecodeError, IOError):
                    continue

        return info

    def _find_skill_in_plugin(self, plugin_path: Path, skill_name: str) -> Optional[Path]:
        """在 plugin 中查找 skill"""
        plugin_json = plugin_path / ".claude-plugin/plugin.json"
        if not plugin_json.exists():
            return None

        try:
            data = json.loads(plugin_json.read_text())
            for skill_def in data.get("skills", []):
                if isinstance(skill_def, str):
                    skill_path = plugin_path / skill_def
                    if skill_path.name == skill_name and skill_path.exists():
                        return skill_path
                elif isinstance(skill_def, dict):
                    if skill_def.get("name") == skill_name:
                        skill_path = plugin_path / skill_def.get("path", "")
                        if skill_path.exists():
                            return skill_path
        except (json.JSONDecodeError, IOError):
            pass

        return None

    def _check_session(self, skill_path: Path) -> bool:
        """检查是否有有效的浏览器 session"""
        # 尝试导入并调用 has_valid_session
        try:
            script_path = skill_path / self.DEEP_RESEARCH_SCRIPT
            if not script_path.exists():
                return False

            # 动态导入模块
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "deep_research_browser", script_path
            )
            if spec is None or spec.loader is None:
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules["deep_research_browser"] = module
            spec.loader.exec_module(module)

            # 调用 has_valid_session
            if hasattr(module, "has_valid_session"):
                return module.has_valid_session("default")

        except Exception:
            pass

        return False

    def list_available_skills(self) -> List[SkillInfo]:
        """列出所有可用的 skills"""
        skills = []

        for search_path in self.search_paths:
            marketplace_path = search_path / ".claude-plugin/marketplace.json"
            if marketplace_path.exists():
                try:
                    data = json.loads(marketplace_path.read_text())
                    for plugin in data.get("plugins", []):
                        plugin_source = plugin.get("source", "")
                        plugin_path = search_path / plugin_source
                        skills.extend(self._list_skills_in_plugin(plugin_path))
                except (json.JSONDecodeError, IOError):
                    continue

        return skills

    def _list_skills_in_plugin(self, plugin_path: Path) -> List[SkillInfo]:
        """列出 plugin 中的所有 skills"""
        skills = []
        plugin_json = plugin_path / ".claude-plugin/plugin.json"

        if not plugin_json.exists():
            return skills

        try:
            data = json.loads(plugin_json.read_text())
            for skill_def in data.get("skills", []):
                if isinstance(skill_def, str):
                    skill_path = plugin_path / skill_def
                    skill_name = skill_path.name
                else:
                    skill_name = skill_def.get("name", "")
                    skill_path = plugin_path / skill_def.get("path", "")

                if skill_path.exists():
                    skills.append(SkillInfo(
                        name=skill_name,
                        path=skill_path,
                        available=True
                    ))
        except (json.JSONDecodeError, IOError):
            pass

        return skills


# CLI 测试
if __name__ == "__main__":
    discovery = SkillDiscovery()

    if len(sys.argv) > 1:
        skill_name = sys.argv[1]
        info = discovery.find_skill(skill_name)
        print(f"Skill: {info.name}")
        print(f"  Available: {info.available}")
        print(f"  Path: {info.path}")
        print(f"  Script: {info.script_path}")
        print(f"  Has Session: {info.has_session}")
        print(f"  Searched: {info.search_paths_tried}")
    else:
        print("Usage: python skill_discovery.py <skill-name>")
        print("\nAvailable skills:")
        for skill in discovery.list_available_skills():
            print(f"  - {skill.name}: {skill.path}")
