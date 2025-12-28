import openai
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from config import Config

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatGPTIntegration:
    """ChatGPT集成类"""
    
    def __init__(self):
        self.client = None
        self.config = Config()
        self.conversation_history = []
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端"""
        try:
            if self.config.OPENAI_API_KEY:
                self.client = openai.OpenAI(api_key=self.config.OPENAI_API_KEY)
                logger.info("ChatGPT客户端初始化成功")
            else:
                logger.warning("未找到OpenAI API密钥，ChatGPT功能将不可用")
        except Exception as e:
            logger.error(f"ChatGPT客户端初始化失败: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查ChatGPT是否可用"""
        return self.client is not None and self.config.USE_CHATGPT
    
    def get_response(self, user_message: str, video_context: str = "", 
                    emotion: str = "平静", context_info: Dict = None) -> str:
        """获取ChatGPT回复"""
        if not self.is_available():
            raise Exception("ChatGPT不可用")
        
        if context_info is None:
            context_info = {}
        
        try:
            # 构建系统提示词
            system_prompt = self._build_system_prompt(emotion, context_info, video_context)
            
            # 构建消息历史
            messages = self._build_messages(system_prompt, user_message, video_context)
            
            # 调用ChatGPT API
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=messages,
                max_tokens=self.config.OPENAI_MAX_TOKENS,
                temperature=self.config.OPENAI_TEMPERATURE,
                stream=False
            )
            
            # 提取回复内容
            ai_response = response.choices[0].message.content.strip()
            
            # 记录对话历史
            self._record_conversation(user_message, ai_response, emotion, context_info)
            
            return ai_response
            
        except Exception as e:
            logger.error(f"ChatGPT API调用失败: {e}")
            raise Exception(f"ChatGPT服务暂时不可用: {str(e)}")
    
    def _build_system_prompt(self, emotion: str, context_info: Dict, video_context: str) -> str:
        """构建系统提示词"""
        base_prompt = self.config.FENCING_SYSTEM_PROMPT
        
        # 添加情感上下文
        emotion_context = self._get_emotion_context(emotion)
        
        # 添加视频上下文
        video_context_prompt = ""
        if video_context:
            video_context_prompt = f"\n\n当前用户正在观看视频内容：{video_context}。请结合视频内容提供相关建议和分析。"
        
        # 添加对话历史上下文
        history_context = ""
        if len(self.conversation_history) > 0:
            history_context = f"\n\n对话历史：用户已经进行了{len(self.conversation_history)}轮对话，请保持对话的连贯性。"
        
        return f"{base_prompt}\n\n{emotion_context}{video_context_prompt}{history_context}"
    
    def _get_emotion_context(self, emotion: str) -> str:
        """根据情感获取上下文提示"""
        emotion_contexts = {
            "兴奋": "用户表现出兴奋和热情，请用积极、鼓励的语气回复，可以分享一些激动人心的击剑故事或技巧。",
            "困惑": "用户可能对击剑知识感到困惑，请用简单易懂的语言详细解释，并提供具体的例子。",
            "好奇": "用户表现出好奇心，请提供有趣、详细的击剑知识，可以分享一些有趣的历史或技巧。",
            "焦虑": "用户可能感到焦虑或担心，请提供鼓励和支持，用温和、耐心的语气回复。",
            "感激": "用户表示感谢，请用友好、谦逊的语气回复，继续提供帮助。",
            "沮丧": "用户可能感到沮丧，请提供鼓励和实用的建议，帮助用户重新燃起兴趣。",
            "平静": "用户处于平静状态，请用专业、友好的语气提供信息和建议。"
        }
        
        return emotion_contexts.get(emotion, emotion_contexts["平静"])
    
    def _build_messages(self, system_prompt: str, user_message: str, video_context: str) -> List[Dict]:
        """构建消息列表"""
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # 添加最近的对话历史（最多5轮）
        recent_history = self.conversation_history[-10:]  # 最近5轮对话
        for entry in recent_history:
            if "user" in entry:
                messages.append({"role": "user", "content": entry["user"]})
            if "ai" in entry:
                messages.append({"role": "assistant", "content": entry["ai"]})
        
        # 添加当前用户消息
        current_message = user_message
        if video_context:
            current_message = f"[视频上下文: {video_context}] {user_message}"
        
        messages.append({"role": "user", "content": current_message})
        
        return messages
    
    def _record_conversation(self, user_message: str, ai_response: str, 
                           emotion: str, context_info: Dict):
        """记录对话历史"""
        self.conversation_history.append({
            "user": user_message,
            "ai": ai_response,
            "emotion": emotion,
            "context_info": context_info,
            "timestamp": datetime.now().isoformat(),
            "source": "chatgpt"
        })
        
        # 限制历史记录长度
        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_history = []
    
    def analyze_video_content(self, video_url: str, current_time: int) -> str:
        """分析视频内容（ChatGPT版本）"""
        if not self.is_available():
            raise Exception("ChatGPT不可用")
        
        try:
            prompt = f"""
            请分析这个击剑视频内容：
            - 视频URL: {video_url}
            - 当前时间: {current_time}秒
            
            请从以下角度分析：
            1. 当前比赛阶段和节奏
            2. 运动员的技术表现
            3. 战术运用和策略
            4. 可能的改进建议
            
            请用专业但易懂的语言回复，适合击剑爱好者理解。
            """
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.config.FENCING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"视频分析失败: {e}")
            return "视频分析功能暂时不可用，请稍后再试。"
    
    def get_fencing_tips(self, user_level: str = "初学者") -> str:
        """获取击剑技巧建议"""
        if not self.is_available():
            raise Exception("ChatGPT不可用")
        
        try:
            prompt = f"""
            请为{user_level}提供击剑技巧建议：
            1. 基础动作练习
            2. 常见错误和纠正方法
            3. 训练计划建议
            4. 装备选择建议
            5. 心理素质培养
            
            请提供实用、具体的建议，适合{user_level}的学习需求。
            """
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.config.FENCING_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"技巧建议获取失败: {e}")
            return "技巧建议功能暂时不可用，请稍后再试。"
    
    def test_connection(self) -> bool:
        """测试ChatGPT连接"""
        try:
            if not self.is_available():
                return False
            
            response = self.client.chat.completions.create(
                model=self.config.OPENAI_MODEL,
                messages=[
                    {"role": "user", "content": "你好"}
                ],
                max_tokens=10
            )
            
            return response.choices[0].message.content is not None
            
        except Exception as e:
            logger.error(f"ChatGPT连接测试失败: {e}")
            return False

