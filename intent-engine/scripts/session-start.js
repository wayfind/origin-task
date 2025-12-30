#!/usr/bin/env node
// Intent-Engine Session Start Hook
// Cross-platform Node.js implementation with auto-install

const { execSync, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

// === Platform detection ===

const isWin = process.platform === 'win32';

// Detect WSL (Windows Subsystem for Linux)
// WSL reports platform as 'linux' but may use Windows npm
function isWSL() {
  if (process.platform !== 'linux') return false;
  try {
    const release = fs.readFileSync('/proc/version', 'utf8').toLowerCase();
    return release.includes('microsoft') || release.includes('wsl');
  } catch {
    return false;
  }
}
const runningInWSL = isWSL();

// === Debug logging ===
const DEBUG = process.env.IE_DEBUG === '1';
const debugLogFile = path.join(os.tmpdir(), 'ie-session-start.log');

function debugLog(message) {
  if (DEBUG) {
    const timestamp = new Date().toISOString();
    const line = `[${timestamp}] ${message}\n`;
    try {
      fs.appendFileSync(debugLogFile, line);
    } catch {}
  }
}

debugLog('=== Session start hook begins ===');
debugLog(`Platform: ${process.platform}, isWin: ${isWin}, runningInWSL: ${runningInWSL}`);

// === TTY output for user-visible progress ===
// Use stderr for user-visible messages (not captured by Claude Code for SessionStart)

/**
 * Output message directly to user's terminal via stderr
 * Claude Code ignores stderr for SessionStart hooks, but terminal still shows it
 */
function ttyLog(message) {
  process.stderr.write(message + '\n');
}

/**
 * Close TTY - no-op for stderr approach
 */
function closeTty() {
  // No cleanup needed for stderr
}

// === Parse stdin (session_id) ===

let sessionId = '';
try {
  // Only read stdin if it's piped (not interactive TTY)
  if (!process.stdin.isTTY) {
    const input = fs.readFileSync(0, 'utf8').trim();
    if (input) {
      const data = JSON.parse(input);
      sessionId = data.session_id || '';
    }
  }
} catch {
  // Ignore parse errors - stdin may be empty or invalid
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

/**
 * Execute a command and return trimmed output
 * Handles Windows shell requirements
 */
function execCommand(cmd) {
  return execSync(cmd, {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'ignore'],
    shell: true,  // Always use shell for cross-platform compatibility
    timeout: 10000
  }).trim().replace(/\r\n/g, '\n');  // Normalize Windows line endings
}

/**
 * Check if a command exists in PATH
 */
function commandExists(cmd) {
  try {
    execCommand(isWin ? `where ${cmd}` : `command -v ${cmd}`);
    return true;
  } catch {
    return false;
  }
}

/**
 * Verify ie binary works by running --version
 * Windows: .cmd files MUST be executed through shell
 */
function verifyIeBinary(iePath) {
  debugLog(`verifyIeBinary: checking ${iePath}`);
  try {
    // Windows: use shell with combined command string to avoid DEP0190 warning
    const result = isWin
      ? spawnSync(`"${iePath}" --version`, {
          encoding: 'utf8',
          timeout: 5000,
          stdio: ['ignore', 'pipe', 'pipe'],
          windowsHide: true,
          shell: true
        })
      : spawnSync(iePath, ['--version'], {
          encoding: 'utf8',
          timeout: 5000,
          stdio: ['ignore', 'pipe', 'pipe'],
          windowsHide: true
        });
    const ok = result.status === 0 && !result.error;
    debugLog(`verifyIeBinary: status=${result.status}, error=${result.error}, ok=${ok}`);
    return ok;
  } catch (e) {
    debugLog(`verifyIeBinary: exception ${e.message}`);
    return false;
  }
}

/**
 * Get npm global bin directory
 */
function getNpmGlobalBinDir() {
  try {
    const prefix = execCommand('npm config get prefix');
    // Windows: binaries are in prefix root
    // Unix: binaries are in prefix/bin
    return isWin ? prefix : path.join(prefix, 'bin');
  } catch {
    return null;
  }
}

/**
 * Find ie binary in PATH or npm global directory
 */
function findIeBinary() {
  debugLog('findIeBinary: starting search');

  // Method 1: Check if ie is in PATH
  try {
    const output = execCommand(isWin ? 'where ie' : 'command -v ie');
    const iePath = output.split('\n')[0].trim();
    debugLog(`findIeBinary: PATH lookup returned: ${iePath}`);
    if (iePath && fs.existsSync(iePath) && verifyIeBinary(iePath)) {
      debugLog(`findIeBinary: found via PATH: ${iePath}`);
      return iePath;
    }
  } catch (e) {
    debugLog(`findIeBinary: PATH lookup failed: ${e.message}`);
  }

  // Method 2: Check npm global bin directory
  const npmBinDir = getNpmGlobalBinDir();
  debugLog(`findIeBinary: npm bin dir: ${npmBinDir}`);
  if (npmBinDir) {
    const iePath = path.join(npmBinDir, isWin ? 'ie.cmd' : 'ie');
    debugLog(`findIeBinary: checking npm path: ${iePath}`);
    if (fs.existsSync(iePath) && verifyIeBinary(iePath)) {
      debugLog(`findIeBinary: found via npm: ${iePath}`);
      return iePath;
    }
  }

  // Method 3: Check common Windows npm locations
  if (isWin) {
    const commonPaths = [
      path.join(process.env.APPDATA || '', 'npm', 'ie.cmd'),
      path.join(process.env.LOCALAPPDATA || '', 'npm', 'ie.cmd'),
      path.join(process.env.ProgramFiles || '', 'nodejs', 'ie.cmd')
    ];
    for (const p of commonPaths) {
      debugLog(`findIeBinary: checking common path: ${p}`);
      if (p && fs.existsSync(p) && verifyIeBinary(p)) {
        debugLog(`findIeBinary: found via common path: ${p}`);
        return p;
      }
    }
  }

  debugLog('findIeBinary: not found');
  return null;
}

/**
 * Run a command with proper error handling
 * Windows: requires shell for .cmd files (npm.cmd, ie.cmd, etc.)
 */
function runCommand(cmd, args, options = {}) {
  // Windows: combine command and args to avoid DEP0190 warning
  // Quote the command and each argument for safety
  const spawnOptions = {
    encoding: 'utf8',
    timeout: options.timeout || 15000,
    stdio: options.stdio || ['ignore', 'pipe', 'pipe'],
    cwd: options.cwd,
    env: options.env || process.env,
    windowsHide: true
  };

  let result;
  if (isWin) {
    const quotedArgs = args.map(a => `"${a}"`).join(' ');
    result = spawnSync(`"${cmd}" ${quotedArgs}`, {
      ...spawnOptions,
      shell: true
    });
  } else {
    result = spawnSync(cmd, args, spawnOptions);
  }

  return {
    success: result.status === 0 && !result.error,
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    error: result.error
  };
}

/**
 * Check if npm is using Windows paths (for WSL detection)
 */
function isWindowsNpm() {
  try {
    const prefix = execCommand('npm prefix -g');
    // Windows paths start with drive letter (C:\, D:\, etc.) or /mnt/c style
    return /^[A-Za-z]:[\\\/]/.test(prefix) || prefix.startsWith('/mnt/');
  } catch {
    return false;
  }
}

/**
 * Install intent-engine via npm
 */
function installIe() {
  debugLog('installIe: starting');
  if (!commandExists('npm')) {
    debugLog('installIe: npm not found');
    ttyLog('[intent-engine] npm not found. Cannot auto-install.');
    return false;
  }

  ttyLog('');
  ttyLog('========================================');
  ttyLog('  Installing intent-engine...');
  ttyLog('  This may take a few seconds.');
  ttyLog('========================================');

  debugLog('installIe: running npm install -g @origintask/intent-engine');
  // Use execSync with shell to run npm install (avoids node_modules lookup issues)
  try {
    const output = execSync('npm install -g @origintask/intent-engine', {
      encoding: 'utf8',
      timeout: 120000,
      stdio: ['pipe', 'pipe', 'pipe'],
      shell: true,
      windowsHide: true
    });
    debugLog(`installIe: success, output=${output?.slice(0,200)}`);
  } catch (e) {
    const errorMsg = (e.stderr || e.stdout || e.message || 'Unknown error').slice(0, 300);
    debugLog(`installIe: failed with: ${errorMsg}`);
    ttyLog('  ✗ Installation failed: ' + errorMsg);
    ttyLog('========================================');
    return false;
  }

  // WSL with Windows npm: also install linux platform package
  // Windows npm installs win32-x64 package, but WSL needs linux-x64
  if (runningInWSL && isWindowsNpm()) {
    debugLog('WSL detected with Windows npm, installing linux-x64 platform package');
    ttyLog('  Installing linux platform package for WSL...');
    const linuxResult = runCommand('npm', ['install', '-g', '@origintask/intent-engine-linux-x64', '--force'], {
      timeout: 60000
    });
    if (!linuxResult.success) {
      debugLog(`linux-x64 install failed: ${linuxResult.stderr}`);
      // Non-fatal: the binary might still work
    }
  }

  ttyLog('  ✓ intent-engine installed successfully!');
  ttyLog('========================================');
  ttyLog('');
  return true;
}

// === Main logic ===

debugLog('=== Main logic starts ===');
let iePath = findIeBinary();
debugLog(`Initial findIeBinary result: ${iePath}`);
let justInstalled = false;

if (!iePath) {
  debugLog('ie not found, attempting install');
  const installed = installIe();
  debugLog(`installIe result: ${installed}`);
  if (installed) {
    // Wait a moment for filesystem to sync on Windows
    if (isWin) {
      try { execSync('timeout /t 1 /nobreak >nul 2>&1', { shell: true }); } catch {}
    }
    iePath = findIeBinary();
    debugLog(`Post-install findIeBinary result: ${iePath}`);
    if (iePath) {
      justInstalled = true;
    } else {
      ttyLog('[intent-engine] Installation succeeded but ie binary not found.');
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
  closeTty();
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
  runCommand(iePath, ['init'], {
    cwd: projectDir,
    stdio: 'ignore',
    timeout: 10000
  });
}

// === Run ie status ===

const statusResult = runCommand(iePath, ['status'], {
  cwd: projectDir,
  env: { ...process.env, IE_SESSION_ID: sessionId }
});

if (statusResult.stdout) {
  console.log(statusResult.stdout);
}
if (statusResult.stderr) {
  console.error(statusResult.stderr);
}
if (statusResult.error) {
  ttyLog('[intent-engine] Failed to run ie status: ' + statusResult.error.message);
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

// === Cleanup ===
closeTty();
