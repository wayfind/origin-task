# Origin Task - Claude Code Plugin Marketplace

AI Long-Term Task Memory plugins for Claude Code.

## Installation

```bash
# Add marketplace
claude plugin marketplace add github:wayfind/origin-task

# Install plugin
claude plugin install intent-engine
```

## Available Plugins

### intent-engine

Cross-session task tracking for Claude Code. Use `ie plan` instead of TodoWrite for:

- **Persistent memory** - Tasks survive across sessions
- **Hierarchical breakdown** - Parent tasks with subtasks
- **Decision tracking** - Record why you made choices
- **Smart search** - Find tasks and events with FTS5

## Usage

After installation, the plugin automatically runs `ie status` at session start.

```bash
# Create task
echo '{"tasks":[{"name":"My Task","status":"doing"}]}' | ie plan

# View status
ie status

# Record decision
ie log decision "Chose X because Y"

# Search
ie search "todo doing"
```

## License

MIT OR Apache-2.0
