/**
 * PPTX Renderer
 * 使用 pptxgenjs 将解析后的 slide 数据渲染为 PPTX
 *
 * 支持布局：
 * - title-only: 仅标题（封面/章节）
 * - bullets: 要点列表
 * - two-column: 双列
 * - three-cards: 三列卡片
 * - table: 表格
 * - quote: 引用
 * - chart: 图表（Mermaid/模板）
 */

const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');

// 延迟加载 ChartRenderer
let ChartRenderer = null;
try {
    ChartRenderer = require('./chart-renderer').ChartRenderer;
} catch (e) {
    // chart-renderer 可能不存在
}

class PPTXRenderer {
    /**
     * @param {Object} theme - 主题配置
     * @param {Object} options - 渲染选项
     */
    constructor(theme, options = {}) {
        this.theme = theme;
        this.pptx = null;
        this.options = {
            chartOutputDir: './charts',
            chartTheme: 'nano-banana',
            verbose: false,
            ...options
        };

        // 初始化 ChartRenderer
        this.chartRenderer = null;
        if (ChartRenderer) {
            this.chartRenderer = new ChartRenderer({
                outputDir: this.options.chartOutputDir,
                theme: this.options.chartTheme,
                verbose: this.options.verbose
            });
        }
    }

    /**
     * 渲染多个 slides 到 PPTX
     * @param {ParsedSlide[]} slides - 解析后的幻灯片数组
     * @param {Object} options - 渲染选项
     * @returns {pptxgen} - pptxgenjs 实例
     */
    render(slides, options = {}) {
        this.pptx = new pptxgen();
        this.pptx.layout = 'LAYOUT_16x9';
        this.pptx.title = options.title || 'Presentation';
        this.pptx.author = options.author || 'Claude Code';
        this.pptx.subject = options.subject || '';

        for (const slide of slides) {
            this.renderSlide(slide);
        }

        return this.pptx;
    }

    /**
     * 渲染单个 slide
     * @param {ParsedSlide} slideData - 解析后的幻灯片数据
     */
    renderSlide(slideData) {
        const { meta, content, notes } = slideData;
        const layout = meta.layout || 'bullets';

        // 根据布局类型分发
        const layoutRenderers = {
            'title-only': () => this.renderTitleOnly(meta, content),
            'bullets': () => this.renderBullets(meta, content),
            'two-column': () => this.renderTwoColumn(meta, content),
            'three-cards': () => this.renderThreeCards(meta, content),
            'table': () => this.renderTable(meta, content),
            'quote': () => this.renderQuote(meta, content),
            'chart': () => this.renderChart(meta, content)
        };

        const renderer = layoutRenderers[layout] || layoutRenderers['bullets'];
        const slide = renderer();

        // 添加演讲者备注
        if (notes) {
            slide.addNotes(notes);
        }

        return slide;
    }

    // ==================== 布局渲染器 ====================

    /**
     * 仅标题布局（封面/章节页）
     */
    renderTitleOnly(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        // 背景色（章节页用主色，其他用默认背景）
        const bgColor = meta.type === 'section'
            ? C.background.section
            : C.background.default;
        slide.background = { color: this.stripHash(bgColor) };

        const textColor = meta.type === 'section'
            ? C.text.inverse
            : C.text.primary;

        // 装饰条
        if (meta.type !== 'section') {
            slide.addShape(this.pptx.shapes.RECTANGLE, {
                x: 0, y: 0, w: 10, h: 0.15,
                fill: { color: this.stripHash(C.primary) }
            });
        }

        // 主标题
        slide.addText(content.title || '', {
            x: 0.5, y: meta.type === 'section' ? 2.0 : 1.8,
            w: 9, h: 1,
            fontSize: this.theme.typography.scale.cover_title,
            color: this.stripHash(textColor),
            bold: true,
            align: 'center'
        });

        // 副标题
        if (content.subtitle) {
            // 分隔线（非章节页）
            if (meta.type !== 'section') {
                slide.addShape(this.pptx.shapes.RECTANGLE, {
                    x: 4, y: 2.9, w: 2, h: 0.06,
                    fill: { color: this.stripHash(C.accent) }
                });
            }

            slide.addText(content.subtitle, {
                x: 0.5, y: meta.type === 'section' ? 3.0 : 3.2,
                w: 9, h: 0.6,
                fontSize: this.theme.typography.scale.subtitle,
                color: this.stripHash(meta.type === 'section' ? C.accent : C.secondary),
                align: 'center'
            });
        }

        // 额外信息（段落元素）
        const paragraphs = content.elements.filter(e => e.type === 'paragraph');
        if (paragraphs.length > 0) {
            slide.addText(paragraphs.map(p => p.text).join('\n'), {
                x: 0.5, y: 4.0,
                w: 9, h: 0.5,
                fontSize: this.theme.typography.scale.caption,
                color: this.stripHash(C.text.secondary),
                align: 'center'
            });
        }

        return slide;
    }

