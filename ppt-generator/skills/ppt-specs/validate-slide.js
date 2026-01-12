#!/usr/bin/env node
/**
 * Slide Markdown Validator
 * 验证 .slide.md 文件是否符合规范
 *
 * 用法：
 *   node validate-slide.js <file.slide.md>           # 验证单个文件
 *   node validate-slide.js <slides-directory>        # 验证目录下所有 .slide.md
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

// 验证结果类型
const ResultType = {
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
};

// 有效枚举值
const VALID_SLIDE_TYPES = ['cover', 'section', 'content', 'case-study', 'quote', 'closing'];
const VALID_LAYOUTS = [
    'title-only', 'bullets', 'two-column', 'three-cards',
    'table', 'quote', 'image-left', 'image-right', 'full-image'
];
const VALID_SOURCE_TYPES = ['report', 'news', 'official', 'academic'];
const VALID_ANIMATIONS = ['none', 'fade', 'slide-left', 'build-bullets'];

class SlideValidator {
    constructor() {
        this.results = [];
    }

    /**
     * 验证单个 slide.md 文件
     * @param {string} filePath - .slide.md 文件路径
     * @returns {object} - 验证结果
     */
    validateFile(filePath) {
        this.results = [];

        // 检查文件存在
        if (!fs.existsSync(filePath)) {
            this.addError(`File not found: ${filePath}`);
            return this.getReport(filePath);
        }

        // 检查文件扩展名
        if (!filePath.endsWith('.slide.md')) {
            this.addWarning(`File should have .slide.md extension`);
        }

        // 读取内容
        let content;
        try {
            content = fs.readFileSync(filePath, 'utf8');
        } catch (e) {
            this.addError(`Cannot read file: ${e.message}`);
            return this.getReport(filePath);
        }

        // 解析文件结构
        const parsed = this.parseSlideFile(content);
        if (!parsed) {
            return this.getReport(filePath);
        }

        // 验证各部分
        this.validateFrontmatter(parsed.frontmatter);
        this.validateContent(parsed.content);
        this.validateNotes(parsed.notes);

        return this.getReport(filePath);
    }

    /**
     * 验证目录下所有 .slide.md 文件
     * @param {string} dirPath - 目录路径
     * @returns {object} - 汇总验证结果
     */
    validateDirectory(dirPath) {
        if (!fs.existsSync(dirPath)) {
            return { valid: false, error: `Directory not found: ${dirPath}` };
        }

        const files = fs.readdirSync(dirPath)
            .filter(f => f.endsWith('.slide.md'))
            .map(f => path.join(dirPath, f))
            .sort();

        if (files.length === 0) {
            return { valid: true, warning: 'No .slide.md files found', files: [] };
        }

        const results = [];
        const ids = new Set();

        for (const file of files) {
            const report = this.validateFile(file);
            results.push(report);

            // 检查 ID 唯一性
            if (report.slideId) {
                if (ids.has(report.slideId)) {
                    report.errors.push(`Duplicate slide ID across files: ${report.slideId}`);
                    report.valid = false;
                }
                ids.add(report.slideId);
            }
        }

        const totalErrors = results.reduce((sum, r) => sum + r.summary.errorCount, 0);
        const totalWarnings = results.reduce((sum, r) => sum + r.summary.warningCount, 0);

        return {
            valid: totalErrors === 0,
            files: results,
            summary: {
                fileCount: files.length,
                validCount: results.filter(r => r.valid).length,
                totalErrors,
                totalWarnings
            }
        };
    }

    // ==================== 文件解析 ====================

    parseSlideFile(content) {
        const result = {
            frontmatter: null,
            content: '',
            notes: ''
        };

        // 分离 frontmatter
        const fmMatch = content.match(/^---\n([\s\S]*?)\n---\n([\s\S]*)$/);
        if (!fmMatch) {
            this.addError('Missing or invalid YAML frontmatter (must start and end with ---)');
            return null;
        }

        // 解析 YAML
        try {
            result.frontmatter = yaml.parse(fmMatch[1]);
        } catch (e) {
            this.addError(`YAML parse error: ${e.message}`);
            return null;
        }

        // 分离内容和备注
        const body = fmMatch[2];
        const notesMatch = body.split(/\n---notes---\n/);
        result.content = notesMatch[0].trim();
        result.notes = notesMatch[1] ? notesMatch[1].trim() : '';

        return result;
    }

    // ==================== Frontmatter 验证 ====================

    validateFrontmatter(fm) {
        if (!fm) return;

        // slide 块是必须的
        if (!fm.slide) {
            this.addError('frontmatter.slide is required');
            return;
        }

        const slide = fm.slide;

        // 必填字段
        if (!slide.id) {
            this.addError('slide.id is required');
        } else {
            this.slideId = slide.id; // 保存用于跨文件检查
        }

        if (!slide.type) {
            this.addError('slide.type is required');
        } else if (!VALID_SLIDE_TYPES.includes(slide.type)) {
            this.addError(`slide.type must be one of: ${VALID_SLIDE_TYPES.join(', ')}`);
        }

        // 可选字段验证
        if (slide.layout && !VALID_LAYOUTS.includes(slide.layout)) {
            this.addWarning(`slide.layout should be one of: ${VALID_LAYOUTS.join(', ')}`);
        }

        if (slide.animation && !VALID_ANIMATIONS.includes(slide.animation)) {
            this.addWarning(`slide.animation should be one of: ${VALID_ANIMATIONS.join(', ')}`);
        }

        if (slide.duration !== undefined && (typeof slide.duration !== 'number' || slide.duration < 0)) {
            this.addWarning('slide.duration should be a positive number (seconds)');
        }

        // 验证来源
        if (fm.sources) {
            this.validateSources(fm.sources);
        }

        // 验证案例数据
        if (fm.cases) {
            this.validateCases(fm.cases);
        }
    }

    validateSources(sources) {
        if (!Array.isArray(sources)) {
            this.addWarning('sources should be an array');
            return;
        }

        for (let i = 0; i < sources.length; i++) {
            const src = sources[i];
            const prefix = `sources[${i}]`;

            if (!src.url && !src.title) {
                this.addWarning(`${prefix}: should have url or title`);
            }

            if (src.type && !VALID_SOURCE_TYPES.includes(src.type)) {
                this.addInfo(`${prefix}.type: unknown type "${src.type}"`);
            }

            if (src.date && !/^\d{4}(-\d{2})?(-\d{2})?$/.test(src.date)) {
                this.addInfo(`${prefix}.date: format should be YYYY, YYYY-MM, or YYYY-MM-DD`);
            }
        }
    }

    validateCases(cases) {
        if (!Array.isArray(cases)) {
            this.addWarning('cases should be an array');
            return;
        }

        for (let i = 0; i < cases.length; i++) {
            const c = cases[i];
            const prefix = `cases[${i}]`;

            if (!c.company) {
                this.addWarning(`${prefix}.company is recommended for case studies`);
            }
        }
    }

    // ==================== 内容验证 ====================

    validateContent(content) {
        if (!content) {
            this.addWarning('Slide content is empty');
            return;
        }

        // 检查一级标题
        const hasH1 = /^# .+$/m.test(content);
        if (!hasH1) {
            this.addWarning('Slide should have a primary heading (# Title)');
        }

        // 检查多个一级标题
        const h1Count = (content.match(/^# .+$/gm) || []).length;
        if (h1Count > 1) {
            this.addWarning(`Slide has ${h1Count} primary headings, expected 1`);
        }

        // 检查未闭合的块
        const openBlocks = (content.match(/^:::\s*\w+/gm) || []).length;
        const closeBlocks = (content.match(/^:::$/gm) || []).length;
        if (openBlocks !== closeBlocks) {
            this.addError(`Unclosed ::: blocks (${openBlocks} opened, ${closeBlocks} closed)`);
        }

        // 检查表格格式
        const tableLines = content.split('\n').filter(l => l.includes('|'));
        if (tableLines.length > 0) {
            const hasHeader = tableLines.some(l => /^\|?[\s-|]+\|?$/.test(l));
            if (tableLines.length >= 2 && !hasHeader) {
                this.addWarning('Table appears to be missing header separator row');
            }
        }

        // 检查图片语法
        const images = content.match(/!\[.*?\]\(.*?\)/g) || [];
        for (const img of images) {
            const pathMatch = img.match(/\(([^)]+)\)/);
            if (pathMatch && pathMatch[1].startsWith('./')) {
                this.addInfo(`Image uses relative path: ${pathMatch[1]}`);
            }
        }
    }

    // ==================== 备注验证 ====================

    validateNotes(notes) {
        // 备注是可选的，只做简单检查
        if (notes && notes.length > 2000) {
            this.addInfo(`Speaker notes are quite long (${notes.length} chars)`);
        }
    }

    // ==================== 结果管理 ====================

    addError(message) {
        this.results.push({ type: ResultType.ERROR, message });
    }

    addWarning(message) {
        this.results.push({ type: ResultType.WARNING, message });
    }

    addInfo(message) {
        this.results.push({ type: ResultType.INFO, message });
    }

    getReport(filePath) {
        const errors = this.results.filter(r => r.type === ResultType.ERROR);
        const warnings = this.results.filter(r => r.type === ResultType.WARNING);
        const infos = this.results.filter(r => r.type === ResultType.INFO);

        return {
            file: filePath,
            slideId: this.slideId,
            valid: errors.length === 0,
            errors: errors.map(r => r.message),
            warnings: warnings.map(r => r.message),
            infos: infos.map(r => r.message),
            summary: {
                errorCount: errors.length,
                warningCount: warnings.length,
                infoCount: infos.length
            }
        };
    }
}

