#!/usr/bin/env node
// Intent-Engine Session Start Hook
// Cross-platform Node.js implementation with auto-install

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// === Parse stdin (session_id) ===

let sessionId = '';
try {
  const input = fs.readFileSync(0, 'utf8').trim();
  if (input) {
    const data = JSON.parse(input);
    sessionId = data.session_id || '';
  }
} catch {
  // Ignore parse errors
}

// === Set environment variable ===

if (process.env.CLAUDE_ENV_FILE && sessionId) {
  if (/^[a-zA-Z0-9_-]+$/.test(sessionId)) {
    try {
      fs.appendFileSync(
        process.env.CLAUDE_ENV_FILE,
        `export IE_SESSION_ID="${sessionId}"\n`
      );
    } catch {}
  }
}

process.env.IE_SESSION_ID = sessionId;

// === Utility functions ===

const isWin = process.platform === 'win32';

function commandExists(cmd) {
  try {
    execSync(isWin ? `where ${cmd}` : `command -v ${cmd}`, { stdio: 'ignore' });
    return true;
  } catch {
    return false;
  }
}

function verifyIeBinary(iePath) {
  try {
    const result = spawnSync(iePath, ['--version'], {
      encoding: 'utf8',
      timeout: 5000,
      stdio: ['ignore', 'pipe', 'pipe']
    });
    return result.status === 0;
  } catch {
    return false;
  }
}

function getNpmGlobalBinDir() {
  try {
    const prefix = execSync('npm config get prefix', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'ignore']
    }).trim();
    return isWin ? prefix : path.join(prefix, 'bin');
  } catch {
    return null;
  }
}

function findIeBinary() {
  // Method 1: Check if ie is in PATH and works
  try {
    const checkCmd = isWin ? 'where ie' : 'command -v ie';
    const result = execSync(checkCmd, { encoding: 'utf8', stdio: ['pipe', 'pipe', 'ignore'] });
    const iePath = result.trim().split('\n')[0];
    if (iePath && fs.existsSync(iePath) && verifyIeBinary(iePath)) {
      return iePath;
    }
  } catch {}

  // Method 2: Check npm global bin directory
  const npmBinDir = getNpmGlobalBinDir();
  if (npmBinDir) {
    const iePath = path.join(npmBinDir, isWin ? 'ie.cmd' : 'ie');
    if (fs.existsSync(iePath) && verifyIeBinary(iePath)) {
      return iePath;
    }
  }

  return null;
}

function installIe() {
  if (!commandExists('npm')) {
    console.log('npm not found. Cannot auto-install intent-engine.');
    return false;
  }

  console.log('');
  console.log('========================================');
  console.log('  Installing intent-engine...');
  console.log('  This may take a few seconds.');
  console.log('========================================');
  console.log('');

  try {
    const result = spawnSync('npm', ['install', '-g', '@m3task/intent-engine'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      timeout: 60000,
      shell: isWin
    });

    if (result.status === 0) {
      console.log('');
      console.log('========================================');
      console.log('  intent-engine installed successfully!');
      console.log('========================================');
      console.log('');
      return true;
    } else {
      const errorMsg = (result.stderr || result.stdout || 'Unknown error').slice(0, 300);
      console.log('Installation failed:', errorMsg);
      return false;
    }
  } catch (e) {
    console.log('Installation error:', e.message);
    return false;
  }
}

// === Main logic ===

let iePath = findIeBinary();
let justInstalled = false;

if (!iePath) {
  const installed = installIe();
  if (installed) {
    iePath = findIeBinary();
    if (iePath) {
      justInstalled = true;
    } else {
      console.log('Installation succeeded but ie binary not found or not working.');
    }
  }
}

if (!iePath) {
  console.log(`<system-reminder>
intent-engine (ie) not available.

Auto-install ${commandExists('npm') ? 'failed' : 'skipped (npm not found)'}.

Please install manually:
  npm install -g @m3task/intent-engine
  cargo install intent-engine
  brew install wayfind/tap/intent-engine
</system-reminder>`);
  process.exit(0);
}

if (justInstalled) {
  console.log(`
<system-reminder>
# intent-engine is now ready to use!

## What is ie?
A cross-session task memory that replaces TodoWrite for persistent, hierarchical task tracking.
Both human and AI can track progress together across multiple sessions.

## Task Lifecycle (Status-Driven)

  Planning Phase (status: todo)
    - Tasks can be rough, no spec required
    - Focus on structure and breakdown

  Execution Phase (status: doing)
    - Task MUST have spec (goal + approach)
    - This is when real work happens

  Completion (status: done)
    - All children must be done first
    - Marks task as finished

## Quick Commands
  ie status                              # View current focus
  echo '{"tasks":[...]}' | ie plan       # Create/update/complete tasks
  ie log decision "why I chose X"        # Record decisions
  ie log blocker "waiting for Y"         # Record blockers
  ie search "keyword"                    # Search tasks and events

## When Plans Change
  Use \`ie plan\` again to update:
    - Task names, descriptions (spec)
    - Parent-child relationships
    - Status transitions

  This keeps human and AI synchronized on current state.

Note: This session uses the full binary path. Future sessions will use 'ie' directly.
</system-reminder>
`);
}

// === Initialize project if needed ===

const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
const ieDir = path.join(projectDir, '.intent-engine');

if (fs.existsSync(projectDir) && !fs.existsSync(ieDir)) {
  try {
    spawnSync(iePath, ['init'], {
      cwd: projectDir,
      stdio: 'ignore',
      timeout: 10000
    });
  } catch {}
}

// === Run ie status ===

try {
  const result = spawnSync(iePath, ['status'], {
    cwd: projectDir,
    encoding: 'utf8',
    timeout: 15000,
    env: { ...process.env, IE_SESSION_ID: sessionId }
  });

  if (result.stdout) {
    console.log(result.stdout);
  }
  if (result.stderr) {
    console.error(result.stderr);
  }
} catch (e) {
  console.log('Failed to run ie status:', e.message);
}

// === Output system reminder ===

console.log(`
<system-reminder>
# Task Management with ie (replaces TodoWrite for persistent work)

## ie vs TodoWrite
  - TodoWrite: Single session, disposable tasks
  - ie: Cross-session, hierarchical, decision-tracking (human + AI collaboration)

## Task Status Lifecycle
  todo  → Planning phase, tasks can be rough (no spec required)
  doing → Execution phase, MUST have spec (goal + approach)
  done  → Completion, all children must be done first

## Core Commands
  ie status                        # Restore context at session start
  echo '{...}' | ie plan           # Create/update/complete tasks
  ie log decision "..."            # Record WHY you made choices
  ie log blocker "..."             # Record impediments
  ie search "query"                # Find tasks and events

## When Plans Change
  Re-run \`ie plan\` to update task names, descriptions, or relationships.
  This keeps human and AI synchronized on the current state.

## Key Rules
  - status:doing requires spec (description with goal + approach)
  - status:done requires all children complete first
  - parent_id:null creates independent root task (ignores current focus)
</system-reminder>`);
