# Origin Task

Claude Code Plugin Marketplace for AI Long-Term Task Memory.

## Installation

```bash
# 1. Add marketplace
claude plugin marketplace add wayfind/origin-task

# 2. Install plugin
claude plugin install intent-engine
```

## Available Plugins

### intent-engine

Cross-session task tracking for Claude Code. Use `ie plan` instead of TodoWrite for:

- **Persistent memory** - Tasks survive across sessions
- **Hierarchical breakdown** - Parent tasks with subtasks
- **Decision tracking** - Record why you made choices
- **Smart search** - Find tasks and events with FTS5

## How It Works

After installation, the plugin automatically:

1. Runs `ie status` at every session start
2. Shows your current focused task and progress
3. Injects session ID for task isolation

## Prerequisites

The plugin will auto-install `ie` CLI via npm if not found. You can also install manually:

```bash
npm install -g @m3task/intent-engine
# or
cargo install intent-engine
# or
brew install wayfind/tap/intent-engine
```

## Usage

```bash
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

## Uninstall

```bash
claude plugin uninstall intent-engine
claude plugin marketplace remove origin-task
```

## Related

- [intent-engine](https://github.com/wayfind/intent-engine) - Core CLI tool
- [npm package](https://www.npmjs.com/package/@m3task/intent-engine)

## License

MIT OR Apache-2.0
