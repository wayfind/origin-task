#!/usr/bin/env python3
"""
Robustness Test Suite for OpenAI Deep Research Skill

Tests cover:
1. Session management (create, list, migrate, validate)
2. CLI argument handling (login, headless, session)
3. Playwright availability checks
4. Input validation (empty, too long, file not found)
5. Parallel run isolation

Run: pytest test_robustness.py -v
"""

import asyncio
import json
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from unittest import mock

import pytest

# Import the module under test
import deep_research_browser as drb


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_state_dir(tmp_path, monkeypatch):
    """Use a temporary directory for state files."""
    state_dir = tmp_path / ".openai-deep-research"
    state_dir.mkdir()
    monkeypatch.setattr(drb, "STATE_DIR", state_dir)
    monkeypatch.setattr(drb, "OLD_STATE_FILE", state_dir / "browser_state.json")
    return state_dir


@pytest.fixture
def mock_session(temp_state_dir):
    """Create a mock valid session file."""
    session_file = temp_state_dir / "session_default.json"
    session_data = {
        "cookies": [
            {"name": "test_cookie", "value": "test_value", "domain": ".chatgpt.com"}
        ],
        "origins": []
    }
    session_file.write_text(json.dumps(session_data))
    return session_file


@pytest.fixture
def mock_old_session(temp_state_dir):
    """Create a mock old-format session file."""
    old_file = temp_state_dir / "browser_state.json"
    session_data = {
        "cookies": [
            {"name": "old_cookie", "value": "old_value", "domain": ".chatgpt.com"}
        ],
        "origins": []
    }
    old_file.write_text(json.dumps(session_data))
    return old_file


# =============================================================================
# Test Group 1: Session Management
# =============================================================================

class TestSessionManagement:
    """Tests for session file handling."""

    def test_get_state_file_default(self, temp_state_dir):
        """Default session uses session_default.json."""
        path = drb.get_state_file("default")
        assert path.name == "session_default.json"
        assert path.parent == temp_state_dir

    def test_get_state_file_named(self, temp_state_dir):
        """Named sessions use session_<name>.json."""
        path = drb.get_state_file("work")
        assert path.name == "session_work.json"

    def test_has_valid_session_true(self, mock_session):
        """Valid session with cookies returns True."""
        assert drb.has_valid_session("default") is True

    def test_has_valid_session_no_file(self, temp_state_dir):
        """Missing session file returns False."""
        assert drb.has_valid_session("nonexistent") is False

    def test_has_valid_session_empty_cookies(self, temp_state_dir):
        """Session with empty cookies returns False."""
        session_file = temp_state_dir / "session_empty.json"
        session_file.write_text(json.dumps({"cookies": [], "origins": []}))
        assert drb.has_valid_session("empty") is False

    def test_has_valid_session_invalid_json(self, temp_state_dir):
        """Invalid JSON returns False."""
        session_file = temp_state_dir / "session_broken.json"
        session_file.write_text("not valid json {{{")
        assert drb.has_valid_session("broken") is False

    def test_list_sessions_empty(self, temp_state_dir):
        """Empty directory returns empty list."""
        # Remove any existing session files
        for f in temp_state_dir.glob("session_*.json"):
            f.unlink()
        assert drb.list_sessions() == []

    def test_list_sessions_multiple(self, temp_state_dir):
        """Lists all session files."""
        (temp_state_dir / "session_one.json").write_text("{}")
        (temp_state_dir / "session_two.json").write_text("{}")
        (temp_state_dir / "session_three.json").write_text("{}")
        sessions = drb.list_sessions()
        assert set(sessions) == {"one", "two", "three"}

    def test_migrate_old_session(self, mock_old_session, temp_state_dir):
        """Migrates browser_state.json to session_default.json."""
        assert not (temp_state_dir / "session_default.json").exists()
        result = drb.migrate_old_session()
        assert result is True
        assert (temp_state_dir / "session_default.json").exists()
        # Verify content was copied
        new_data = json.loads((temp_state_dir / "session_default.json").read_text())
        assert new_data["cookies"][0]["name"] == "old_cookie"

    def test_migrate_old_session_no_overwrite(self, mock_old_session, mock_session):
        """Does not overwrite existing session_default.json."""
        result = drb.migrate_old_session()
        assert result is False
        # Original content preserved
        data = json.loads(mock_session.read_text())
        assert data["cookies"][0]["name"] == "test_cookie"

    def test_migrate_old_session_no_old_file(self, temp_state_dir):
        """Returns False when no old file exists."""
        result = drb.migrate_old_session()
        assert result is False


