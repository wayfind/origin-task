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


def get_active_key_entry(config: dict) -> dict | None:
    """Get the active key entry from config."""
    for entry in config.get("keys", []):
        if entry.get("active"):
            return entry
    # If no active key, return first one
    keys = config.get("keys", [])
    return keys[0] if keys else None


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

    print(f"Configured API Keys ({len(keys)}):")
    print("-" * 50)
    for entry in keys:
        name = entry.get("name", "unnamed")
        key = entry.get("key", "")
        active = entry.get("active", False)
        masked_key = f"{key[:10]}...{key[-4:]}" if len(key) > 14 else "***"
        marker = " [ACTIVE]" if active else ""
        print(f"  {name}: {masked_key}{marker}")
    print("-" * 50)
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

    # If this is the first key, make it active
    is_first = len(keys) == 0

    keys.append({
        "name": name,
        "key": api_key,
        "active": is_first
    })
    config["keys"] = keys
    save_config(config)

    masked_key = f"{api_key[:10]}...{api_key[-4:]}"
    print(f"OK: Added key '{name}' ({masked_key})")
    if is_first:
        print(f"    Set as active key.")


def keys_remove(name: str) -> None:
    """Remove an API key by name."""
    config = load_config()
    keys = config.get("keys", [])

    # Find and remove the key
    found = False
    was_active = False
    new_keys = []
    for entry in keys:
        if entry.get("name") == name:
            found = True
            was_active = entry.get("active", False)
        else:
            new_keys.append(entry)

    if not found:
        print(f"ERROR: Key '{name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    # If removed key was active, activate first remaining key
    if was_active and new_keys:
        new_keys[0]["active"] = True
        print(f"OK: Removed key '{name}'")
        print(f"    Activated '{new_keys[0]['name']}' as new default.")
    else:
        print(f"OK: Removed key '{name}'")

    config["keys"] = new_keys
    save_config(config)


def keys_use(name: str) -> None:
    """Set a key as active by name."""
    config = load_config()
    keys = config.get("keys", [])

    # Find the key and set it as active
    found = False
    for entry in keys:
        if entry.get("name") == name:
            entry["active"] = True
            found = True
        else:
            entry["active"] = False

    if not found:
        print(f"ERROR: Key '{name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    config["keys"] = keys
    save_config(config)
    print(f"OK: Now using key '{name}'")


# =============================================================================
# Legacy Commands (for backward compatibility)
# =============================================================================


def setup_config(api_key: str, project_id: str = None) -> None:
    """Setup API key (legacy command, adds as 'default')."""
    config = load_config()
    keys = config.get("keys", [])

    # Remove existing 'default' if exists
    keys = [k for k in keys if k.get("name") != "default"]

    # Deactivate all existing keys
    for k in keys:
        k["active"] = False

    # Add new default key as active
    keys.insert(0, {"name": "default", "key": api_key, "active": True})

    config["keys"] = keys
    if project_id:
        config["project_id"] = project_id
    save_config(config)
    print(f"OK: Configuration saved to {CONFIG_FILE}")


def check_config() -> bool:
    """Check if configuration exists and is valid."""
    config = load_config()
    active = get_active_key_entry(config)

    if not active:
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

    api_key = active.get("key", "")
    if not validate_key_format(api_key):
        print("STATUS: INVALID_KEY")
        print(f"The stored API key appears invalid: {api_key[:10]}...")
        print("Please provide a valid Gemini API key.")
        return False

    print("STATUS: CONFIGURED")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Active key: {active.get('name')} ({api_key[:10]}...{api_key[-4:]})")

    total_keys = len(config.get("keys", []))
    if total_keys > 1:
        print(f"Total keys: {total_keys}")

    project_id = config.get("project_id")
    if project_id:
        print(f"Project ID: {project_id}")
    return True


def get_api_key(key_name: str = None) -> str:
    """Get API key from config file."""
    config = load_config()

    if key_name:
        # Use specific key by name
        for entry in config.get("keys", []):
            if entry.get("name") == key_name:
                return entry.get("key")
        print(f"ERROR: Key '{key_name}' not found.")
        print("Use 'keys list' to see available keys.")
        sys.exit(1)

    # Use active key
    active = get_active_key_entry(config)
    if active:
        return active.get("key")

    # Fallback to environment variable
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        return api_key

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

    api_key = get_api_key(key_name)
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


def main():
    parser = argparse.ArgumentParser(
        description="Generate Nano Banana Pro styled images using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Key Management:
  %(prog)s keys list                    List all API keys
  %(prog)s keys add <name> <key>        Add a new API key
  %(prog)s keys remove <name>           Remove an API key
  %(prog)s keys use <name>              Set active API key

Image Generation:
  %(prog)s "description" output.png
  %(prog)s "description" output.png --aspect 1:1
  %(prog)s "description" output.png --key work    # Use specific key

Legacy Commands:
  %(prog)s --setup --api-key "AIza..."  Add key as 'default'
  %(prog)s --check                      Check configuration

Configuration:
  Keys stored in: ~/.config/nano-banana-image/config.json
"""
    )

    # Subcommand for key management
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    keys_parser = subparsers.add_parser("keys", help="Manage API keys")
    keys_subparsers = keys_parser.add_subparsers(dest="keys_command")

    # keys list
    keys_subparsers.add_parser("list", help="List all API keys")

    # keys add
    keys_add_parser = keys_subparsers.add_parser("add", help="Add a new API key")
    keys_add_parser.add_argument("name", help="Name for the key (e.g., 'work', 'personal')")
    keys_add_parser.add_argument("api_key", help="Gemini API key")

    # keys remove
    keys_remove_parser = keys_subparsers.add_parser("remove", help="Remove an API key")
    keys_remove_parser.add_argument("name", help="Name of the key to remove")

    # keys use
    keys_use_parser = keys_subparsers.add_parser("use", help="Set active API key")
    keys_use_parser.add_argument("name", help="Name of the key to activate")

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

    # Handle keys subcommand
    if args.command == "keys":
        if args.keys_command == "list":
            keys_list()
        elif args.keys_command == "add":
            keys_add(args.name, args.api_key)
        elif args.keys_command == "remove":
            keys_remove(args.name)
        elif args.keys_command == "use":
            keys_use(args.name)
        else:
            keys_parser.print_help()
        return

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
