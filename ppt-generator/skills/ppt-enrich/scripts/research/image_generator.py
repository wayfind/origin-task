#!/usr/bin/env python3
"""
Image Generator - Nano Banana Image 适配器

调用 nano-banana-image skill 生成 PPT 装饰性图片。
支持：
- 封面页、章节页、内容页、结尾页的装饰图片
- 主题一致的色彩风格
- 多种宽高比
"""

import logging
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .skill_discovery import SkillDiscovery, SkillInfo

log = logging.getLogger("research.image_generator")


@dataclass
class ImageRequest:
    """图片生成请求"""
    section_id: str
    section_title: str
    description: str
    position: str  # cover, section, content, ending
    aspect_ratio: str = "16:9"
    output_name: Optional[str] = None


@dataclass
class ImageResult:
    """图片生成结果"""
    success: bool
    path: Optional[Path] = None
    error: Optional[str] = None
    section_id: str = ""


# Nano Banana Pro 色彩定义
COLOR_PALETTE = {
    'nano-banana-pro': {
        'navy': '#1C2833',
        'gold': '#F4C430',
        'teal': '#00D9C0',
        'accent': '#E74C3C',
    },
    'corporate-light': {
        'primary': '#2C3E50',
        'secondary': '#3498DB',
        'accent': '#E74C3C',
        'light': '#ECF0F1',
    }
}

# 图片位置对应的宽高比推荐
POSITION_ASPECT_RATIOS = {
    'cover': '16:9',       # 封面主视觉
    'section': '16:9',     # 章节标题页
    'content': '4:3',      # 内容页侧边
    'ending': '16:9',      # 结尾感谢页
    'background': '16:9',  # 背景图
    'icon': '1:1',         # 图标类
}

# 位置对应的 prompt 增强
POSITION_STYLE_HINTS = {
    'cover': 'Hero image, impactful, keynote style, central focus',
    'section': 'Section header, thematic, abstract representation',
    'content': 'Supporting visual, informative, clean composition',
    'ending': 'Thank you visual, warm, professional, closing feel',
    'background': 'Subtle texture, low contrast, suitable as background',
    'icon': 'Icon style, simple, symbolic, centered',
}


class NanoBananaImageAdapter:
    """Nano Banana Image 适配器"""

    SKILL_NAME = "nano-banana-image"

    def __init__(
        self,
        skill_info: SkillInfo,
        output_dir: Path,
        theme: str = "nano-banana-pro",
        verbose: bool = False
    ):
        self.skill_info = skill_info
        self.output_dir = Path(output_dir)
        self.theme = theme
        self.verbose = verbose

        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if verbose:
            log.setLevel(logging.DEBUG)

    def generate_image(self, request: ImageRequest) -> ImageResult:
        """生成单张图片"""
        if not self.skill_info.available:
            return ImageResult(
                success=False,
                error="nano-banana-image skill not available",
                section_id=request.section_id
            )

        if not self.skill_info.script_path:
            return ImageResult(
                success=False,
                error="Script path not found",
                section_id=request.section_id
            )

        # 确定输出文件名
        if request.output_name:
            output_name = request.output_name
        else:
            output_name = f"{request.section_id}_{request.position}.png"

        output_path = self.output_dir / output_name

        # 增强 prompt
        enhanced_prompt = self._enhance_prompt(request)

        # 确定宽高比
        aspect_ratio = request.aspect_ratio or POSITION_ASPECT_RATIOS.get(request.position, "16:9")

        log.info(f"Generating image for {request.section_id}/{request.position}")
        log.debug(f"  Prompt: {enhanced_prompt[:100]}...")
        log.debug(f"  Aspect: {aspect_ratio}")
        log.debug(f"  Output: {output_path}")

        try:
            cmd = [
                sys.executable,
                str(self.skill_info.script_path),
                enhanced_prompt,
                str(output_path),
                "--aspect", aspect_ratio
            ]

            if self.verbose:
                cmd.append("-v")

            log.debug(f"Running: {' '.join(cmd[:4])}...")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2分钟超时
            )

            if result.returncode != 0:
                log.error(f"Image generation failed: {result.stderr}")
                return ImageResult(
                    success=False,
                    error=result.stderr or "Unknown error",
                    section_id=request.section_id
                )

            if output_path.exists():
                log.info(f"Image generated: {output_path}")
                return ImageResult(
                    success=True,
                    path=output_path,
                    section_id=request.section_id
                )
            else:
                return ImageResult(
                    success=False,
                    error="Output file not created",
                    section_id=request.section_id
                )

        except subprocess.TimeoutExpired:
            log.error("Image generation timeout")
            return ImageResult(
                success=False,
                error="Generation timeout (120s)",
                section_id=request.section_id
            )
        except Exception as e:
            log.error(f"Image generation error: {e}")
            return ImageResult(
                success=False,
                error=str(e),
                section_id=request.section_id
            )

    def _enhance_prompt(self, request: ImageRequest) -> str:
        """增强 prompt 以适应 PPT 风格"""
        base_description = request.description or request.section_title

        # 添加位置风格提示
        style_hint = POSITION_STYLE_HINTS.get(request.position, "")

        # 添加主题色彩提示（nano-banana 本身就会应用色彩）
        # 这里可以添加额外的上下文
        prompt = f"{base_description}"

        if style_hint:
            prompt += f". {style_hint}"

        # 添加专业 PPT 上下文
        prompt += ". For professional presentation slide."

        return prompt

    def generate_batch(self, requests: List[ImageRequest]) -> Dict[str, ImageResult]:
        """批量生成图片"""
        results = {}
        total = len(requests)

        for i, request in enumerate(requests, 1):
            log.info(f"Generating image {i}/{total}: {request.section_id}")
            result = self.generate_image(request)
            results[request.section_id] = result

            if not result.success:
                log.warning(f"  Failed: {result.error}")

        return results

    def check_prerequisites(self) -> Dict[str, Any]:
        """检查前置条件"""
        checks = {
            "skill_available": self.skill_info.available,
            "script_exists": self.skill_info.script_path and self.skill_info.script_path.exists(),
            "output_dir_exists": self.output_dir.exists(),
            "gemini_configured": self._check_gemini_config(),
        }

        checks["all_passed"] = all([
            checks["skill_available"],
            checks["script_exists"],
            checks["gemini_configured"],
        ])

        if not checks["gemini_configured"]:
            checks["setup_hint"] = (
                "Gemini API key not configured.\n"
                "Please run: python generate_image.py --check\n"
                "And follow the setup instructions."
            )

        return checks

    def _check_gemini_config(self) -> bool:
        """检查 Gemini API 是否已配置"""
        config_file = Path.home() / ".config" / "nano-banana-image" / "config.json"
        if not config_file.exists():
            return False

        try:
            import json
            config = json.loads(config_file.read_text())
            keys = config.get("keys", [])
            return len(keys) > 0
        except Exception:
            return False


