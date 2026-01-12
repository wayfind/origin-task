/**
 * Slide Markdown Parser
 * 将 .slide.md 文件解析为结构化数据
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

/**
 * 解析后的幻灯片结构
 * @typedef {Object} ParsedSlide
 * @property {Object} meta - frontmatter 元数据
 * @property {string} meta.id - 幻灯片 ID
 * @property {string} meta.type - 类型 (cover|section|content|case-study|quote|closing)
 * @property {string} meta.layout - 布局
 * @property {Object[]} [meta.sources] - 来源
 * @property {Object[]} [meta.cases] - 案例数据
 * @property {Object} content - 解析后的内容
 * @property {string} content.title - 主标题
 * @property {string} [content.subtitle] - 副标题
 * @property {Object[]} content.elements - 内容元素
 * @property {string} [notes] - 演讲者备注
 * @property {string} rawContent - 原始 Markdown 内容
 */

class SlideParser {
    constructor(options = {}) {
        this.options = {
            strictMode: false,  // 严格模式下遇到错误抛出异常
            ...options
        };
    }

    /**
     * 解析单个 slide.md 文件
     * @param {string} filePath - 文件路径
     * @returns {ParsedSlide|null}
     */
    parseFile(filePath) {
        if (!fs.existsSync(filePath)) {
            return this.handleError(`File not found: ${filePath}`);
        }

        const content = fs.readFileSync(filePath, 'utf8');
        return this.parseContent(content, filePath);
    }

    /**
     * 解析 slide.md 内容
     * @param {string} content - 文件内容
     * @param {string} [source] - 来源标识（用于错误信息）
     * @returns {ParsedSlide|null}
     */
    parseContent(content, source = 'unknown') {
        // 1. 分离 frontmatter、正文、备注
        const parts = this.splitParts(content);
        if (!parts) {
            return this.handleError(`Invalid slide format: ${source}`);
        }

        // 2. 解析 frontmatter
        let meta;
        try {
            meta = yaml.parse(parts.frontmatter);
        } catch (e) {
            return this.handleError(`YAML parse error in ${source}: ${e.message}`);
        }

        // 3. 验证必填字段
        if (!meta?.slide?.id || !meta?.slide?.type) {
            return this.handleError(`Missing required fields (slide.id, slide.type) in ${source}`);
        }

        // 4. 解析正文内容
        const parsedContent = this.parseBody(parts.body, meta.slide.layout);

        // 5. 构建结果
        return {
            meta: {
                id: meta.slide.id,
                type: meta.slide.type,
                layout: meta.slide.layout || this.inferLayout(meta.slide.type),
                sourceSection: meta.slide.source_section,
                duration: meta.slide.duration,
                animation: meta.slide.animation,
                sources: meta.sources || [],
                cases: meta.cases || [],
                style: meta.style || {}
            },
            content: parsedContent,
            notes: parts.notes || '',
            rawContent: parts.body,
            source
        };
    }

    /**
     * 解析目录下所有 slide.md 文件
     * @param {string} dirPath - 目录路径
     * @returns {ParsedSlide[]}
     */
    parseDirectory(dirPath) {
        if (!fs.existsSync(dirPath)) {
            return this.handleError(`Directory not found: ${dirPath}`) || [];
        }

        const files = fs.readdirSync(dirPath)
            .filter(f => f.endsWith('.slide.md'))
            .sort()
            .map(f => path.join(dirPath, f));

        const slides = [];
        for (const file of files) {
            const parsed = this.parseFile(file);
            if (parsed) {
                slides.push(parsed);
            }
        }

        return slides;
    }

    // ==================== 内部方法 ====================

    /**
     * 分离文件的三个部分
     */
    splitParts(content) {
        // 匹配 frontmatter
        const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
        if (!fmMatch) {
            return null;
        }

        const frontmatter = fmMatch[1];
        const rest = fmMatch[2];

        // 分离备注
        const notesSplit = rest.split(/\n---notes---\n/);
        const body = notesSplit[0].trim();
        const notes = notesSplit[1] ? notesSplit[1].trim() : '';

        return { frontmatter, body, notes };
    }

    /**
     * 解析正文内容
     */
    parseBody(body, layout) {
        const result = {
            title: '',
            subtitle: '',
            elements: []
        };

        const lines = body.split('\n');
        let currentBlock = null;
        let blockContent = [];
        let inCodeBlock = false;
        let codeBlockLang = null;
        let codeBlockContent = [];

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];

