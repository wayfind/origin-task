#!/usr/bin/env node
/**
 * PPT Render 测试脚本
 */

const path = require('path');
const fs = require('fs');
const { SlideParser } = require('../scripts/slide-parser');
const { PPTXRenderer } = require('../scripts/pptx-renderer');
const { loadTheme, listThemes } = require('../scripts/theme-loader');
const { PPTRender } = require('../scripts/render');

const FIXTURES_DIR = path.join(__dirname, 'fixtures');
const OUTPUT_DIR = path.join(__dirname, 'output');

// 确保输出目录存在
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

let passed = 0;
let failed = 0;

function test(name, fn) {
    try {
        fn();
        console.log(`✓ ${name}`);
        passed++;
    } catch (e) {
        console.log(`✗ ${name}`);
        console.log(`  Error: ${e.message}`);
        failed++;
    }
}

function assert(condition, message) {
    if (!condition) {
        throw new Error(message || 'Assertion failed');
    }
}

// ==================== SlideParser 测试 ====================

console.log('\n=== SlideParser Tests ===\n');

test('parseFile - cover slide', () => {
    const parser = new SlideParser();
    const slide = parser.parseFile(path.join(FIXTURES_DIR, '00-cover.slide.md'));

    assert(slide !== null, 'Should parse successfully');
    assert(slide.meta.id === '00-cover', 'ID should match');
    assert(slide.meta.type === 'cover', 'Type should be cover');
    assert(slide.meta.layout === 'title-only', 'Layout should be title-only');
    assert(slide.content.title.includes('生成式AI'), 'Title should contain 生成式AI');
    assert(slide.content.subtitle.includes('清华经管'), 'Subtitle should contain 清华经管');
});

test('parseFile - content slide with bullets', () => {
    const parser = new SlideParser();
    const slide = parser.parseFile(path.join(FIXTURES_DIR, '02-content.slide.md'));

    assert(slide !== null, 'Should parse successfully');
    assert(slide.meta.type === 'content', 'Type should be content');
    assert(slide.meta.layout === 'bullets', 'Layout should be bullets');

    const bullets = slide.content.elements.filter(e => e.type === 'bullet');
    assert(bullets.length === 4, 'Should have 4 bullet points');
    assert(bullets[0].bold === true, 'First bullet should be bold');
});

test('parseFile - case study with cards', () => {
    const parser = new SlideParser();
    const slide = parser.parseFile(path.join(FIXTURES_DIR, '03-cases.slide.md'));

    assert(slide !== null, 'Should parse successfully');
    assert(slide.meta.type === 'case-study', 'Type should be case-study');

    const cards = slide.content.elements.filter(e => e.type === 'card');
    assert(cards.length === 3, 'Should have 3 cards');
    assert(cards[0].title === '美的集团', 'First card title');
    assert(cards[0].metric.includes('30%'), 'First card metric');
});

test('parseFile - speaker notes', () => {
    const parser = new SlideParser();
    const slide = parser.parseFile(path.join(FIXTURES_DIR, '02-content.slide.md'));

    assert(slide.notes !== '', 'Should have speaker notes');
    assert(slide.notes.includes('重点强调'), 'Notes content');
});

test('parseDirectory', () => {
    const parser = new SlideParser();
    const slides = parser.parseDirectory(FIXTURES_DIR);

    assert(slides.length === 4, 'Should parse 4 slides');
    assert(slides[0].meta.id === '00-cover', 'Should be sorted');
});

// ==================== ThemeLoader 测试 ====================

console.log('\n=== ThemeLoader Tests ===\n');

test('loadTheme - corporate-light', () => {
    const theme = loadTheme('corporate-light');

    assert(theme.theme.name === 'corporate-light', 'Theme name');
    assert(theme.colors.primary === '#1E3A5F', 'Primary color');
    assert(theme.colors.background.default === '#FFFFFF', 'Background color');
});

test('loadTheme - nano-banana-pro', () => {
    const theme = loadTheme('nano-banana-pro');

    assert(theme.theme.name === 'nano-banana-pro', 'Theme name');
    assert(theme.colors.primary === '#F4C430', 'Primary color (gold)');
    assert(theme.colors.background.default === '#1C2833', 'Background color (dark)');
});

test('listThemes', () => {
    const themes = listThemes();

    assert(Array.isArray(themes), 'Should return array');
    assert(themes.includes('corporate-light'), 'Should include corporate-light');
    assert(themes.includes('nano-banana-pro'), 'Should include nano-banana-pro');
});

// ==================== PPTXRenderer 测试 ====================

console.log('\n=== PPTXRenderer Tests ===\n');

test('render - creates pptx object', () => {
    const theme = loadTheme('corporate-light');
    const renderer = new PPTXRenderer(theme);
    const parser = new SlideParser();

    const slides = parser.parseDirectory(FIXTURES_DIR);
    const pptx = renderer.render(slides, { title: 'Test' });

    assert(pptx !== null, 'Should create pptx');
    assert(pptx.slides.length === 4, 'Should have 4 slides');
});

// ==================== 集成测试 ====================

console.log('\n=== Integration Tests ===\n');

test('PPTRender - full pipeline corporate-light', async () => {
    const render = new PPTRender({
        theme: 'corporate-light',
        verbose: false
    });

    const outputPath = path.join(OUTPUT_DIR, 'test-corporate-light.pptx');
    const result = await render.renderDirectory(FIXTURES_DIR, outputPath);

    assert(result !== null, 'Should complete');
    assert(result.slideCount === 4, 'Should render 4 slides');
    assert(fs.existsSync(outputPath), 'Output file should exist');
});

test('PPTRender - full pipeline nano-banana-pro', async () => {
    const render = new PPTRender({
        theme: 'nano-banana-pro',
        verbose: false
    });

    const outputPath = path.join(OUTPUT_DIR, 'test-nano-banana-pro.pptx');
    const result = await render.renderDirectory(FIXTURES_DIR, outputPath);

    assert(result !== null, 'Should complete');
    assert(result.slideCount === 4, 'Should render 4 slides');
    assert(fs.existsSync(outputPath), 'Output file should exist');
});

// ==================== 结果 ====================

console.log('\n' + '='.repeat(40));
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log('='.repeat(40));

if (failed > 0) {
    process.exit(1);
}
