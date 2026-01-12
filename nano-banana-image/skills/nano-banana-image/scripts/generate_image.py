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
    python generate_image.py keys use <name>
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path

# =============================================================================
# Constants
# =============================================================================

CONFIG_DIR = Path.home() / ".config" / "nano-banana-image"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_MODEL = "gemini-3-pro-image-preview"

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
            config["keys"] = [{"name": "default", "key": old_key, "active": True}]
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


def get_next_key_index(config: dict) -> int:
    """Get the next key index using round-robin strategy."""
    keys = config.get("keys", [])
    if not keys:
        return -1
    last_index = config.get("last_used_index", -1)
    return (last_index + 1) % len(keys)


def update_last_used_index(index: int) -> None:
    """Update the last used key index in config."""
    config = load_config()
    config["last_used_index"] = index
    save_config(config)


def validate_key_format(key: str) -> bool:
    """Basic validation of Gemini API key format."""
    return key.startswith("AIza") and len(key) >= 30


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

    print(f"Configured API Keys ({len(keys)}) - Round Robin Mode:")
    print("-" * 50)
    for i, entry in enumerate(keys):
        name = entry.get("name", "unnamed")
        key = entry.get("key", "")
        masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        marker = ""
        if i == next_index:
            marker = " [NEXT]"
        elif i == last_index:
            marker = " [LAST USED]"
        print(f"  {i+1}. {name}: {masked_key}{marker}")
    print("-" * 50)
    print(f"Strategy: Round-robin (auto-rotate on each call)")
    print(f"Config: {CONFIG_FILE}")


def keys_add(name: str, api_key: str) -> None:
    """Add a new API key."""
    if not validate_key_format(api_key):
        print(f"ERROR: Invalid API key format. Key should start with 'AIza' and be 39 characters.")
        sys.exit(1)

    config = load_config()
    keys = config.get("keys", [])

    # Check if name already exists
    for entry in keys:
        if entry.get("name") == name:
            print(f"ERROR: Key with name '{name}' already exists.")
            print(f"Use 'keys remove {name}' first, or choose a different name.")
            sys.exit(1)

    keys.append({"name": name, "key": api_key})
    config["keys"] = keys
    save_config(config)

    masked_key = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"OK: Added key '{name}' ({masked_key})")
    print(f"    Total keys: {len(keys)} (round-robin)")


def keys_remove(name: str) -> None:
    """Remove an API key by name."""
    config = load_config()
    keys = config.get("keys", [])

    # Find and remove the key
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


def keys_reset() -> None:
    """Reset round-robin to start from first key."""
    config = load_config()
    config["last_used_index"] = -1
    save_config(config)
    print("OK: Round-robin reset. Next call will use first key.")


# =============================================================================
# Legacy Commands (for backward compatibility)
# =============================================================================


def setup_config(api_key: str, project_id: str = None) -> None:
    """Setup API key (legacy command, adds as 'default')."""
    config = load_config()
    keys = config.get("keys", [])

    # Remove existing 'default' if exists
    keys = [k for k in keys if k.get("name") != "default"]

    # Add new default key at the beginning
    keys.insert(0, {"name": "default", "key": api_key})

    config["keys"] = keys
    config["last_used_index"] = -1  # Reset to start with this key
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
    next_key = keys[next_index]
    api_key = next_key.get("key", "")

    if not validate_key_format(api_key):
        print("STATUS: INVALID_KEY")
        print(f"The stored API key appears invalid: {api_key[:10]}...")
        print("Please provide a valid Gemini API key.")
        return False

    print("STATUS: CONFIGURED")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Total keys: {len(keys)} (round-robin)")
    print(f"Next key: {next_key.get('name')} ({api_key[:10]}...{api_key[-4:]})")

    project_id = config.get("project_id")
    if project_id:
        print(f"Project ID: {project_id}")
    return True


def get_api_key(key_name: str = None) -> tuple[str, str]:
    """Get API key from config file using round-robin.

    Returns: (api_key, key_name)
    """
    config = load_config()
    keys = config.get("keys", [])

    if key_name:
        # Use specific key by name (doesn't affect round-robin)
        for entry in keys:
            if entry.get("name") == key_name:
                return entry.get("key"), key_name
        print(f"ERROR: Key '{key_name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    # Use round-robin
    if keys:
        next_index = get_next_key_index(config)
        entry = keys[next_index]
        update_last_used_index(next_index)
        return entry.get("key"), entry.get("name")

    # Fallback to environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key, "ENV"

    print("ERROR: Gemini API key not configured")
    print("")
    print("Run: python generate_image.py --check")
    print("to see setup instructions.")
    sys.exit(1)


# =============================================================================
# Image Generation
# =============================================================================


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "16:9",
                   model: str = DEFAULT_MODEL, key_name: str = None) -> str:
    """Generate an image using Gemini API with Nano Banana Pro style."""

    api_key, used_key_name = get_api_key(key_name)
    width, height = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])
    styled_prompt = f"{prompt}\n\n{NANO_BANANA_STYLE}\n\nImage dimensions: {width}x{height} pixels ({aspect_ratio} aspect ratio)"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": styled_prompt}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }

    print(f"Generating image: {prompt[:50]}...")
    print(f"Using key: {used_key_name}")
    print(f"Aspect ratio: {aspect_ratio}")
    print(f"Output: {output_path}")

    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

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
                    return output_path

                elif "text" in part:
                    print(f"Model response: {part['text'][:200]}")

        print("ERROR: No image generated in response")
        print(f"Response: {json.dumps(result, indent=2)[:500]}")
        sys.exit(1)

    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"ERROR: HTTP {e.code} - {e.reason}")
        if e.code == 403:
            print("The API key may be invalid or lack permissions.")
            print("Please verify your key at: https://aistudio.google.com/apikey")
        print(f"Details: {error_body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Connection failed - {e.reason}")
        sys.exit(1)
    except Exception as e:
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
        if len(args) < 3:
            print("Usage: keys add <name> <api-key>")
            sys.exit(1)
        keys_add(args[1], args[2])
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
Key Management (Round-Robin):
  %(prog)s keys list                    List all API keys
  %(prog)s keys add <name> <key>        Add a new API key
  %(prog)s keys remove <name>           Remove an API key
  %(prog)s keys reset                   Reset to start from first key

Image Generation:
  %(prog)s "description" output.png
  %(prog)s "description" output.png --aspect 1:1
  %(prog)s "description" output.png --key work    # Use specific key (skip rotation)

Legacy Commands:
  %(prog)s --setup --api-key "AIza..."  Add key as 'default'
  %(prog)s --check                      Check configuration

Strategy:
  Keys are used in round-robin order. Each generation uses the next key.
  Use --key <name> to use a specific key without affecting rotation.

Configuration:
  Keys stored in: ~/.config/nano-banana-image/config.json
"""
    )

    # Legacy setup/check commands
    parser.add_argument("--setup", action="store_true", help="Setup mode (legacy)")
    parser.add_argument("--check", action="store_true", help="Check configuration")
    parser.add_argument("--api-key", help="API key (used with --setup)")
    parser.add_argument("--project-id", help="Optional GCP Project ID")

    # Generation arguments
    parser.add_argument("prompt", nargs="?", help="Description of the image")
    parser.add_argument("output", nargs="?", default="output.png", help="Output file path")
    parser.add_argument("--aspect", default="16:9", choices=["1:1", "16:9", "9:16", "4:3", "3:4"])
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--key", dest="key_name", help="Use specific key by name")

    args = parser.parse_args()

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
