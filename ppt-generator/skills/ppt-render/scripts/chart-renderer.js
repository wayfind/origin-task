/**
 * Chart Renderer - Mermaid 图表渲染器
 *
 * 将 Mermaid 代码和预定义模板转换为 PNG 图片
 *
 * 依赖：npm install -g @mermaid-js/mermaid-cli
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');

// 预定义的图表模板
const CHART_TEMPLATES = {
    /**
     * 流程图模板
     * @param {Object} data - { title, steps: [{label, detail}] }
     */
    'process-flow': (data) => {
        const steps = data.steps || [];
        const nodes = steps.map((s, i) => {
            const nodeId = String.fromCharCode(65 + i); // A, B, C...
            const label = s.detail ? `${s.label}<br/><small>${s.detail}</small>` : s.label;
            return `    ${nodeId}["${label}"]`;
        }).join('\n');

        const links = steps.slice(0, -1).map((_, i) => {
            const from = String.fromCharCode(65 + i);
            const to = String.fromCharCode(66 + i);
            return `    ${from} --> ${to}`;
        }).join('\n');

        return `flowchart LR
${nodes}
${links}`;
    },

    /**
     * 对比图模板
     * @param {Object} data - { left: {title, items}, right: {title, items} }
     */
    'comparison': (data) => {
        const left = data.left || { title: 'Left', items: [] };
        const right = data.right || { title: 'Right', items: [] };

        const leftItems = left.items.map((item, i) =>
            `    L${i}["${item}"]`
        ).join('\n');

        const rightItems = right.items.map((item, i) =>
            `    R${i}["${item}"]`
        ).join('\n');

        return `flowchart TB
    subgraph "${left.title}"
${leftItems}
    end
    subgraph "${right.title}"
${rightItems}
    end`;
    },

    /**
     * 时间线模板
     * @param {Object} data - { events: [{year, title}] }
     */
    'timeline': (data) => {
        const events = data.events || [];
        const nodes = events.map((e, i) => {
            const nodeId = `E${i}`;
            return `    ${nodeId}["<b>${e.year}</b><br/>${e.title}"]`;
        }).join('\n');

        const links = events.slice(0, -1).map((_, i) => {
            return `    E${i} --> E${i + 1}`;
        }).join('\n');

        return `flowchart LR
${nodes}
${links}`;
    },

    /**
     * 金字塔模板
     * @param {Object} data - { levels: [{label}] } - 从顶部到底部
     */
    'pyramid': (data) => {
        const levels = data.levels || [];
        const nodes = levels.map((l, i) => {
            const nodeId = `L${i}`;
            const width = (i + 1) * 2;  // 越往下越宽
            return `    ${nodeId}["${l.label}"]`;
        }).join('\n');

        const links = levels.slice(0, -1).map((_, i) => {
            return `    L${i} --> L${i + 1}`;
        }).join('\n');

        return `flowchart TB
${nodes}
${links}`;
    },

    /**
     * 圆形分组
     * @param {Object} data - { center, items: [string] }
     */
    'circle-group': (data) => {
        const center = data.center || 'Center';
        const items = data.items || [];

        const itemNodes = items.map((item, i) => {
            return `    I${i}(("${item}"))`;
        }).join('\n');

        const links = items.map((_, i) => {
            return `    C --- I${i}`;
        }).join('\n');

        return `flowchart TB
    C(("${center}"))
${itemNodes}
${links}`;
    }
};

// Mermaid 主题配置
const MERMAID_THEMES = {
    'dark': {
        theme: 'dark',
        themeVariables: {
            primaryColor: '#1C2833',
            primaryTextColor: '#F4C430',
            primaryBorderColor: '#00D9C0',
            lineColor: '#00D9C0',
            secondaryColor: '#2C3E50',
            tertiaryColor: '#34495E',
            fontFamily: 'system-ui, sans-serif'
        }
    },
    'light': {
        theme: 'default',
        themeVariables: {
            primaryColor: '#3498DB',
            primaryTextColor: '#2C3E50',
            primaryBorderColor: '#2980B9',
            lineColor: '#2980B9',
            fontFamily: 'system-ui, sans-serif'
        }
    },
    'nano-banana': {
        theme: 'dark',
        themeVariables: {
            primaryColor: '#1C2833',
            primaryTextColor: '#F4C430',
            primaryBorderColor: '#F4C430',
            lineColor: '#00D9C0',
            secondaryColor: '#2C3E50',
            tertiaryColor: '#00D9C0',
            edgeLabelBackground: '#1C2833',
            fontFamily: 'system-ui, sans-serif'
        }
    }
};