// CLI 入口
if (require.main === module) {
    const args = process.argv.slice(2);

    if (args.length === 0) {
        console.log('Usage:');
        console.log('  node validate-slide.js <file.slide.md>     # Validate single file');
        console.log('  node validate-slide.js <slides-directory>  # Validate all .slide.md files');
        process.exit(1);
    }

    const target = args[0];
    const validator = new SlideValidator();
    const isDirectory = fs.existsSync(target) && fs.statSync(target).isDirectory();

    console.log('\n' + '='.repeat(60));
    console.log('Slide Markdown Validation Report');
    console.log('='.repeat(60));

    if (isDirectory) {
        const report = validator.validateDirectory(target);

        if (report.error) {
            console.log(`\n✗ ${report.error}`);
            process.exit(1);
        }

        console.log(`\nDirectory: ${target}`);
        console.log(`Files: ${report.summary.fileCount}`);
        console.log(`Valid: ${report.summary.validCount}/${report.summary.fileCount}`);

        for (const file of report.files) {
            const status = file.valid ? '✓' : '✗';
            console.log(`\n${status} ${path.basename(file.file)}`);

            if (file.errors.length > 0) {
                file.errors.forEach(e => console.log(`    ✗ ${e}`));
            }
            if (file.warnings.length > 0) {
                file.warnings.forEach(w => console.log(`    ⚠ ${w}`));
            }
        }

        console.log('\n' + '-'.repeat(60));
        console.log(`Summary: ${report.summary.totalErrors} errors, ${report.summary.totalWarnings} warnings`);
        process.exit(report.valid ? 0 : 1);

    } else {
        const report = validator.validateFile(target);

        if (report.valid) {
            console.log(`\n✓ ${target} is valid`);
        } else {
            console.log(`\n✗ ${target} has errors`);
        }

        if (report.errors.length > 0) {
            console.log('\n[ERRORS]');
            report.errors.forEach(e => console.log(`  ✗ ${e}`));
        }

        if (report.warnings.length > 0) {
            console.log('\n[WARNINGS]');
            report.warnings.forEach(w => console.log(`  ⚠ ${w}`));
        }

        if (report.infos.length > 0) {
            console.log('\n[INFO]');
            report.infos.forEach(i => console.log(`  ℹ ${i}`));
        }

        console.log('\n' + '-'.repeat(60));
        console.log(`Summary: ${report.summary.errorCount} errors, ${report.summary.warningCount} warnings`);
        process.exit(report.valid ? 0 : 1);
    }

    console.log('='.repeat(60) + '\n');
}

module.exports = { SlideValidator };