class ImageGeneratorManager:
    """图片生成管理器（高级 API）"""

    def __init__(
        self,
        output_dir: Path = None,
        theme: str = "nano-banana-pro",
        verbose: bool = False
    ):
        self.output_dir = Path(output_dir) if output_dir else Path("./images")
        self.theme = theme
        self.verbose = verbose
        self.discovery = SkillDiscovery()
        self._adapter: Optional[NanoBananaImageAdapter] = None

    def get_adapter(self) -> Optional[NanoBananaImageAdapter]:
        """获取适配器（延迟初始化）"""
        if self._adapter is None:
            skill_info = self.discovery.find_skill("nano-banana-image")
            if skill_info.available:
                self._adapter = NanoBananaImageAdapter(
                    skill_info=skill_info,
                    output_dir=self.output_dir,
                    theme=self.theme,
                    verbose=self.verbose
                )
                log.info(f"Found nano-banana-image at: {skill_info.path}")
            else:
                log.warning("nano-banana-image skill not found")
                if skill_info.search_paths_tried:
                    log.debug(f"Searched paths: {skill_info.search_paths_tried}")

        return self._adapter

    def is_available(self) -> bool:
        """检查图片生成是否可用"""
        adapter = self.get_adapter()
        if not adapter:
            return False
        checks = adapter.check_prerequisites()
        return checks.get("all_passed", False)

    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        adapter = self.get_adapter()

        status = {
            "available": False,
            "skill_found": False,
            "gemini_configured": False,
            "output_dir": str(self.output_dir),
            "theme": self.theme,
        }

        if adapter:
            checks = adapter.check_prerequisites()
            status.update({
                "available": checks.get("all_passed", False),
                "skill_found": checks.get("skill_available", False),
                "gemini_configured": checks.get("gemini_configured", False),
            })

        return status

    def generate_for_skeleton(self, skeleton: Dict) -> Dict[str, Path]:
        """为骨架生成配图

        Args:
            skeleton: 骨架数据，包含 sections 列表

        Returns:
            section_id -> image_path 的映射
        """
        adapter = self.get_adapter()
        if not adapter:
            log.warning("Image generation not available")
            return {}

        if not self.is_available():
            log.warning("Prerequisites not met for image generation")
            return {}

        # 构建请求列表
        requests = []

        # 封面图
        meta = skeleton.get("meta", {})
        title = meta.get("title", "Presentation")
        requests.append(ImageRequest(
            section_id="00-cover",
            section_title=title,
            description=f"Cover image for presentation about {title}",
            position="cover"
        ))

        # 章节图
        sections = skeleton.get("sections", [])
        for section in sections:
            section_id = section.get("id", "")
            section_title = section.get("title", "")
            section_focus = section.get("focus", "")

            requests.append(ImageRequest(
                section_id=section_id,
                section_title=section_title,
                description=section_focus or section_title,
                position="section"
            ))

        # 结尾图
        requests.append(ImageRequest(
            section_id="99-ending",
            section_title="Thank You",
            description="Professional thank you and conclusion",
            position="ending"
        ))

        # 批量生成
        results = adapter.generate_batch(requests)

        # 返回成功的路径
        paths = {}
        for section_id, result in results.items():
            if result.success and result.path:
                paths[section_id] = result.path

        log.info(f"Generated {len(paths)}/{len(requests)} images")
        return paths

    def generate_single(
        self,
        description: str,
        position: str = "content",
        output_name: str = None
    ) -> Optional[Path]:
        """生成单张图片"""
        adapter = self.get_adapter()
        if not adapter:
            return None

        request = ImageRequest(
            section_id="single",
            section_title=description,
            description=description,
            position=position,
            output_name=output_name
        )

        result = adapter.generate_image(request)
        return result.path if result.success else None


# CLI 测试
if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Image Generator CLI")
    parser.add_argument("description", nargs="?", help="Image description")
    parser.add_argument("-o", "--output", default="./images", help="Output directory")
    parser.add_argument("-p", "--position", default="content",
                       choices=["cover", "section", "content", "ending"],
                       help="Image position type")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    manager = ImageGeneratorManager(
        output_dir=Path(args.output),
        verbose=args.verbose
    )

    if args.status:
        status = manager.get_status()
        print("\nImage Generator Status:")
        print(json.dumps(status, indent=2))

    elif args.description:
        print(f"\nGenerating: {args.description[:50]}...")
        path = manager.generate_single(
            args.description,
            position=args.position
        )
        if path:
            print(f"Generated: {path}")
        else:
            print("Failed to generate image")

    else:
        parser.print_help()
