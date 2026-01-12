#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator
Generates images using Gemini API with Nano Banana Pro style.

Usage:
    python generate_image.py "your description" [output.png] [--aspect 16:9]

Key Management:
    python generate_image.py keys list
    python generate_image.py keys add <name> <api-key>
    python generate_image.py keys remove <name>
    python generate_image.py keys reset
"""

import argparse
import base64
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

# =============================================================================
# Logging Setup
# =============================================================================

LOG_DIR = Path.home() / ".config" / "nano-banana-image" / "logs"
LOG_FILE = LOG_DIR / "generate.log"

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Setup logging with file and optional console output."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("nano-banana")
    logger.setLevel(logging.DEBUG)

    # Clear existing handlers to prevent duplicates
    logger.handlers.clear()

    # File handler - always log everything
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - only if verbose
    if verbose:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    return logger

log = setup_logging()

# =============================================================================
# Constants
# =============================================================================

CONFIG_DIR = Path.home() / ".config" / "nano-banana-image"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_MODEL = "gemini-3-pro-image-preview"
VALIDATION_MODEL = "gemini-2.0-flash"  # Faster model for key validation

# Cooldown duration for failed keys (seconds)
KEY_COOLDOWN_SECONDS = 300  # 5 minutes

ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 896),
    "3:4": (896, 1152),
}

NANO_BANANA_STYLE = """
Style guidelines for the image:
- Color palette: Deep navy background (#1C2833), golden yellow accents (#F4C430), teal highlights (#00D9C0)
- Visual style: Modern, minimalist, tech-forward, premium feel
- Mood: Professional yet energetic, innovative, clean
- Elements: Geometric shapes (circles, diamonds), subtle gradients, high contrast
- Aesthetic: Dark mode UI style, sleek product visualization, futuristic
"""

# =============================================================================
# Configuration Management (Multi-Key Support)
# =============================================================================


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {"keys": []}
    try:
        config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        # Migrate old single-key format to new multi-key format
        if "gemini_api_key" in config and "keys" not in config:
            old_key = config.pop("gemini_api_key")
            config["keys"] = [{"name": "default", "key": old_key}]
            save_config(config)
        if "keys" not in config:
            config["keys"] = []
        return config
    except (json.JSONDecodeError, IOError):
        return {"keys": []}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass


def get_next_key_index(config: dict, skip_cooldown: bool = True) -> int:
    """Get the next key index using round-robin strategy.

    If skip_cooldown is True, skip keys that are in cooldown.
    Returns -1 if no valid keys available.
    """
    keys = config.get("keys", [])
    if not keys:
        return -1

    last_index = config.get("last_used_index", -1)
    now = time.time()

    # Try each key in round-robin order
    for offset in range(1, len(keys) + 1):
        candidate_index = (last_index + offset) % len(keys)
        entry = keys[candidate_index]

        if skip_cooldown:
            cooldown_until = entry.get("cooldown_until", 0)
            if cooldown_until > now:
                log.debug(f"Skipping key '{entry.get('name')}' - in cooldown until {datetime.fromtimestamp(cooldown_until)}")
                continue

        return candidate_index

    # All keys in cooldown - return first one anyway
    log.warning("All keys in cooldown, using first key anyway")
    return (last_index + 1) % len(keys)


def update_last_used_index(index: int) -> None:
    """Update the last used key index in config."""
    config = load_config()
    config["last_used_index"] = index
    save_config(config)


def mark_key_cooldown(key_name: str, duration: int = KEY_COOLDOWN_SECONDS) -> None:
    """Mark a key as in cooldown after a failure."""
    config = load_config()
    keys = config.get("keys", [])

    for entry in keys:
        if entry.get("name") == key_name:
            entry["cooldown_until"] = time.time() + duration
            entry["last_error_time"] = time.time()
            entry["error_count"] = entry.get("error_count", 0) + 1
            log.warning(f"Key '{key_name}' marked in cooldown for {duration}s (error #{entry['error_count']})")
            break

    config["keys"] = keys
    save_config(config)


def clear_key_cooldown(key_name: str) -> None:
    """Clear cooldown for a key after successful use."""
    config = load_config()
    keys = config.get("keys", [])

    for entry in keys:
        if entry.get("name") == key_name:
            if "cooldown_until" in entry:
                del entry["cooldown_until"]
                log.debug(f"Cleared cooldown for key '{key_name}'")
            break

    config["keys"] = keys
    save_config(config)


def validate_key_format(key: str) -> bool:
    """Basic validation of Gemini API key format."""
    return key.startswith("AIza") and len(key) >= 30


def validate_key_api(api_key: str) -> tuple[bool, str]:
    """Validate API key by making a test API call.

    Returns: (is_valid, error_message)
    """
    log.info(f"Validating API key: {api_key[:10]}...")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{VALIDATION_MODEL}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": "Say 'OK' in one word."}]}],
        "generationConfig": {"maxOutputTokens": 10}
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        if "candidates" in result:
            log.info("API key validation successful")
            return True, ""
        else:
            return False, "Unexpected API response"

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        log.error(f"API key validation failed: HTTP {e.code} - {error_body[:200]}")

        if e.code == 400:
            return False, "Invalid request - key may be malformed"
        elif e.code == 403:
            return False, "Permission denied - key invalid or lacks API access"
        elif e.code == 429:
            # Rate limited but key is valid
            return True, ""
        else:
            return False, f"HTTP {e.code}: {e.reason}"

    except urllib.error.URLError as e:
        log.error(f"API key validation failed: {e.reason}")
        return False, f"Connection error: {e.reason}"
    except Exception as e:
        log.error(f"API key validation failed: {e}")
        return False, str(e)


# =============================================================================
# Key Management Commands
# =============================================================================


def keys_list() -> None:
    """List all configured API keys."""
    config = load_config()
    keys = config.get("keys", [])

    if not keys:
        print("No API keys configured.")
        print("")
        print("Add a key with:")
        print("  python generate_image.py keys add <name> <api-key>")
        print("")
        print("Get your key from: https://aistudio.google.com/apikey")
        return

    next_index = get_next_key_index(config)
    last_index = config.get("last_used_index", -1)
    now = time.time()

    print(f"Configured API Keys ({len(keys)}) - Round Robin with Failover:")
    print("-" * 60)
    for i, entry in enumerate(keys):
        name = entry.get("name", "unnamed")
        key = entry.get("key", "")
        masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"

        markers = []
        if i == next_index:
            markers.append("NEXT")
        elif i == last_index:
            markers.append("LAST")

        cooldown_until = entry.get("cooldown_until", 0)
        if cooldown_until > now:
            remaining = int(cooldown_until - now)
            markers.append(f"COOLDOWN {remaining}s")

        error_count = entry.get("error_count", 0)
        if error_count > 0:
            markers.append(f"errors:{error_count}")

        marker_str = f" [{', '.join(markers)}]" if markers else ""
        print(f"  {i+1}. {name}: {masked_key}{marker_str}")

    print("-" * 60)
    print(f"Strategy: Round-robin with automatic failover")
    print(f"Config: {CONFIG_FILE}")
    print(f"Logs: {LOG_FILE}")


def keys_add(name: str, api_key: str, skip_validation: bool = False) -> None:
    """Add a new API key with validation."""
    # Format validation
    if not validate_key_format(api_key):
        print(f"ERROR: Invalid API key format.")
        print("Key should start with 'AIza' and be ~39 characters.")
        sys.exit(1)

    config = load_config()
    keys = config.get("keys", [])

    # Check if name already exists
    for entry in keys:
        if entry.get("name") == name:
            print(f"ERROR: Key with name '{name}' already exists.")
            print(f"Use 'keys remove {name}' first, or choose a different name.")
            sys.exit(1)

    # API validation
    if not skip_validation:
        print(f"Validating API key...")
        is_valid, error_msg = validate_key_api(api_key)
        if not is_valid:
            print(f"ERROR: API key validation failed.")
            print(f"Reason: {error_msg}")
            print("")
            print("To add without validation: keys add --no-validate <name> <key>")
            sys.exit(1)
        print("API key validated successfully.")

    keys.append({"name": name, "key": api_key})
    config["keys"] = keys
    save_config(config)

    masked_key = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"OK: Added key '{name}' ({masked_key})")
    print(f"    Total keys: {len(keys)} (round-robin with failover)")
    log.info(f"Added key '{name}'")


def keys_remove(name: str) -> None:
    """Remove an API key by name."""
    config = load_config()
    keys = config.get("keys", [])

    found_index = -1
    for i, entry in enumerate(keys):
        if entry.get("name") == name:
            found_index = i
            break

    if found_index == -1:
        print(f"ERROR: Key '{name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    keys.pop(found_index)
    config["keys"] = keys

    # Adjust last_used_index if needed
    last_index = config.get("last_used_index", -1)
    if last_index >= len(keys):
        config["last_used_index"] = len(keys) - 1 if keys else -1
    elif last_index >= found_index and last_index > 0:
        config["last_used_index"] = last_index - 1

    save_config(config)
    print(f"OK: Removed key '{name}'")
    print(f"    Remaining keys: {len(keys)}")
    log.info(f"Removed key '{name}'")


def keys_reset() -> None:
    """Reset round-robin and clear all cooldowns."""
    config = load_config()
    config["last_used_index"] = -1

    # Clear all cooldowns
    for entry in config.get("keys", []):
        if "cooldown_until" in entry:
            del entry["cooldown_until"]
        if "error_count" in entry:
            del entry["error_count"]

    save_config(config)
    print("OK: Round-robin reset. All cooldowns cleared.")
    log.info("Reset round-robin and cleared cooldowns")


# =============================================================================
# Legacy Commands (for backward compatibility)
# =============================================================================


def setup_config(api_key: str, project_id: str = None) -> None:
    """Setup API key (legacy command, adds as 'default')."""
    config = load_config()
    keys = config.get("keys", [])

    # Remove existing 'default' if exists
    keys = [k for k in keys if k.get("name") != "default"]

    # Validate key
    print("Validating API key...")
    is_valid, error_msg = validate_key_api(api_key)
    if not is_valid:
        print(f"WARNING: API key validation failed: {error_msg}")
        print("Adding key anyway...")

    # Add new default key at the beginning
    keys.insert(0, {"name": "default", "key": api_key})

    config["keys"] = keys
    config["last_used_index"] = -1
    if project_id:
        config["project_id"] = project_id
    save_config(config)
    print(f"OK: Configuration saved to {CONFIG_FILE}")


def check_config() -> bool:
    """Check if configuration exists and is valid."""
    config = load_config()
    keys = config.get("keys", [])

    if not keys:
        print("STATUS: NOT_CONFIGURED")
        print("")
        print("=" * 60)
        print("NANO BANANA IMAGE - FIRST TIME SETUP REQUIRED")
        print("=" * 60)
        print("")
        print("To use this skill, you need a Gemini API key.")
        print("")
        print("Steps for user:")
        print("  1. Go to: https://aistudio.google.com/apikey")
        print("  2. Click 'Create API Key'")
        print("  3. Copy the key (starts with 'AIza...')")
        print("  4. Provide the key to me")
        print("")
        print("Once you have the key, tell me:")
        print('  "My Gemini API key is: AIza..."')
        print("")
        print("=" * 60)
        return False

    next_index = get_next_key_index(config)
    if next_index < 0:
        print("STATUS: NO_VALID_KEYS")
        return False

    next_key = keys[next_index]
    api_key = next_key.get("key", "")

    if not validate_key_format(api_key):
        print("STATUS: INVALID_KEY")
        print(f"The stored API key appears invalid: {api_key[:10]}...")
        print("Please provide a valid Gemini API key.")
        return False

    print("STATUS: CONFIGURED")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Log file: {LOG_FILE}")
    print(f"Total keys: {len(keys)} (round-robin with failover)")
    print(f"Next key: {next_key.get('name')} ({api_key[:10]}...{api_key[-4:]})")

    project_id = config.get("project_id")
    if project_id:
        print(f"Project ID: {project_id}")
    return True


def get_api_key_with_failover(key_name: str = None) -> tuple[str, str, int]:
    """Get API key with failover support.

    Returns: (api_key, key_name, key_index)
    """
    config = load_config()
    keys = config.get("keys", [])

    if key_name:
        # Use specific key by name (doesn't affect round-robin)
        for i, entry in enumerate(keys):
            if entry.get("name") == key_name:
                return entry.get("key"), key_name, i
        print(f"ERROR: Key '{key_name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    # Use round-robin with cooldown skip
    if keys:
        next_index = get_next_key_index(config, skip_cooldown=True)
        if next_index >= 0:
            entry = keys[next_index]
            return entry.get("key"), entry.get("name"), next_index

    # Fallback to environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key, "ENV", -1

    print("ERROR: Gemini API key not configured")
    print("")
    print("Run: python generate_image.py --check")
    print("to see setup instructions.")
    sys.exit(1)


# =============================================================================
# Image Generation
# =============================================================================


def call_gemini_api(api_key: str, prompt: str, model: str) -> dict:
    """Call Gemini API and return result or raise exception."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "16:9",
                   model: str = DEFAULT_MODEL, key_name: str = None) -> str:
    """Generate an image using Gemini API with Nano Banana Pro style.

    Implements failover: if one key fails, tries the next one.
    """
    config = load_config()
    keys = config.get("keys", [])
    num_keys = len(keys)

    width, height = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
    styled_prompt = f"{prompt}\n\n{NANO_BANANA_STYLE}\n\nImage dimensions: {width}x{height} pixels ({aspect_ratio} aspect ratio)"

    print(f"Generating image: {prompt[:50]}...")
    print(f"Aspect ratio: {aspect_ratio}")
    print(f"Output: {output_path}")

    log.info(f"Starting generation: prompt='{prompt[:50]}...', aspect={aspect_ratio}, output={output_path}")

    # If specific key requested, use only that key
    if key_name:
        api_key, used_key_name, key_index = get_api_key_with_failover(key_name)
        print(f"Using key: {used_key_name} (specified)")
        log.info(f"Using specified key: {used_key_name}")

        return _try_generate(api_key, used_key_name, key_index, styled_prompt, output_path, model)

    # Round-robin with failover
    tried_keys = set()
    last_error = None

    while len(tried_keys) < num_keys:
        api_key, used_key_name, key_index = get_api_key_with_failover()

        if used_key_name in tried_keys:
            break  # Already tried this key

        tried_keys.add(used_key_name)
        print(f"Using key: {used_key_name}")
        log.info(f"Trying key: {used_key_name} (index {key_index})")

        try:
            result = _try_generate(api_key, used_key_name, key_index, styled_prompt, output_path, model)
            # Success - clear any cooldown
            clear_key_cooldown(used_key_name)
            return result

        except KeyFailureError as e:
            last_error = e
            log.warning(f"Key '{used_key_name}' failed: {e}, trying next key...")
            mark_key_cooldown(used_key_name)
            print(f"Key '{used_key_name}' failed, trying next...")
            continue

    # All keys failed
    log.error(f"All {num_keys} keys failed")
    print(f"ERROR: All {num_keys} keys failed.")
    if last_error:
        print(f"Last error: {last_error}")
    sys.exit(1)


