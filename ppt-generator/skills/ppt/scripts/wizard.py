#!/usr/bin/env python3
"""
Interactive Wizard - PPT 生成交互式向导

检测缺失信息并引导用户输入：
- 文档目录
- 演示标题
- 目标时长
- 受众类型
- 演示场合
- 账号能力（deep-research, nano-banana-image）
"""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml


# ============================================================
# Capabilities Checker - 能力检测器
# ============================================================

@dataclass
class Capabilities:
    """用户能力配置"""
    deep_research: bool = False      # 有 ChatGPT Plus
    image_generation: bool = False   # 有 Gemini API
    chatgpt_logged_in: bool = False
    gemini_api_key_set: bool = False

    # Skill 路径
    deep_research_path: Optional[Path] = None
    nano_banana_path: Optional[Path] = None


class CapabilitiesChecker:
    """能力检测和初始化"""

    # Skill 相对路径（从 ppt-generator 出发）
    SKILL_PATHS = {
        'deep_research': [
            Path('../openai-deep-research'),
            Path('../../openai-deep-research'),
            Path('/home/david/prj/origin-task/openai-deep-research'),
        ],
        'nano_banana': [
            Path('../nano-banana-image'),
            Path('../../nano-banana-image'),
            Path('/home/david/prj/origin-task/nano-banana-image'),
        ],
    }

    def __init__(self, work_dir: Path = None, config_path: Path = None):
        self.work_dir = Path(work_dir) if work_dir else Path('.')
        self.config_path = config_path or (self.work_dir / '.pptrc.yaml')
        self.capabilities = Capabilities()

    def check_existing_config(self) -> bool:
        """检查是否已有配置文件"""
        if self.config_path.exists():
            try:
                config = yaml.safe_load(self.config_path.read_text(encoding='utf-8'))
                if caps := config.get('capabilities', {}):
                    self.capabilities.deep_research = caps.get('deep_research', False)
                    self.capabilities.image_generation = caps.get('image_generation', False)
                if auth := config.get('auth', {}):
                    self.capabilities.chatgpt_logged_in = auth.get('chatgpt_logged_in', False)
                    self.capabilities.gemini_api_key_set = auth.get('gemini_api_key_set', False)
                return True
            except Exception:
                pass
        return False

    def detect_skills(self) -> Dict[str, Optional[Path]]:
        """检测可用的 skill 路径"""
        result = {}

        for skill_name, paths in self.SKILL_PATHS.items():
            for path in paths:
                # 处理相对路径
                if not path.is_absolute():
                    full_path = (self.work_dir / path).resolve()
                else:
                    full_path = path

                if full_path.exists() and full_path.is_dir():
                    result[skill_name] = full_path
                    break
            else:
                result[skill_name] = None

        # 更新 capabilities
        if result.get('deep_research'):
            self.capabilities.deep_research_path = result['deep_research']
        if result.get('nano_banana'):
            self.capabilities.nano_banana_path = result['nano_banana']

        return result

    def check_gemini_api_key(self) -> bool:
        """检查 Gemini API Key 是否设置"""
        return bool(os.environ.get('GEMINI_API_KEY'))

    def save_config(self):
        """保存能力配置到 .pptrc.yaml"""
        config = {}

        # 读取现有配置
        if self.config_path.exists():
            try:
                config = yaml.safe_load(self.config_path.read_text(encoding='utf-8')) or {}
            except Exception:
                pass

        # 更新 capabilities
        config['capabilities'] = {
            'deep_research': self.capabilities.deep_research,
            'image_generation': self.capabilities.image_generation,
        }

        config['auth'] = {
            'chatgpt_logged_in': self.capabilities.chatgpt_logged_in,
            'gemini_api_key_set': self.capabilities.gemini_api_key_set,
        }

        # 保存 skill 路径
        config['skill_paths'] = {}
        if self.capabilities.deep_research_path:
            config['skill_paths']['deep_research'] = str(self.capabilities.deep_research_path)
        if self.capabilities.nano_banana_path:
            config['skill_paths']['nano_banana'] = str(self.capabilities.nano_banana_path)

        # 写入文件
        self.config_path.write_text(
            yaml.dump(config, default_flow_style=False, allow_unicode=True),
            encoding='utf-8'
        )

    def print_status(self):
        """打印能力状态"""
        print("\n" + "=" * 55)
        print("  能力检测结果")
        print("=" * 55)

        # Deep Research
        if self.capabilities.deep_research_path:
            status = "✓ 可用" if self.capabilities.deep_research else "○ 未启用"
            print(f"  Deep Research: {status}")
            print(f"    路径: {self.capabilities.deep_research_path}")
            if self.capabilities.deep_research:
                logged_in = "✓ 已登录" if self.capabilities.chatgpt_logged_in else "○ 需要登录"
                print(f"    ChatGPT: {logged_in}")
        else:
            print("  Deep Research: ✗ 未找到 skill")

        # Nano Banana
        if self.capabilities.nano_banana_path:
            status = "✓ 可用" if self.capabilities.image_generation else "○ 未启用"
            print(f"  Nano Banana Image: {status}")
            print(f"    路径: {self.capabilities.nano_banana_path}")
            if self.capabilities.image_generation:
                api_key = "✓ 已设置" if self.capabilities.gemini_api_key_set else "○ 需要设置"
                print(f"    GEMINI_API_KEY: {api_key}")
        else:
            print("  Nano Banana Image: ✗ 未找到 skill")

        print("=" * 55)


