#!/usr/bin/env python3
"""
Deep Research Adapter - 调用 openai-deep-research skill

使用 subprocess 执行研究，支持：
- 后台运行
- 超时控制
- 进度输出
"""

import json
import logging
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .skill_discovery import SkillDiscovery, SkillInfo

log = logging.getLogger("research.adapter")


@dataclass
class ResearchResult:
    """研究结果"""
    success: bool
    markdown: str = ""
    error: Optional[str] = None
    duration_seconds: float = 0
    output_file: Optional[Path] = None
    process_output: str = ""


@dataclass
class ResearchProgress:
    """研究进度"""
    elapsed_seconds: int
    status: str
    message: str


class DeepResearchAdapter:
    """Deep Research 适配器"""

    # 默认配置
    DEFAULT_TIMEOUT = 2400  # 40 分钟
    DEFAULT_SESSION = "default"  # 复用已有的 openai-deep-research session
    POLL_INTERVAL = 30  # 每30秒检查一次进度

    def __init__(
        self,
        skill_info: SkillInfo,
        headless: bool = True,
        timeout: int = DEFAULT_TIMEOUT,
        session: str = DEFAULT_SESSION,
        verbose: bool = False,
        progress_callback: Optional[Callable[[ResearchProgress], None]] = None
    ):
        self.skill_info = skill_info
        self.headless = headless
        self.timeout = timeout
        self.session = session
        self.verbose = verbose
        self.progress_callback = progress_callback

        if verbose:
            log.setLevel(logging.DEBUG)

    def run_query(self, query: str) -> ResearchResult:
        """执行研究查询"""
        if not self.skill_info.available:
            return ResearchResult(
                success=False,
                error="openai-deep-research skill not available"
            )

        if not self.skill_info.script_path:
            return ResearchResult(
                success=False,
                error="Script path not found"
            )

        # 创建临时输出文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.md',
            delete=False,
            prefix='research_'
        ) as f:
            output_file = Path(f.name)

        start_time = time.time()
        log.info(f"Starting Deep Research (timeout: {self.timeout}s)")
        log.info(f"  Query: {query[:100]}...")
        log.info(f"  Output: {output_file}")

        try:
            result = self._run_subprocess(query, output_file)
            result.duration_seconds = time.time() - start_time

            # 读取输出文件
            if output_file.exists():
                result.markdown = output_file.read_text(encoding='utf-8')
                result.output_file = output_file
                if result.markdown:
                    result.success = True
                    log.info(f"Research completed: {len(result.markdown)} chars in {result.duration_seconds:.1f}s")

            return result

        except subprocess.TimeoutExpired:
            log.warning(f"Research timeout after {self.timeout}s")
            # 尝试读取部分结果
            partial_content = ""
            if output_file.exists():
                partial_content = output_file.read_text(encoding='utf-8')

            return ResearchResult(
                success=bool(partial_content),
                markdown=partial_content,
                error=f"Timeout after {self.timeout}s",
                duration_seconds=time.time() - start_time,
                output_file=output_file
            )

        except Exception as e:
            log.error(f"Research failed: {e}")
            return ResearchResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def _run_subprocess(self, query: str, output_file: Path) -> ResearchResult:
        """运行子进程执行研究"""
        cmd = [
            sys.executable,
            str(self.skill_info.script_path),
            query,
            "-o", str(output_file),
            "--timeout", str(self.timeout),
            "--session", self.session,
        ]

        if self.headless:
            cmd.append("--headless")

        if self.verbose:
            cmd.append("-v")

        log.debug(f"Running: {' '.join(cmd[:4])}...")

        # 使用 Popen 以便监控进度
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,  # 行缓冲
        )

        output_lines: List[str] = []
        start_time = time.time()

        try:
            while True:
                # 检查进程是否结束
                return_code = process.poll()
                if return_code is not None:
                    # 读取剩余输出
                    remaining = process.stdout.read() if process.stdout else ""
                    if remaining:
                        output_lines.append(remaining)
                    break

                # 读取输出（非阻塞）
                if process.stdout:
                    line = process.stdout.readline()
                    if line:
                        output_lines.append(line)
                        if self.verbose:
                            print(f"  [research] {line.strip()}")

                # 检查超时
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    log.warning(f"Killing process after {elapsed:.0f}s")
                    process.kill()
                    raise subprocess.TimeoutExpired(cmd, self.timeout)

                # 报告进度
                if self.progress_callback and int(elapsed) % self.POLL_INTERVAL == 0:
                    self.progress_callback(ResearchProgress(
                        elapsed_seconds=int(elapsed),
                        status="running",
                        message=f"Research in progress ({int(elapsed)}s elapsed)"
                    ))

                time.sleep(1)

            process_output = ''.join(output_lines)

            if return_code != 0:
                return ResearchResult(
                    success=False,
                    error=f"Process exited with code {return_code}",
                    process_output=process_output
                )

            return ResearchResult(
                success=True,
                process_output=process_output
            )

        finally:
            # 确保进程终止
            if process.poll() is None:
                process.kill()
                process.wait()

    def check_prerequisites(self) -> Dict[str, Any]:
        """检查前置条件"""
        # 检查实际使用的 session 是否有效
        has_session = self._check_session_valid(self.session)

        checks = {
            "skill_available": self.skill_info.available,
            "script_exists": self.skill_info.script_path and self.skill_info.script_path.exists(),
            "has_session": has_session,
            "session_name": self.session,
            "playwright_installed": self._check_playwright(),
        }

        # headless 模式必须有 session
        if self.headless:
            checks["all_passed"] = all([
                checks["skill_available"],
                checks["script_exists"],
                checks["playwright_installed"],
                checks["has_session"],  # headless 模式必须有 session
            ])
        else:
            # 非 headless 模式可以不需要 session（会弹出浏览器让用户登录）
            checks["all_passed"] = all([
                checks["skill_available"],
                checks["script_exists"],
                checks["playwright_installed"],
            ])

        if not checks["has_session"]:
            checks["session_hint"] = (
                f"Session '{self.session}' 不存在。首次使用需要手动登录。\n"
                f"请运行: python deep_research_browser.py --login --session {self.session}"
            )

        return checks

    def _check_session_valid(self, session_name: str) -> bool:
        """检查指定 session 是否有效"""
        try:
            session_dir = Path.home() / ".openai-deep-research"
            session_file = session_dir / f"session_{session_name}.json"

            if not session_file.exists():
                return False

            import json
            data = json.loads(session_file.read_text())
            return bool(data.get("cookies"))
        except Exception:
            return False

    def _check_playwright(self) -> bool:
        """检查 playwright 是否安装"""
        try:
            import importlib.util
            return importlib.util.find_spec("playwright") is not None
        except Exception:
            return False

    def login(self) -> bool:
        """交互式登录"""
        if not self.skill_info.script_path:
            log.error("Script path not found")
            return False

        log.info("Starting login process...")
        log.info("A browser window will open. Please log in to ChatGPT.")

        cmd = [
            sys.executable,
            str(self.skill_info.script_path),
            "--login",
            "--session", self.session,
        ]

        try:
            result = subprocess.run(cmd, timeout=600)  # 10分钟登录超时
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            log.error("Login timeout")
            return False
        except Exception as e:
            log.error(f"Login failed: {e}")
            return False


