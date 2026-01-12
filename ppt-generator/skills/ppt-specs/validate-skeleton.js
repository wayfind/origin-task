#!/usr/bin/env node
/**
 * Skeleton YAML Validator
 * 验证 skeleton.yaml 文件是否符合规范
 *
 * 用法：node validate-skeleton.js <skeleton.yaml>
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

// 加载 JSON Schema
const SCHEMA_PATH = path.join(__dirname, 'skeleton.schema.json');

// 验证结果类型
const ResultType = {
    ERROR: 'error',
    WARNING: 'warning',
    INFO: 'info'
};

class SkeletonValidator {
    constructor() {
        this.schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf8'));
        this.results = [];
    }

    /**
     * 验证 skeleton 文件
     * @param {string} filePath - skeleton.yaml 文件路径
     * @returns {object} - 验证结果
     */
    validate(filePath) {
        this.results = [];

        // 检查文件存在
        if (!fs.existsSync(filePath)) {
            this.addError(`File not found: ${filePath}`);
            return this.getReport();
        }

        // 解析 YAML
        let skeleton;
        try {
            const content = fs.readFileSync(filePath, 'utf8');
            skeleton = yaml.parse(content);
        } catch (e) {
            this.addError(`YAML parse error: ${e.message}`);
            return this.getReport();
        }

        // 执行验证
        this.validateRequired(skeleton);
        this.validateMeta(skeleton.meta);
        this.validateAudience(skeleton.audience);
        this.validatePresentation(skeleton.presentation);
        this.validateStructure(skeleton.structure);
        this.validateGlobalResearch(skeleton.global_research, skeleton.structure);
        this.validateConsistency(skeleton);

        return this.getReport();
    }

    // ==================== 必填字段验证 ====================

    validateRequired(skeleton) {
        const required = ['meta', 'audience', 'presentation', 'structure'];
        for (const field of required) {
            if (!skeleton[field]) {
                this.addError(`Missing required field: ${field}`);
            }
        }
    }

    validateMeta(meta) {
        if (!meta) return;

        if (!meta.title) {
            this.addError('meta.title is required');
        }
        if (!meta.version) {
            this.addError('meta.version is required');
        } else if (!/^\d+\.\d+$/.test(meta.version)) {
            this.addWarning(`meta.version format should be "X.Y", got: ${meta.version}`);
        }

        if (meta.date && !/^\d{4}(-\d{2})?(-\d{2})?$/.test(meta.date)) {
            this.addWarning(`meta.date format should be YYYY, YYYY-MM, or YYYY-MM-DD, got: ${meta.date}`);
        }
    }

    validateAudience(audience) {
        if (!audience) return;

        const validTypes = ['executives', 'managers', 'professionals', 'general'];
        if (!audience.type) {
            this.addError('audience.type is required');
        } else if (!validTypes.includes(audience.type)) {
            this.addError(`audience.type must be one of: ${validTypes.join(', ')}`);
        }

        if (audience.knowledge_level) {
            const validLevels = ['novice', 'intermediate', 'expert'];
            if (!validLevels.includes(audience.knowledge_level)) {
                this.addWarning(`audience.knowledge_level should be: ${validLevels.join(', ')}`);
            }
        }

        if (audience.industries) {
            let totalPercentage = 0;
            for (const ind of audience.industries) {
                if (!ind.name) {
                    this.addWarning('audience.industries[].name is recommended');
                }
                if (ind.percentage) {
                    totalPercentage += ind.percentage;
                }
            }
            if (totalPercentage > 0 && Math.abs(totalPercentage - 100) > 5) {
                this.addInfo(`audience.industries percentages sum to ${totalPercentage}%, expected ~100%`);
            }
        }
    }

    validatePresentation(presentation) {
        if (!presentation) return;

        if (!presentation.duration || presentation.duration <= 0) {
            this.addError('presentation.duration must be a positive integer');
        }

        if (!presentation.style) {
            this.addError('presentation.style is required');
        }

        const validOccasions = ['training', 'pitch', 'conference', 'workshop', 'marketing'];
        if (presentation.occasion && !validOccasions.includes(presentation.occasion)) {
            this.addWarning(`presentation.occasion should be: ${validOccasions.join(', ')}`);
        }

        if (presentation.output_formats) {
            const validFormats = ['pptx', 'html', 'pdf'];
            for (const fmt of presentation.output_formats) {
                if (!validFormats.includes(fmt)) {
                    this.addWarning(`Unknown output format: ${fmt}`);
                }
            }
        }
    }

    validateStructure(structure) {
        if (!structure || !Array.isArray(structure)) {
            this.addError('structure must be a non-empty array');
            return;
        }

        if (structure.length === 0) {
            this.addError('structure must have at least one section');
            return;
        }

        const validTypes = ['opening', 'content', 'case-study', 'framework', 'closing', 'transition'];
        const ids = new Set();

        for (let i = 0; i < structure.length; i++) {
            const section = structure[i];
            const prefix = `structure[${i}]`;

            // 必填字段
            if (!section.id) {
                this.addError(`${prefix}.id is required`);
            } else {
                if (ids.has(section.id)) {
                    this.addError(`Duplicate section id: ${section.id}`);
                }
                ids.add(section.id);
            }

            if (!section.title) {
                this.addError(`${prefix}.title is required`);
            }

            if (!section.type) {
                this.addError(`${prefix}.type is required`);
            } else if (!validTypes.includes(section.type)) {
                this.addError(`${prefix}.type must be one of: ${validTypes.join(', ')}`);
            }

            // 建议性检查
            if (section.type === 'content' && !section.research_needs) {
                this.addInfo(`${prefix} (${section.id}): content sections typically need research_needs`);
            }

            // 验证研究需求
            if (section.research_needs) {
                this.validateResearchNeeds(section.research_needs, `${prefix}.research_needs`);
            }

            // 验证子章节
            if (section.subsections) {
                for (let j = 0; j < section.subsections.length; j++) {
                    const sub = section.subsections[j];
                    if (!sub.id) {
                        this.addWarning(`${prefix}.subsections[${j}].id is recommended`);
                    }
                    if (!sub.title) {
                        this.addWarning(`${prefix}.subsections[${j}].title is recommended`);
                    }
                }
            }
        }
    }

    validateResearchNeeds(needs, prefix) {
        const validTypes = ['case_study', 'statistics', 'quote', 'trend', 'comparison'];
        const validPriorities = ['high', 'medium', 'low'];

        for (let i = 0; i < needs.length; i++) {
            const need = needs[i];
            const p = `${prefix}[${i}]`;

            if (!need.type) {
                this.addError(`${p}.type is required`);
            } else if (!validTypes.includes(need.type)) {
                this.addError(`${p}.type must be one of: ${validTypes.join(', ')}`);
            }

            if (!need.query) {
                this.addError(`${p}.query is required`);
            }

            if (need.priority && !validPriorities.includes(need.priority)) {
                this.addWarning(`${p}.priority should be: ${validPriorities.join(', ')}`);
            }

            if (need.count !== undefined && need.count <= 0) {
                this.addError(`${p}.count must be > 0`);
            }
        }
    }

    validateGlobalResearch(globalResearch, structure) {
        if (!globalResearch) return;

        const sectionIds = new Set((structure || []).map(s => s.id));

        for (let i = 0; i < globalResearch.length; i++) {
            const item = globalResearch[i];
            const prefix = `global_research[${i}]`;

            if (item.apply_to) {
                for (const id of item.apply_to) {
                    if (id !== '*' && !sectionIds.has(id)) {
                        this.addWarning(`${prefix}.apply_to references unknown section: ${id}`);
                    }
                }
            }
        }
    }

    // ==================== 一致性检查 ====================

    validateConsistency(skeleton) {
        if (!skeleton.structure || !skeleton.presentation) return;

        // 检查时长一致性
        const totalDuration = skeleton.structure.reduce((sum, s) => sum + (s.duration || 0), 0);
        const expectedDuration = skeleton.presentation.duration;

        if (expectedDuration && totalDuration > 0) {
            const diff = Math.abs(totalDuration - expectedDuration);
            if (diff > expectedDuration * 0.1) {
                this.addWarning(`Total section duration (${totalDuration}min) differs from presentation.duration (${expectedDuration}min) by more than 10%`);
            }
        }

        // 检查幻灯片数量
        if (skeleton.constraints?.content?.max_slides) {
            const totalEstimate = skeleton.structure.reduce((sum, s) => sum + (s.slides_estimate || 0), 0);
            if (totalEstimate > skeleton.constraints.content.max_slides) {
                this.addWarning(`Total slides estimate (${totalEstimate}) exceeds max_slides (${skeleton.constraints.content.max_slides})`);
            }
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

    getReport() {
        const errors = this.results.filter(r => r.type === ResultType.ERROR);
        const warnings = this.results.filter(r => r.type === ResultType.WARNING);
        const infos = this.results.filter(r => r.type === ResultType.INFO);

        return {
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
        console.log('Usage: node validate-skeleton.js <skeleton.yaml>');
        process.exit(1);
    }

    const validator = new SkeletonValidator();
    const report = validator.validate(args[0]);

    // 输出结果
    console.log('\n' + '='.repeat(60));
    console.log('Skeleton Validation Report');
    console.log('='.repeat(60));

    if (report.valid) {
        console.log('\n✓ Skeleton is valid');
    } else {
        console.log('\n✗ Skeleton has errors');
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
    console.log(`Summary: ${report.summary.errorCount} errors, ${report.summary.warningCount} warnings, ${report.summary.infoCount} info`);
    console.log('='.repeat(60) + '\n');

    process.exit(report.valid ? 0 : 1);
}

module.exports = { SkeletonValidator };
