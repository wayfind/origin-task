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
| `ie status <id>` | **Ancestor context** - get full task chain for sub-agent work |
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

## Workflow-Specific Patterns

### Bug Fix Workflow (reproduce→diagnose→fix→verify)

```
Task Structure: FLAT (linear steps, not deeply nested)

Events pattern:
- Heavy `note` for investigation findings
- `blocker` when investigation stuck (missing logs, can't reproduce)
- `decision` for fix approach (quick patch vs proper fix)
- `milestone` when root cause identified

Example:
#1 Fix checkout crash [doing]
├── #2 Reproduce issue [todo]
├── #3 Diagnose root cause [todo]
├── #4 Implement fix [todo]
└── #5 Verify fix [todo]
```

### Refactoring/Migration Workflow (analyze→design→migrate→verify)

```
Task Structure: DEEP hierarchy (phase→component→step)

Events pattern:
- `decision` for risk mitigation strategies
- `milestone` after each component migrated
- Sequential `depends_on` chain (migrate A before B)

Example:
#1 Migrate to PostgreSQL [doing]
├── #2 Phase 1: Analysis [todo]
│   ├── #3 Inventory queries [todo]
│   └── #4 Map dependencies [todo]
├── #5 Phase 2: Migration [todo]
│   ├── #6 Migrate UserService [todo]
│   ├── #7 Migrate OrderService [todo] depends_on:#6
│   └── #8 Migrate PaymentService [todo] depends_on:#7
└── #9 Phase 3: Cleanup [todo] depends_on:#8
```

### Feature Development Workflow (design→implement→integrate→test)

```
Task Structure: PARALLEL branches with depends_on

Events pattern:
- Backend and Frontend as parallel tracks
- Integration depends on BOTH branches
- Rich specs with API contracts, schemas, diagrams

Example:
#1 Notification System [doing]
├── #2 Backend Track [todo]        ← NO depends_on (can start)
│   ├── #3 API design [todo]
│   └── #4 Database schema [todo]
├── #5 Frontend Track [todo]       ← NO depends_on (can start parallel)
│   ├── #6 UI components [todo]
│   └── #7 State management [todo]
└── #8 Integration [todo]          ← depends_on:#2,#5 (waits for BOTH)
```

---

## Events as CQRS Audit Trail

| Type | When to Use | Workflow Hint |
|------|-------------|---------------|
| decision | Chose X over Y with trade-offs | All workflows |
| blocker | Cannot proceed, waiting for X | Bug fix (stuck), Migration (dependency) |
| milestone | Significant checkpoint | Migration (component done), Feature (phase done) |
| note | Observations, findings | Bug fix (investigation clues) |

**Events support rich markdown** - document thoroughly, not just short strings.

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

### Record Decision (Rich Markdown)
```bash
ie log decision "## Token Algorithm Decision

### Context
Multi-service architecture

### Options
1. HS256 - symmetric, simpler
2. RS256 - asymmetric, verifiable

### Decision
RS256 - services only need public key

### Trade-offs
- (+) No shared secret
- (-) Larger tokens"
```

### Hierarchical Breakdown with Dependencies
```bash
echo '{"tasks":[{
  "name":"User Authentication",
  "status":"doing",
  "spec":"Complete auth system with JWT",
  "children":[
    {"name":"Design token schema","status":"todo"},
    {"name":"Implement validation","status":"todo","depends_on":["Design token schema"]},
    {"name":"Add refresh mechanism","status":"todo","depends_on":["Implement validation"]}
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
5. **spec is documentation store** - Supports GB-scale markdown, mermaid, code blocks

---

## Habits to Build

1. **Session start**: `ie status` (always first)
2. **Before doing**: Write spec (goal + approach + boundary)
3. **Decisions**: `ie log decision "..."` (immediately, with rich markdown)
4. **Blocked**: `ie log blocker "..."` (don't hide it)
5. **Completion**: Depth-first, verify criteria, then done
6. **Search first**: `ie search` before making decisions

---

## Anti-Patterns to Avoid

| Don't | Do Instead |
|-------|------------|
| Decide without checking history | `ie search` first |
| Hide errors and retry silently | `ie log blocker "error"` |
| Start task without spec | Write Goal + Approach first |
| Use TodoWrite for persistent work | Use `ie plan` |
| Multiple `ie plan` calls for hierarchy | Single call with nested `children` |
| Forget what you were doing | `ie status` at session start |

---

## Amnesia Test

> Before recording, ask: "If I lost memory now, is this enough to continue?"

---

## Full Documentation

Run `ie --help` for complete reference.