class KeyFailureError(Exception):
    """Exception for recoverable key failures (should try next key)."""
    pass


def _try_generate(api_key: str, key_name: str, key_index: int,
                  styled_prompt: str, output_path: str, model: str) -> str:
    """Try to generate image with a specific key. Raises KeyFailureError on recoverable failures."""

    # Update last used index
    if key_index >= 0:
        update_last_used_index(key_index)

    try:
        result = call_gemini_api(api_key, styled_prompt, model)

        if "candidates" in result and result["candidates"]:
            parts = result["candidates"][0].get("content", {}).get("parts", [])

            for part in parts:
                if "inlineData" in part:
                    image_data = part["inlineData"]["data"]
                    mime_type = part["inlineData"].get("mimeType", "image/png")
                    image_bytes = base64.b64decode(image_data)

                    ext = ".png"
                    if "jpeg" in mime_type or "jpg" in mime_type:
                        ext = ".jpg"
                    elif "webp" in mime_type:
                        ext = ".webp"

                    if not output_path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        output_path = output_path + ext

                    with open(output_path, "wb") as f:
                        f.write(image_bytes)

                    print(f"Image saved: {output_path}")
                    print(f"Size: {len(image_bytes) / 1024:.1f} KB")
                    log.info(f"Image saved: {output_path}, size={len(image_bytes)} bytes, key={key_name}")
                    return output_path

                elif "text" in part:
                    log.debug(f"Model text response: {part['text'][:200]}")
                    print(f"Model response: {part['text'][:200]}")

        log.error(f"No image in response: {json.dumps(result)[:500]}")
        print("ERROR: No image generated in response")
        print(f"Response: {json.dumps(result, indent=2)[:500]}")
        sys.exit(1)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        log.error(f"HTTP {e.code} from key '{key_name}': {error_body[:300]}")

        # Recoverable errors - try next key
        if e.code in (429, 503, 500):
            raise KeyFailureError(f"HTTP {e.code} - {e.reason}")

        # 403 might be key-specific issue
        if e.code == 403:
            raise KeyFailureError(f"HTTP 403 - key may be invalid or rate limited")

        # Other errors - don't retry
        print(f"ERROR: HTTP {e.code} - {e.reason}")
        print(f"Details: {error_body[:500]}")
        sys.exit(1)

    except urllib.error.URLError as e:
        log.error(f"Connection error: {e.reason}")
        print(f"ERROR: Connection failed - {e.reason}")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {type(e).__name__} - {e}")
        print(f"ERROR: {type(e).__name__} - {e}")
        sys.exit(1)