            // 代码块开始 ```mermaid 或 ```其他
            const codeBlockStart = line.match(/^```(\w+)?/);
            if (codeBlockStart && !inCodeBlock) {
                inCodeBlock = true;
                codeBlockLang = codeBlockStart[1] || 'text';
                codeBlockContent = [];
                continue;
            }

            // 代码块结束 ```
            if (line === '```' && inCodeBlock) {
                // 处理 Mermaid 代码块
                if (codeBlockLang === 'mermaid') {
                    result.elements.push({
                        type: 'mermaid',
                        code: codeBlockContent.join('\n'),
                        lang: 'mermaid'
                    });
                } else {
                    // 普通代码块
                    result.elements.push({
                        type: 'codeblock',
                        code: codeBlockContent.join('\n'),
                        lang: codeBlockLang
                    });
                }
                inCodeBlock = false;
                codeBlockLang = null;
                codeBlockContent = [];
                continue;
            }

            // 在代码块内
            if (inCodeBlock) {
                codeBlockContent.push(line);
                continue;
            }

            // 主标题
            if (line.startsWith('# ')) {
                result.title = line.substring(2).trim();
                continue;
            }

            // 副标题
            if (line.startsWith('## ')) {
                result.subtitle = line.substring(3).trim();
                continue;
            }

            // 块开始 ::: type
            const blockStart = line.match(/^:::\s*(\w+)/);
            if (blockStart) {
                if (currentBlock) {
                    result.elements.push(this.finalizeBlock(currentBlock, blockContent));
                }
                currentBlock = blockStart[1];
                blockContent = [];
                continue;
            }

            // 块结束 :::
            if (line === ':::') {
                if (currentBlock) {
                    result.elements.push(this.finalizeBlock(currentBlock, blockContent));
                    currentBlock = null;
                    blockContent = [];
                }
                continue;
            }

            // 在块内
            if (currentBlock) {
                blockContent.push(line);
                continue;
            }

            // 列表项
            if (line.match(/^[-*]\s+/)) {
                const item = this.parseListItem(line);
                result.elements.push({
                    type: 'bullet',
                    ...item
                });
                continue;
            }

            // 表格行
            if (line.includes('|')) {
                const tableResult = this.parseTable(lines, i);
                if (tableResult.table) {
                    result.elements.push({
                        type: 'table',
                        headers: tableResult.table.headers,
                        rows: tableResult.table.rows
                    });
                    i = tableResult.endIndex;
                }
                continue;
            }

            // 引用
            if (line.startsWith('> ')) {
                const quoteResult = this.parseQuote(lines, i);
                result.elements.push({
                    type: 'quote',
                    text: quoteResult.text,
                    attribution: quoteResult.attribution
                });
                i = quoteResult.endIndex;
                continue;
            }

            // 图片
            const imgMatch = line.match(/!\[(.*?)\]\((.*?)\)(\{.*?\})?/);
            if (imgMatch) {
                result.elements.push({
                    type: 'image',
                    alt: imgMatch[1],
                    src: imgMatch[2],
                    attrs: this.parseAttrs(imgMatch[3])
                });
                continue;
            }

            // 普通段落
            if (line.trim()) {
                result.elements.push({
                    type: 'paragraph',
                    text: line.trim()
                });
            }
        }

        // 处理最后一个块
        if (currentBlock) {
            result.elements.push(this.finalizeBlock(currentBlock, blockContent));
        }

