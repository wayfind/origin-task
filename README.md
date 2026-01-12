# Origin Task

Claude Code Plugin Marketplace for AI-powered productivity tools.

## Installation

```bash
# 1. Add marketplace
/plugin marketplace add wayfind/origin-task

# 2. Install plugin
/plugin install intent-engine
```

## Available Plugins

### intent-engine

Cross-session task tracking and AI productivity tools for Claude Code.

#### Skills Included

| Skill | Description |
|-------|-------------|
| [intent-engine](#intent-engine-skill) | AI Long-Term Task Memory |
| [openai-deep-research](#openai-deep-research-skill) | Deep Research via browser automation |

---

## intent-engine Skill

Cross-session task tracking for Claude Code. Use `ie plan` instead of TodoWrite for:

- **Persistent memory** — Tasks survive across sessions
- **Hierarchical breakdown** — Parent tasks with subtasks
- **Decision tracking** — Record why you made choices
- **Smart search** — Find tasks and events with FTS5
- **Visual dashboard** — Web UI for task management

### Dashboard

After installation, launch the visual dashboard:

```bash
ie dashboard
```

![IE Dashboard](https://raw.githubusercontent.com/wayfind/intent-engine/main/docs/iedashboard.png)

**Features:**
- Task Navigator with hierarchical tree view
- Full spec rendering (markdown, mermaid diagrams)
- Decision timeline with chronological logs
- Multi-project support via tabs

### How It Works

After installation, the plugin automatically:

1. Runs `ie status` at every session start
2. Shows your current focused task and progress
3. Injects session ID for task isolation

### Prerequisites

The plugin will auto-install `ie` CLI via npm if not found. You can also install manually:

```bash
npm install -g @origintask/intent-engine
# or
cargo install intent-engine
# or
brew install wayfind/tap/intent-engine
```

### Usage

```bash
# View dashboard
ie dashboard

# Create task
echo '{"tasks":[{"name":"My Task","status":"doing"}]}' | ie plan

# View status
ie status

# Hierarchical tasks
echo '{"tasks":[{
  "name":"Parent task",
  "status":"doing",
  "children":[
    {"name":"Subtask 1","status":"todo"},
    {"name":"Subtask 2","status":"todo"}
  ]
}]}' | ie plan

# Record decision
ie log decision "Chose X because Y"

# Search tasks
ie search "todo doing"
```

---

## openai-deep-research Skill

Browser automation for OpenAI's Deep Research feature via Playwright.

### Features

- **Login mode** — `--login` for first-time session setup with clear UX
- **Session isolation** — `--session NAME` for parallel runs
- **Headless mode** — `--headless` with auto-fallback if no session
- **Session management** — `--list-sessions` to view saved sessions
- **Robust detection** — Auto-detects thinking vs final report

### Prerequisites

```bash
pip install playwright
playwright install chromium
```

### Quick Start

```bash
# 1. First time: login and save session
python deep_research_browser.py --login

# 2. Run queries (can be headless after login)
python deep_research_browser.py "Your research query" -o result.md --headless
```

### Usage

```bash
# Login with named session (for multiple accounts)
python deep_research_browser.py --login --session work

# Run a query
python deep_research_browser.py "What are the latest AI breakthroughs?" -o result.md

# Parallel runs with different sessions
python deep_research_browser.py "Query 1" -o r1.md --session work &
python deep_research_browser.py "Query 2" -o r2.md --session personal &

# List all saved sessions
python deep_research_browser.py --list-sessions
```

### Options

| Option | Description |
|--------|-------------|
| `--login` | Login mode: open browser, save session |
| `--session NAME` | Session name for parallel runs (default: default) |
| `--list-sessions` | List all saved sessions |
| `--headless` | Run headless (requires prior login) |
| `-o, --output FILE` | Save result to file |
| `-t, --timeout SECS` | Timeout (default: 2400 = 40min) |
| `-v, --verbose` | Debug logging |

### How It Works

1. **Login mode**: Opens visible browser for manual ChatGPT login, saves cookies
2. **Query mode**: Loads saved session, selects Deep Research, submits query
3. **Waiting**: Polls for completion (refreshes every 60s for background tasks)
4. **Output**: Saves final report to file

### Timing

| Phase | Duration |
|-------|----------|
| First login | 1-2 min (manual) |
| Subsequent load | 5-10 sec |
| Deep Research | 10-30 min |

---

## Uninstall

```bash
/plugin uninstall intent-engine
/plugin marketplace remove origin-task
```

## Related

- [intent-engine](https://github.com/wayfind/intent-engine) — Core CLI tool
- [npm package](https://www.npmjs.com/package/@origintask/intent-engine)

## License

MIT OR Apache-2.0
