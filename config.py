import os
from dotenv import load_dotenv

# 加载环境变量（如果.env文件存在且可读）
try:
    load_dotenv()
except (PermissionError, FileNotFoundError):
    # 如果无法读取.env文件，使用默认值
    pass

class Config:
    """应用配置类"""
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # DeepSeek配置
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_MODEL = os.getenv('DEEPSEEK_MODEL', 'deepseek-chat')
    DEEPSEEK_MAX_TOKENS = int(os.getenv('DEEPSEEK_MAX_TOKENS', '1000'))
    DEEPSEEK_TEMPERATURE = float(os.getenv('DEEPSEEK_TEMPERATURE', '0.7'))
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com/v1')
    
    # AI系统配置
    USE_DEEPSEEK = os.getenv('USE_DEEPSEEK', 'True').lower() == 'true'
    FALLBACK_TO_LOCAL = os.getenv('FALLBACK_TO_LOCAL', 'True').lower() == 'true'
    
    # 击剑AI专业提示词
    FENCING_SYSTEM_PROMPT = """你是一位专业的击剑AI专家，具有以下特点：

1. 专业知识：
   - 精通花剑、重剑、佩剑三个剑种
   - 了解击剑规则、技术、战术和历史
   - 熟悉国际击剑联合会(FIE)的规则和标准

2. 回复风格：
   - 专业但易懂，用简单语言解释复杂概念
   - 根据用户情感调整语气（兴奋、困惑、好奇等）
   - 提供实用的建议和技巧
   - 保持友好和鼓励的态度

3. 回复内容：
   - 优先回答击剑相关问题
   - 提供准确的技术分析和建议
   - 分享击剑历史和趣闻
   - 分析比赛和战术运用

4. 个性化：
   - 根据对话历史提供连贯的回复
   - 考虑用户的学习水平和兴趣
   - 适时提供鼓励和激励

请用中文回复，保持专业性和趣味性的平衡。"""

    # 快速问题模板
    QUICK_QUESTIONS = [
        "击剑的基本规则是什么？",
        "花剑、重剑、佩剑有什么区别？",
        "如何提高击剑技术？",
        "击剑的历史发展如何？",
        "击剑比赛如何计分？"
    ]
