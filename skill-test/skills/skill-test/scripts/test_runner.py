#!/usr/bin/env python3
"""
Claude Code Skill Test Runner

Validates skill installation, configuration, and execution readiness.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class Status(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    SKIP = "skip"


@dataclass
class TestResult:
    name: str
    status: Status
    message: str = ""
    details: list[str] = field(default_factory=list)


@dataclass
class SkillTestResult:
    name: str
    plugin: str
    path: Path
    installation: TestResult | None = None
    dependencies: TestResult | None = None
    smoke_test: TestResult | None = None

    @property
    def status(self) -> Status:
        results = [self.installation, self.dependencies, self.smoke_test]
        results = [r for r in results if r is not None]
        if not results:
            return Status.SKIP
        if any(r.status == Status.FAIL for r in results):
            return Status.FAIL
        if any(r.status == Status.WARN for r in results):
            return Status.WARN
        return Status.PASS


class SkillValidator:
    """Validates Claude Code skills."""

    def __init__(self, root: Path, verbose: bool = False):
        self.root = root
        self.verbose = verbose
        self.skills: list[dict] = []
        self.results: list[SkillTestResult] = []

    def log(self, msg: str, level: str = "info") -> None:
        if self.verbose or level == "error":
            prefix = {"info": "  ", "warn": "  [!]", "error": "  [X]", "ok": "  [+]"}
            print(f"{prefix.get(level, '  ')}{msg}")

    def discover_plugins(self) -> list[dict]:
        """Discover all plugins in the project."""
        plugins = []

        # Check marketplace.json
        marketplace_path = self.root / ".claude-plugin" / "marketplace.json"
        if marketplace_path.exists():
            try:
                with open(marketplace_path) as f:
                    data = json.load(f)
                    for plugin in data.get("plugins", []):
                        plugin_path = self.root / plugin.get("source", "")
                        if plugin_path.exists():
                            plugins.append({
                                "name": plugin.get("name", ""),
                                "path": plugin_path,
                                "source": "marketplace"
                            })
            except json.JSONDecodeError as e:
                self.log(f"Error parsing marketplace.json: {e}", "error")

        # Also search for plugin.json files directly
        for plugin_json in self.root.rglob(".claude-plugin/plugin.json"):
            plugin_path = plugin_json.parent.parent
            if plugin_path not in [p["path"] for p in plugins]:
                try:
                    with open(plugin_json) as f:
                        data = json.load(f)
                        plugins.append({
                            "name": data.get("name", plugin_path.name),
                            "path": plugin_path,
                            "source": "direct"
                        })
                except json.JSONDecodeError:
                    pass

        return plugins

    def discover_skills(self) -> list[dict]:
        """Discover all skills from plugins."""
        plugins = self.discover_plugins()
        skills = []

        for plugin in plugins:
            plugin_json = plugin["path"] / ".claude-plugin" / "plugin.json"
            if not plugin_json.exists():
                continue

            try:
                with open(plugin_json) as f:
                    data = json.load(f)

                for skill_def in data.get("skills", []):
                    # Handle both string paths and object definitions
                    if isinstance(skill_def, str):
                        skill_path = plugin["path"] / skill_def
                        skill_name = skill_path.name
                    else:
                        skill_path = plugin["path"] / skill_def.get("path", "")
                        skill_name = skill_def.get("name", skill_path.name)

                    if skill_path.exists():
                        skills.append({
                            "name": skill_name,
                            "plugin": plugin["name"],
                            "path": skill_path,
                            "plugin_path": plugin["path"]
                        })
            except json.JSONDecodeError:
                self.log(f"Error parsing {plugin_json}", "error")

        self.skills = skills
        return skills

    def validate_skill_md(self, skill: dict) -> TestResult:
        """Validate SKILL.md format and content."""
        skill_md = skill["path"] / "SKILL.md"
        details = []

        if not skill_md.exists():
            return TestResult(
                name="SKILL.md",
                status=Status.FAIL,
                message="SKILL.md not found"
            )

        try:
            content = skill_md.read_text(encoding="utf-8")
        except Exception as e:
            return TestResult(
                name="SKILL.md",
                status=Status.FAIL,
                message=f"Cannot read file: {e}"
            )

        # Check YAML frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return TestResult(
                name="SKILL.md",
                status=Status.FAIL,
                message="Missing YAML frontmatter"
            )

        frontmatter = frontmatter_match.group(1)

        # Check required fields
        has_name = re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE)
        has_description = re.search(r"^description:\s*", frontmatter, re.MULTILINE)

        if not has_name:
            details.append("Missing 'name' field in frontmatter")
        if not has_description:
            details.append("Missing 'description' field in frontmatter")

        if details:
            return TestResult(
                name="SKILL.md",
                status=Status.FAIL,
                message="Invalid frontmatter",
                details=details
            )

        # Check for markdown body
        body = content[frontmatter_match.end():].strip()
        if len(body) < 100:
            details.append("SKILL.md body is very short (< 100 chars)")

        # Check for usage section
        if "## " not in body:
            details.append("No sections (##) found in body")

        status = Status.WARN if details else Status.PASS
        return TestResult(
            name="SKILL.md",
            status=status,
            message="Valid" if status == Status.PASS else "Valid with warnings",
            details=details
        )

    def validate_plugin_json(self, skill: dict) -> TestResult:
        """Validate plugin.json for the skill's plugin."""
        plugin_json = skill["plugin_path"] / ".claude-plugin" / "plugin.json"
        details = []

        if not plugin_json.exists():
            return TestResult(
                name="plugin.json",
                status=Status.FAIL,
                message="plugin.json not found"
            )

        try:
            with open(plugin_json) as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            return TestResult(
                name="plugin.json",
                status=Status.FAIL,
                message=f"Invalid JSON: {e}"
            )

        # Check required fields
        required = ["name", "version", "skills"]
        for field in required:
            if field not in data:
                details.append(f"Missing required field: {field}")

        # Check skills array
        if "skills" in data:
            skill_found = False
            for s in data["skills"]:
                # Handle both string paths and object definitions
                if isinstance(s, str):
                    # String format: just the path
                    if Path(s).name == skill["name"] or s.endswith(skill["name"]):
                        skill_found = True
                        break
                else:
                    # Object format: {name, path}
                    if s.get("name") == skill["name"]:
                        skill_found = True
                        if "path" not in s:
                            details.append(f"Skill {skill['name']} missing 'path'")
                        break
            if not skill_found:
                details.append(f"Skill {skill['name']} not in skills array")

        # Check version format
        if "version" in data:
            if not re.match(r"^\d+\.\d+\.\d+", data["version"]):
                details.append("Version should follow semver (x.y.z)")

        if details:
            return TestResult(
                name="plugin.json",
                status=Status.FAIL if any("Missing required" in d for d in details) else Status.WARN,
                message="Validation issues",
                details=details
            )

        return TestResult(
            name="plugin.json",
            status=Status.PASS,
            message="Valid"
        )

    def check_python_deps(self, skill: dict) -> list[str]:
        """Check Python dependencies."""
        issues = []
        skill_path = skill["path"]

        # Check for requirements.txt
        req_file = skill_path / "requirements.txt"
        if req_file.exists():
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    installed = {p["name"].lower() for p in json.loads(result.stdout)}
                    with open(req_file) as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                pkg = re.split(r"[<>=!]", line)[0].lower()
                                if pkg not in installed:
                                    issues.append(f"Python package not installed: {pkg}")
            except Exception as e:
                issues.append(f"Cannot check pip packages: {e}")

        # Check scripts directory for Python files
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "py_compile", str(py_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        issues.append(f"Python syntax error in {py_file.name}")
                except subprocess.TimeoutExpired:
                    issues.append(f"Timeout checking {py_file.name}")

        return issues

    def check_nodejs_deps(self, skill: dict) -> list[str]:
        """Check Node.js dependencies."""
        issues = []
        skill_path = skill["path"]

        # Check for package.json
        pkg_file = skill_path / "package.json"
        if pkg_file.exists():
            try:
                with open(pkg_file) as f:
                    pkg_data = json.load(f)

                deps = pkg_data.get("dependencies", {})
                dev_deps = pkg_data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}

                if all_deps:
                    node_modules = skill_path / "node_modules"
                    if not node_modules.exists():
                        issues.append("node_modules not found - run npm install")
                    else:
                        for dep in all_deps:
                            dep_path = node_modules / dep
                            if not dep_path.exists():
                                issues.append(f"Node package not installed: {dep}")
            except json.JSONDecodeError as e:
                issues.append(f"Invalid package.json: {e}")

        # Check scripts directory for JS files
        scripts_dir = skill_path / "scripts"
        if scripts_dir.exists():
            for js_file in scripts_dir.glob("*.js"):
                try:
                    result = subprocess.run(
                        ["node", "--check", str(js_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode != 0:
                        issues.append(f"Node.js syntax error in {js_file.name}")
                except FileNotFoundError:
                    issues.append("Node.js not found")
                    break
                except subprocess.TimeoutExpired:
                    issues.append(f"Timeout checking {js_file.name}")

        return issues

    def check_cli_deps(self, skill: dict) -> list[str]:
        """Check CLI tool dependencies from SKILL.md."""
        issues = []
        skill_md = skill["path"] / "SKILL.md"

        if not skill_md.exists():
            return issues

        content = skill_md.read_text(encoding="utf-8")

        # Common CLI patterns
        cli_patterns = [
            (r"npm install -g\s+(\S+)", "npm"),
            (r"cargo install\s+(\S+)", "cargo"),
            (r"brew install\s+(\S+)", "brew"),
        ]

        for pattern, _ in cli_patterns:
            matches = re.findall(pattern, content)
            for pkg in matches:
                pkg_name = pkg.split("/")[-1]
                try:
                    result = subprocess.run(
                        ["which", pkg_name],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode != 0:
                        issues.append(f"CLI tool not found: {pkg_name}")
                except Exception:
                    pass

        return issues

    def validate_dependencies(self, skill: dict) -> TestResult:
        """Validate all dependencies for a skill."""
        details = []

        # Check Python dependencies
        details.extend(self.check_python_deps(skill))

        # Check Node.js dependencies
        details.extend(self.check_nodejs_deps(skill))

        # Check CLI dependencies
        details.extend(self.check_cli_deps(skill))

        if not details:
            return TestResult(
                name="Dependencies",
                status=Status.PASS,
                message="All dependencies satisfied"
            )

        # Determine severity
        critical = any("not installed" in d or "not found" in d for d in details)
        return TestResult(
            name="Dependencies",
            status=Status.FAIL if critical else Status.WARN,
            message=f"{len(details)} issue(s) found",
            details=details
        )

    def run_smoke_test(self, skill: dict) -> TestResult:
        """Run smoke tests for a skill."""
        details = []
        scripts_dir = skill["path"] / "scripts"

        if not scripts_dir.exists():
            return TestResult(
                name="Smoke Test",
                status=Status.SKIP,
                message="No scripts directory"
            )

        # Find main script
        main_scripts = []
        for pattern in ["main.py", "*.py", "render.js", "main.js", "*.js"]:
            scripts = list(scripts_dir.glob(pattern))
            if scripts:
                main_scripts = scripts[:3]  # Test up to 3 scripts
                break

        if not main_scripts:
            return TestResult(
                name="Smoke Test",
                status=Status.SKIP,
                message="No testable scripts found"
            )

        passed = 0
        for script in main_scripts:
            if script.suffix == ".py":
                # Try --help or --check
                for flag in ["--help", "--check", "-h"]:
                    try:
                        result = subprocess.run(
                            [sys.executable, str(script), flag],
                            capture_output=True,
                            text=True,
                            timeout=10,
                            cwd=scripts_dir
                        )
                        if result.returncode == 0:
                            passed += 1
                            details.append(f"[PASS] {script.name} {flag}")
                            break
                    except subprocess.TimeoutExpired:
                        details.append(f"[TIMEOUT] {script.name} {flag}")
                    except Exception as e:
                        details.append(f"[ERROR] {script.name}: {e}")
                else:
                    # Syntax check as fallback
                    try:
                        result = subprocess.run(
                            [sys.executable, "-m", "py_compile", str(script)],
                            capture_output=True,
                            timeout=10
                        )
                        if result.returncode == 0:
                            passed += 1
                            details.append(f"[PASS] {script.name} (syntax ok)")
                    except Exception:
                        details.append(f"[FAIL] {script.name}")

            elif script.suffix == ".js":
                # Node.js syntax check
                try:
                    result = subprocess.run(
                        ["node", "--check", str(script)],
                        capture_output=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        passed += 1
                        details.append(f"[PASS] {script.name} (syntax ok)")
                    else:
                        details.append(f"[FAIL] {script.name}")
                except FileNotFoundError:
                    details.append("[SKIP] Node.js not available")
                except Exception as e:
                    details.append(f"[ERROR] {script.name}: {e}")

        total = len(main_scripts)
        if passed == total:
            status = Status.PASS
            message = f"All {total} script(s) passed"
        elif passed > 0:
            status = Status.WARN
            message = f"{passed}/{total} script(s) passed"
        else:
            status = Status.FAIL
            message = "No scripts passed"

        return TestResult(
            name="Smoke Test",
            status=status,
            message=message,
            details=details
        )

    def test_skill(self, skill: dict, level: int = 3) -> SkillTestResult:
        """Run all tests for a skill."""
        result = SkillTestResult(
            name=skill["name"],
            plugin=skill["plugin"],
            path=skill["path"]
        )

        # Level 1: Installation
        skill_md_result = self.validate_skill_md(skill)
        plugin_json_result = self.validate_plugin_json(skill)

        # Combine into installation result
        details = skill_md_result.details + plugin_json_result.details
        if skill_md_result.status == Status.FAIL or plugin_json_result.status == Status.FAIL:
            status = Status.FAIL
        elif skill_md_result.status == Status.WARN or plugin_json_result.status == Status.WARN:
            status = Status.WARN
        else:
            status = Status.PASS

        result.installation = TestResult(
            name="Installation",
            status=status,
            message=f"SKILL.md: {skill_md_result.status.value}, plugin.json: {plugin_json_result.status.value}",
            details=details
        )

        if level < 2:
            return result

        # Level 2: Dependencies
        result.dependencies = self.validate_dependencies(skill)

        if level < 3:
            return result

        # Level 3: Smoke Test
        result.smoke_test = self.run_smoke_test(skill)

        return result

    def run_all(self, skill_filter: list[str] | None = None, level: int = 3) -> list[SkillTestResult]:
        """Run tests on all discovered skills."""
        skills = self.discover_skills()

        if skill_filter:
            skills = [s for s in skills if s["name"] in skill_filter]

        for skill in skills:
            result = self.test_skill(skill, level)
            self.results.append(result)

        return self.results

    def print_results(self) -> None:
        """Print test results to console."""
        status_icons = {
            Status.PASS: "\033[32m[PASS]\033[0m",
            Status.WARN: "\033[33m[WARN]\033[0m",
            Status.FAIL: "\033[31m[FAIL]\033[0m",
            Status.SKIP: "\033[90m[SKIP]\033[0m",
        }

        print("\n=== Skill Test Suite ===\n")

        for result in self.results:
            icon = status_icons[result.status]
            print(f"{icon} {result.name} ({result.plugin})")

            for test in [result.installation, result.dependencies, result.smoke_test]:
                if test is None:
                    continue
                test_icon = status_icons[test.status]
                print(f"    {test_icon} {test.name}: {test.message}")
                if self.verbose and test.details:
                    for detail in test.details:
                        print(f"        - {detail}")

            print()

        # Summary
        counts = {s: 0 for s in Status}
        for r in self.results:
            counts[r.status] += 1

        print("=" * 40)
        print(f"Summary: {counts[Status.PASS]} passed, {counts[Status.WARN]} warnings, {counts[Status.FAIL]} failed, {counts[Status.SKIP]} skipped")
        print()

    def to_json(self) -> dict:
        """Convert results to JSON format."""
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "pass": sum(1 for r in self.results if r.status == Status.PASS),
                "warn": sum(1 for r in self.results if r.status == Status.WARN),
                "fail": sum(1 for r in self.results if r.status == Status.FAIL),
                "skip": sum(1 for r in self.results if r.status == Status.SKIP),
            },
            "skills": [
                {
                    "name": r.name,
                    "plugin": r.plugin,
                    "path": str(r.path),
                    "status": r.status.value,
                    "tests": {
                        "installation": {
                            "status": r.installation.status.value if r.installation else "skip",
                            "message": r.installation.message if r.installation else "",
                            "details": r.installation.details if r.installation else [],
                        } if r.installation else None,
                        "dependencies": {
                            "status": r.dependencies.status.value if r.dependencies else "skip",
                            "message": r.dependencies.message if r.dependencies else "",
                            "details": r.dependencies.details if r.dependencies else [],
                        } if r.dependencies else None,
                        "smoke_test": {
                            "status": r.smoke_test.status.value if r.smoke_test else "skip",
                            "message": r.smoke_test.message if r.smoke_test else "",
                            "details": r.smoke_test.details if r.smoke_test else [],
                        } if r.smoke_test else None,
                    }
                }
                for r in self.results
            ]
        }

    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            "# Skill Test Report",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Summary",
            "",
        ]

        counts = {s: 0 for s in Status}
        for r in self.results:
            counts[r.status] += 1

        lines.extend([
            f"| Status | Count |",
            f"|--------|-------|",
            f"| Pass | {counts[Status.PASS]} |",
            f"| Warn | {counts[Status.WARN]} |",
            f"| Fail | {counts[Status.FAIL]} |",
            f"| Skip | {counts[Status.SKIP]} |",
            "",
            "## Results",
            "",
        ])

        for result in self.results:
            status_emoji = {
                Status.PASS: ":white_check_mark:",
                Status.WARN: ":warning:",
                Status.FAIL: ":x:",
                Status.SKIP: ":grey_question:",
            }[result.status]

            lines.append(f"### {status_emoji} {result.name}")
            lines.append(f"")
            lines.append(f"**Plugin:** {result.plugin}")
            lines.append(f"**Path:** `{result.path}`")
            lines.append("")

            for test in [result.installation, result.dependencies, result.smoke_test]:
                if test is None:
                    continue
                lines.append(f"#### {test.name}: {test.status.value.upper()}")
                lines.append(f"{test.message}")
                if test.details:
                    lines.append("")
                    for detail in test.details:
                        lines.append(f"- {detail}")
                lines.append("")

        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code Skill Test Runner"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Project root directory"
    )
    parser.add_argument(
        "--skill",
        action="append",
        dest="skills",
        help="Test specific skill(s) only"
    )
    parser.add_argument(
        "--level",
        type=int,
        choices=[1, 2, 3],
        default=3,
        help="Test level (1=installation, 2=dependencies, 3=smoke test)"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Output markdown report file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format"
    )

    args = parser.parse_args()

    validator = SkillValidator(args.root, verbose=args.verbose)
    validator.run_all(skill_filter=args.skills, level=args.level)

    if args.json:
        print(json.dumps(validator.to_json(), indent=2))
    elif args.report:
        report = validator.to_markdown()
        args.report.write_text(report)
        print(f"Report written to: {args.report}")
    else:
        validator.print_results()

    # Exit with error if any failures
    if any(r.status == Status.FAIL for r in validator.results):
        sys.exit(1)


if __name__ == "__main__":
    main()
