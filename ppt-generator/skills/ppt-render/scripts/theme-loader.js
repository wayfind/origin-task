/**
 * Theme Loader
 * 加载和合并主题配置
 */

const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

// 预置主题目录
const THEMES_DIR = path.join(__dirname, '..', 'themes');

// 基础默认配置
const BASE_THEME = {
    theme: {
        name: '_base',
        version: '1.0',
        base: 'light',
        mood: 'professional'
    },
    colors: {
        primary: '#1E3A5F',
        secondary: '#2C5282',
        accent: '#3182CE',
        background: {
            default: '#FFFFFF',
            alternate: '#F7FAFC',
            section: '#1E3A5F'
        },
        text: {
            primary: '#1A202C',
            secondary: '#4A5568',
            inverse: '#FFFFFF'
        },
        semantic: {
            success: '#38A169',
            warning: '#D69E2E',
            danger: '#E53E3E',
            info: '#3182CE'
        },
        decorative: {
            border: '#E2E8F0',
            divider: '#CBD5E0'
        }
    },
    typography: {
        fonts: {
            heading: 'Microsoft YaHei',
            body: 'Microsoft YaHei',
            mono: 'Consolas'
        },
        scale: {
            cover_title: 44,
            section_title: 36,
            slide_title: 24,
            subtitle: 20,
            body: 18,
            caption: 14,
            footnote: 12
        },
        line_height: {
            tight: 1.2,
            normal: 1.5,
            loose: 1.8
        },
        weight: {
            normal: 400,
            medium: 500,
            bold: 700
        }
    },
    layout: {
        canvas: {
            aspect_ratio: '16:9'
        },
        margins: {
            top: 0.5,
            right: 0.5,
            bottom: 0.5,
            left: 0.5
        },
        spacing: {
            xs: 0.1,
            sm: 0.2,
            md: 0.4,
            lg: 0.6,
            xl: 1.0
        }
    },
    components: {
        accent_bar: {
            height: 0.15,
            position: 'top'
        },
        card: {
            border_radius: 0.05,
            shadow: false,
            border_width: 1
        },
        table: {
            header_style: 'filled',
            stripe: true
        },
        bullets: {
            style: 'disc',
            indent: 0.3,
            spacing: 0.15
        },
        quote: {
            style: 'large-mark',
            mark_size: 120
        }
    }
};

class ThemeLoader {
    constructor() {
        this.cache = new Map();
    }

    /**
     * 加载主题
     * @param {string} themeName - 主题名称
     * @returns {Object} - 完整的主题配置
     */
    load(themeName) {
        // 检查缓存
        if (this.cache.has(themeName)) {
            return this.cache.get(themeName);
        }

        // 尝试加载主题文件
        let themeConfig = this.loadThemeFile(themeName);

        // 如果有 extends，先加载父主题
        if (themeConfig?.extends) {
            const parentTheme = this.load(themeConfig.extends);
            themeConfig = this.deepMerge(parentTheme, themeConfig);
        } else {
            // 与基础主题合并
            themeConfig = this.deepMerge(BASE_THEME, themeConfig || {});
        }

        // 缓存
        this.cache.set(themeName, themeConfig);
        return themeConfig;
    }

    /**
     * 加载主题文件
     */
    loadThemeFile(themeName) {
        // 可能的文件路径
        const possiblePaths = [
            path.join(THEMES_DIR, `${themeName}.yaml`),
            path.join(THEMES_DIR, `${themeName}.yml`),
            path.join(THEMES_DIR, 'custom', `${themeName}.yaml`),
            path.join(THEMES_DIR, 'custom', `${themeName}.yml`)
        ];

        for (const filePath of possiblePaths) {
            if (fs.existsSync(filePath)) {
                try {
                    const content = fs.readFileSync(filePath, 'utf8');
                    return yaml.parse(content);
                } catch (e) {
                    console.warn(`Failed to parse theme file ${filePath}: ${e.message}`);
                }
            }
        }

        // 如果是预置主题名，返回内置配置
        const builtinThemes = {
            'corporate-light': this.getCorporateLightTheme(),
            'nano-banana-pro': this.getNanaBananaProTheme()
        };

        return builtinThemes[themeName] || null;
    }