# ============================================================
# Wizard Context
# ============================================================

@dataclass
class WizardContext:
    """Wizard 上下文状态"""
    # 检测到的信息
    has_title: bool = False
    has_duration: bool = False
    has_audience: bool = False
    has_documents: bool = False
    has_skeleton: bool = False

    # 检测到的值
    detected_title: str = ""
    detected_duration: int = 0
    detected_docs_dir: Optional[Path] = None
    detected_skeleton: Optional[Path] = None

    # 文档统计
    doc_stats: Dict[str, Any] = field(default_factory=dict)

    # 缺失信息
    missing_fields: List[str] = field(default_factory=list)


class InteractiveWizard:
    """PPT 生成交互式向导"""

    # 必填字段
    REQUIRED_FIELDS = ['title', 'duration', 'documents']

    # 受众选项
    AUDIENCE_OPTIONS = {
        '1': ('executives', '高管决策层'),
        '2': ('managers', '中层管理'),
        '3': ('professionals', '专业人士'),
        '4': ('general', '通用受众'),
    }

    # 场合选项
    OCCASION_OPTIONS = {
        '1': ('training', '培训'),
        '2': ('pitch', '汇报/提案'),
        '3': ('conference', '会议演讲'),
        '4': ('workshop', '工作坊'),
    }

    # 主题选项
    THEME_OPTIONS = {
        '1': ('corporate-light', '企业浅色（正式场合）'),
        '2': ('nano-banana-pro', 'Nano Banana Pro（创意/科技）'),
    }

    def __init__(self, work_dir: Path = None, config: Dict = None):
        self.work_dir = Path(work_dir) if work_dir else Path('.')
        self.config = config or {}
        self.context = WizardContext()
        self.capabilities_checker = CapabilitiesChecker(self.work_dir)
        self.capabilities = self.capabilities_checker.capabilities

    def detect_context(self) -> WizardContext:
        """自动检测当前目录的上下文信息"""
        # 1. 检测文档目录
        self._detect_documents()

        # 2. 检测已有骨架
        self._detect_skeleton()

        # 3. 从配置文件获取默认值
        self._apply_config_defaults()

        # 4. 计算缺失字段
        self._calculate_missing_fields()

        return self.context

    def _detect_documents(self):
        """检测文档目录"""
        doc_dir_names = ['docs', 'documents', 'content', '文档', 'materials']

        for doc_dir_name in doc_dir_names:
            doc_dir = self.work_dir / doc_dir_name
            if doc_dir.exists() and doc_dir.is_dir():
                docs = self._scan_documents(doc_dir)
                if docs:
                    self.context.has_documents = True
                    self.context.detected_docs_dir = doc_dir
                    self.context.doc_stats = {
                        'count': len(docs),
                        'total_chars': sum(f.stat().st_size for f in docs),
                        'files': [f.name for f in docs[:10]],  # 前10个文件名
                    }
                    return

        # 检查当前目录是否有文档
        docs = self._scan_documents(self.work_dir)
        if docs:
            self.context.has_documents = True
            self.context.detected_docs_dir = self.work_dir
            self.context.doc_stats = {
                'count': len(docs),
                'total_chars': sum(f.stat().st_size for f in docs),
                'files': [f.name for f in docs[:10]],
            }

    def _scan_documents(self, directory: Path) -> List[Path]:
        """扫描目录中的文档文件"""
        extensions = ['.md', '.txt', '.docx', '.pdf']
        docs = []
        for ext in extensions:
            docs.extend(directory.glob(f'*{ext}'))
        # 排除 README 和配置文件
        docs = [d for d in docs if not d.name.lower().startswith(('readme', '_', '.'))]
        return docs

    def _detect_skeleton(self):
        """检测已有骨架"""
        skeleton_names = ['skeleton.yaml', 'skeleton.yml', 'outline.yaml']

        for name in skeleton_names:
            skeleton_path = self.work_dir / name
            if skeleton_path.exists():
                self.context.has_skeleton = True
                self.context.detected_skeleton = skeleton_path

                # 从骨架读取标题/时长
                try:
                    skeleton = yaml.safe_load(skeleton_path.read_text(encoding='utf-8'))
                    if meta := skeleton.get('meta', {}):
                        if title := meta.get('title'):
                            self.context.has_title = True
                            self.context.detected_title = title
                    if presentation := skeleton.get('presentation', {}):
                        if duration := presentation.get('duration'):
                            self.context.has_duration = True
                            self.context.detected_duration = duration
                except Exception:
                    pass
                return

    def _apply_config_defaults(self):
        """从配置文件应用默认值"""
        if defaults := self.config.get('defaults', {}):
            if not self.context.has_duration and 'duration' in defaults:
                self.context.detected_duration = defaults['duration']

    def _calculate_missing_fields(self):
        """计算缺失字段"""
        self.context.missing_fields = []

        if not self.context.has_title:
            self.context.missing_fields.append('title')
        if not self.context.has_duration and not self.context.detected_duration:
            self.context.missing_fields.append('duration')
        if not self.context.has_documents:
            self.context.missing_fields.append('documents')

    def needs_interaction(self) -> bool:
        """检查是否需要交互式输入"""
        return len(self.context.missing_fields) > 0

    def check_capabilities(self, force_recheck: bool = False) -> Capabilities:
        """检查并确认用户能力"""
        # 检查是否已有配置
        has_config = self.capabilities_checker.check_existing_config()

        if has_config and not force_recheck:
            # 已有配置，跳过确认
            self.capabilities_checker.detect_skills()
            return self.capabilities

        # 检测可用 skill
        self.capabilities_checker.detect_skills()

        # 需要用户确认
        return self._prompt_capabilities()

    def _prompt_capabilities(self) -> Capabilities:
        """交互式确认用户能力"""
        print("\n" + "=" * 55)
        print("  首次使用配置")
        print("=" * 55)
        print("\n为了提供最佳体验，请确认您的账号情况：\n")

        # 1. ChatGPT Plus
        if self.capabilities.deep_research_path:
            print("检测到 deep-research skill。")
            print("  → 需要 ChatGPT Plus/Pro 账号才能使用深度研究功能。")
            has_plus = input("\n您是否有 ChatGPT Plus/Pro 账号？[y/N]: ").strip().lower()
            if has_plus in ('y', 'yes', '是'):
                self.capabilities.deep_research = True
                print("  → 请确保已在浏览器中登录 chat.openai.com")
                logged_in = input("  已登录 ChatGPT？[y/N]: ").strip().lower()
                self.capabilities.chatgpt_logged_in = logged_in in ('y', 'yes', '是')
            else:
                self.capabilities.deep_research = False
                print("  → 将使用 WebSearch 作为备选（研究质量较低）")
        else:
            print("未检测到 deep-research skill。")
            print("  → 将使用 WebSearch（研究质量较低）")
            self.capabilities.deep_research = False

        # 2. Gemini API
        print()
        if self.capabilities.nano_banana_path:
            print("检测到 nano-banana-image skill。")
            print("  → 需要 Gemini API Key 才能生成配图。")
            has_gemini = input("\n您是否有 Gemini API Key？[y/N]: ").strip().lower()
            if has_gemini in ('y', 'yes', '是'):
                self.capabilities.image_generation = True

                # 检查环境变量
                if self.capabilities_checker.check_gemini_api_key():
                    self.capabilities.gemini_api_key_set = True
                    print("  ✓ GEMINI_API_KEY 已设置")
                else:
                    print("  → 请设置环境变量: export GEMINI_API_KEY='your-key'")
                    api_key = input("  或直接输入 API Key（留空跳过）: ").strip()
                    if api_key:
                        os.environ['GEMINI_API_KEY'] = api_key
                        self.capabilities.gemini_api_key_set = True
                        print("  ✓ API Key 已临时设置（本次会话有效）")
                    else:
                        self.capabilities.gemini_api_key_set = False
                        print("  → 将跳过配图生成")
            else:
                self.capabilities.image_generation = False
                print("  → 将跳过配图生成")
        else:
            print("未检测到 nano-banana-image skill。")
            print("  → 将跳过配图生成")
            self.capabilities.image_generation = False

        # 保存配置
        self.capabilities_checker.save_config()
        print("\n配置已保存到 .pptrc.yaml")

        # 显示状态
        self.capabilities_checker.print_status()

        return self.capabilities

    def run_interactive(self) -> Dict[str, Any]:
        """运行交互式向导，返回收集的参数"""
        result = {
            'title': self.context.detected_title,
            'duration': self.context.detected_duration or 30,
            'audience': 'professionals',
            'occasion': 'conference',
            'theme': 'corporate-light',
            'context_dir': str(self.context.detected_docs_dir) if self.context.detected_docs_dir else None,
            'skeleton_path': str(self.context.detected_skeleton) if self.context.detected_skeleton else None,
        }

        # 首先检查能力配置
        self.check_capabilities()

        # 将能力信息添加到结果
        result['capabilities'] = {
            'deep_research': self.capabilities.deep_research,
            'image_generation': self.capabilities.image_generation,
        }

        self._print_header()
        self._print_detected_context()

        # 如果有骨架，询问是否从骨架继续
        if self.context.has_skeleton:
            choice = self._prompt_skeleton_choice()
            if choice == 'continue':
                result['start_stage'] = 'enrich'
                return result
            elif choice == 'restart':
                result['skeleton_path'] = None

        # 提示用户缺失信息
        if 'documents' in self.context.missing_fields:
            doc_path = self._prompt_documents()
            if doc_path:
                result['context_dir'] = doc_path

        if 'title' in self.context.missing_fields:
            result['title'] = self._prompt_title()

        if 'duration' in self.context.missing_fields:
            result['duration'] = self._prompt_duration()

        # 可选信息
        result['audience'] = self._prompt_audience()
        result['occasion'] = self._prompt_occasion()
        result['theme'] = self._prompt_theme()

        # 确认摘要
        self._print_summary(result)

        return result

    def _print_header(self):
        """打印向导头部"""
        print("\n" + "=" * 55)
        print("  PPT 生成向导")
        print("=" * 55)

    def _print_detected_context(self):
        """打印检测到的上下文"""
        print("\n检测到的上下文:")

        if self.context.has_documents:
            stats = self.context.doc_stats
            size_kb = stats.get('total_chars', 0) / 1024
            print(f"  - 文档目录: {self.context.detected_docs_dir}")
            print(f"  - 文档数量: {stats.get('count', 0)} 个 ({size_kb:.1f} KB)")
            if files := stats.get('files', []):
                print(f"  - 包含: {', '.join(files[:3])}{'...' if len(files) > 3 else ''}")

        if self.context.has_skeleton:
            print(f"  - 已有骨架: {self.context.detected_skeleton}")

        if self.context.has_title:
            print(f"  - 标题: {self.context.detected_title}")

        if self.context.detected_duration:
            print(f"  - 时长: {self.context.detected_duration} 分钟")

        if not any([self.context.has_documents, self.context.has_skeleton]):
            print("  (未检测到相关文件)")

        if self.context.missing_fields:
            print(f"\n缺少信息: {', '.join(self.context.missing_fields)}")

    def _prompt_skeleton_choice(self) -> str:
        """询问是否从骨架继续"""
        print("\n检测到已有骨架文件。")
        print("  1. 从骨架继续（跳过 outline 阶段）")
        print("  2. 重新开始（覆盖骨架）")
        choice = input("选择 [1]: ").strip() or "1"
        return 'continue' if choice == '1' else 'restart'

    def _prompt_documents(self) -> Optional[str]:
        """提示用户放置文档"""
        print("\n" + "-" * 40)
        print("未检测到参考文档。")
        print("\n请将参考文档放入以下目录之一：")
        print(f"  - {self.work_dir / 'docs/'}")
        print(f"  - {self.work_dir / 'documents/'}")
        print("  - 或当前目录")
        print("\n支持的格式: .md, .txt, .docx, .pdf")
        print("-" * 40)

        doc_path = input("\n或输入文档目录路径 [跳过]: ").strip()
        if doc_path:
            path = Path(doc_path)
            if path.exists() and path.is_dir():
                return str(path)
            else:
                print(f"  警告: 目录不存在 - {doc_path}")
        return None

    def _prompt_title(self) -> str:
        """提示输入标题"""
        default = self.context.detected_title or "Untitled Presentation"
        title = input(f"\n演示标题 [{default}]: ").strip()
        return title or default

    def _prompt_duration(self) -> int:
        """提示输入时长"""
        default = self.context.detected_duration or 30
        duration_str = input(f"\n目标时长(分钟) [{default}]: ").strip()
        try:
            return int(duration_str) if duration_str else default
        except ValueError:
            print("  无效输入，使用默认值")
            return default

    def _prompt_audience(self) -> str:
        """提示选择受众"""
        print("\n受众类型:")
        for k, (_, display) in self.AUDIENCE_OPTIONS.items():
            print(f"  {k}. {display}")
        choice = input("选择 [3]: ").strip() or "3"
        return self.AUDIENCE_OPTIONS.get(choice, self.AUDIENCE_OPTIONS['3'])[0]

    def _prompt_occasion(self) -> str:
        """提示选择场合"""
        print("\n演示场合:")
        for k, (_, display) in self.OCCASION_OPTIONS.items():
            print(f"  {k}. {display}")
        choice = input("选择 [3]: ").strip() or "3"
        return self.OCCASION_OPTIONS.get(choice, self.OCCASION_OPTIONS['3'])[0]

    def _prompt_theme(self) -> str:
        """提示选择主题"""
        print("\n视觉主题:")
        for k, (_, display) in self.THEME_OPTIONS.items():
            print(f"  {k}. {display}")
        choice = input("选择 [1]: ").strip() or "1"
        return self.THEME_OPTIONS.get(choice, self.THEME_OPTIONS['1'])[0]

    def _print_summary(self, params: Dict):
        """打印参数摘要"""
        print("\n" + "=" * 55)
        print("  生成参数确认")
        print("=" * 55)
        print(f"  标题: {params.get('title', 'N/A')}")
        print(f"  时长: {params.get('duration', 30)} 分钟")
        print(f"  受众: {params.get('audience', 'professionals')}")
        print(f"  场合: {params.get('occasion', 'conference')}")
        print(f"  主题: {params.get('theme', 'corporate-light')}")
        if params.get('context_dir'):
            print(f"  文档: {params['context_dir']}")
        if params.get('skeleton_path'):
            print(f"  骨架: {params['skeleton_path']}")
        print("=" * 55)


def run_wizard(work_dir: Path = None, config: Dict = None) -> Optional[Dict]:
    """便捷函数：运行向导并返回参数"""
    wizard = InteractiveWizard(work_dir, config)
    wizard.detect_context()

    if wizard.needs_interaction():
        return wizard.run_interactive()
    else:
        # 不需要交互，返回检测到的参数
        return {
            'title': wizard.context.detected_title,
            'duration': wizard.context.detected_duration or 30,
            'context_dir': str(wizard.context.detected_docs_dir) if wizard.context.detected_docs_dir else None,
            'skeleton_path': str(wizard.context.detected_skeleton) if wizard.context.detected_skeleton else None,
        }


# CLI 测试
if __name__ == '__main__':
    import json

    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    params = run_wizard(work_dir)

    if params:
        print("\n返回参数:")
        print(json.dumps(params, ensure_ascii=False, indent=2))