# =============================================================================
# CLI
# =============================================================================


def handle_keys_command(args: list) -> None:
    """Handle 'keys' subcommand."""
    if not args or args[0] == "list":
        keys_list()
    elif args[0] == "add":
        # Check for --no-validate flag
        skip_validate = "--no-validate" in args
        args = [a for a in args if a != "--no-validate"]

        if len(args) < 3:
            print("Usage: keys add [--no-validate] <name> <api-key>")
            sys.exit(1)
        keys_add(args[1], args[2], skip_validation=skip_validate)
    elif args[0] == "remove":
        if len(args) < 2:
            print("Usage: keys remove <name>")
            sys.exit(1)
        keys_remove(args[1])
    elif args[0] == "reset":
        keys_reset()
    else:
        print(f"Unknown keys command: {args[0]}")
        print("Available: list, add, remove, reset")
        sys.exit(1)


def main():
    # Handle 'keys' subcommand manually (before argparse)
    if len(sys.argv) > 1 and sys.argv[1] == "keys":
        handle_keys_command(sys.argv[2:])
        return

    parser = argparse.ArgumentParser(
        description="Generate Nano Banana Pro styled images using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Key Management (Round-Robin with Failover):
  %(prog)s keys list                              List all API keys
  %(prog)s keys add <name> <key>                  Add key (validates first)
  %(prog)s keys add --no-validate <name> <key>    Add key without validation
  %(prog)s keys remove <name>                     Remove an API key
  %(prog)s keys reset                             Reset rotation & cooldowns

Image Generation:
  %(prog)s "description" output.png
  %(prog)s "description" output.png --aspect 1:1
  %(prog)s "description" output.png --key work    # Use specific key

Legacy Commands:
  %(prog)s --setup --api-key "AIza..."  Add key as 'default'
  %(prog)s --check                      Check configuration

Strategy:
  Keys are used in round-robin order with automatic failover.
  Failed keys are put in cooldown (5 min) and skipped.

Configuration:
  Keys: ~/.config/nano-banana-image/config.json
  Logs: ~/.config/nano-banana-image/logs/generate.log
"""
    )

    # Legacy setup/check commands
    parser.add_argument("--setup", action="store_true", help="Setup mode (legacy)")
    parser.add_argument("--check", action="store_true", help="Check configuration")
    parser.add_argument("--api-key", help="API key (used with --setup)")
    parser.add_argument("--project-id", help="Optional GCP Project ID")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging to console")

    # Generation arguments
    parser.add_argument("prompt", nargs="?", help="Description of the image")
    parser.add_argument("output", nargs="?", default="output.png", help="Output file path")
    parser.add_argument("--aspect", default="16:9", choices=["1:1", "16:9", "9:16", "4:3", "3:4"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--key", dest="key_name", help="Use specific key by name")

    args = parser.parse_args()

    # Re-setup logging with verbose if requested
    if args.verbose:
        global log
        log = setup_logging(verbose=True)

    # Handle legacy setup command
    if args.setup:
        if not args.api_key:
            print("ERROR: --api-key is required with --setup")
            sys.exit(1)
        setup_config(args.api_key, args.project_id)
        return

    # Handle check command
    if args.check:
        sys.exit(0 if check_config() else 1)

    # Generate image
    if not args.prompt:
        if not check_config():
            sys.exit(1)
        parser.print_help()
        sys.exit(0)

    generate_image(args.prompt, args.output, args.aspect, args.model, args.key_name)


if __name__ == "__main__":
    main()