    /**
     * Corporate Light 内置主题
     */
    getCorporateLightTheme() {
        return {
            theme: {
                name: 'corporate-light',
                display_name: 'Corporate Light',
                base: 'light',
                mood: 'professional'
            },
            colors: {
                primary: '#1E3A5F',
                secondary: '#2C5282',
                accent: '#3182CE',
                background: {
                    default: '#FFFFFF',
                    alternate: '#F7FAFC',
                    section: '#1E3A5F'
                },
                text: {
                    primary: '#1A202C',
                    secondary: '#4A5568',
                    inverse: '#FFFFFF'
                },
                semantic: {
                    success: '#38A169',
                    warning: '#D69E2E',
                    danger: '#E53E3E',
                    info: '#3182CE'
                },
                decorative: {
                    border: '#E2E8F0',
                    divider: '#CBD5E0'
                }
            }
        };
    }

    /**
     * Nano Banana Pro 内置主题
     */
    getNanaBananaProTheme() {
        return {
            theme: {
                name: 'nano-banana-pro',
                display_name: 'Nano Banana Pro',
                base: 'dark',
                mood: 'bold'
            },
            colors: {
                primary: '#F4C430',
                secondary: '#00D9C0',
                accent: '#F4C430',
                background: {
                    default: '#1C2833',
                    alternate: '#232F3E',
                    section: '#1C2833'
                },
                text: {
                    primary: '#FFFFFF',
                    secondary: '#AAB7B8',
                    inverse: '#1C2833'
                },
                semantic: {
                    success: '#27AE60',
                    warning: '#F39C12',
                    danger: '#E74C3C',
                    info: '#3498DB'
                },
                decorative: {
                    border: '#2C3E50',
                    divider: '#34495E'
                }
            },
            typography: {
                scale: {
                    cover_title: 48,
                    section_title: 40,
                    slide_title: 28,
                    subtitle: 22,
                    body: 18,
                    caption: 14,
                    footnote: 12
                }
            },
            components: {
                accent_bar: {
                    height: 0.1,
                    position: 'top'
                },
                card: {
                    border_radius: 0.1,
                    shadow: true,
                    border_width: 0
                },
                bullets: {
                    style: 'arrow',
                    indent: 0.4,
                    spacing: 0.2
                },
                quote: {
                    style: 'bar-left',
                    mark_size: 100
                }
            }
        };
    }

    /**
     * 深度合并对象
     */
    deepMerge(target, source) {
        const result = { ...target };

        for (const key of Object.keys(source)) {
            if (key === 'extends') continue; // 跳过 extends 字段

            if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
                result[key] = this.deepMerge(target[key] || {}, source[key]);
            } else {
                result[key] = source[key];
            }
        }

        return result;
    }

    /**
     * 获取可用主题列表
     */
    listThemes() {
        const themes = ['corporate-light', 'nano-banana-pro'];

        // 扫描 themes 目录
        if (fs.existsSync(THEMES_DIR)) {
            const files = fs.readdirSync(THEMES_DIR);
            for (const file of files) {
                if (file.endsWith('.yaml') || file.endsWith('.yml')) {
                    const name = file.replace(/\.(yaml|yml)$/, '');
                    if (!themes.includes(name)) {
                        themes.push(name);
                    }
                }
            }
        }

        // 扫描 custom 目录
        const customDir = path.join(THEMES_DIR, 'custom');
        if (fs.existsSync(customDir)) {
            const files = fs.readdirSync(customDir);
            for (const file of files) {
                if (file.endsWith('.yaml') || file.endsWith('.yml')) {
                    const name = file.replace(/\.(yaml|yml)$/, '');
                    if (!themes.includes(name)) {
                        themes.push(name);
                    }
                }
            }
        }

        return themes;
    }

    /**
     * 清除缓存
     */
    clearCache() {
        this.cache.clear();
    }
}

// 单例
const loader = new ThemeLoader();

module.exports = {
    ThemeLoader,
    loadTheme: (name) => loader.load(name),
    listThemes: () => loader.listThemes(),
    BASE_THEME
};
