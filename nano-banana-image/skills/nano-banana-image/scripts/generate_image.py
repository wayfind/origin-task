#!/usr/bin/env python3
"""
Nano Banana Pro Image Generator
Generates images using Gemini API with Nano Banana Pro style.

Usage:
    python generate_image.py "your description" [output.png] [--aspect 16:9]

Environment:
    GEMINI_API_KEY - Required. Get from https://aistudio.google.com/apikey
"""

import argparse
import base64
import json
import os
import sys
import urllib.request
import urllib.error

# =============================================================================
# Constants
# =============================================================================

# Gemini model for image generation
# gemini-3-pro-image-preview is a new model with native image generation
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
# Core Functions
# =============================================================================


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY environment variable not set")
        print("")
        print("To fix:")
        print("  1. Get your API key from: https://aistudio.google.com/apikey")
        print("  2. Set the environment variable:")
        print('     export GEMINI_API_KEY="your-api-key-here"')
        sys.exit(1)
    return api_key


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
        print(f"Details: {error_body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"ERROR: Connection failed - {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {type(e).__name__} - {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate Nano Banana Pro styled images using Gemini API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "a futuristic productivity device" product.png
  %(prog)s "abstract geometric pattern" bg.png --aspect 16:9
  %(prog)s "minimalist sync icon" icon.png --aspect 1:1

Environment:
  GEMINI_API_KEY    Required. Get from https://aistudio.google.com/apikey
"""
    )
    parser.add_argument(
        "prompt",
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
    generate_image(args.prompt, args.output, args.aspect, args.model)


if __name__ == "__main__":
    main()
