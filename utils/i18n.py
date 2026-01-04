"""
国际化支持模块 - 支持中英文双语切换
"""
import json
import os
from typing import Dict

class I18n:
    """国际化类"""
    
    def __init__(self, default_language: str = 'zh_CN'):
        self.default_language = default_language
        self.current_language = default_language
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """加载翻译文件"""
        # 加载中文翻译
        zh_translations = self._load_language_file('zh_CN')
        # 加载英文翻译
        en_translations = self._load_language_file('en_US')
        
        self.translations = {
            'zh_CN': zh_translations,
            'en_US': en_translations
        }
    
    def _load_language_file(self, lang_code: str) -> Dict:
        """加载语言文件"""
        # 获取项目根目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        lang_file = os.path.join(project_root, 'locales', f'{lang_code}.json')
        
        try:
            if os.path.exists(lang_file):
                with open(lang_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Language file not found: {lang_file}")
        except Exception as e:
            print(f"Failed to load language file {lang_file}: {e}")
        
        return {}
    
    def set_language(self, lang_code: str):
        """设置当前语言"""
        if lang_code in self.translations:
            self.current_language = lang_code
        else:
            self.current_language = self.default_language
    
    def get_language(self) -> str:
        """获取当前语言"""
        return self.current_language
    
    def t(self, key: str, default: str = None, **kwargs) -> str:
        """翻译文本（支持嵌套键，如'app.title'）"""
        translation = self.translations.get(
            self.current_language, 
            self.translations.get(self.default_language, {})
        )
        
        # 支持嵌套键，如 'app.title'
        keys = key.split('.')
        value = translation
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                # 如果找不到，尝试使用默认值
                if default:
                    value = default
                else:
                    value = key
                break
        
        text = value if isinstance(value, str) else (default or key)
        
        # 支持参数替换
        if kwargs and isinstance(text, str):
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text
    
    def get_all_translations(self) -> Dict:
        """获取当前语言的所有翻译"""
        return self.translations.get(
            self.current_language,
            self.translations.get(self.default_language, {})
        )

# 全局i18n实例
i18n = I18n()

