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
      stdio: ['ignore', 'pipe', 'pipe'],
      shell: isWin  // Windows needs shell: true
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
    if (DEBUG) {
      console.log(`[DEBUG] Method 1 - where/command -v result: ${iePath}`);
    }
    if (iePath && fs.existsSync(iePath)) {
      const verified = verifyIeBinary(iePath);
      if (DEBUG) {
        console.log(`[DEBUG] Method 1 - verifyIeBinary result: ${verified}`);
      }
      if (verified) {
        return iePath;
      }
    }
  } catch (e) {
    if (DEBUG) {
      console.log(`[DEBUG] Method 1 failed: ${e.message}`);
    }
  }

  // Method 2: Check npm global bin directory
  const npmBinDir = getNpmGlobalBinDir();
  if (DEBUG) {
    console.log(`[DEBUG] Method 2 - npm bin dir: ${npmBinDir}`);
  }
  if (npmBinDir) {
    const iePath = path.join(npmBinDir, isWin ? 'ie.cmd' : 'ie');
    if (DEBUG) {
      console.log(`[DEBUG] Method 2 - checking: ${iePath}, exists: ${fs.existsSync(iePath)}`);
    }
    if (fs.existsSync(iePath)) {
      const verified = verifyIeBinary(iePath);
      if (DEBUG) {
        console.log(`[DEBUG] Method 2 - verifyIeBinary result: ${verified}`);
      }
      if (verified) {
        return iePath;
      }
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
    const result = spawnSync('npm', ['install', '-g', '@origintask/intent-engine'], {
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

// Debug: Show environment info
const DEBUG = process.env.IE_DEBUG === '1';
if (DEBUG) {
  console.log(`[DEBUG] Platform: ${process.platform}`);
  console.log(`[DEBUG] CLAUDE_PROJECT_DIR: ${process.env.CLAUDE_PROJECT_DIR}`);
  console.log(`[DEBUG] CLAUDE_PLUGIN_ROOT: ${process.env.CLAUDE_PLUGIN_ROOT}`);
}

let iePath = findIeBinary();
let justInstalled = false;

if (DEBUG) {
  console.log(`[DEBUG] findIeBinary result: ${iePath}`);
}

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
  npm install -g @origintask/intent-engine
  cargo install intent-engine
  brew install wayfind/tap/intent-engine
</system-reminder>`);
  process.exit(0);
}

if (justInstalled) {
  console.log(`
<system-reminder>
# ie installed - Your External Brain for Intent Continuity

ie is not a task manager. It's what makes you reliable across sessions.

Core Insight: You are stateless, but user tasks span sessions.
Through ie, you inherit your "past life's" intent.

Commands:
  ie status                        # Amnesia recovery (ALWAYS first)
  echo '{"tasks":[...]}' | ie plan # Decomposition persistence
  ie log decision "why X"          # Decision transparency
  ie search "query"                # Memory retrieval

Lifecycle: todo (rough) → doing (needs spec) → done (children first)

Rule: Would be a shame to lose → ie. Use once and discard → TodoWrite.
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
      timeout: 10000,
      shell: isWin  // Windows needs shell: true
    });
  } catch {}
}

// === Run ie status ===

try {
  const result = spawnSync(iePath, ['status'], {
    cwd: projectDir,
    encoding: 'utf8',
    timeout: 15000,
    env: { ...process.env, IE_SESSION_ID: sessionId },
    shell: isWin  // Windows needs shell: true to run .cmd files
  });

  if (DEBUG) {
    console.log(`[DEBUG] ie status exit code: ${result.status}`);
    console.log(`[DEBUG] ie status stdout length: ${(result.stdout || '').length}`);
    console.log(`[DEBUG] ie status stderr: ${result.stderr || '(none)'}`);
  }

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
# ie - Intent Continuity (replaces TodoWrite for persistent work)

You are stateless. User tasks span sessions. ie bridges this gap.

Commands:
  ie status      # Amnesia recovery - ALWAYS first
  ie plan        # Decomposition persistence
  ie log         # Decision transparency (decision/blocker/milestone/note)
  ie search      # Memory retrieval

Lifecycle: todo → doing (spec required) → done (children first)

Habits:
  1. Session start: ie status
  2. Before doing: spec with goal + approach
  3. Decisions: ie log decision "..." immediately
  4. Blocked: ie log blocker "..."
  5. Amnesia test: "Is this enough to continue if I forget?"
</system-reminder>`);