class ChartRenderer {
    constructor(options = {}) {
        this.options = {
            outputDir: './charts',
            theme: 'dark',
            width: 1200,
            height: 800,
            backgroundColor: 'transparent',
            verbose: false,
            ...options
        };

        // 确保输出目录存在
        if (!fs.existsSync(this.options.outputDir)) {
            fs.mkdirSync(this.options.outputDir, { recursive: true });
        }
    }

    /**
     * 检查 mermaid-cli 是否可用
     */
    checkMermaidCli() {
        try {
            const result = spawnSync('mmdc', ['--version'], {
                encoding: 'utf8',
                shell: true
            });
            if (result.status === 0) {
                if (this.options.verbose) {
                    console.log(`[ChartRenderer] mermaid-cli version: ${result.stdout.trim()}`);
                }
                return true;
            }
        } catch (e) {
            // ignore
        }

        console.warn('[ChartRenderer] mermaid-cli not found');
        console.warn('  Install with: npm install -g @mermaid-js/mermaid-cli');
        return false;
    }

    /**
     * 渲染 Mermaid 代码为 PNG
     * @param {string} mermaidCode - Mermaid 代码
     * @param {string} outputName - 输出文件名（不含扩展名）
     * @returns {string|null} - 输出文件路径
     */
    async renderMermaid(mermaidCode, outputName) {
        if (!this.checkMermaidCli()) {
            return null;
        }

        const outputPath = path.join(this.options.outputDir, `${outputName}.png`);
        const inputPath = path.join(this.options.outputDir, `${outputName}.mmd`);
        const configPath = path.join(this.options.outputDir, `${outputName}.config.json`);

        try {
            // 写入 Mermaid 代码
            fs.writeFileSync(inputPath, mermaidCode, 'utf8');

            // 写入配置
            const themeConfig = MERMAID_THEMES[this.options.theme] || MERMAID_THEMES['dark'];
            fs.writeFileSync(configPath, JSON.stringify(themeConfig, null, 2), 'utf8');

            // 执行 mmdc
            const cmd = [
                'mmdc',
                '-i', inputPath,
                '-o', outputPath,
                '-c', configPath,
                '-w', String(this.options.width),
                '-H', String(this.options.height),
                '-b', this.options.backgroundColor
            ].join(' ');

            if (this.options.verbose) {
                console.log(`[ChartRenderer] Running: ${cmd}`);
            }

            execSync(cmd, {
                encoding: 'utf8',
                shell: true,
                timeout: 30000  // 30秒超时
            });

            // 清理临时文件
            if (fs.existsSync(inputPath)) fs.unlinkSync(inputPath);
            if (fs.existsSync(configPath)) fs.unlinkSync(configPath);

            if (fs.existsSync(outputPath)) {
                if (this.options.verbose) {
                    console.log(`[ChartRenderer] Generated: ${outputPath}`);
                }
                return outputPath;
            }

            return null;

        } catch (e) {
            console.error(`[ChartRenderer] Error: ${e.message}`);
            return null;
        }
    }

    /**
     * 从模板生成图表
     * @param {string} templateName - 模板名称
     * @param {Object} data - 模板数据
     * @param {string} outputName - 输出文件名
     * @returns {string|null}
     */
    async renderTemplate(templateName, data, outputName) {
        const template = CHART_TEMPLATES[templateName];
        if (!template) {
            console.error(`[ChartRenderer] Unknown template: ${templateName}`);
            console.error(`  Available: ${Object.keys(CHART_TEMPLATES).join(', ')}`);
            return null;
        }

        const mermaidCode = template(data);

        if (this.options.verbose) {
            console.log(`[ChartRenderer] Template: ${templateName}`);
            console.log(`[ChartRenderer] Generated Mermaid:\n${mermaidCode}`);
        }

        return this.renderMermaid(mermaidCode, outputName);
    }

