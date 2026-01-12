---
name: nano-banana-image
description: |
  Generate images in Nano Banana Pro visual style using Gemini API.
  Use when: (1) User wants to create images/illustrations for Nano Banana Pro presentations, (2) User needs product mockups, icons, or visual assets in the Nano Banana color scheme, (3) User asks for AI-generated images with dark mode tech aesthetic.
  Triggers: "生成图片", "generate image", "Nano Banana 图片", "配图", "illustration", "visual asset"
---

# Nano Banana Image Generator

Generate AI images styled with the Nano Banana Pro visual identity using Google Gemini API.

## API Key Management

Supports multiple API keys with named profiles.

### List Keys

```bash
python scripts/generate_image.py keys list
```

### Add a Key

```bash
python scripts/generate_image.py keys add <name> <api-key>

# Examples:
python scripts/generate_image.py keys add default AIzaSy...
python scripts/generate_image.py keys add work AIzaSy...
python scripts/generate_image.py keys add personal AIzaSy...
```

### Remove a Key

```bash
python scripts/generate_image.py keys remove <name>
```

### Switch Active Key

```bash
python scripts/generate_image.py keys use <name>
```

### First-Time Setup

On first use, if no keys configured:

```bash
python scripts/generate_image.py --check
```

Shows setup instructions. Once user provides key:

```bash
python scripts/generate_image.py keys add default "AIzaSy..."
```

## Image Generation

### Quick Start

```bash
python scripts/generate_image.py "a futuristic productivity device" output.png
```

### Full Usage

```bash
python scripts/generate_image.py "<description>" [output_path] [options]
```

| Argument | Description | Default |
|----------|-------------|---------|
| `description` | What to generate (required) | - |
| `output_path` | Output file path | `output.png` |
| `--aspect` | Aspect ratio: 1:1, 16:9, 9:16, 4:3, 3:4 | `16:9` |
| `--model` | Gemini model to use | `gemini-3-pro-image-preview` |
| `--key` | Use specific key by name | active key |

### Use Specific Key for Generation

```bash
python scripts/generate_image.py "prompt" output.png --key work
```

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

**Using Different Keys**
```bash
# Use work key for this generation
python scripts/generate_image.py "presentation hero image" hero.png --key work
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
| `No API keys configured` | Run `keys add <name> <key>` |
| `Key 'xxx' not found` | Run `keys list` to see available keys |
| `HTTP 403` | Key invalid or lacks permissions |
| `HTTP 429` | Rate limited, wait and retry |
| `No image generated` | Rephrase prompt, avoid restricted content |

## Security

- Keys stored in `~/.config/nano-banana-image/config.json`
- File permissions set to 600 (owner read/write only)
- Keys never logged or displayed in full (masked as `AIza...xxxx`)
- Fallback to `GEMINI_API_KEY` environment variable supported

## Command Reference

| Command | Description |
|---------|-------------|
| `keys list` | List all configured API keys |
| `keys add <name> <key>` | Add a new API key |
| `keys remove <name>` | Remove an API key |
| `keys use <name>` | Set active API key |
| `--check` | Check configuration status |
| `--key <name>` | Use specific key for generation |
