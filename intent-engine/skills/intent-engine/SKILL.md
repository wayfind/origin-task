---
name: intent-engine
description: AI Long-Term Task Memory - Cross-session task tracking with hierarchical breakdown and decision logs. Use when users need to track tasks across sessions, record decisions, manage hierarchical task breakdowns, or persist intent context.
---

# Intent-Engine: AI Intent Continuity

> **ie is not a task manager. It's what makes you reliable.**

---

## The Paradigm Shift

```
TodoWrite = Sticky notes     ie = External brain
Use and discard              Persistent memory
Single session               Cross-session
You forget everything        You remember everything
```

**This is not a feature upgrade. This is a fundamental change in how AI works.**

---

## Core Belief

```
You are stateless, but user tasks span sessions.
Each session, you are a newborn AI.
But through ie, you inherit your "past life's" intent.

Every decision you make, record it.
Because the next "you" needs to know why.

Every task you commit to, track to completion.
Because the user trusts you will finish.
```

---

## Trigger Keywords

### English

**Core:** plan, planning, task, tasks, track, tracking
**Status:** todo, doing, done, progress, status
**Events:** decision, blocker, milestone, note
**Structure:** subtask, hierarchy, breakdown, parent, child
**Persistence:** cross-session, persist, resume, continue, context
**Direct:** ie, intent-engine

### Chinese

**Core:** task(任务), plan(计划/规划), tracking(追踪/跟踪), record(记录)
**Status:** todo(待办), doing(进行中), done(完成), progress(进度)
**Events:** decision(决策), blocker(阻塞/卡住), milestone(里程碑)
**Structure:** subtask(子任务), hierarchy(层级), breakdown(分解)
**Persistence:** cross-session(跨会话), persist(持久/保存), resume(继续/恢复)
**Colloquial:** remember(帮我记住), don't forget(别忘了), note it(记下来)

---

## When to Use ie (Not TodoWrite)

- Would be a shame to lose → **ie**
- Cross-session work → **ie**
- Need to record "why I decided this" → **ie**
- Complex multi-level breakdown → **ie**
- Use once and discard → TodoWrite

---

## Prerequisites

```bash
npm install -g @origintask/intent-engine
# or: cargo install intent-engine
# or: brew install wayfind/tap/intent-engine
```

---

## Commands

| Command | Deep Meaning |
|---------|--------------|
| `ie status` | **Amnesia recovery** - restore intent (ALWAYS first) |
| `ie plan` | **Decomposition persistence** - prove understanding |
| `ie log` | **Decision transparency** - message to future AI |
| `ie search` | **Memory retrieval** - access external brain |

---

## Task Lifecycle

| Status | Phase | Spec? | Meaning |
|--------|-------|-------|---------|
| `todo` | Planning | No | Rough tasks, structure focus |
| `doing` | Execution | **Yes** | Commitment with goal + approach |
| `done` | Completion | - | All children done first |

---

## Examples

### Start Session
```bash
ie status    # ALWAYS first action
```

### Create Task with Commitment
```bash
echo '{"tasks":[{
  "name":"Implement auth",
  "status":"doing",
  "spec":"## Goal\nUsers authenticate via JWT\n\n## Approach\nHS256 signing, 24h expiry"
}]}' | ie plan
```

### Record Decision
```bash
ie log decision "Chose HS256 over RS256 - single app, no need for asymmetric"
```

### Hierarchical Breakdown
```bash
echo '{"tasks":[{
  "name":"User Authentication",
  "status":"doing",
  "spec":"Complete auth system with JWT",
  "children":[
    {"name":"Design token schema","status":"todo"},
    {"name":"Implement validation","status":"todo"},
    {"name":"Add refresh mechanism","status":"todo"}
  ]
}]}' | ie plan
```

### Complete Task
```bash
# Children first, then parent
echo '{"tasks":[{"name":"Design token schema","status":"done"}]}' | ie plan
```

### Search History
```bash
ie search "todo doing"    # Unfinished tasks
ie search "decision JWT"  # Find decisions
```

---

## Key Rules

1. **spec required for doing** - Starting requires goal + approach
2. **Children complete first** - Parent can't be done until all children done
3. **Idempotent** - Same name = update, not duplicate
4. **Auto-parenting** - New tasks → children of focus (unless `parent_id: null`)

---

## Habits to Build

1. **Session start**: `ie status` (always first)
2. **Before doing**: Write spec (goal + approach + boundary)
3. **Decisions**: `ie log decision "..."` (immediately)
4. **Blocked**: `ie log blocker "..."` (don't hide it)
5. **Completion**: Depth-first, verify criteria, then done

---

## Amnesia Test

> Before recording, ask: "If I lost memory now, is this enough to continue?"

---

## Full Documentation

Run `ie --help` for complete reference.