    /**
     * 要点列表布局
     */
    renderBullets(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.default) };

        // 标题栏
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x: 0, y: 0, w: 10, h: 0.8,
            fill: { color: this.stripHash(C.background.alternate) }
        });
        slide.addText(content.title || '', {
            x: 0.4, y: 0.15, w: 9, h: 0.5,
            fontSize: this.theme.typography.scale.slide_title,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 副标题
        let contentStartY = 1.0;
        if (content.subtitle) {
            slide.addText(content.subtitle, {
                x: 0.5, y: 0.9, w: 9, h: 0.4,
                fontSize: this.theme.typography.scale.caption,
                color: this.stripHash(C.text.secondary)
            });
            contentStartY = 1.4;
        }

        // 要点列表
        const bullets = content.elements.filter(e => e.type === 'bullet');
        if (bullets.length > 0) {
            const bulletText = bullets.map(b => ({
                text: b.rawText || b.text,
                options: {
                    bullet: { type: 'bullet', color: this.stripHash(C.accent) },
                    indentLevel: 0
                }
            }));

            slide.addText(bulletText, {
                x: 0.5, y: contentStartY, w: 9, h: 3.2,
                fontSize: this.theme.typography.scale.body,
                color: this.stripHash(C.text.primary),
                lineSpacing: 28
            });
        }

        return slide;
    }

    /**
     * 双列布局
     */
    renderTwoColumn(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.default) };

        // 标题
        slide.addText(content.title || '', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: this.theme.typography.scale.slide_title,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 分隔线
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x: 0.5, y: 0.85, w: 1.5, h: 0.04,
            fill: { color: this.stripHash(C.accent) }
        });

        // 左列
        const leftCol = content.elements.find(e => e.type === 'column' && e.position === 'left');
        if (leftCol) {
            this.renderColumnContent(slide, leftCol.content, 0.5, 1.1, 4.3);
        }

        // 右列
        const rightCol = content.elements.find(e => e.type === 'column' && e.position === 'right');
        if (rightCol) {
            this.renderColumnContent(slide, rightCol.content, 5.2, 1.1, 4.3);
        }

        return slide;
    }

    /**
     * 渲染列内容
     */
    renderColumnContent(slide, content, x, y, w) {
        const C = this.theme.colors;
        let currentY = y;

        // 列标题
        if (content.subtitle) {
            slide.addText(content.subtitle, {
                x, y: currentY, w, h: 0.4,
                fontSize: this.theme.typography.scale.body,
                color: this.stripHash(C.secondary),
                bold: true
            });
            currentY += 0.5;
        }

        // 列表项
        const bullets = content.elements.filter(e => e.type === 'bullet');
        if (bullets.length > 0) {
            const bulletText = bullets.map(b => ({
                text: b.rawText || b.text,
                options: {
                    bullet: { type: 'bullet', color: this.stripHash(C.accent) },
                    indentLevel: 0
                }
            }));

            slide.addText(bulletText, {
                x, y: currentY, w, h: 2.5,
                fontSize: this.theme.typography.scale.caption,
                color: this.stripHash(C.text.primary),
                lineSpacing: 24
            });
        }
    }

    /**
     * 三列卡片布局
     */
    renderThreeCards(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.default) };

        // 标题
        slide.addText(content.title || '', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: this.theme.typography.scale.slide_title,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 分隔线
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x: 0.5, y: 0.85, w: 1.5, h: 0.04,
            fill: { color: this.stripHash(C.accent) }
        });

        // 卡片
        const cards = content.elements.filter(e => e.type === 'card');
        cards.slice(0, 3).forEach((card, i) => {
            const x = 0.4 + i * 3.1;
            this.renderCard(slide, card, x, 1.1, 3.0, 3.3);
        });

        return slide;
    }

    /**
     * 渲染单个卡片
     */
    renderCard(slide, card, x, y, w, h) {
        const C = this.theme.colors;

        // 卡片背景
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x, y, w, h,
            fill: { color: this.stripHash(C.background.alternate) },
            line: { color: this.stripHash(C.decorative?.border || 'E2E8F0'), width: 1 }
        });

        // 顶部强调条
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x, y, w, h: 0.08,
            fill: { color: this.stripHash(C.accent) }
        });

        // 卡片标题
        slide.addText(card.title || '', {
            x: x + 0.15, y: y + 0.2, w: w - 0.3, h: 0.5,
            fontSize: 16,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 卡片描述
        slide.addText(card.description || '', {
            x: x + 0.15, y: y + 0.75, w: w - 0.3, h: 1.5,
            fontSize: 12,
            color: this.stripHash(C.text.secondary)
        });

        // 指标
        if (card.metric) {
            slide.addShape(this.pptx.shapes.RECTANGLE, {
                x: x + 0.15, y: y + h - 0.9, w: w - 0.3, h: 0.7,
                fill: { color: 'E8F5E9' }
            });
            slide.addText(card.metric, {
                x: x + 0.15, y: y + h - 0.85, w: w - 0.3, h: 0.6,
                fontSize: 14,
                color: this.stripHash(C.semantic?.success || '38A169'),
                bold: true,
                align: 'center'
            });
        }
    }

    /**
     * 表格布局
     */
    renderTable(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.default) };

        // 标题
        slide.addText(content.title || '', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: this.theme.typography.scale.slide_title,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 查找表格元素
        const tableEl = content.elements.find(e => e.type === 'table');
        if (tableEl) {
            const { headers, rows } = tableEl;

            // 构建表格数据
            const tableData = [
                headers.map(h => ({
                    text: h,
                    options: {
                        fill: { color: this.stripHash(C.primary) },
                        color: 'FFFFFF',
                        bold: true
                    }
                })),
                ...rows.map(row => row.map(cell => ({
                    text: cell,
                    options: { color: this.stripHash(C.text.primary) }
                })))
            ];

            slide.addTable(tableData, {
                x: 0.5, y: 1.0,
                w: 9, h: 0.5 + rows.length * 0.5,
                colW: headers.map(() => 9 / headers.length),
                border: { pt: 0.5, color: this.stripHash(C.decorative?.border || 'E2E8F0') },
                fill: { color: this.stripHash(C.background.default) },
                fontSize: 12,
                valign: 'middle'
            });
        }

        return slide;
    }

    /**
     * 引用布局
     */
    renderQuote(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.alternate) };

        // 查找引用元素
        const quoteEl = content.elements.find(e => e.type === 'quote');
        const quoteText = quoteEl?.text || content.title || '';
        const attribution = quoteEl?.attribution || content.subtitle || '';

        // 引号装饰
        slide.addText('"', {
            x: 0.8, y: 1.0, w: 1, h: 1,
            fontSize: 120,
            color: this.stripHash(C.accent),
            bold: true
        });

        // 引用内容
        slide.addText(quoteText, {
            x: 1.5, y: 1.6, w: 7, h: 2,
            fontSize: 28,
            color: this.stripHash(C.primary),
            italic: true,
            align: 'center'
        });

        // 归属
        if (attribution) {
            slide.addText(`— ${attribution}`, {
                x: 1.5, y: 3.7, w: 7, h: 0.5,
                fontSize: 16,
                color: this.stripHash(C.text.secondary),
                align: 'center'
            });
        }

        return slide;
    }

    /**
     * 图表布局（Mermaid 或模板）
     */
    renderChart(meta, content) {
        const slide = this.pptx.addSlide();
        const C = this.theme.colors;

        slide.background = { color: this.stripHash(C.background.default) };

        // 标题
        slide.addText(content.title || '', {
            x: 0.5, y: 0.3, w: 9, h: 0.5,
            fontSize: this.theme.typography.scale.slide_title,
            color: this.stripHash(C.primary),
            bold: true
        });

        // 分隔线
        slide.addShape(this.pptx.shapes.RECTANGLE, {
            x: 0.5, y: 0.85, w: 1.5, h: 0.04,
            fill: { color: this.stripHash(C.accent) }
        });

        // 查找图表元素
        const chartEl = content.elements.find(e => e.type === 'chart');
        const mermaidEl = content.elements.find(e => e.type === 'mermaid');

        let imagePath = null;

        // 处理 Mermaid 代码块
        if (mermaidEl && this.chartRenderer) {
            const outputName = `chart-${meta.id || Date.now()}`;
            imagePath = this.chartRenderer.renderMermaid(mermaidEl.code, outputName);
        }

        // 处理预定义模板
        if (chartEl && chartEl.template && this.chartRenderer) {
            const outputName = `chart-${meta.id || Date.now()}`;
            imagePath = this.chartRenderer.renderTemplate(
                chartEl.template,
                chartEl.data,
                outputName
            );
        }

        // 添加图表图片
        if (imagePath && fs.existsSync(imagePath)) {
            slide.addImage({
                path: imagePath,
                x: 0.5, y: 1.1,
                w: 9, h: 4.0
            });

            if (this.options.verbose) {
                console.log(`[PPTXRenderer] Added chart image: ${imagePath}`);
            }
        } else {
            // 图表渲染失败，显示占位符
            slide.addText('图表渲染中...', {
                x: 0.5, y: 2.5, w: 9, h: 1,
                fontSize: 20,
                color: this.stripHash(C.text.secondary),
                align: 'center'
            });

            // 如果有 chart 元素，显示模板信息
            if (chartEl) {
                slide.addText(`模板: ${chartEl.template || 'N/A'}`, {
                    x: 0.5, y: 3.5, w: 9, h: 0.5,
                    fontSize: 14,
                    color: this.stripHash(C.text.secondary),
                    align: 'center'
                });
            }

            // 如果有 mermaid 元素，显示部分代码
            if (mermaidEl) {
                const codePreview = mermaidEl.code.split('\n').slice(0, 3).join('\n') + '...';
                slide.addText(codePreview, {
                    x: 1, y: 3.0, w: 8, h: 1.5,
                    fontSize: 10,
                    fontFace: 'Consolas',
                    color: this.stripHash(C.text.secondary),
                    align: 'left'
                });
            }
        }

        return slide;
    }

    /**
     * 在 bullets 布局中处理 Mermaid 元素
     */
    handleMermaidInLayout(slide, mermaidEl, x, y, w, h) {
        if (!mermaidEl || !this.chartRenderer) {
            return false;
        }

        const outputName = `inline-chart-${Date.now()}`;
        const imagePath = this.chartRenderer.renderMermaid(mermaidEl.code, outputName);

        if (imagePath && fs.existsSync(imagePath)) {
            slide.addImage({
                path: imagePath,
                x, y, w, h
            });
            return true;
        }

        return false;
    }

    // ==================== 工具方法 ====================

    /**
     * 去除颜色值的 # 前缀
     */
    stripHash(color) {
        if (!color) return 'FFFFFF';
        return color.replace(/^#/, '');
    }

    /**
     * 保存 PPTX 文件
     * @param {string} outputPath - 输出路径
     */
    async save(outputPath) {
        if (!this.pptx) {
            throw new Error('No presentation to save. Call render() first.');
        }
        await this.pptx.writeFile({ fileName: outputPath });
        return outputPath;
    }
}

module.exports = { PPTXRenderer };
