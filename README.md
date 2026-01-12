# Origin Task

Claude Code Plugin Marketplace for AI-powered productivity tools.

## Installation

```bash
# 1. Add marketplace
/plugin marketplace add wayfind/origin-task

# 2. Install plugin
/plugin install intent-engine
/plugin install nano-banana-image
/plugin install ppt-generator
```

## Available Plugins

| Plugin | Description |
|--------|-------------|
| [intent-engine](#intent-engine) | Cross-session task tracking + Deep Research |
| [nano-banana-image](#nano-banana-image) | AI image generation with Nano Banana Pro style |
| [ppt-generator](#ppt-generator) | Modular PPT generation pipeline |

---

## intent-engine

Cross-session task tracking and AI productivity tools for Claude Code.

### Skills Included

| Skill | Description |
|-------|-------------|
| intent-engine | AI Long-Term Task Memory |
| openai-deep-research | Deep Research via browser automation |

### Dashboard

```bash
ie dashboard
```

**Features:**
- Task Navigator with hierarchical tree view
- Full spec rendering (markdown, mermaid diagrams)
- Decision timeline with chronological logs
- Multi-project support via tabs

### Quick Start

```bash
# View status
ie status

# Create task
echo '{"tasks":[{"name":"My Task","status":"doing"}]}' | ie plan

# Record decision
ie log decision "Chose X because Y"

# Search tasks
ie search "todo doing"
```

### Deep Research

Browser automation for OpenAI's Deep Research feature.

```bash
# First time: login
python deep_research_browser.py --login

# Run queries
python deep_research_browser.py "Your research query" -o result.md --headless

# Parallel runs with different sessions
python deep_research_browser.py "Query 1" -o r1.md --session work &
python deep_research_browser.py "Query 2" -o r2.md --session personal &
```

---

## nano-banana-image

AI image generation with Nano Banana Pro visual style using Gemini API.

### Features

- **Nano Banana Pro Style**: Auto-applies signature dark navy, golden yellow, teal color palette
- **Multi-Key Support**: Manage multiple Gemini API keys
- **Round-Robin Rotation**: Automatically rotates keys to distribute API usage
- **Multiple Aspect Ratios**: 1:1, 16:9, 9:16, 4:3, 3:4

### Quick Start

```bash
# First time: add API key
python scripts/generate_image.py keys add default "AIzaSy..."

# Generate image
python scripts/generate_image.py "a futuristic productivity device" output.png

# With aspect ratio
python scripts/generate_image.py "app icon" icon.png --aspect 1:1
```

### Key Management (Round-Robin)

```bash
# List all keys
python scripts/generate_image.py keys list

# Add keys
python scripts/generate_image.py keys add default AIzaSy...
python scripts/generate_image.py keys add work AIzaSy...

# Remove key
python scripts/generate_image.py keys remove <name>

# Reset rotation
python scripts/generate_image.py keys reset
```

Each image generation automatically uses the next key in rotation:
```
Call 1 → Using key: default
Call 2 → Using key: work
Call 3 → Using key: default
...
```

### Style Applied

All images automatically include:
- **Colors**: Deep navy (#1C2833), golden yellow (#F4C430), teal (#00D9C0)
- **Aesthetic**: Dark mode, geometric shapes, high contrast, minimalist

---

## ppt-generator

Modular PPT generation pipeline: outline → enrich → render.

### Skills Included

| Skill | Description |
|-------|-------------|
| /ppt | Main orchestrator |
| /ppt-outline | Generate skeleton from context |
| /ppt-enrich | Fill content, run research |
| /ppt-render | Render to PPTX |

### Quick Start

```bash
# Full pipeline
/ppt ./docs/ -o presentation.pptx

# Step by step
/ppt-outline --context ./docs/ -o skeleton.yaml
/ppt-enrich skeleton.yaml -o slides/
/ppt-render slides/ -o output.pptx
```

### Architecture

```
                    /ppt (orchestrator)
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
   /ppt-outline    /ppt-enrich      /ppt-render
   (skeleton)      (content)        (PPTX)
        │                │                │
        ▼                ▼                ▼
   skeleton.yaml    slides/*.md     output.pptx
```

### Themes

| Theme | Description |
|-------|-------------|
| `corporate-light` | Professional white background |
| `nano-banana-pro` | Dark tech aesthetic |

---

## Uninstall

```bash
/plugin uninstall intent-engine
/plugin uninstall nano-banana-image
/plugin uninstall ppt-generator
/plugin marketplace remove origin-task
```

## Related

- [intent-engine](https://github.com/wayfind/intent-engine) — Core CLI tool
- [npm package](https://www.npmjs.com/package/@origintask/intent-engine)

## License

MIT OR Apache-2.0