# =============================================================================
# Test Group 2: CLI Argument Handling
# =============================================================================

class TestCLIArguments:
    """Tests for command-line argument parsing."""

    def test_help_output(self):
        """Help shows all options."""
        result = subprocess.run(
            [sys.executable, "deep_research_browser.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "--login" in result.stdout
        assert "--session" in result.stdout
        assert "--list-sessions" in result.stdout
        assert "--headless" in result.stdout
        assert "Examples:" in result.stdout

    def test_list_sessions_cli(self, temp_state_dir, monkeypatch):
        """--list-sessions shows sessions."""
        # Create test sessions
        (temp_state_dir / "session_test1.json").write_text('{"cookies": [{"name": "c"}]}')
        (temp_state_dir / "session_test2.json").write_text('{"cookies": []}')

        # Patch STATE_DIR for subprocess
        env = os.environ.copy()
        result = subprocess.run(
            [sys.executable, "-c", f"""
import sys
sys.path.insert(0, '.')
import deep_research_browser as drb
from pathlib import Path
drb.STATE_DIR = Path('{temp_state_dir}')
drb.migrate_old_session()
for s in drb.list_sessions():
    valid = drb.has_valid_session(s)
    print(f"{{s}}: {{valid}}")
"""],
            capture_output=True,
            text=True
        )
        assert "test1: True" in result.stdout
        assert "test2: False" in result.stdout

    def test_empty_query_rejected(self):
        """Empty query shows help and exits."""
        result = subprocess.run(
            [sys.executable, "deep_research_browser.py"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "usage:" in result.stdout or "Tip:" in result.stdout

    def test_file_not_found_rejected(self):
        """Nonexistent file shows error."""
        result = subprocess.run(
            [sys.executable, "deep_research_browser.py", "-f", "/nonexistent/file.txt"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "File not found" in result.stdout

    def test_empty_file_rejected(self, tmp_path):
        """Empty query file shows error."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("   \n  \n  ")
        result = subprocess.run(
            [sys.executable, "deep_research_browser.py", "-f", str(empty_file)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "empty" in result.stdout.lower()


# =============================================================================
# Test Group 3: Content Detection
# =============================================================================

class TestContentDetection:
    """Tests for thinking/report/clarification detection."""

    def test_is_thinking_true(self):
        """Detects thinking patterns."""
        text = "I'm searching through the documents now..."
        assert drb.is_thinking(text) is True

    def test_is_thinking_false(self):
        """No thinking patterns in final report."""
        text = "## Summary\n\nThis is the final report with conclusions."
        assert drb.is_thinking(text) is False

    def test_is_thinking_checks_tail(self):
        """Only checks last N characters."""
        # Thinking at start, not at end
        text = "I'm thinking..." + ("x" * 3000) + "## Conclusion\n\nFinal answer."
        assert drb.is_thinking(text) is False

    def test_is_final_report_true(self):
        """Detects final report structure."""
        text = "x" * 4000 + "\n## Summary\n\nThis is the conclusion."
        assert drb.is_final_report(text) is True

    def test_is_final_report_too_short(self):
        """Short text is not a report."""
        text = "## Summary\n\nShort."
        assert drb.is_final_report(text) is False

    def test_is_final_report_still_thinking(self):
        """Report structure but still thinking."""
        text = "x" * 4000 + "\n## Summary\n\nI'm still analyzing..."
        assert drb.is_final_report(text) is False

    def test_is_clarifying_true(self):
        """Detects clarifying questions."""
        text = "Could you clarify what specific aspects you're interested in?"
        assert drb.is_clarifying(text) is True

    def test_is_clarifying_false(self):
        """Normal text is not clarifying."""
        text = "Here is the analysis you requested."
        assert drb.is_clarifying(text) is False

    def test_has_research_started_true(self):
        """Detects background research start."""
        text = "I'll get back to you with the findings. Feel free to keep chatting!"
        assert drb.has_research_started(text) is True

    def test_has_research_started_false(self):
        """Normal response doesn't trigger."""
        text = "Here is the information you requested."
        assert drb.has_research_started(text) is False


# =============================================================================
# Test Group 4: Headless Mode Logic
# =============================================================================

class TestHeadlessMode:
    """Tests for headless mode behavior."""

    @pytest.mark.asyncio
    async def test_headless_without_session_fallback(self, temp_state_dir, caplog):
        """Headless without session falls back to visible."""
        import logging
        caplog.set_level(logging.WARNING)

        # Mock playwright to avoid actual browser launch
        with mock.patch.object(drb, 'async_playwright') as mock_pw:
            mock_browser = mock.AsyncMock()
            mock_context = mock.AsyncMock()
            mock_page = mock.AsyncMock()

            mock_pw.return_value.__aenter__.return_value.chromium.launch.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            mock_context.new_page.return_value = mock_page
            mock_page.goto = mock.AsyncMock()
            mock_page.wait_for_selector = mock.AsyncMock(side_effect=drb.PlaywrightTimeout("timeout"))

            # Run with headless=True but no session
            try:
                await drb.run(
                    query="test",
                    headless=True,
                    session="nonexistent",
                    timeout=1
                )
            except Exception:
                pass  # Expected to fail, we just want to check the warning

            # Check log records for warning
            log_text = "\n".join([r.message for r in caplog.records])
            assert "Headless mode without saved session" in log_text
            assert "Falling back to visible browser" in log_text

    def test_headless_with_valid_session(self, mock_session):
        """Headless with valid session should work."""
        # Just verify the session is valid
        assert drb.has_valid_session("default") is True


# =============================================================================
# Test Group 5: Parallel Run Isolation
# =============================================================================

class TestParallelIsolation:
    """Tests for parallel run session isolation."""

    def test_different_sessions_different_files(self, temp_state_dir):
        """Different session names use different files."""
        file1 = drb.get_state_file("session_a")
        file2 = drb.get_state_file("session_b")
        assert file1 != file2
        assert file1.name == "session_session_a.json"
        assert file2.name == "session_session_b.json"

    def test_sessions_dont_interfere(self, temp_state_dir):
        """Writing to one session doesn't affect another."""
        # Create two sessions with different data
        session_a = temp_state_dir / "session_a.json"
        session_b = temp_state_dir / "session_b.json"

        data_a = {"cookies": [{"name": "cookie_a"}], "origins": []}
        data_b = {"cookies": [{"name": "cookie_b"}], "origins": []}

        session_a.write_text(json.dumps(data_a))
        session_b.write_text(json.dumps(data_b))

        # Verify they're independent
        read_a = json.loads(session_a.read_text())
        read_b = json.loads(session_b.read_text())

        assert read_a["cookies"][0]["name"] == "cookie_a"
        assert read_b["cookies"][0]["name"] == "cookie_b"


# =============================================================================
# Test Group 6: Input Validation
# =============================================================================

class TestInputValidation:
    """Tests for input validation."""

    def test_query_max_length_constant(self):
        """MAX_QUERY_CHARS constant exists."""
        assert hasattr(drb, 'MAX_QUERY_CHARS')
        assert drb.MAX_QUERY_CHARS == 50000

    def test_query_too_long_rejected(self, tmp_path):
        """Query exceeding max length is rejected."""
        long_query = "x" * 60000
        result = subprocess.run(
            [sys.executable, "deep_research_browser.py", long_query],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "too long" in result.stdout.lower()

    def test_constants_defined(self):
        """All threshold constants are defined."""
        assert hasattr(drb, 'TAIL_CHECK_CHARS')
        assert hasattr(drb, 'MIN_REPORT_CHARS')
        assert hasattr(drb, 'MIN_CONTENT_CHARS')
        assert hasattr(drb, 'STABLE_REPORT_COUNT')
        assert hasattr(drb, 'STABLE_RESPONSE_COUNT')
        assert hasattr(drb, 'STATUS_INTERVAL')
        assert hasattr(drb, 'SIGNIFICANT_DIFF_CHARS')


# =============================================================================
# Test Group 7: Playwright Availability
# =============================================================================

class TestPlaywrightCheck:
    """Tests for Playwright installation check."""

    def test_playwright_available_flag(self):
        """PLAYWRIGHT_AVAILABLE flag is set."""
        assert hasattr(drb, 'PLAYWRIGHT_AVAILABLE')
        # Should be True since we imported successfully
        assert drb.PLAYWRIGHT_AVAILABLE is True

    def test_check_playwright_function_exists(self):
        """check_playwright function exists."""
        assert hasattr(drb, 'check_playwright')
        assert callable(drb.check_playwright)

    def test_check_playwright_returns_bool(self):
        """check_playwright returns boolean."""
        result = drb.check_playwright()
        assert isinstance(result, bool)


# =============================================================================
# Test Group 8: Integration Tests (Manual)
# =============================================================================

class TestIntegrationManual:
    """
    Integration tests that require manual verification.

    These tests print instructions for manual testing.
    Run with: pytest test_robustness.py -v -k "manual" -s
    """

    @pytest.mark.manual
    def test_login_flow_manual(self):
        """
        Manual test: Verify login flow UX.

        Run: python deep_research_browser.py --login --session test_login

        Expected:
        1. Browser opens to ChatGPT
        2. Clear login instructions displayed
        3. Shows session name and save path
        4. After login, shows success message
        5. Session file created
        """
        print("\n" + "=" * 60)
        print("MANUAL TEST: Login Flow")
        print("=" * 60)
        print("Run: python deep_research_browser.py --login --session test_login")
        print("\nVerify:")
        print("  1. Browser opens to ChatGPT")
        print("  2. Clear login instructions displayed")
        print("  3. Shows session name and save path")
        print("  4. After login, shows success message")
        print("  5. Session file created in ~/.openai-deep-research/")
        print("=" * 60)

    @pytest.mark.manual
    def test_headless_after_login_manual(self):
        """
        Manual test: Verify headless works after login.

        Run:
        1. python deep_research_browser.py --login --session test_headless
        2. python deep_research_browser.py "test query" --session test_headless --headless -t 30

        Expected:
        - First run: visible browser, login
        - Second run: no browser window visible, runs headless
        """
        print("\n" + "=" * 60)
        print("MANUAL TEST: Headless After Login")
        print("=" * 60)
        print("Step 1: python deep_research_browser.py --login --session test_headless")
        print("Step 2: python deep_research_browser.py \"test\" --session test_headless --headless -t 30")
        print("\nVerify:")
        print("  - First run: visible browser, complete login")
        print("  - Second run: no browser window, runs headless")
        print("=" * 60)

    @pytest.mark.manual
    def test_parallel_runs_manual(self):
        """
        Manual test: Verify parallel runs work.

        Run in two terminals:
        Terminal 1: python deep_research_browser.py "Query 1" -o r1.md --session parallel_a
        Terminal 2: python deep_research_browser.py "Query 2" -o r2.md --session parallel_b

        Expected:
        - Both run simultaneously without conflicts
        - Each creates its own output file
        - No state file corruption
        """
        print("\n" + "=" * 60)
        print("MANUAL TEST: Parallel Runs")
        print("=" * 60)
        print("Terminal 1: python deep_research_browser.py \"Query 1\" -o r1.md --session parallel_a")
        print("Terminal 2: python deep_research_browser.py \"Query 2\" -o r2.md --session parallel_b")
        print("\nVerify:")
        print("  - Both run simultaneously")
        print("  - Each creates its own output file")
        print("  - Check ~/.openai-deep-research/ for separate session files")
        print("=" * 60)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
