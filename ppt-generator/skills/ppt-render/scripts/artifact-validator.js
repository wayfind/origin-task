/**
 * Artifact Validator - 渲染前强制检查
 *
 * P0 级别改动：阻断虚假完成
 *
 * 功能：
 * 1. 检查 skeleton.yaml 中的 research_tasks 是否都有对应的结果文件
 * 2. 检查 research_results/ 目录是否存在且包含必要文件
 * 3. 验证研究结果文件的完整性（非空、有内容、有来源）
 */

const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

class ArtifactValidator {
    constructor(options = {}) {
        this.options = {
            strict: true,           // 严格模式：缺失必需研究则阻断
            warnOnly: false,        // 仅警告模式
            verbose: false,
            ...options
        };
        this.errors = [];
        this.warnings = [];
    }

    /**
     * 验证项目目录的所有 artifact
     * @param {string} projectDir - 项目目录（包含 skeleton.yaml 和 slides/）
     * @returns {{ valid: boolean, errors: string[], warnings: string[] }}
     */
    validate(projectDir) {
        this.errors = [];
        this.warnings = [];

        const skeletonPath = path.join(projectDir, 'skeleton.yaml');
        const researchDir = path.join(projectDir, 'research_results');
        const slidesDir = path.join(projectDir, 'slides');

        // 1. 检查 skeleton.yaml 存在
        if (!fs.existsSync(skeletonPath)) {
            this.warnings.push(`skeleton.yaml 不存在: ${skeletonPath}`);
            return this._result();
        }

        // 2. 加载 skeleton
        let skeleton;
        try {
            skeleton = yaml.load(fs.readFileSync(skeletonPath, 'utf-8'));
        } catch (e) {
            this.errors.push(`skeleton.yaml 解析失败: ${e.message}`);
            return this._result();
        }

        // 3. 检查 research_tasks
        const researchTasks = skeleton.research_tasks || [];
        if (researchTasks.length > 0) {
            this._validateResearchTasks(researchTasks, researchDir);
        }

        // 4. 检查 slides 中的 @RESEARCH 标记是否有对应结果
        if (fs.existsSync(slidesDir)) {
            this._validateSlideResearchRefs(slidesDir, researchTasks, researchDir);
        }

        return this._result();
    }

    /**
     * 验证研究任务是否都有对应结果
     */
    _validateResearchTasks(tasks, researchDir) {
        const requiredTasks = tasks.filter(t => t.required !== false);
        const optionalTasks = tasks.filter(t => t.required === false);

        // 检查 research_results 目录
        if (!fs.existsSync(researchDir)) {
            if (requiredTasks.length > 0) {
                this.errors.push(
                    `\n` +
                    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
                    `🚫 RENDER BLOCKED: research_results/ 目录不存在\n` +
                    `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n` +
                    `\n` +
                    `skeleton.yaml 定义了 ${requiredTasks.length} 个必需研究任务：\n` +
                    requiredTasks.map(t => `  - [${t.id}] ${t.query.split('\n')[0].trim()}`).join('\n') +
                    `\n\n` +
                    `这些任务必须执行并将结果保存到 research_results/ 目录。\n` +
                    `\n` +
                    `解决方法：\n` +
                    `  1. 使用 /ppt-enrich 执行研究任务\n` +
                    `  2. 确保每个任务都调用 deep-research skill\n` +
                    `  3. 将结果保存为 research_results/{task_id}.md\n`
                );
            } else if (optionalTasks.length > 0) {
                this.warnings.push(`research_results/ 目录不存在，${optionalTasks.length} 个可选研究任务未执行`);
            }
            return;
        }

        // 检查每个必需任务
        for (const task of requiredTasks) {
            const resultFile = path.join(researchDir, `${task.id}.md`);
            const metaFile = path.join(researchDir, `${task.id}.meta.json`);

            if (!fs.existsSync(resultFile)) {
                this.errors.push(
                    `\n` +
                    `🚫 研究任务 [${task.id}] 未执行\n` +
                    `   Query: ${task.query.split('\n')[0].trim()}...\n` +
                    `   Expected: ${resultFile}\n` +
                    `   Status: FILE NOT FOUND\n`
                );
            } else {
                // 验证内容非空
                const content = fs.readFileSync(resultFile, 'utf-8').trim();
                if (content.length < 100) {
                    this.errors.push(
                        `\n` +
                        `🚫 研究任务 [${task.id}] 结果不完整\n` +
                        `   File: ${resultFile}\n` +
                        `   Content length: ${content.length} chars (minimum: 100)\n`
                    );
                }

                // 检查是否有来源引用
                if (!content.includes('来源') && !content.includes('Source') && !content.includes('*来源')) {
                    this.warnings.push(`研究任务 [${task.id}] 结果中没有发现来源引用`);
                }
            }

            // 检查 meta 文件（可选但推荐）
            if (!fs.existsSync(metaFile)) {
                this.warnings.push(`研究任务 [${task.id}] 缺少 meta 文件: ${metaFile}`);
            }
        }

        // 检查可选任务（仅警告）
        for (const task of optionalTasks) {
            const resultFile = path.join(researchDir, `${task.id}.md`);
            if (!fs.existsSync(resultFile)) {
                this.warnings.push(`可选研究任务 [${task.id}] 未执行`);
            }
        }
    }

    /**
     * 验证 slide-md 中的 @RESEARCH 引用
     */
    _validateSlideResearchRefs(slidesDir, tasks, researchDir) {
        const taskIds = new Set(tasks.map(t => t.id));
        const files = fs.readdirSync(slidesDir).filter(f => f.endsWith('.slide.md'));

        for (const file of files) {
            const content = fs.readFileSync(path.join(slidesDir, file), 'utf-8');

            // 查找 @RESEARCH 标记
            const matches = content.matchAll(/<!--\s*@RESEARCH:\s*(\w+)\s*-->/g);

            for (const match of matches) {
                const refId = match[1];

                // 检查引用的任务是否存在
                if (!taskIds.has(refId)) {
                    this.warnings.push(`${file}: 引用了未定义的研究任务 [${refId}]`);
                    continue;
                }

                // 检查引用的研究结果是否存在
                const resultFile = path.join(researchDir, `${refId}.md`);
                if (fs.existsSync(researchDir) && !fs.existsSync(resultFile)) {
                    this.warnings.push(`${file}: 引用的研究任务 [${refId}] 没有结果文件`);
                }
            }
        }
    }

    /**
     * 构建验证结果
     */
    _result() {
        const valid = this.options.warnOnly ? true : this.errors.length === 0;
        return {
            valid,
            errors: this.errors,
            warnings: this.warnings
        };
    }

    /**
     * 打印验证报告
     */
    printReport(result) {
        if (result.errors.length > 0) {
            console.error('\n╔════════════════════════════════════════════════════════════╗');
            console.error('║          ARTIFACT VALIDATION FAILED                        ║');
            console.error('╚════════════════════════════════════════════════════════════╝');
            result.errors.forEach(e => console.error(e));
        }

        if (result.warnings.length > 0) {
            console.warn('\n⚠️  Warnings:');
            result.warnings.forEach(w => console.warn(`   - ${w}`));
        }

        if (result.valid && result.errors.length === 0 && result.warnings.length === 0) {
            console.log('✅ Artifact validation passed');
        }
    }
}

module.exports = { ArtifactValidator };
