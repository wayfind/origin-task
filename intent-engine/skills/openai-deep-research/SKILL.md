---
name: openai-deep-research
description: Deep Research via browser automation
version: 2.0.0
---

# OpenAI Deep Research Skill

Browser automation for OpenAI's Deep Research feature.

## Install

```bash
pip install playwright
playwright install chromium
```

## Quick Start

```bash
# 1. First time: login and save session
python deep_research_browser.py --login

# 2. Run queries (can be headless after login)
python deep_research_browser.py "Your query" -o result.md --headless
```

## Usage

### Login Mode (First Time)

```bash
# Open browser for manual login, save session
python deep_research_browser.py --login

# Login with a named session (for parallel runs)
python deep_research_browser.py --login --session work
```

### Query Mode

```bash
# Basic query
python deep_research_browser.py "What are the latest AI breakthroughs?" -o result.md

# Headless (after login)
python deep_research_browser.py "Your query" -o result.md --headless

# Read query from file
python deep_research_browser.py -f query.txt -o result.md
```

### Parallel Runs

```bash
# Run multiple queries simultaneously with named sessions
python deep_research_browser.py "Query 1" -o r1.md --session work &
python deep_research_browser.py "Query 2" -o r2.md --session personal &

# List all saved sessions
python deep_research_browser.py --list-sessions
```

## Options

```
positional arguments:
  query                 Research query

options:
  -h, --help            Show help message
  -f, --file FILE       Read query from file
  -o, --output FILE     Save result to file

Session management:
  --login               Login mode: open browser, save session
  --session NAME        Session name for parallel runs (default: default)
  --list-sessions       List all saved sessions

Execution options:
  -t, --timeout SECS    Timeout (default: 2400 = 40min)
  -s, --skip-model      Skip Deep Research selection
  --headless            Run headless (requires prior login)
  -v, --verbose         Debug logging
```

## How It Works

1. **Login mode**: Opens visible browser for manual ChatGPT login, saves cookies
2. **Query mode**: Loads saved session, selects Deep Research, submits query
3. **Waiting**: Polls for completion (refreshes every 60s for background tasks)
4. **Output**: Saves final report to file

## Session Management

Sessions are stored in `~/.openai-deep-research/`:

```
~/.openai-deep-research/
├── session_default.json    # Default session
├── session_work.json       # Named session "work"
└── session_personal.json   # Named session "personal"
```

Each session has isolated cookies, allowing:
- Multiple ChatGPT accounts
- Parallel Deep Research queries
- No state file conflicts

## Headless Mode

Headless mode works **only after** saving a valid session:

```bash
# This will fail (no session)
python deep_research_browser.py "Query" --headless  # Falls back to visible

# This works
python deep_research_browser.py --login
python deep_research_browser.py "Query" --headless  # Runs headless
```

If headless is requested without a saved session, the script:
1. Warns the user
2. Falls back to visible browser
3. Saves the session for future headless runs

## Timing

| Phase | Duration |
|-------|----------|
| First login | 1-2 min (manual) |
| Subsequent load | 5-10 sec |
| Deep Research | 10-30 min |

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "Headless mode without saved session"

Run `--login` first to save credentials:

```bash
python deep_research_browser.py --login
```

### Session expired

Re-run `--login` to refresh the session:

```bash
python deep_research_browser.py --login --session default
```
