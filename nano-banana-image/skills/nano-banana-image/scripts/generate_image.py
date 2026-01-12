#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator
Generates images using Gemini API with Nano Banana Pro style.

Usage:
    python generate_image.py "your description" [output.png] [--aspect 16:9]

Configuration:
    First run: python generate_image.py --setup --api-key "YOUR_KEY"
    Check:     python generate_image.py --check
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

# Config file location: ~/.config/nano-banana-image/config.json
CONFIG_DIR = Path.home() / ".config" / "nano-banana-image"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Gemini model for image generation
DEFAULT_MODEL = "gemini-3-pro-image-preview"

# Aspect ratio dimensions
ASPECT_RATIOS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 896),
    "3:4": (896, 1152),
}

# Nano Banana Pro style prompt template
NANO_BANANA_STYLE = """
Style guidelines for the image:
- Color palette: Deep navy background (#1C2833), golden yellow accents (#F4C430), teal highlights (#00D9C0)
- Visual style: Modern, minimalist, tech-forward, premium feel
- Mood: Professional yet energetic, innovative, clean
- Elements: Geometric shapes (circles, diamonds), subtle gradients, high contrast
- Aesthetic: Dark mode UI style, sleek product visualization, futuristic
"""

# =============================================================================
# Configuration Management
# =============================================================================


def load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    # Secure permissions (owner read/write only)
    try:
        CONFIG_FILE.chmod(0o600)
    except OSError:
        pass  # Windows doesn't support chmod the same way


def setup_config(api_key: str, project_id: str = None) -> None:
    """Setup API key and optional project ID."""
    config = load_config()
    config["gemini_api_key"] = api_key
    if project_id:
        config["project_id"] = project_id
    save_config(config)
    print(f"OK: Configuration saved to {CONFIG_FILE}")


def check_config() -> bool:
    """Check if configuration exists and is valid."""
    config = load_config()
    api_key = config.get("gemini_api_key", "")

    if not api_key:
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
        print("Optional: If using a specific GCP project, also provide the Project ID.")
        print("")
        print("Once you have the key, tell me:")
        print('  "My Gemini API key is: AIza..."')
        print("")
        print("=" * 60)
        return False

    # Validate key format (basic check)
    if not api_key.startswith("AIza") or len(api_key) < 30:
        print("STATUS: INVALID_KEY")
        print(f"The stored API key appears invalid: {api_key[:10]}...")
        print("Please provide a valid Gemini API key.")
        return False

    print("STATUS: CONFIGURED")
    print(f"Config file: {CONFIG_FILE}")
    print(f"API key: {api_key[:10]}...{api_key[-4:]}")
    project_id = config.get("project_id")
    if project_id:
        print(f"Project ID: {project_id}")
    return True


def get_api_key() -> str:
    """Get API key from config file, with fallback to environment variable."""
    # First try config file
    config = load_config()
    api_key = config.get("gemini_api_key")

    # Fallback to environment variable for backward compatibility
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        print("ERROR: Gemini API key not configured")
        print("")
        print("Run: python generate_image.py --check")
        print("to see setup instructions.")
        sys.exit(1)

    return api_key


# =============================================================================
# Image Generation
# =============================================================================


def generate_image(prompt: str, output_path: str, aspect_ratio: str = "16:9", model: str = DEFAULT_MODEL) -> str:
    """Generate an image using Gemini API with Nano Banana Pro style."""

    api_key = get_api_key()

    # Get dimensions for aspect ratio
    width, height = ASPECT_RATIOS.get(aspect_ratio, ASPECT_RATIOS["16:9"])

    # Combine user prompt with Nano Banana style and aspect ratio hint
    styled_prompt = f"{prompt}\n\n{NANO_BANANA_STYLE}\n\nImage dimensions: {width}x{height} pixels ({aspect_ratio} aspect ratio)"

    # API endpoint
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    # Request payload
    payload = {
        "contents": [{
            "parts": [{"text": styled_prompt}]
        }],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"]
        }
    }

    # Make request
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

        # Extract image from response
        if "candidates" in result and result["candidates"]:
            parts = result["candidates"][0].get("content", {}).get("parts", [])

            for part in parts:
                if "inlineData" in part:
                    image_data = part["inlineData"]["data"]
                    mime_type = part["inlineData"].get("mimeType", "image/png")

                    # Decode and save image
                    image_bytes = base64.b64decode(image_data)

                    # Determine extension from mime type
                    ext = ".png"
                    if "jpeg" in mime_type or "jpg" in mime_type:
                        ext = ".jpg"
                    elif "webp" in mime_type:
                        ext = ".webp"

                    # Add extension if not present
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
Examples:
  # First time setup (run by Claude after user provides key)
  %(prog)s --setup --api-key "AIzaSy..."

  # Check configuration status
  %(prog)s --check

  # Generate images
  %(prog)s "a futuristic productivity device" product.png
  %(prog)s "abstract geometric pattern" bg.png --aspect 16:9
  %(prog)s "minimalist sync icon" icon.png --aspect 1:1

Configuration:
  API key is stored in: ~/.config/nano-banana-image/config.json
"""
    )

    # Setup/check commands
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Setup mode: save API key to config file"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if API key is configured"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (used with --setup)"
    )
    parser.add_argument(
        "--project-id",
        help="Optional GCP Project ID (used with --setup)"
    )

    # Generation arguments
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Description of the image to generate"
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="output.png",
        help="Output file path (default: output.png)"
    )
    parser.add_argument(
        "--aspect",
        default="16:9",
        choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
        help="Aspect ratio (default: 16:9)"
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Gemini model to use (default: {DEFAULT_MODEL})"
    )

    args = parser.parse_args()

    # Handle setup command
    if args.setup:
        if not args.api_key:
            print("ERROR: --api-key is required with --setup")
            print("Usage: python generate_image.py --setup --api-key 'AIzaSy...'")
            sys.exit(1)
        setup_config(args.api_key, args.project_id)
        return

    # Handle check command
    if args.check:
        sys.exit(0 if check_config() else 1)

    # Generate image requires prompt
    if not args.prompt:
        # No prompt provided, check config and show help
        if not check_config():
            sys.exit(1)
        parser.print_help()
        sys.exit(0)

    generate_image(args.prompt, args.output, args.aspect, args.model)


if __name__ == "__main__":
    main()
