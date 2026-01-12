#!/usr/bin/env python3
"""
PPT Generator Initializer - 首次使用初始化

检测用户能力并安装依赖 skill：
- ChatGPT Plus → deep-research skill
- Gemini API Key → nano-banana-image skill
"""

import os
import sys
import subprocess
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml


@dataclass
class Capabilities:
    """用户能力配置"""
    deep_research: bool = False
    ai_images: bool = False

    # 配置详情
    chatgpt_logged_in: bool = False
    gemini_api_key: str = ""

    # 安装状态
    deep_research_installed: bool = False
    nano_banana_installed: bool = False


@dataclass
class SkillInfo:
    """Skill 信息"""
    name: str
    relative_path: str  # 相对于 ppt-generator 的路径
    description: str
    requires: str  # 需要的能力


class PPTInitializer:
    """PPT 生成器初始化器"""

    # Skill 仓库结构（同一个 git 库）
    MARKETPLACE_SKILLS = {
        'deep-research': SkillInfo(
            name='openai-deep-research',
            relative_path='../openai-deep-research',
            description='深度研究 - 使用浏览器自动化进行多轮深度搜索',
            requires='ChatGPT Plus'
        ),
        'nano-banana-image': SkillInfo(
            name='nano-banana-image',
            relative_path='../nano-banana-image',
            description='AI 配图 - 使用 Gemini 生成专业配图',
            requires='Gemini API Key'
        ),
    }

    CONFIG_FILE = '.pptrc.yaml'

    def __init__(self, work_dir: Path = None):
        self.work_dir = Path(work_dir) if work_dir else Path('.')
        self.skill_base_dir = Path(__file__).parent.parent.parent.parent  # ppt-generator 父目录
        self.capabilities = Capabilities()
        self._config_path = self.work_dir / self.CONFIG_FILE

    def is_initialized(self) -> bool:
        """检查是否已完成初始化"""
        if not self._config_path.exists():
            return False

        try:
            config = yaml.safe_load(self._config_path.read_text(encoding='utf-8'))
            return config.get('initialized', False)
        except Exception:
            return False

    def load_capabilities(self) -> Capabilities:
        """从配置文件加载已保存的能力配置"""
        if not self._config_path.exists():
            return self.capabilities

        try:
            config = yaml.safe_load(self._config_path.read_text(encoding='utf-8'))
            caps = config.get('capabilities', {})

            self.capabilities.deep_research = caps.get('deep_research', False)
            self.capabilities.ai_images = caps.get('ai_images', False)
            self.capabilities.deep_research_installed = caps.get('deep_research_installed', False)
            self.capabilities.nano_banana_installed = caps.get('nano_banana_installed', False)

        except Exception:
            pass

        return self.capabilities

    def save_capabilities(self):
        """保存能力配置到文件"""
        config = {}

        # 如果配置文件存在，先读取
        if self._config_path.exists():
            try:
                config = yaml.safe_load(self._config_path.read_text(encoding='utf-8')) or {}
            except Exception:
                config = {}

        # 更新 capabilities 部分
        config['initialized'] = True
        config['capabilities'] = {
            'deep_research': self.capabilities.deep_research,
            'ai_images': self.capabilities.ai_images,
            'deep_research_installed': self.capabilities.deep_research_installed,
            'nano_banana_installed': self.capabilities.nano_banana_installed,
        }

        # 设置研究模式
        if 'research' not in config:
            config['research'] = {}
        config['research']['mode'] = 'browser' if self.capabilities.deep_research else 'websearch'

        # 设置图片配置
        if 'images' not in config:
            config['images'] = {}
        config['images']['enabled'] = self.capabilities.ai_images
        config['images']['generator'] = 'nano-banana-image' if self.capabilities.ai_images else 'none'

        # 写入文件
        self._config_path.write_text(
            yaml.dump(config, allow_unicode=True, default_flow_style=False),
            encoding='utf-8'
        )

    def check_skill_installed(self, skill_key: str) -> bool:
        """检查 skill 是否已安装"""
        skill_info = self.MARKETPLACE_SKILLS.get(skill_key)
        if not skill_info:
            return False

        skill_path = self.skill_base_dir / skill_info.relative_path
        return skill_path.exists()

    def install_skill(self, skill_key: str) -> Tuple[bool, str]:
        """安装 skill (从同一个 git 库)"""
        skill_info = self.MARKETPLACE_SKILLS.get(skill_key)
        if not skill_info:
            return False, f"未知的 skill: {skill_key}"

        skill_path = self.skill_base_dir / skill_info.relative_path

        # 检查是否已存在
        if skill_path.exists():
            return True, f"Skill 已存在: {skill_path}"

        # 检查源目录是否存在（同一个 git 库内）
        # 由于都在同一个仓库，实际上应该已经存在
        # 如果不存在，可能需要 git pull 或者 git clone

        return False, f"Skill 目录不存在: {skill_path}\n请确保已克隆完整的 origin-task 仓库"

    def check_gemini_api_key(self) -> Tuple[bool, str]:
        """检查 Gemini API Key"""
        # 检查环境变量
        api_key = os.environ.get('GEMINI_API_KEY', '')
        if api_key:
            return True, "已配置 (环境变量)"

        # 检查 .env 文件
        env_file = self.work_dir / '.env'
        if env_file.exists():
            content = env_file.read_text(encoding='utf-8')
            for line in content.split('\n'):
                if line.startswith('GEMINI_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    if key:
                        return True, "已配置 (.env 文件)"

        return False, "未配置"

    def get_initialization_questions(self) -> List[Dict]:
        """获取初始化问题（供 AI 使用 AskUserQuestion）"""
        return [
            {
                "question": "您是否有 ChatGPT Plus 或以上账号？(用于深度研究)",
                "header": "Deep Research",
                "multiSelect": False,
                "options": [
                    {
                        "label": "有 Plus 账号 (推荐)",
                        "description": "启用 deep-research，获得更深度、更可靠的数据分析"
                    },
                    {
                        "label": "没有",
                        "description": "使用基础 WebSearch，结果可能较浅"
                    }
                ]
            },
            {
                "question": "您是否有 Google Gemini API Key？(用于 AI 配图)",
                "header": "AI 配图",
                "multiSelect": False,
                "options": [
                    {
                        "label": "有 API Key (推荐)",
                        "description": "启用 nano-banana-image，为封面和章节页生成专业配图"
                    },
                    {
                        "label": "没有",
                        "description": "跳过配图，仅生成文字内容"
                    }
                ]
            }
        ]

    def process_user_answers(self, has_chatgpt_plus: bool, has_gemini_key: bool) -> Dict:
        """处理用户回答，执行初始化"""
        result = {
            'success': True,
            'messages': [],
            'next_steps': [],
        }

        self.capabilities.deep_research = has_chatgpt_plus
        self.capabilities.ai_images = has_gemini_key

        # 检查并安装 deep-research
        if has_chatgpt_plus:
            installed = self.check_skill_installed('deep-research')
            if installed:
                self.capabilities.deep_research_installed = True
                result['messages'].append("deep-research skill 已就绪")
                result['next_steps'].append(
                    "请在浏览器中登录 ChatGPT (chat.openai.com)，确保是 Plus 账号"
                )
            else:
                success, msg = self.install_skill('deep-research')
                if success:
                    self.capabilities.deep_research_installed = True
                    result['messages'].append("deep-research skill 安装成功")
                    result['next_steps'].append(
                        "请在浏览器中登录 ChatGPT (chat.openai.com)"
                    )
                else:
                    result['messages'].append(f"deep-research 安装失败: {msg}")
                    result['success'] = False

        # 检查并安装 nano-banana-image
        if has_gemini_key:
            installed = self.check_skill_installed('nano-banana-image')
            if installed:
                self.capabilities.nano_banana_installed = True
                result['messages'].append("nano-banana-image skill 已就绪")

                # 检查 API Key
                has_key, key_status = self.check_gemini_api_key()
                if has_key:
                    result['messages'].append(f"Gemini API Key: {key_status}")
                else:
                    result['next_steps'].append(
                        "请设置 Gemini API Key:\n"
                        "  export GEMINI_API_KEY=\"your-api-key\"\n"
                        "  或在 .env 文件中添加: GEMINI_API_KEY=your-api-key"
                    )
            else:
                success, msg = self.install_skill('nano-banana-image')
                if success:
                    self.capabilities.nano_banana_installed = True
                    result['messages'].append("nano-banana-image skill 安装成功")
                else:
                    result['messages'].append(f"nano-banana-image 安装失败: {msg}")
                    result['success'] = False

        # 保存配置
        self.save_capabilities()
        result['config_path'] = str(self._config_path)

        return result

    def get_status_report(self) -> str:
        """获取当前状态报告"""
        self.load_capabilities()

        lines = [
            "PPT Generator 能力状态:",
            "=" * 40,
            "",
            f"Deep Research: {'启用' if self.capabilities.deep_research else '禁用'}",
        ]

        if self.capabilities.deep_research:
            installed = "已安装" if self.capabilities.deep_research_installed else "未安装"
            lines.append(f"  - skill 状态: {installed}")
            lines.append(f"  - 研究模式: browser")
        else:
            lines.append(f"  - 研究模式: websearch (基础)")

        lines.append("")
        lines.append(f"AI 配图: {'启用' if self.capabilities.ai_images else '禁用'}")

        if self.capabilities.ai_images:
            installed = "已安装" if self.capabilities.nano_banana_installed else "未安装"
            lines.append(f"  - skill 状态: {installed}")
            has_key, key_status = self.check_gemini_api_key()
            lines.append(f"  - API Key: {key_status}")

        lines.append("")
        lines.append(f"配置文件: {self._config_path}")

        return "\n".join(lines)


def run_initialization(work_dir: Path = None) -> Dict:
    """运行初始化流程（CLI 模式）"""
    initializer = PPTInitializer(work_dir)

    if initializer.is_initialized():
        print("已完成初始化。")
        print(initializer.get_status_report())
        return {'already_initialized': True}

    print("\n" + "=" * 55)
    print("  PPT Generator 首次初始化")
    print("=" * 55)

    # 询问 ChatGPT Plus
    print("\n问题 1/2: 您是否有 ChatGPT Plus 或以上账号？")
    print("  (用于启用 deep-research 深度研究功能)")
    print("  1. 有 Plus 账号 [推荐]")
    print("  2. 没有")
    choice1 = input("选择 [1]: ").strip() or "1"
    has_chatgpt_plus = choice1 == "1"

    # 询问 Gemini API Key
    print("\n问题 2/2: 您是否有 Google Gemini API Key？")
    print("  (用于启用 nano-banana-image AI 配图功能)")
    print("  1. 有 API Key [推荐]")
    print("  2. 没有")
    choice2 = input("选择 [1]: ").strip() or "1"
    has_gemini_key = choice2 == "1"

    # 处理回答
    result = initializer.process_user_answers(has_chatgpt_plus, has_gemini_key)

    # 显示结果
    print("\n" + "-" * 40)
    print("初始化结果:")
    for msg in result['messages']:
        print(f"  {msg}")

    if result['next_steps']:
        print("\n后续步骤:")
        for i, step in enumerate(result['next_steps'], 1):
            print(f"  {i}. {step}")

    print("\n" + initializer.get_status_report())

    return result


# CLI 入口
if __name__ == '__main__':
    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')

    if len(sys.argv) > 2 and sys.argv[2] == '--status':
        initializer = PPTInitializer(work_dir)
        print(initializer.get_status_report())
    else:
        run_initialization(work_dir)