        return result;
    }

    /**
     * 完成一个块的解析
     */
    finalizeBlock(type, lines) {
        const content = lines.join('\n').trim();

        if (type === 'card') {
            return this.parseCard(content);
        }

        if (type === 'chart') {
            return this.parseChartBlock(content);
        }

        if (type === 'left' || type === 'right') {
            return {
                type: 'column',
                position: type,
                content: this.parseBody(content, null)
            };
        }

        return {
            type: 'block',
            blockType: type,
            rawContent: content
        };
    }

    /**
     * 解析图表块 ::: chart
     */
    parseChartBlock(content) {
        const chart = {
            type: 'chart',
            template: null,
            title: '',
            data: {}
        };

        const lines = content.split('\n');
        let currentKey = null;
        let currentList = [];

        for (const line of lines) {
            const trimmed = line.trim();

            // template: xxx
            const templateMatch = trimmed.match(/^template:\s*(.+)/);
            if (templateMatch) {
                chart.template = templateMatch[1].trim();
                continue;
            }

            // title: xxx
            const titleMatch = trimmed.match(/^title:\s*(.+)/);
            if (titleMatch) {
                chart.title = titleMatch[1].trim();
                continue;
            }

            // key: (开始一个列表)
            const keyMatch = trimmed.match(/^(\w+):$/);
            if (keyMatch) {
                if (currentKey && currentList.length > 0) {
                    chart.data[currentKey] = currentList;
                }
                currentKey = keyMatch[1];
                currentList = [];
                continue;
            }

            // - label: xxx 或 - label | detail
            if (trimmed.startsWith('- ')) {
                const item = trimmed.substring(2).trim();

                // 检查 label: value 格式
                const labelMatch = item.match(/^label:\s*(.+)/);
                if (labelMatch) {
                    currentList.push({ label: labelMatch[1] });
                    continue;
                }

                // 检查 label | detail 格式
                const pipeMatch = item.match(/^(.+?)\s*\|\s*(.+)$/);
                if (pipeMatch) {
                    currentList.push({
                        label: pipeMatch[1].trim(),
                        detail: pipeMatch[2].trim()
                    });
                    continue;
                }

                // 简单字符串
                currentList.push({ label: item });
                continue;
            }

            // detail: xxx (附加到最后一个项)
            const detailMatch = trimmed.match(/^detail:\s*(.+)/);
            if (detailMatch && currentList.length > 0) {
                currentList[currentList.length - 1].detail = detailMatch[1];
            }
        }

        // 保存最后的列表
        if (currentKey && currentList.length > 0) {
            chart.data[currentKey] = currentList;
        }

        return chart;
    }

    /**
     * 解析卡片块
     */
    parseCard(content) {
        const card = {
            type: 'card',
            title: '',
            description: '',
            metric: ''
        };

        const lines = content.split('\n');
        const descLines = [];

        for (const line of lines) {
            // 卡片标题
            if (line.startsWith('### ')) {
                card.title = line.substring(4).trim();
                continue;
            }

            // 指标（带 .metric 类）
            const metricMatch = line.match(/`(.+?)`\{\.metric.*?\}/);
            if (metricMatch) {
                card.metric = metricMatch[1];
                continue;
            }

            // 普通描述
            if (line.trim()) {
                descLines.push(line.trim());
            }
        }

        card.description = descLines.join('\n');
        return card;
    }

    /**
     * 解析列表项
     */
    parseListItem(line) {
        const text = line.replace(/^[-*]\s+/, '').trim();

        // 检查是否有内联指标
        const metricMatch = text.match(/`(.+?)`(\{\.metric.*?\})?/);

        return {
            text: text.replace(/`(.+?)`(\{\.metric.*?\})?/g, '$1'),
            rawText: text,
            bold: text.startsWith('**'),
            metric: metricMatch ? metricMatch[1] : null
        };
    }

    /**
     * 解析表格
     */
    parseTable(lines, startIndex) {
        const tableLines = [];
        let i = startIndex;

        // 收集表格行
        while (i < lines.length && lines[i].includes('|')) {
            tableLines.push(lines[i]);
            i++;
        }

        if (tableLines.length < 2) {
            return { table: null, endIndex: startIndex };
        }

        // 解析表头
        const headers = tableLines[0]
            .split('|')
            .map(c => c.trim())
            .filter(c => c);

        // 跳过分隔行
        const dataStart = tableLines[1].match(/^[\s|:-]+$/) ? 2 : 1;

        // 解析数据行
        const rows = tableLines.slice(dataStart).map(line =>
            line.split('|').map(c => c.trim()).filter(c => c)
        );

        return {
            table: { headers, rows },
            endIndex: i - 1
        };
    }

    /**
     * 解析引用块
     */
    parseQuote(lines, startIndex) {
        const quoteLines = [];
        let i = startIndex;
        let attribution = '';

        while (i < lines.length && lines[i].startsWith('>')) {
            const line = lines[i].substring(1).trim();

            // 检查是否是来源行
            if (line.startsWith('—') || line.startsWith('-')) {
                attribution = line.replace(/^[—-]\s*/, '');
            } else if (line) {
                quoteLines.push(line);
            }
            i++;
        }

        return {
            text: quoteLines.join(' '),
            attribution,
            endIndex: i - 1
        };
    }

    /**
     * 解析属性字符串 {.class width=80%}
     */
    parseAttrs(attrStr) {
        if (!attrStr) return {};

        const attrs = {};
        const content = attrStr.replace(/^\{|\}$/g, '');

        // 类名
        const classes = content.match(/\.[\w-]+/g);
        if (classes) {
            attrs.classes = classes.map(c => c.substring(1));
        }

        // 键值对
        const kvMatches = content.matchAll(/(\w+)=([^\s}]+)/g);
        for (const match of kvMatches) {
            attrs[match[1]] = match[2];
        }

        return attrs;
    }

    /**
     * 根据类型推断默认布局
     */
    inferLayout(type) {
        const defaults = {
            'cover': 'title-only',
            'section': 'title-only',
            'content': 'bullets',
            'case-study': 'three-cards',
            'quote': 'quote',
            'closing': 'title-only'
        };
        return defaults[type] || 'bullets';
    }

    /**
     * 错误处理
     */
    handleError(message) {
        if (this.options.strictMode) {
            throw new Error(message);
        }
        console.warn(`[SlideParser] ${message}`);
        return null;
    }
}

module.exports = { SlideParser };

// CLI 测试
if (require.main === module) {
    const args = process.argv.slice(2);
    if (args.length === 0) {
        console.log('Usage: node slide-parser.js <file.slide.md | directory>');
        process.exit(1);
    }

    const parser = new SlideParser();
    const target = args[0];
    const stat = fs.existsSync(target) ? fs.statSync(target) : null;

    if (stat?.isDirectory()) {
        const slides = parser.parseDirectory(target);
        console.log(`Parsed ${slides.length} slides:`);
        slides.forEach(s => {
            console.log(`  - ${s.meta.id}: ${s.content.title} (${s.meta.type}/${s.meta.layout})`);
        });
    } else {
        const slide = parser.parseFile(target);
        if (slide) {
            console.log(JSON.stringify(slide, null, 2));
        }
    }
}
