---
name: nano-banana-image
description: |
  Generate images in Nano Banana Pro visual style using Gemini API.
  Use when: (1) User wants to create images/illustrations for Nano Banana Pro presentations, (2) User needs product mockups, icons, or visual assets in the Nano Banana color scheme, (3) User asks for AI-generated images with dark mode tech aesthetic.
  Triggers: "生成图片", "generate image", "Nano Banana 图片", "配图", "illustration", "visual asset"
---

# Nano Banana Image Generator

Generate AI images styled with the Nano Banana Pro visual identity using Google Gemini API.

## Prerequisites

**IMPORTANT: Set your Gemini API key before using this skill.**

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Get your API key from: https://aistudio.google.com/apikey

## Quick Start

```bash
python scripts/generate_image.py "a futuristic productivity device" output.png
```

## Usage

```bash
python scripts/generate_image.py "<description>" [output_path] [--aspect RATIO] [--model MODEL]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `description` | What to generate (required) | - |
| `output_path` | Output file path | `output.png` |
| `--aspect` | Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4 | `16:9` |
| `--model` | Gemini model to use | `gemini-3-pro-image-preview` |

## Style Applied

All generated images automatically include Nano Banana Pro styling:

- **Colors**: Deep navy (#1C2833), golden yellow (#F4C430), teal (#00D9C0)
- **Mood**: Professional, tech-forward, premium, innovative
- **Aesthetic**: Dark mode, geometric shapes, high contrast, minimalist

## Examples

**Product Visualization**
```bash
python scripts/generate_image.py "a compact smart device with glowing edges" product.png
```

**Abstract Background**
```bash
python scripts/generate_image.py "abstract geometric pattern with circles and lines" bg.png --aspect 16:9
```

**Icon/Logo**
```bash
python scripts/generate_image.py "minimalist sync icon with two rotating arrows" icon.png --aspect 1:1
```

**Presentation Hero Image**
```bash
python scripts/generate_image.py "professional holding a tiny glowing device, dark environment" hero.png
```

## Prompt Tips

For best results, describe:
1. **Subject**: What is the main focus
2. **Context**: Environment or setting
3. **Mood**: Energy level, feeling
4. **Details**: Specific elements to include

The Nano Banana style (colors, aesthetic) is automatically added.

**Good prompts:**
- "a sleek handheld device floating above a hand, soft glow"
- "abstract data visualization with flowing particles"
- "modern office desk with minimal tech accessories"

**Avoid:**
- Overly detailed color specifications (style is auto-applied)
- Conflicting aesthetic directions (e.g., "vintage rustic style")

## Output

- Format: PNG (or JPG/WebP based on API response)
- Resolution: Determined by Gemini model
- Watermark: SynthID embedded (invisible, for authenticity)

## Troubleshooting

| Error | Solution |
|-------|----------|
| `GEMINI_API_KEY not set` | Run `export GEMINI_API_KEY="your-key"` |
| `HTTP 403` | Check API key validity at aistudio.google.com |
| `HTTP 429` | Rate limited, wait and retry |
| `No image generated` | Rephrase prompt, avoid restricted content |