class DeepResearchManager:
    """Deep Research 管理器（高级 API）"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.discovery = SkillDiscovery()
        self._adapter: Optional[DeepResearchAdapter] = None

    def get_adapter(self) -> Optional[DeepResearchAdapter]:
        """获取适配器（延迟初始化）"""
        if self._adapter is None:
            skill_info = self.discovery.find_skill("openai-deep-research")
            if skill_info.available:
                self._adapter = DeepResearchAdapter(
                    skill_info=skill_info,
                    verbose=self.verbose
                )
        return self._adapter

    def is_available(self) -> bool:
        """检查 Deep Research 是否可用"""
        adapter = self.get_adapter()
        if not adapter:
            return False
        checks = adapter.check_prerequisites()
        return checks.get("all_passed", False)

    def research(self, query: str, timeout: int = 2400) -> ResearchResult:
        """执行研究"""
        adapter = self.get_adapter()
        if not adapter:
            return ResearchResult(
                success=False,
                error="openai-deep-research not available"
            )

        adapter.timeout = timeout
        return adapter.run_query(query)


# CLI 测试
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Deep Research Adapter CLI")
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("--check", action="store_true", help="Check prerequisites")
    parser.add_argument("--login", action="store_true", help="Interactive login")
    parser.add_argument("-t", "--timeout", type=int, default=2400, help="Timeout in seconds")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    manager = DeepResearchManager(verbose=args.verbose)
    adapter = manager.get_adapter()

    if args.check:
        if adapter:
            checks = adapter.check_prerequisites()
            print("\nPrerequisite Checks:")
            for key, value in checks.items():
                status = "OK" if value else "FAIL"
                print(f"  {key}: {status}")
        else:
            print("openai-deep-research skill not found")

    elif args.login:
        if adapter:
            success = adapter.login()
            print(f"\nLogin {'successful' if success else 'failed'}")
        else:
            print("openai-deep-research skill not found")

    elif args.query:
        print(f"\nResearching: {args.query[:50]}...")
        result = manager.research(args.query, timeout=args.timeout)
        print(f"\nResult:")
        print(f"  Success: {result.success}")
        print(f"  Duration: {result.duration_seconds:.1f}s")
        print(f"  Content length: {len(result.markdown)} chars")
        if result.error:
            print(f"  Error: {result.error}")
        if result.markdown:
            print(f"\n--- Content Preview ---\n{result.markdown[:500]}...")

    else:
        parser.print_help()
