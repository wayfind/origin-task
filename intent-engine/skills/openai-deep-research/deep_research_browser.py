#!/usr/bin/env python3
"""
OpenAI Deep Research via browser automation.

Usage:
    # First time: login and save session
    python deep_research_browser.py --login

    # Subsequent runs (can be headless)
    python deep_research_browser.py "Your query" -o result.md --headless

    # Parallel runs with named sessions
    python deep_research_browser.py "Query 1" -o r1.md --session work &
    python deep_research_browser.py "Query 2" -o r2.md --session personal &
"""

import argparse
import asyncio
import logging
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

# =============================================================================
# Configuration
# =============================================================================

STATE_DIR = Path.home() / ".openai-deep-research"
DEFAULT_SESSION = "default"


@dataclass
class TimeoutConfig:
    """Timeout settings in various units."""
    default_s: int = 2400          # 40 minutes total timeout
    poll_interval_s: int = 60      # Check for completion every 60s
    selector_ms: int = 2000        # Wait for UI elements
    login_check_ms: int = 5000     # Quick check if logged in
    login_wait_ms: int = 300000    # 5 minutes for manual login
    input_wait_ms: int = 3000      # Wait for input field


@dataclass
class ContentConfig:
    """Content detection thresholds."""
    tail_check_chars: int = 2000       # Check last N chars for thinking patterns
    min_report_chars: int = 3000       # Minimum chars for a valid report
    min_content_chars: int = 2000      # Minimum chars for any useful content
    max_query_chars: int = 50000       # Maximum query length
    stable_report_count: int = 15      # Iterations before report is complete
    stable_response_count: int = 45    # Iterations before response is stable
    status_interval: int = 30          # Show status every N iterations
    significant_diff_chars: int = 50   # Minimum chars to log as progress


@dataclass
class BrowserConfig:
    """Browser settings."""
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1400, "height": 900})
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"


@dataclass
class SelectorsConfig:
    """ChatGPT UI selectors (may need updates as UI changes)."""
    plus_btn: List[str] = field(default_factory=lambda: [
        'button[aria-label*="Attach"]', 'button[aria-label*="Add"]'
    ])
    input_field: List[str] = field(default_factory=lambda: [
        '#prompt-textarea', 'textarea[placeholder*="Message"]', 'div[contenteditable="true"]'
    ])
    submit_btn: List[str] = field(default_factory=lambda: [
        'button[data-testid="send-button"]', 'button[aria-label*="Send"]'
    ])
    assistant_msg: str = '[data-message-author-role="assistant"]'
    login_indicator: List[str] = field(default_factory=lambda: [
        'nav', '[data-testid="profile-button"]'
    ])


@dataclass
class PatternsConfig:
    """Text patterns for content detection."""
    thinking: Tuple[str, ...] = (
        "i'm ", "i'll ", "let me ", "searching ", "reading ", "analyzing ",
        "gathering ", "piecing ", "feel free to keep chatting", "i'll get back to you",
    )
    report: Tuple[str, ...] = (
        "## Summary", "## Overview", "## Conclusion", "## Key Findings",
        "In conclusion,", "Based on my research,",
    )
    research_started: Tuple[str, ...] = (
        "I'll get back to you", "I'll let you know", "feel free to keep chatting",
    )
    clarifying: Tuple[str, ...] = (
        "could you clarify", "what specific", "would you like me to",
    )


@dataclass
class Config:
    """Main configuration container."""
    timeouts: TimeoutConfig = field(default_factory=TimeoutConfig)
    content: ContentConfig = field(default_factory=ContentConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    selectors: SelectorsConfig = field(default_factory=SelectorsConfig)
    patterns: PatternsConfig = field(default_factory=PatternsConfig)


# Global config instance
cfg = Config()

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    level=logging.INFO,
    stream=sys.stdout,
)
log = logging.getLogger("deep_research")

# =============================================================================
# Session management
# =============================================================================

OLD_STATE_FILE = STATE_DIR / "browser_state.json"  # Legacy format


def get_state_file(session: str) -> Path:
    """Get state file path for a named session."""
    return STATE_DIR / f"session_{session}.json"


