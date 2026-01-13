#!/usr/bin/env python3
"""
Stage Reflector - P1 强制反思机制

每个 PPT 生成阶段完成后，强制输出反思报告，
检查是否有遗漏或问题，帮助 AI 发现并修正错误。
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class StageCheck:
    """单项检查结果"""
    name: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error


@dataclass
class StageReflection:
    """阶段反思结果"""
    stage: str
    timestamp: str
    duration_seconds: float = 0
    checks: List[StageCheck] = field(default_factory=list)
    summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "checks": [{"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity} for c in self.checks],
            "summary": self.summary,
            "warnings": self.warnings,
            "errors": self.errors,
            "next_steps": self.next_steps,
        }


class StageReflector:
    """阶段反思器"""

    def __init__(self, project_dir: Path):
        self.project_dir = Path(project_dir)
        self.reflections: List[StageReflection] = []

    def reflect_init(self, pptrc_path: Optional[Path] = None) -> StageReflection:
        """Stage 0: 初始化阶段反思"""
        checks = []
        warnings = []
        errors = []

        # 检查 .pptrc.yaml
        pptrc = pptrc_path or self.project_dir / ".pptrc.yaml"
        if pptrc.exists():
            checks.append(StageCheck("config_exists", True, f".pptrc.yaml 已创建: {pptrc}"))

            # 检查内容
            content = pptrc.read_text()
            if "deep_research: true" in content:
                checks.append(StageCheck("deep_research", True, "deep-research 已启用"))
            else:
                warnings.append("deep-research 未启用，研究质量可能较低")
                checks.append(StageCheck("deep_research", False, "deep-research 未启用", "warning"))

            if "image_generation: true" in content:
                checks.append(StageCheck("image_generation", True, "图片生成已启用"))
            else:
                warnings.append("图片生成未启用，PPT 将没有装饰图")
                checks.append(StageCheck("image_generation", False, "图片生成未启用", "warning"))
        else:
            errors.append(".pptrc.yaml 不存在，用户能力未确认")
            checks.append(StageCheck("config_exists", False, ".pptrc.yaml 不存在", "error"))

        reflection = StageReflection(
            stage="init",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"初始化完成，{len(checks)}项检查，{len(warnings)}个警告，{len(errors)}个错误",
            next_steps=["生成 skeleton.yaml"] if not errors else ["修复初始化问题"]
        )

        self.reflections.append(reflection)
        return reflection

    def reflect_skeleton(self, skeleton_path: Optional[Path] = None) -> StageReflection:
        """Stage 1: 骨架生成阶段反思"""
        checks = []
        warnings = []
        errors = []

        skeleton = skeleton_path or self.project_dir / "skeleton.yaml"
        if skeleton.exists():
            checks.append(StageCheck("skeleton_exists", True, f"skeleton.yaml 已创建"))

            content = skeleton.read_text()

            # 检查 research_tasks
            if "research_tasks:" in content:
                # 计算任务数量
                import re
                task_count = len(re.findall(r'- id: "r\d+', content))
                if task_count > 0:
                    checks.append(StageCheck("research_tasks", True, f"定义了 {task_count} 个研究任务"))
                else:
                    warnings.append("research_tasks 为空，没有研究任务")
                    checks.append(StageCheck("research_tasks", False, "无研究任务", "warning"))
            else:
                warnings.append("skeleton.yaml 中没有 research_tasks 定义")
                checks.append(StageCheck("research_tasks", False, "缺少 research_tasks", "warning"))

            # 检查 structure
            if "structure:" in content:
                section_count = len(re.findall(r'- id: "\d+-', content))
                checks.append(StageCheck("structure", True, f"定义了 {section_count} 个章节"))
            else:
                errors.append("skeleton.yaml 中没有 structure 定义")
                checks.append(StageCheck("structure", False, "缺少 structure", "error"))

        else:
            errors.append("skeleton.yaml 不存在")
            checks.append(StageCheck("skeleton_exists", False, "skeleton.yaml 不存在", "error"))

        reflection = StageReflection(
            stage="skeleton",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"骨架生成完成，{len(checks)}项检查，{len(warnings)}个警告，{len(errors)}个错误",
            next_steps=["执行研究任务"] if not errors else ["修复骨架问题"]
        )

        self.reflections.append(reflection)
        return reflection

    def reflect_research(self, skeleton_path: Optional[Path] = None) -> StageReflection:
        """Stage 2: 研究执行阶段反思"""
        checks = []
        warnings = []
        errors = []

        research_dir = self.project_dir / "research_results"

        if research_dir.exists():
            checks.append(StageCheck("dir_exists", True, "research_results/ 目录已创建"))

            # 检查研究结果文件
            result_files = list(research_dir.glob("*.md"))
            if result_files:
                checks.append(StageCheck("results_exist", True, f"找到 {len(result_files)} 个研究结果文件"))

                # 检查每个文件的内容质量
                for f in result_files:
                    content = f.read_text()
                    if len(content) < 100:
                        warnings.append(f"{f.name} 内容过短 ({len(content)} 字符)")
                    if "来源" not in content and "Source" not in content:
                        warnings.append(f"{f.name} 缺少来源引用")
            else:
                errors.append("research_results/ 目录为空，没有研究结果")
                checks.append(StageCheck("results_exist", False, "无研究结果文件", "error"))

            # 检查与 skeleton 的一致性
            skeleton = skeleton_path or self.project_dir / "skeleton.yaml"
            if skeleton.exists():
                import re
                skeleton_content = skeleton.read_text()
                expected_tasks = re.findall(r'- id: "(r\d+)"', skeleton_content)
                actual_results = [f.stem for f in result_files]

                missing = set(expected_tasks) - set(actual_results)
                if missing:
                    for task_id in missing:
                        errors.append(f"研究任务 [{task_id}] 未执行")
                    checks.append(StageCheck("tasks_complete", False, f"缺少 {len(missing)} 个研究结果", "error"))
                else:
                    checks.append(StageCheck("tasks_complete", True, "所有研究任务已执行"))

        else:
            errors.append("research_results/ 目录不存在")
            checks.append(StageCheck("dir_exists", False, "research_results/ 不存在", "error"))

        reflection = StageReflection(
            stage="research",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"研究执行完成，{len(checks)}项检查，{len(warnings)}个警告，{len(errors)}个错误",
            next_steps=["生成 slide-md 文件"] if not errors else ["补充缺失的研究任务"]
        )

        self.reflections.append(reflection)
        return reflection

    def reflect_images(self) -> StageReflection:
        """Stage 2.5: 图片生成阶段反思"""
        checks = []
        warnings = []
        errors = []

        images_dir = self.project_dir / "images"
        pptrc = self.project_dir / ".pptrc.yaml"

        # 检查是否应该生成图片
        should_generate = False
        if pptrc.exists():
            content = pptrc.read_text()
            should_generate = "image_generation: true" in content

        if should_generate:
            if images_dir.exists():
                image_files = list(images_dir.glob("*.png"))
                if image_files:
                    checks.append(StageCheck("images_exist", True, f"生成了 {len(image_files)} 张图片"))
                else:
                    warnings.append("images/ 目录为空，没有生成图片")
                    checks.append(StageCheck("images_exist", False, "无图片文件", "warning"))
            else:
                warnings.append("images/ 目录不存在，图片未生成")
                checks.append(StageCheck("dir_exists", False, "images/ 不存在", "warning"))
        else:
            checks.append(StageCheck("skipped", True, "图片生成已跳过（未启用）"))

        reflection = StageReflection(
            stage="images",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"图片生成{'已跳过' if not should_generate else '完成'}",
            next_steps=["生成 slide-md 文件"]
        )

        self.reflections.append(reflection)
        return reflection

    def reflect_enrich(self) -> StageReflection:
        """Stage 3: 内容填充阶段反思"""
        checks = []
        warnings = []
        errors = []

        slides_dir = self.project_dir / "slides"

        if slides_dir.exists():
            slide_files = sorted(slides_dir.glob("*.slide.md"))
            if slide_files:
                checks.append(StageCheck("slides_exist", True, f"生成了 {len(slide_files)} 张幻灯片"))

                # 检查内容质量
                empty_slides = []
                no_research_ref = []

                for f in slide_files:
                    content = f.read_text()
                    # 检查是否有实际内容（除了 frontmatter）
                    lines = [l for l in content.split("\n") if l.strip() and not l.startswith("---") and not l.startswith("slide:")]
                    if len(lines) < 3:
                        empty_slides.append(f.name)

                    # 检查是否有 @RESEARCH 标记但内容为空
                    if "<!-- @RESEARCH:" in content and "此区域将由研究结果" in content:
                        no_research_ref.append(f.name)

                if empty_slides:
                    warnings.append(f"{len(empty_slides)} 张幻灯片内容过少: {', '.join(empty_slides[:3])}")
                if no_research_ref:
                    errors.append(f"{len(no_research_ref)} 张幻灯片的研究内容未填充: {', '.join(no_research_ref[:3])}")
                    checks.append(StageCheck("research_filled", False, "研究内容未填充", "error"))
                else:
                    checks.append(StageCheck("research_filled", True, "研究内容已填充"))
            else:
                errors.append("slides/ 目录为空")
                checks.append(StageCheck("slides_exist", False, "无幻灯片文件", "error"))
        else:
            errors.append("slides/ 目录不存在")
            checks.append(StageCheck("dir_exists", False, "slides/ 不存在", "error"))

        reflection = StageReflection(
            stage="enrich",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"内容填充完成，{len(checks)}项检查，{len(warnings)}个警告，{len(errors)}个错误",
            next_steps=["渲染 PPTX"] if not errors else ["修复内容问题"]
        )

        self.reflections.append(reflection)
        return reflection

    def reflect_render(self, output_path: Optional[Path] = None) -> StageReflection:
        """Stage 4: 渲染阶段反思"""
        checks = []
        warnings = []
        errors = []

        # 查找 PPTX 文件
        pptx_files = list(self.project_dir.glob("*.pptx"))
        if output_path:
            pptx_files = [output_path] if output_path.exists() else []

        if pptx_files:
            pptx = pptx_files[0]
            size_kb = pptx.stat().st_size / 1024
            checks.append(StageCheck("pptx_exists", True, f"PPTX 已生成: {pptx.name} ({size_kb:.1f} KB)"))

            if size_kb < 10:
                warnings.append(f"PPTX 文件过小 ({size_kb:.1f} KB)，可能内容不完整")
        else:
            errors.append("PPTX 文件未生成")
            checks.append(StageCheck("pptx_exists", False, "PPTX 不存在", "error"))

        reflection = StageReflection(
            stage="render",
            timestamp=datetime.now().isoformat(),
            checks=checks,
            warnings=warnings,
            errors=errors,
            summary=f"渲染完成，{len(checks)}项检查，{len(warnings)}个警告，{len(errors)}个错误",
            next_steps=["PPT 生成完成！"] if not errors else ["修复渲染问题"]
        )

        self.reflections.append(reflection)
        return reflection

    def get_final_report(self) -> str:
        """生成最终反思报告"""
        total_warnings = sum(len(r.warnings) for r in self.reflections)
        total_errors = sum(len(r.errors) for r in self.reflections)

        lines = [
            "",
            "━" * 60,
            "📋 PPT 生成反思报告",
            "━" * 60,
            "",
        ]

        for r in self.reflections:
            status = "✅" if not r.has_errors else "❌"
            lines.append(f"{status} Stage: {r.stage}")
            for check in r.checks:
                icon = "✓" if check.passed else ("⚠" if check.severity == "warning" else "✗")
                lines.append(f"   {icon} {check.message}")
            if r.warnings:
                for w in r.warnings:
                    lines.append(f"   ⚠️  {w}")
            if r.errors:
                for e in r.errors:
                    lines.append(f"   ❌ {e}")
            lines.append("")

        lines.extend([
            "━" * 60,
            f"总计: {total_warnings} 警告, {total_errors} 错误",
            "━" * 60,
        ])

        return "\n".join(lines)

    def save_report(self, output_path: Optional[Path] = None):
        """保存反思报告到文件"""
        path = output_path or self.project_dir / ".ppt-reflection.json"
        data = {
            "project_dir": str(self.project_dir),
            "generated_at": datetime.now().isoformat(),
            "reflections": [r.to_dict() for r in self.reflections],
        }
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return path


def format_reflection(reflection: StageReflection) -> str:
    """格式化单个阶段的反思输出"""
    lines = [
        "",
        "━" * 50,
        f"📋 STAGE REFLECTION: {reflection.stage.upper()}",
        "━" * 50,
    ]

    for check in reflection.checks:
        icon = "✅" if check.passed else ("⚠️" if check.severity == "warning" else "❌")
        lines.append(f"{icon} {check.message}")

    if reflection.warnings:
        lines.append("")
        lines.append("⚠️  Warnings:")
        for w in reflection.warnings:
            lines.append(f"   - {w}")

    if reflection.errors:
        lines.append("")
        lines.append("❌ Errors:")
        for e in reflection.errors:
            lines.append(f"   - {e}")

    lines.append("")
    lines.append(f"📌 Next: {', '.join(reflection.next_steps)}")
    lines.append("━" * 50)

    return "\n".join(lines)


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stage Reflector CLI")
    parser.add_argument("project_dir", help="Project directory")
    parser.add_argument("--stage", choices=["init", "skeleton", "research", "images", "enrich", "render", "all"],
                       default="all", help="Stage to reflect on")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    args = parser.parse_args()

    reflector = StageReflector(Path(args.project_dir))

    if args.stage == "all":
        reflector.reflect_init()
        reflector.reflect_skeleton()
        reflector.reflect_research()
        reflector.reflect_images()
        reflector.reflect_enrich()
        reflector.reflect_render()
        print(reflector.get_final_report())
    else:
        method = getattr(reflector, f"reflect_{args.stage}")
        reflection = method()
        print(format_reflection(reflection))

    if args.save:
        path = reflector.save_report()
        print(f"\nReport saved to: {path}")