    /**
     * 解析 slide-md 中的图表块
     * @param {string} blockContent - ::: chart 块的内容
     * @returns {Object|null} - {template, title, data}
     */
    parseChartBlock(blockContent) {
        const lines = blockContent.split('\n');
        const result = {
            template: null,
            title: '',
            data: {}
        };

        let currentKey = null;
        let currentList = [];

        for (const line of lines) {
            const trimmed = line.trim();

            // template: xxx
            const templateMatch = trimmed.match(/^template:\s*(.+)/);
            if (templateMatch) {
                result.template = templateMatch[1].trim();
                continue;
            }

            // title: xxx
            const titleMatch = trimmed.match(/^title:\s*(.+)/);
            if (titleMatch) {
                result.title = titleMatch[1].trim();
                continue;
            }

            // key: (开始一个列表)
            const keyMatch = trimmed.match(/^(\w+):$/);
            if (keyMatch) {
                if (currentKey && currentList.length > 0) {
                    result.data[currentKey] = currentList;
                }
                currentKey = keyMatch[1];
                currentList = [];
                continue;
            }

            // - label: xxx / - xxx
            if (trimmed.startsWith('- ')) {
                const item = trimmed.substring(2).trim();

                // 检查是否是对象格式 - label: xxx
                const labelMatch = item.match(/^label:\s*(.+)/);
                if (labelMatch) {
                    currentList.push({ label: labelMatch[1] });
                } else {
                    // 检查是否有 detail
                    const detailMatch = item.match(/^(.+?)\s*\|\s*(.+)$/);
                    if (detailMatch) {
                        currentList.push({
                            label: detailMatch[1].trim(),
                            detail: detailMatch[2].trim()
                        });
                    } else {
                        currentList.push({ label: item });
                    }
                }
                continue;
            }

            // detail: xxx (附加到最后一个 item)
            const detailMatch = trimmed.match(/^detail:\s*(.+)/);
            if (detailMatch && currentList.length > 0) {
                currentList[currentList.length - 1].detail = detailMatch[1];
            }
        }

        // 保存最后的列表
        if (currentKey && currentList.length > 0) {
            result.data[currentKey] = currentList;
        }

        return result;
    }

    /**
     * 获取可用的模板列表
     */
    static getTemplates() {
        return Object.keys(CHART_TEMPLATES);
    }

    /**
     * 获取可用的主题列表
     */
    static getThemes() {
        return Object.keys(MERMAID_THEMES);
    }
}

module.exports = { ChartRenderer, CHART_TEMPLATES, MERMAID_THEMES };

// CLI 测试
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length === 0 || args.includes('--help')) {
        console.log(`
Chart Renderer - Mermaid 图表渲染器

Usage:
  node chart-renderer.js --check                # 检查 mermaid-cli
  node chart-renderer.js --templates            # 列出可用模板
  node chart-renderer.js <mermaid.mmd> <output> # 渲染 Mermaid 文件
  node chart-renderer.js --demo                 # 生成演示图表

Options:
  --theme <name>    主题 (dark, light, nano-banana)
  -o <dir>          输出目录
  -v                详细输出
        `);
        process.exit(0);
    }

    const verbose = args.includes('-v');
    const themeIndex = args.indexOf('--theme');
    const theme = themeIndex >= 0 ? args[themeIndex + 1] : 'nano-banana';
    const outputIndex = args.indexOf('-o');
    const outputDir = outputIndex >= 0 ? args[outputIndex + 1] : './charts';

    const renderer = new ChartRenderer({
        theme,
        outputDir,
        verbose
    });

    if (args.includes('--check')) {
        const ok = renderer.checkMermaidCli();
        console.log(ok ? '✓ mermaid-cli is available' : '✗ mermaid-cli not found');
        process.exit(ok ? 0 : 1);
    }

    if (args.includes('--templates')) {
        console.log('Available templates:');
        ChartRenderer.getTemplates().forEach(t => console.log(`  - ${t}`));
        console.log('\nAvailable themes:');
        ChartRenderer.getThemes().forEach(t => console.log(`  - ${t}`));
        process.exit(0);
    }

    if (args.includes('--demo')) {
        console.log('Generating demo charts...\n');

        // 流程图
        renderer.renderTemplate('process-flow', {
            title: 'AI Implementation Phases',
            steps: [
                { label: 'Quick Wins', detail: '0-6 months' },
                { label: 'Scale Up', detail: '6-18 months' },
                { label: 'Transform', detail: '18+ months' }
            ]
        }, 'demo-process').then(p => console.log(`  Process: ${p}`));

        // 时间线
        renderer.renderTemplate('timeline', {
            events: [
                { year: '2020', title: 'AI Foundation' },
                { year: '2022', title: 'GenAI Boom' },
                { year: '2024', title: 'Enterprise Adoption' },
                { year: '2026', title: 'AI-First Era' }
            ]
        }, 'demo-timeline').then(p => console.log(`  Timeline: ${p}`));

        // 对比图
        renderer.renderTemplate('comparison', {
            left: {
                title: 'Traditional',
                items: ['Manual Process', 'High Cost', 'Slow']
            },
            right: {
                title: 'AI-Powered',
                items: ['Automated', 'Cost Efficient', 'Fast']
            }
        }, 'demo-comparison').then(p => console.log(`  Comparison: ${p}`));
    }

    // 渲染 Mermaid 文件
    const mmdFile = args.find(a => a.endsWith('.mmd'));
    if (mmdFile && fs.existsSync(mmdFile)) {
        const code = fs.readFileSync(mmdFile, 'utf8');
        const output = args[args.indexOf(mmdFile) + 1] || path.basename(mmdFile, '.mmd');
        renderer.renderMermaid(code, output).then(p => {
            if (p) console.log(`✓ Generated: ${p}`);
        });
    }
}