def migrate_old_session():
    """Migrate old browser_state.json to new session format."""
    if OLD_STATE_FILE.exists():
        new_file = get_state_file(DEFAULT_SESSION)
        if not new_file.exists():
            shutil.copy(OLD_STATE_FILE, new_file)
            log.info(f"Migrated old session to: {new_file}")
            return True
    return False


def has_valid_session(session: str) -> bool:
    """Check if a session has saved credentials."""
    state_file = get_state_file(session)
    if not state_file.exists():
        return False
    # Check file is not empty and has cookies
    try:
        import json
        data = json.loads(state_file.read_text())
        return bool(data.get("cookies"))
    except Exception:
        return False


def list_sessions() -> list:
    """List all available sessions."""
    if not STATE_DIR.exists():
        return []
    return [f.stem.replace("session_", "") for f in STATE_DIR.glob("session_*.json")]


# =============================================================================
# Playwright check
# =============================================================================


def check_playwright() -> bool:
    """Check if Playwright and Chromium are properly installed."""
    # Check playwright module
    try:
        import playwright
    except ImportError:
        log.error("Playwright not installed.")
        log.error("")
        log.error("To install, run:")
        log.error("  pip install playwright")
        log.error("  playwright install chromium")
        return False

    # Check chromium browser
    chromium_path = shutil.which("chromium") or shutil.which("chromium-browser")

    # Also check playwright's bundled chromium
    try:
        result = subprocess.run(
            ["playwright", "install", "--dry-run", "chromium"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # If dry-run says nothing to install, chromium is installed
        if "chromium" in result.stdout.lower() and "up to date" not in result.stdout.lower():
            # Chromium needs installation
            log.error("Playwright Chromium not installed.")
            log.error("")
            log.error("To install, run:")
            log.error("  playwright install chromium")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # playwright CLI not available, try importing directly
        pass

    # Final check: try to import the async API
    try:
        from playwright.async_api import async_playwright
        return True
    except Exception as e:
        log.error(f"Playwright import failed: {e}")
        return False


# Try importing playwright (will be checked again in main)
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeout = Exception  # Placeholder

# =============================================================================
# Core functions
# =============================================================================


def is_thinking(text):
    """Check if text contains thinking patterns (check last N chars)."""
    tail = text[-cfg.content.tail_check_chars:].lower() if len(text) > cfg.content.tail_check_chars else text.lower()
    return any(p in tail for p in cfg.patterns.thinking)


def is_final_report(text):
    """Check if text looks like a final report."""
    if len(text) < cfg.content.min_report_chars:
        return False
    has_structure = any(p in text for p in cfg.patterns.report)
    return has_structure and not is_thinking(text)


def has_research_started(text):
    """Check if Deep Research started in background."""
    return any(p in text for p in cfg.patterns.research_started)


def is_clarifying(text):
    """Check if asking clarifying question."""
    return any(p in text.lower() for p in cfg.patterns.clarifying)


async def save_state(context, session: str):
    """Save browser state for a session."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = get_state_file(session)
    await context.storage_state(path=str(state_file))
    log.debug(f"State saved to {state_file}")


async def try_click(page, selectors, timeout_ms=cfg.timeouts.selector_ms):
    """Try clicking first matching selector from list."""
    for sel in selectors:
        try:
            elem = await page.wait_for_selector(sel, timeout=timeout_ms)
            if elem:
                await elem.click()
                return True
        except PlaywrightTimeout:
            continue
        except Exception as e:
            log.debug(f"try_click error for {sel}: {e}")
    return False


async def extract_content(page):
    """Extract assistant response content."""
    content = ""
    try:
        elems = await page.query_selector_all(cfg.selectors.assistant_msg)
        for elem in elems:
            try:
                content += await elem.inner_text() + "\n\n"
            except Exception as e:
                log.debug(f"extract_content inner error: {e}")
    except Exception as e:
        log.debug(f"extract_content error: {e}")
    return content


async def wait_for_login(page, session: str, is_login_mode: bool = False):
    """Wait for user to login if needed."""
    # Check if already logged in
    for sel in cfg.selectors.login_indicator:
        try:
            await page.wait_for_selector(sel, timeout=cfg.timeouts.login_check_ms)
            if is_login_mode:
                log.info("Already logged in!")
            return True
        except PlaywrightTimeout:
            continue

    # Show login instructions
    log.info("")
    log.info("=" * 60)
    log.info("  LOGIN REQUIRED")
    log.info("=" * 60)
    log.info("")
    log.info("  1. Log in to ChatGPT in the browser window")
    log.info("  2. Complete any 2FA if prompted")
    log.info("  3. Wait until you see the chat interface")
    log.info("")
    log.info(f"  Session: {session}")
    log.info(f"  Cookies will be saved to: {get_state_file(session)}")
    log.info("")
    log.info("  (Waiting up to 5 minutes...)")
    log.info("=" * 60)
    log.info("")

    # Wait for login
    for sel in cfg.selectors.login_indicator:
        try:
            await page.wait_for_selector(sel, timeout=cfg.timeouts.login_wait_ms)
            log.info("")
            log.info("=" * 60)
            log.info("  LOGIN SUCCESSFUL!")
            log.info("=" * 60)
            log.info(f"  Session '{session}' saved.")
            log.info("  You can now run with --headless for future queries.")
            log.info("=" * 60)
            log.info("")
            return True
        except PlaywrightTimeout:
            continue

    log.error("Login timeout (5 minutes)")
    return False


async def select_deep_research(page):
    """Try to select Deep Research mode using Playwright's text locator."""
    log.info("Looking for Deep Research option...")

    # Click plus button
    if not await try_click(page, cfg.selectors.plus_btn):
        log.warning("Could not find plus button")
        return False

    await asyncio.sleep(1)

    # Use Playwright's get_by_text for cleaner selection
    try:
        deep_research = page.get_by_text("Deep research", exact=False)
        if await deep_research.count() > 0:
            # Click the first visible match
            await deep_research.first.click()
            log.info("Selected Deep Research")
            return True
    except Exception as e:
        log.debug(f"get_by_text failed: {e}")

    log.warning("Could not find Deep Research - using current model")
    return False


async def submit_query(page, query):
    """Submit a query."""
    log.info(f"Submitting: {query[:50]}...")

    # Find input
    input_field = None
    for sel in cfg.selectors.input_field:
        try:
            input_field = await page.wait_for_selector(sel, timeout=cfg.timeouts.input_wait_ms)
            if input_field:
                break
        except PlaywrightTimeout:
            continue

    if not input_field:
        raise RuntimeError("Could not find input field")

    await input_field.click()
    await input_field.fill(query)
    await asyncio.sleep(0.5)

    # Submit - try button first, then Enter key
    submitted = False
    for sel in cfg.selectors.submit_btn:
        try:
            btn = await page.query_selector(sel)
            if btn:
                await btn.click()
                submitted = True
                break
        except Exception as e:
            log.debug(f"Submit button click failed: {e}")

    if not submitted:
        await page.keyboard.press("Enter")

    log.info("Query submitted")


async def auto_respond_if_clarifying(page):
    """Auto-respond to clarifying questions."""
    await asyncio.sleep(3)
    try:
        elems = await page.query_selector_all(f"{cfg.selectors.assistant_msg} .markdown")
        if elems:
            text = await elems[-1].inner_text()
            if is_clarifying(text):
                log.info("Auto-responding to clarifying question...")
                await submit_query(page, "Please provide a comprehensive analysis covering all major aspects.")
                return True
    except Exception as e:
        log.debug(f"auto_respond_if_clarifying error: {e}")
    return False


async def wait_for_report(page, timeout):
    """Wait for Deep Research, refreshing periodically."""
    log.info(f"Waiting for report (max {timeout // 60} min, checking every {cfg.timeouts.poll_interval_s}s)")
    start = time.time()

    while time.time() - start < timeout:
        await asyncio.sleep(cfg.timeouts.poll_interval_s)
        elapsed = int(time.time() - start)
        mins = elapsed // 60

        log.info(f"  [{mins + 1} min] Checking...")

        try:
            await page.reload(wait_until="domcontentloaded", timeout=15000)
            await asyncio.sleep(5)

            text = await page.inner_text("body")
            if any(p in text for p in cfg.patterns.report):
                content = await extract_content(page)
                if content and len(content) > cfg.content.min_content_chars:
                    log.info(f"  [{mins + 1} min] Report found!")
                    return content

        except Exception as e:
            log.warning(f"  [{mins + 1} min] Error: {e}")

    log.warning(f"Timeout after {timeout // 60} minutes")
    return ""


async def wait_for_response(page, timeout):
    """Wait for streaming response."""
    log.info(f"Waiting for response (timeout: {timeout}s)")
    start = time.time()
    last_content = ""
    stable_count = 0
    auto_responded = False

    while time.time() - start < timeout:
        await asyncio.sleep(2)
        elapsed = int(time.time() - start)

        # Auto-respond to clarification
        if not auto_responded and stable_count >= 2:
            if await auto_respond_if_clarifying(page):
                auto_responded = True
                stable_count = 0
                last_content = ""
                await asyncio.sleep(10)

                # Check if switched to background mode
                text = await page.inner_text("body")
                if has_research_started(text):
                    log.info("Switching to refresh mode...")
                    return await wait_for_report(page, timeout - elapsed)
                continue

        # Extract content
        content = await extract_content(page)
        if not content:
            continue

        if content == last_content:
            stable_count += 1

            # Check completion
            if is_final_report(content) and stable_count >= cfg.content.stable_report_count:
                log.info(f"  [{elapsed}s] Report complete!")
                break
            elif stable_count >= cfg.content.stable_response_count and len(content) > cfg.content.min_content_chars:
                log.info(f"  [{elapsed}s] Response stable")
                break

            # Status every N iterations
            if stable_count % cfg.content.status_interval == 0:
                status = "thinking" if is_thinking(content) else "waiting"
                log.info(f"  [{elapsed}s] {status}, {len(content)} chars")
        else:
            if len(content) > len(last_content):
                diff = len(content) - len(last_content)
                if diff > cfg.content.significant_diff_chars:
                    log.info(f"  [{elapsed}s] +{diff} chars")
            stable_count = 0

        last_content = content

    is_report = is_final_report(last_content) if last_content else False
    log.info(f"  Done: {len(last_content)} chars, {'report' if is_report else 'partial'}")
    return last_content


async def run(query, output_file=None, headless=False, skip_model=False,
              timeout=cfg.timeouts.default_s, session=DEFAULT_SESSION, login_only=False):
    """Main entry point."""
    state_file = get_state_file(session)

    # Login-only mode
    if login_only:
        log.info("=" * 60)
        log.info("    OpenAI Deep Research - Login Mode")
        log.info("=" * 60)
        log.info(f"Session: {session}")
        headless = False  # Force visible browser for login
    else:
        log.info("=" * 60)
        log.info("    OpenAI Deep Research (Browser Automation)")
        log.info("=" * 60)
        log.info(f"Session: {session}")

    # Warn if headless without saved session
    if headless and not has_valid_session(session):
        log.warning("")
        log.warning("=" * 60)
        log.warning("  WARNING: Headless mode without saved session!")
        log.warning("=" * 60)
        log.warning("  Headless login is not possible.")
        log.warning("  Run with --login first to save credentials:")
        log.warning(f"    python deep_research_browser.py --login --session {session}")
        log.warning("")
        log.warning("  Falling back to visible browser...")
        log.warning("=" * 60)
        log.warning("")
        headless = False

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )

        # Setup context
        ctx_opts = {"viewport": cfg.browser.viewport, "user_agent": cfg.browser.user_agent}
        if state_file.exists():
            ctx_opts["storage_state"] = str(state_file)
            log.info(f"Loading session from {state_file}")

        context = await browser.new_context(**ctx_opts)
        page = await context.new_page()

        try:
            # Open ChatGPT
            log.info("Opening ChatGPT...")
            await page.goto("https://chatgpt.com/", wait_until="networkidle")

            if not await wait_for_login(page, session, is_login_mode=login_only):
                return ""

            await save_state(context, session)

            # Login-only mode: exit after saving
            if login_only:
                log.info("")
                log.info("Login complete. You can now run queries:")
                log.info(f'  python deep_research_browser.py "Your query" --session {session} --headless')
                return "login_success"

            # Select Deep Research
            if not skip_model:
                await select_deep_research(page)

            # Submit query
            await submit_query(page, query)
            await asyncio.sleep(5)

            # Wait for response
            text = await page.inner_text("body")
            if has_research_started(text):
                log.info("Deep Research running in background...")
                response = await wait_for_report(page, timeout)
            else:
                response = await wait_for_response(page, timeout)

            # Save state
            await save_state(context, session)

            # Format output
            result = f"# Deep Research: {query[:50]}...\n\n{response}"

            if output_file:
                Path(output_file).write_text(result, encoding="utf-8")
                log.info(f"Saved to: {output_file}")

            log.info("=" * 60)
            log.info("    Complete!")
            log.info("=" * 60)

            return response

        except KeyboardInterrupt:
            log.info("Cancelled")
            await save_state(context, session)  # Save state on cancel
            return ""
        except Exception as e:
            log.error(f"Error: {e}")
            return ""
        finally:
            await browser.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="OpenAI Deep Research via browser automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # First time: login and save session
  %(prog)s --login

  # Run a query (visible browser)
  %(prog)s "What are the latest AI breakthroughs?" -o result.md

  # Run headless (after login)
  %(prog)s "Your query" -o result.md --headless

  # Parallel runs with named sessions
  %(prog)s "Query 1" -o r1.md --session work &
  %(prog)s "Query 2" -o r2.md --session personal &

  # List saved sessions
  %(prog)s --list-sessions
"""
    )

    # Main arguments
    parser.add_argument("query", nargs="?", help="Research query")
    parser.add_argument("-f", "--file", help="Read query from file")
    parser.add_argument("-o", "--output", help="Output file")

    # Session management
    parser.add_argument("--login", action="store_true",
                        help="Login mode: open browser for manual login, save session")
    parser.add_argument("--session", default=DEFAULT_SESSION,
                        help=f"Session name for parallel runs (default: {DEFAULT_SESSION})")
    parser.add_argument("--list-sessions", action="store_true",
                        help="List all saved sessions")

    # Execution options
    parser.add_argument("-t", "--timeout", type=int, default=cfg.timeouts.default_s,
                        help=f"Timeout in seconds (default: {cfg.timeouts.default_s})")
    parser.add_argument("-s", "--skip-model", action="store_true",
                        help="Skip Deep Research model selection")
    parser.add_argument("--headless", action="store_true",
                        help="Run headless (requires prior login)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Debug logging")

    args = parser.parse_args()

    if args.verbose:
        log.setLevel(logging.DEBUG)

    # Migrate old session format if needed
    migrate_old_session()

    # List sessions mode
    if args.list_sessions:
        sessions = list_sessions()
        if sessions:
            log.info("Saved sessions:")
            for s in sessions:
                valid = "✓" if has_valid_session(s) else "✗"
                log.info(f"  [{valid}] {s}")
        else:
            log.info("No saved sessions found.")
            log.info(f"Run with --login to create a session.")
        return

    # Check playwright installation
    if not PLAYWRIGHT_AVAILABLE:
        if not check_playwright():
            sys.exit(1)
        # If check_playwright passed but import failed, something is wrong
        log.error("Playwright check passed but import failed. Please reinstall.")
        sys.exit(1)

    # Login mode
    if args.login:
        asyncio.run(run(
            query="",
            session=args.session,
            login_only=True
        ))
        return

    # Query mode - get query from file or argument
    query = None
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            log.error(f"File not found: {args.file}")
            sys.exit(1)
        query = file_path.read_text().strip()
    elif args.query:
        query = args.query

    # Validate query
    if not query:
        if args.file:
            log.error("Query file is empty")
        else:
            parser.print_help()
            print()
            log.info("Tip: Run with --login first to save your session.")
        sys.exit(1)

    if len(query) > cfg.content.max_query_chars:
        log.error(f"Query too long: {len(query)} chars (max {cfg.content.max_query_chars})")
        sys.exit(1)

    asyncio.run(run(
        query=query,
        output_file=args.output,
        headless=args.headless,
        skip_model=args.skip_model,
        timeout=args.timeout,
        session=args.session
    ))


if __name__ == "__main__":
    main()
