# Intent-Engine Task Memory

A **cross-session task memory** for human + AI collaboration.
Replaces TodoWrite for persistent, hierarchical task tracking with decision logs.

---

## Trigger Keywords

### English

**Core Commands:**
- `plan`, `planning`, `task`, `tasks`

**Actions:**
- `track`, `tracking`, `record`, `log`, `search`, `find`

**Status:**
- `todo`, `todos`, `doing`, `done`, `progress`, `status`

**Events:**
- `decision`, `blocker`, `milestone`, `note`

**Structure:**
- `subtask`, `subtasks`, `hierarchy`, `hierarchical`, `parent`, `child`, `children`, `breakdown`

**Scenarios:**
- `cross-session`, `persist`, `resume`, `continue`, `context`

**Direct:**
- `ie`, `intent-engine`

### 中文

**核心命令：**
- `计划`, `规划`, `任务`, `任务管理`

**操作动词：**
- `追踪`, `跟踪`, `记录`, `记一下`, `日志`, `搜索`, `查找`, `查一下`

**状态词：**
- `待办`, `待办事项`, `进行中`, `完成`, `进度`

**事件类型：**
- `决策`, `决定`, `阻塞`, `阻碍`, `卡住`, `卡住了`, `里程碑`, `备注`

**结构词：**
- `子任务`, `层级`, `分解`, `拆分`, `父任务`

**场景词：**
- `跨会话`, `跨对话`, `持久`, `保存`, `继续`, `恢复`, `上下文`

**口语化：**
- `帮我记住`, `别忘了`, `记下来`, `追踪一下`, `跟踪一下`

---

## Prerequisites

If `ie` not installed, install first:

```bash
npm install -g @m3task/intent-engine
# or: cargo install intent-engine
# or: brew install wayfind/tap/intent-engine
```

---

## ie vs TodoWrite

| Scenario | TodoWrite | ie |
|----------|-----------|-----|
| Single session, disposable | ✅ | |
| Cross-session persistence | | ✅ |
| Hierarchical task breakdown | | ✅ |
| Record decisions ("why") | | ✅ |
| Human + AI collaboration | | ✅ |

**Rule**: Would be a shame to lose it → ie. Use once and discard → TodoWrite.

---

## Task Status Lifecycle

Tasks have **three states** representing different phases:

| Status | Phase | Spec Required? | Description |
|--------|-------|----------------|-------------|
| `todo` | **Planning** | No | Tasks can be rough, focus on structure |
| `doing` | **Execution** | **Yes** | Must have spec (goal + approach) |
| `done` | **Completion** | - | All children must be done first |

### Planning Phase (todo)
- Tasks can be rough and undetailed
- Focus on structure and breakdown
- Good for brainstorming task hierarchy

### Execution Phase (doing)
- Task **MUST have spec** with goal and approach
- This is when real work happens
- Record decisions with `ie log`

### Completion (done)
- All children must be completed first
- Marks task as finished

---

## Command Reference

| Command | Purpose |
|---------|---------|
| `ie status` | View current focus and context |
| `ie plan` | Create/update/complete tasks (JSON stdin) |
| `ie log <type> <msg>` | Record decision/blocker/milestone/note |
| `ie search <query>` | Search tasks and events |

---

## Task Examples

### Planning Phase (rough tasks)

```bash
# Create rough tasks without spec
echo '{"tasks":[
  {"name":"Feature A","status":"todo"},
  {"name":"Feature B","status":"todo"}
]}' | ie plan
```

### Start Execution (spec required)

```bash
# Starting work - must provide spec
echo '{"tasks":[{
  "name":"Feature A",
  "status":"doing",
  "spec":"## Goal\nAdd user authentication\n\n## Approach\nUse JWT tokens"
}]}' | ie plan
```

### Hierarchical Tasks

```bash
echo '{"tasks":[{
  "name":"User Authentication",
  "status":"doing",
  "spec":"Implement complete auth system",
  "children":[
    {"name":"Design JWT schema","status":"todo"},
    {"name":"Implement login endpoint","status":"todo"},
    {"name":"Add middleware","status":"todo"},
    {"name":"Write tests","status":"todo"}
  ]
}]}' | ie plan
```

### Complete Tasks

```bash
# Complete children first, then parent
echo '{"tasks":[{"name":"Design JWT schema","status":"done"}]}' | ie plan
echo '{"tasks":[{"name":"Implement login endpoint","status":"done"}]}' | ie plan
# ... complete all children ...
echo '{"tasks":[{"name":"User Authentication","status":"done"}]}' | ie plan
```

### Include Description from File

```bash
cat > /tmp/spec.md << 'EOF'
## Goal
Implement rate limiting

## Approach
- Sliding window algorithm
- Redis storage
EOF

echo '{"tasks":[{"name":"Rate Limiting","status":"doing","spec":"@file(/tmp/spec.md)"}]}' | ie plan
```

---

## When Plans Change

Re-run `ie plan` to update task names, descriptions, or relationships.
This keeps **human and AI synchronized** on the current state.

```bash
# Update task description
echo '{"tasks":[{"name":"Task Name","spec":"Updated description"}]}' | ie plan

# Move task to different parent
echo '{"tasks":[{"name":"Task Name","parent_id":42}]}' | ie plan

# Create independent root task (ignore current focus)
echo '{"tasks":[{"name":"New Root Task","parent_id":null}]}' | ie plan
```

---

## Event Logging

Record context and decisions as you work:

```bash
ie log decision "Chose PostgreSQL for ACID support"   # Design choices
ie log blocker "Waiting for API credentials"          # What's blocking progress
ie log milestone "MVP feature complete"               # Key achievements
ie log note "Consider caching optimization"           # General observations

# Log to specific task
ie log decision "message" --task 42
```

---

## Search Examples

```bash
ie search "todo doing"           # Find unfinished tasks
ie search "authentication"       # Full-text search
ie search "API AND client"       # Boolean operators
```

---

## Session Workflow

```
Session Start:
  ie status                    # Restore context

During Work:
  ie plan {...}                # Update task status
  ie log decision "..."        # Record decisions as you make them
  ie log blocker "..."         # Record what's blocking you

When Plans Change:
  ie plan {...}                # Update task names, specs, relationships

Session End:
  ie plan {"status":"done"}    # Complete finished tasks
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "spec required" | `doing` without description | Add `spec` field with goal + approach |
| "incomplete subtasks" | Parent done before children | Complete all children first |
| "Task not found" | Wrong task name | Use exact name from `ie search` |

---

## Full Documentation

Run `ie --help` for complete documentation.
