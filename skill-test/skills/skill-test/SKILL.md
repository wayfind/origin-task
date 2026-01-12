---
name: skill-test
description: |
  Claude Code skill testing and validation toolkit.
  Use when: (1) Validating skill installation and configuration, (2) Running smoke tests on skills, (3) Checking dependencies and prerequisites, (4) Generating test reports for skill suite.
  Triggers: "test skill", "validate plugin", "skill check", "verify skills", "test installation"
---

# /skill-test - Claude Code Skill Validator

> Validate skill installation, configuration, and execution readiness.

## Overview

`/skill-test` is a development tool for testing Claude Code skills. It validates:
- SKILL.md format and frontmatter
- plugin.json configuration
- marketplace.json references
- Script dependencies (Python/Node.js)
- Smoke test execution

## Quick Start

```bash
# Test all skills in current project
/skill-test

# Test specific skill
/skill-test --skill ppt-render

# Verbose output
/skill-test -v

# Generate report
/skill-test --report test-report.md
```

## Test Levels

### Level 1: Installation (Fast)
Validates file structure and configuration:
- SKILL.md exists with valid YAML frontmatter
- plugin.json is well-formed JSON
- marketplace.json references are valid
- Required directories exist

### Level 2: Dependencies (Medium)
Checks prerequisites:
- Python packages installed (from requirements.txt)
- Node.js packages installed (from package.json)
- CLI tools available (e.g., `ie`, `node`, `python`)
- Environment variables configured

### Level 3: Smoke Test (Full)
Executes minimal validation:
- Python scripts: syntax check + `--help` if supported
- Node.js scripts: syntax check + `--help` if supported
- Config validation commands

## Usage

### Command

```bash
python scripts/test_runner.py [options]
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--root` | Project root directory | Current directory |
| `--skill` | Test specific skill only | All skills |
| `--level` | Test level (1-3) | 3 |
| `--report` | Output report file | None (stdout) |
| `-v, --verbose` | Verbose output | False |
| `--json` | JSON output format | False |

### Examples

```bash
# Full test suite
python scripts/test_runner.py --root /path/to/origin-task

# Quick installation check
python scripts/test_runner.py --level 1

# Test ppt-generator skills only
python scripts/test_runner.py --skill ppt --skill ppt-outline --skill ppt-enrich --skill ppt-render

# Generate markdown report
python scripts/test_runner.py --report ./test-results.md
```

## Test Output

### Console Output

```
=== Skill Test Suite ===

[PASS] intent-engine
  - SKILL.md: valid
  - Dependencies: all satisfied
  - Smoke test: passed

[WARN] ppt-render
  - SKILL.md: valid
  - Dependencies: pptxgenjs missing
  - Smoke test: skipped

[FAIL] nano-banana-image
  - SKILL.md: valid
  - Dependencies: all satisfied
  - Smoke test: API key not configured

Summary: 1 passed, 1 warning, 1 failed
```

### JSON Output

```json
{
  "summary": {"pass": 1, "warn": 1, "fail": 1},
  "skills": [
    {
      "name": "intent-engine",
      "status": "pass",
      "tests": {
        "installation": {"status": "pass"},
        "dependencies": {"status": "pass"},
        "smoke_test": {"status": "pass"}
      }
    }
  ]
}
```

## Test Cases

### SKILL.md Validation

| Check | Required | Description |
|-------|----------|-------------|
| File exists | Yes | SKILL.md in skill directory |
| YAML frontmatter | Yes | Valid `---` delimited YAML |
| `name` field | Yes | Skill identifier |
| `description` field | Yes | Skill description |
| Markdown body | Recommended | Usage documentation |

### plugin.json Validation

| Check | Required | Description |
|-------|----------|-------------|
| Valid JSON | Yes | Parseable JSON |
| `name` field | Yes | Plugin name |
| `version` field | Yes | Semantic version |
| `skills` array | Yes | Skill definitions |

### Dependency Checks

| Language | Source | Check |
|----------|--------|-------|
| Python | requirements.txt | `pip list` comparison |
| Python | SKILL.md prerequisites | Module import test |
| Node.js | package.json | `npm ls` check |
| CLI | SKILL.md prerequisites | `which` command |

### Smoke Tests

| Type | Command | Success Criteria |
|------|---------|------------------|
| Python script | `python -m py_compile script.py` | Exit 0 |
| Python --help | `python script.py --help` | Exit 0 |
| Node.js script | `node --check script.js` | Exit 0 |
| Node.js --help | `node script.js --help` | Exit 0 |
| Config check | `script --check` | Exit 0 or config info |

## Integration

### CI/CD

```yaml
# GitHub Actions example
- name: Test Skills
  run: |
    cd origin-task
    python skill-test/skills/skill-test/scripts/test_runner.py \
      --level 2 \
      --report test-results.md
```

### Pre-commit Hook

```bash
#!/bin/bash
python skill-test/skills/skill-test/scripts/test_runner.py --level 1
```

## File Structure

```
skill-test/
├── .claude-plugin/
│   └── plugin.json
└── skills/
    └── skill-test/
        ├── SKILL.md          # This document
        └── scripts/
            └── test_runner.py  # Main test runner
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No skills found" | Check `--root` points to project with `.claude-plugin/` |
| Python import errors | Install test requirements: `pip install pyyaml` |
| Permission denied | Check script execute permissions |
| Timeout on smoke test | Increase timeout or use `--level 2` |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-12 | Initial release |
