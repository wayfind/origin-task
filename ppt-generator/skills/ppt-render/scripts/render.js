#!/usr/bin/env node
/**
 * PPT Render - 主入口脚本
 * 从 slide-md 文件渲染生成 PPTX
 *
 * 用法:
 *   node render.js <input> [options]
 *   node render.js ./slides/ -o presentation.pptx
 *   node render.js ./slides/ --theme nano-banana-pro
 */

const fs = require('fs');
const path = require('path');
const { SlideParser } = require('./slide-parser');
const { PPTXRenderer } = require('./pptx-renderer');
const { loadTheme, listThemes } = require('./theme-loader');

class PPTRender {
    constructor(options = {}) {
        this.options = {
            theme: 'corporate-light',
            output: 'output.pptx',
            verbose: false,
            validate: false,
            title: 'Presentation',
            author: 'Claude Code',
            ...options
        };

        this.parser = new SlideParser({ strictMode: false });
        this.theme = loadTheme(this.options.theme);
        this.renderer = new PPTXRenderer(this.theme);
    }

    /**
     * 渲染目录下的所有 slide-md 文件
     * @param {string} inputDir - 输入目录
     * @param {string} outputPath - 输出 PPTX 路径
     */
    async renderDirectory(inputDir, outputPath) {
        this.log(`Input: ${inputDir}`);
        this.log(`Theme: ${this.options.theme}`);

        // 解析所有 slides
        const slides = this.parser.parseDirectory(inputDir);
        this.log(`Parsed: ${slides.length} slides`);

        if (slides.length === 0) {
            console.error('No valid slides found.');
            return null;
        }

        // 仅验证模式
        if (this.options.validate) {
            this.log('Validation complete.');
            return { validated: true, slideCount: slides.length };
        }

        // 渲染
        this.renderer.render(slides, {
            title: this.options.title,
            author: this.options.author
        });

        // 保存
        const finalPath = outputPath || this.options.output;
        await this.renderer.save(finalPath);
        this.log(`Output: ${finalPath}`);

        return { output: finalPath, slideCount: slides.length };
    }

    /**
     * 渲染单个 slide-md 文件
     * @param {string} inputFile - 输入文件
     * @param {string} outputPath - 输出 PPTX 路径
     */
    async renderFile(inputFile, outputPath) {
        this.log(`Input: ${inputFile}`);
        this.log(`Theme: ${this.options.theme}`);

        // 解析 slide
        const slide = this.parser.parseFile(inputFile);
        if (!slide) {
            console.error('Failed to parse slide.');
            return null;
        }

        // 仅验证模式
        if (this.options.validate) {
            this.log('Validation complete.');
            return { validated: true, slideCount: 1 };
        }

        // 渲染
        this.renderer.render([slide], {
            title: slide.content.title || this.options.title,
            author: this.options.author
        });

        // 保存
        const finalPath = outputPath || this.options.output;
        await this.renderer.save(finalPath);
        this.log(`Output: ${finalPath}`);

        return { output: finalPath, slideCount: 1 };
    }

    log(message) {
        if (this.options.verbose) {
            console.log(`[ppt-render] ${message}`);
        }
    }
}

// CLI
function parseArgs(args) {
    const options = {
        input: null,
        output: 'output.pptx',
        theme: 'corporate-light',
        verbose: false,
        validate: false,
        help: false,
        listThemes: false
    };

    for (let i = 0; i < args.length; i++) {
        const arg = args[i];

        if (arg === '-h' || arg === '--help') {
            options.help = true;
        } else if (arg === '-v' || arg === '--verbose') {
            options.verbose = true;
        } else if (arg === '--validate') {
            options.validate = true;
        } else if (arg === '--list-themes') {
            options.listThemes = true;
        } else if (arg === '-o' || arg === '--output') {
            options.output = args[++i];
        } else if (arg === '-t' || arg === '--theme') {
            options.theme = args[++i];
        } else if (!arg.startsWith('-')) {
            options.input = arg;
        }
    }

    return options;
}

function printHelp() {
    console.log(`
PPT Render - Generate PPTX from Slide Markdown files

Usage:
  node render.js <input> [options]

Arguments:
  <input>                  Input .slide.md file or directory

Options:
  -o, --output <path>      Output PPTX file path (default: output.pptx)
  -t, --theme <name>       Theme name (default: corporate-light)
  -v, --verbose            Verbose output
  --validate               Validate only, don't generate
  --list-themes            List available themes
  -h, --help               Show this help message

Examples:
  node render.js ./slides/ -o presentation.pptx
  node render.js ./slides/ --theme nano-banana-pro -o dark-theme.pptx
  node render.js intro.slide.md -o intro.pptx
  node render.js --list-themes
`);
}

async function main() {
    const args = process.argv.slice(2);
    const options = parseArgs(args);

    if (options.help) {
        printHelp();
        process.exit(0);
    }

    if (options.listThemes) {
        console.log('Available themes:');
        listThemes().forEach(t => console.log(`  - ${t}`));
        process.exit(0);
    }

    if (!options.input) {
        console.error('Error: Input file or directory required.');
        console.log('Use --help for usage information.');
        process.exit(1);
    }

    const render = new PPTRender(options);

    try {
        const stat = fs.statSync(options.input);
        let result;

        if (stat.isDirectory()) {
            result = await render.renderDirectory(options.input, options.output);
        } else {
            result = await render.renderFile(options.input, options.output);
        }

        if (result) {
            if (result.validated) {
                console.log(`✓ Validated ${result.slideCount} slides`);
            } else {
                console.log(`✓ Generated ${result.slideCount} slides → ${result.output}`);
            }
        }
    } catch (e) {
        console.error(`Error: ${e.message}`);
        if (options.verbose) {
            console.error(e.stack);
        }
        process.exit(1);
    }
}

// 导出供编程使用
module.exports = { PPTRender };

// CLI 入口
if (require.main === module) {
    main();
}
