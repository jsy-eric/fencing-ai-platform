import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional
from config import Config

class FencingAI:
    def __init__(self):
        self.config = Config()
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = []
        self.fencing_terms = self._load_fencing_terms()
        self.competition_contexts = self._load_competition_contexts()
        self.use_deepseek = self.config.USE_DEEPSEEK and bool(self.config.DEEPSEEK_API_KEY)
        self.fallback_to_local = self.config.FALLBACK_TO_LOCAL
        
    def _load_knowledge_base(self) -> Dict:
        """加载击剑知识库"""
        return {
            "剑种": {
                "花剑": {
                    "description": "花剑是击剑三个剑种之一，有效部位是躯干，使用剑尖刺击。",
                    "rules": ["有效部位：躯干", "武器：剑尖刺击", "重量：500克以下"],
                    "techniques": ["直刺", "转移刺", "击打刺", "格挡"],
                    "scoring": "击中有效部位得1分，先得15分者获胜"
                },
                "重剑": {
                    "description": "重剑是击剑三个剑种之一，全身都是有效部位，使用剑尖刺击。",
                    "rules": ["有效部位：全身", "武器：剑尖刺击", "重量：770克以下"],
                    "techniques": ["直刺", "转移刺", "击打刺", "格挡", "闪避"],
                    "scoring": "击中有效部位得1分，先得15分者获胜"
                },
                "佩剑": {
                    "description": "佩剑是击剑三个剑种之一，有效部位是上半身，使用剑尖刺击和剑刃劈砍。",
                    "rules": ["有效部位：上半身", "武器：剑尖刺击+剑刃劈砍", "重量：500克以下"],
                    "techniques": ["直刺", "转移刺", "击打刺", "劈砍", "格挡"],
                    "scoring": "击中有效部位得1分，先得15分者获胜"
                }
            },
            "规则": {
                "基本规则": "击剑比赛采用单败淘汰制，每局3分钟，先得15分者获胜。",
                "得分规则": "击中有效部位得1分，同时击中则双方各得1分。",
                "场地规则": "击剑场地长14米，宽1.5-2米，中央有中线。",
                "装备要求": "必须穿戴击剑服、面罩、手套等防护装备。",
                "裁判规则": "比赛由主裁判和边裁判共同执裁。"
            },
            "技术": {
                "基本动作": ["立正", "敬礼", "实战姿势", "前进", "后退", "冲刺"],
                "进攻技术": ["直刺", "转移刺", "击打刺", "复合进攻", "假动作"],
                "防守技术": ["格挡", "闪避", "后退", "反击", "距离控制"],
                "战术运用": ["距离控制", "时机把握", "节奏变化", "假动作", "心理战"]
            },
            "历史": {
                "起源": "击剑起源于欧洲，最初是贵族决斗的武器。",
                "发展": "从决斗武器发展为体育运动，19世纪末开始规范化。",
                "奥运会": "1896年第一届现代奥运会就包含击剑项目。",
                "中国": "中国击剑在1984年洛杉矶奥运会获得首枚金牌。",
                "现代": "现代击剑已成为奥运会正式比赛项目，分为个人和团体赛。"
            },
            "比赛": {
                "奥运会": "奥运会击剑比赛包括个人和团体赛，共10枚金牌。",
                "世锦赛": "世界击剑锦标赛每年举办一次，是最高水平的国际比赛。",
                "世界杯": "击剑世界杯系列赛全年举办，积分决定年终排名。",
                "洲际赛": "各大洲都有自己的击剑锦标赛。"
            },
            "训练": {
                "教练作用": "击剑教练对运动员的作用包括：1) 技术指导：教授正确的技术动作和战术运用；2) 训练计划：制定科学的训练计划，提高运动员体能和技术水平；3) 心理辅导：帮助运动员建立自信，应对比赛压力；4) 比赛策略：分析对手特点，制定针对性战术；5) 成长培养：关注运动员全面发展，培养良好的体育精神。",
                "训练方法": "击剑训练包括：基础技术训练、体能训练、战术训练、心理训练、实战训练等。训练要循序渐进，注重基本功，同时结合实战演练。",
                "运动员培养": "击剑运动员的培养是一个长期过程，需要从基础技术开始，逐步提高技术水平、战术意识和心理素质。教练要根据运动员的特点制定个性化培养方案。",
                "教练职责": "击剑教练的主要职责包括：技术教学、训练计划制定、比赛指导、心理辅导、运动员管理、团队建设等。优秀的教练不仅要懂技术，还要懂心理学和管理学。"
            },
            "角色": {
                "教练": "击剑教练是运动员成长道路上的重要引路人，负责技术指导、训练计划制定、比赛策略分析和心理辅导等工作。优秀的教练能够帮助运动员充分发挥潜力，在比赛中取得好成绩。",
                "运动员": "击剑运动员需要具备良好的身体素质、扎实的技术基础、敏锐的战术意识和强大的心理素质。通过系统训练和比赛磨练，不断提高自己的竞技水平。",
                "裁判": "击剑裁判负责判定比赛中的得分、犯规等情况，确保比赛公平公正进行。裁判需要熟悉击剑规则，具备敏锐的观察力和公正的判断力。"
            }
        }
    
    def _load_fencing_terms(self) -> List[str]:
        """加载击剑专业术语"""
        return [
            "花剑", "重剑", "佩剑", "进攻", "防守", "格挡", "闪避",
            "直刺", "转移刺", "击打刺", "复合进攻", "战术", "策略",
            "距离控制", "时机把握", "节奏变化", "假动作", "心理战",
            "立正", "敬礼", "实战姿势", "前进", "后退", "冲刺",
            "有效部位", "得分", "裁判", "场地", "装备", "规则"
        ]
    
    def _load_competition_contexts(self) -> List[str]:
        """加载比赛上下文"""
        return [
            "精彩进攻", "巧妙防守", "战术运用", "技术展示", "心理博弈",
            "关键时刻", "比分胶着", "优势领先", "绝地反击", "完美配合"
        ]
    
    def get_response(self, user_message: str, video_context: str = "") -> str:
        """获取AI回复"""
        # 记录对话历史
        self.conversation_history.append({
            "user": user_message,
            "timestamp": datetime.now().isoformat(),
            "video_context": video_context
        })
        
        # 分析用户意图
        intent = self._analyze_intent(user_message)
        
        # 优先尝试使用DeepSeek（如果可用）
        if self.use_deepseek:
            print(f"[DeepSeek] 尝试调用DeepSeek API...")
            try:
                response = self._get_deepseek_response(user_message, video_context)
                if response and len(response.strip()) > 0:
                    print(f"[DeepSeek] 成功获取回复，长度: {len(response)}")
                    # 记录AI回复
                    self.conversation_history.append({
                        "ai": response,
                        "timestamp": datetime.now().isoformat()
                    })
                    return response
                else:
                    print(f"[DeepSeek] 返回空响应，回退到本地知识库")
            except Exception as e:
                # DeepSeek调用失败，如果启用了回退，继续使用本地知识库
                print(f"[DeepSeek] 调用失败，使用本地知识库: {e}")
                if not self.fallback_to_local:
                    raise e
        else:
            print(f"[DeepSeek] DeepSeek未启用或未配置API密钥，使用本地知识库")
        
        # 根据意图生成回复（使用本地知识库）
        if intent == "训练询问":
            response = self._answer_training_question(user_message)
        elif intent == "角色询问":
            response = self._answer_role_question(user_message)
        elif intent == "规则询问":
            response = self._answer_rules_question(user_message)
        elif intent == "技术询问":
            response = self._answer_technique_question(user_message)
        elif intent == "历史询问":
            response = self._answer_history_question(user_message)
        elif intent == "比赛分析":
            response = self._analyze_competition(user_message, video_context)
        elif intent == "术语解释":
            response = self._explain_terminology(user_message)
        else:
            response = self._generate_general_response(user_message, video_context)
        
        # 记录AI回复
        self.conversation_history.append({
            "ai": response,
            "timestamp": datetime.now().isoformat()
        })
        
        return response
    
    def _analyze_intent(self, message: str) -> str:
        """分析用户意图"""
        message_lower = message.lower()
        
        # 角色询问：识别作用、职责、重要性等相关问题（优先检查，因为更具体）
        if any(word in message_lower for word in ["作用", "职责", "重要性", "角色", "功能"]):
            return "角色询问"
        # 训练询问：识别教练、训练、培养等相关问题
        elif any(word in message_lower for word in ["教练", "训练", "培养", "指导", "教学", "训练方法", "训练计划"]):
            return "训练询问"
        elif any(word in message_lower for word in ["规则", "得分", "场地", "装备", "裁判"]):
            return "规则询问"
        elif any(word in message_lower for word in ["技术", "动作", "进攻", "防守", "战术"]):
            return "技术询问"
        elif any(word in message_lower for word in ["历史", "起源", "发展", "奥运会"]):
            return "历史询问"
        elif any(word in message_lower for word in ["比赛", "分析", "精彩", "战术"]):
            return "比赛分析"
        elif any(word in message_lower for word in ["花剑", "重剑", "佩剑", "术语"]):
            return "术语解释"
        else:
            return "一般询问"
    
    def _answer_rules_question(self, question: str) -> str:
        """回答规则相关问题"""
        if "得分" in question:
            return "击剑比赛的得分规则是：击中有效部位得1分，同时击中则双方各得1分。先得15分者获胜，如果时间到比分相同则加时赛。"
        elif "场地" in question:
            return "击剑比赛场地长14米，宽1.5-2米，中央有中线。场地表面必须平整，不能有障碍物。"
        elif "装备" in question:
            return "击剑运动员必须穿戴完整的防护装备，包括击剑服、面罩、手套、护胸等。装备必须符合国际击剑联合会(FIE)的安全标准。"
        elif "裁判" in question:
            return "击剑比赛由主裁判和边裁判共同执裁。主裁判负责判定得分，边裁判协助观察。比赛过程中运动员必须服从裁判的判罚。"
        else:
            return "击剑比赛的基本规则是：采用单败淘汰制，每局3分钟，先得15分者获胜。比赛过程中必须遵守击剑礼仪和规则。"
    
    def _answer_technique_question(self, question: str) -> str:
        """回答技术相关问题"""
        if "进攻" in question:
            return "击剑的进攻技术包括直刺、转移刺、击打刺、复合进攻等。进攻时要把握时机，利用假动作迷惑对手，寻找破绽。"
        elif "防守" in question:
            return "防守技术包括格挡、闪避、后退、反击等。好的防守不仅要化解对手进攻，还要为反击创造机会。"
        elif "战术" in question:
            return "击剑战术包括距离控制、时机把握、节奏变化、假动作运用等。要根据对手特点制定相应战术，灵活调整。"
        else:
            return "击剑技术分为基本动作、进攻技术、防守技术和战术运用。基本功很重要，要在训练中不断磨练各种技术。"
    
    def _answer_history_question(self, question: str) -> str:
        """回答历史相关问题"""
        if "起源" in question:
            return "击剑起源于欧洲中世纪，最初是贵族决斗的武器。随着时代发展，逐渐演变为体育运动和奥运会项目。"
        elif "中国" in question:
            return "中国击剑起步较晚，但在1984年洛杉矶奥运会上，栾菊杰获得女子花剑金牌，这是中国击剑的首枚奥运金牌。"
        elif "奥运会" in question:
            return "击剑从1896年第一届现代奥运会就是正式比赛项目。现在包括个人和团体赛，共设10枚金牌。"
        else:
            return "击剑有着悠久的历史，从贵族决斗武器发展为现代体育运动。现代击剑强调技术、战术和心理素质的综合运用。"
    
    def _analyze_competition(self, question: str, video_context: str) -> str:
        """分析比赛内容"""
        if "精彩" in question or "漂亮" in question:
            return "从技术角度看，这个动作展现了运动员扎实的基本功和临场应变能力。进攻时机把握得很好，防守也很到位。"
        elif "战术" in question:
            return "这场比赛体现了高水平的战术运用。运动员能够根据对手特点调整策略，在关键时刻做出正确判断。"
        elif "心理" in question:
            return "击剑不仅是技术的较量，更是心理的博弈。运动员需要在压力下保持冷静，在关键时刻发挥出最佳水平。"
        else:
            return "这场比赛展现了击剑运动的魅力。运动员的技术、战术和心理素质都达到了很高水平，是一场精彩的比赛。"
    
    def _explain_terminology(self, question: str) -> str:
        """解释专业术语"""
        if "花剑" in question:
            return "花剑是击剑三个剑种之一，有效部位是躯干，使用剑尖刺击。花剑比赛强调技术和战术，被称为'击剑中的芭蕾'。"
        elif "重剑" in question:
            return "重剑是击剑三个剑种之一，全身都是有效部位，使用剑尖刺击。重剑比赛节奏相对较慢，更注重战术思考。"
        elif "佩剑" in question:
            return "佩剑是击剑三个剑种之一，有效部位是上半身，使用剑尖刺击和剑刃劈砍。佩剑比赛节奏最快，最具观赏性。"
        else:
            return "击剑有很多专业术语，比如进攻、防守、格挡、闪避等。这些术语反映了击剑运动的技术特点和战术要求。"
    
    def _answer_training_question(self, question: str) -> str:
        """回答训练相关问题"""
        question_lower = question.lower()
        
        if "教练" in question and ("作用" in question or "职责" in question or "重要性" in question):
            return self.knowledge_base.get("训练", {}).get("教练作用", 
                "击剑教练对运动员的作用非常重要，包括技术指导、训练计划制定、心理辅导、比赛策略分析和运动员培养等方面。")
        elif "训练方法" in question or "如何训练" in question:
            return self.knowledge_base.get("训练", {}).get("训练方法",
                "击剑训练包括基础技术训练、体能训练、战术训练、心理训练和实战训练等，要循序渐进，注重基本功。")
        elif "培养" in question or "运动员培养" in question:
            return self.knowledge_base.get("训练", {}).get("运动员培养",
                "击剑运动员的培养是一个长期过程，需要从基础技术开始，逐步提高技术水平、战术意识和心理素质。")
        elif "教练" in question:
            return self.knowledge_base.get("训练", {}).get("教练职责",
                "击剑教练的主要职责包括技术教学、训练计划制定、比赛指导、心理辅导和运动员管理等。")
        else:
            return "击剑训练是一个系统性的过程，包括技术、体能、战术和心理等多个方面。教练在这个过程中起着关键的指导作用，帮助运动员不断提高竞技水平。"
    
    def _answer_role_question(self, question: str) -> str:
        """回答角色相关问题"""
        question_lower = question.lower()
        
        if "教练" in question and "作用" in question:
            return self.knowledge_base.get("训练", {}).get("教练作用",
                "击剑教练对运动员的作用包括技术指导、训练计划制定、心理辅导、比赛策略分析和运动员培养等。")
        elif "教练" in question:
            return self.knowledge_base.get("角色", {}).get("教练",
                "击剑教练是运动员成长道路上的重要引路人，负责技术指导、训练计划制定、比赛策略分析和心理辅导等工作。")
        elif "运动员" in question:
            return self.knowledge_base.get("角色", {}).get("运动员",
                "击剑运动员需要具备良好的身体素质、扎实的技术基础、敏锐的战术意识和强大的心理素质。")
        elif "裁判" in question:
            return self.knowledge_base.get("角色", {}).get("裁判",
                "击剑裁判负责判定比赛中的得分、犯规等情况，确保比赛公平公正进行。")
        else:
            # 尝试从知识库中搜索相关内容
            response = self._search_knowledge_base(question)
            if response:
                return response
            return "在击剑运动中，教练、运动员和裁判都扮演着重要角色。教练负责指导和培养，运动员负责训练和比赛，裁判负责确保比赛公平。"
    
    def _search_knowledge_base(self, question: str) -> Optional[str]:
        """在知识库中搜索相关内容"""
        question_lower = question.lower()
        
        # 搜索训练相关
        if "教练" in question_lower or "训练" in question_lower:
            if "作用" in question_lower or "职责" in question_lower:
                return self.knowledge_base.get("训练", {}).get("教练作用")
            return self.knowledge_base.get("训练", {}).get("教练职责")
        
        # 搜索角色相关
        if "角色" in question_lower or "作用" in question_lower:
            if "教练" in question_lower:
                return self.knowledge_base.get("角色", {}).get("教练")
            elif "运动员" in question_lower:
                return self.knowledge_base.get("角色", {}).get("运动员")
        
        return None
    
    def _generate_general_response(self, question: str, video_context: str) -> str:
        """生成一般性回复"""
        # 首先尝试在知识库中搜索相关内容
        response = self._search_knowledge_base(question)
        if response:
            # 如果有视频上下文，可以添加相关说明
            if video_context and "正在观看" not in video_context:
                return f"{response}\n\n（当前正在观看{video_context}，如需分析视频内容，请告诉我具体时间点。）"
            return response
        
        # 如果找不到相关内容，返回友好的提示
        if video_context:
            # 修复文本重复问题：检查video_context是否已经包含"正在观看"
            if "正在观看" in video_context:
                context_text = video_context
            else:
                context_text = f"正在观看{video_context}"
            return f"我当前{context_text}。作为击剑AI专家，我可以为您解答击剑相关问题，包括规则、技术、历史、训练、教练作用等方面。请问您想了解什么？"
        else:
            return "您好！我是击剑AI专家，可以为您解答击剑相关问题，包括规则、技术、历史、比赛分析、训练方法、教练作用等。请问有什么可以帮助您的吗？"
    
    def analyze_video_context(self, video_url: str, current_time: int) -> str:
        """分析视频内容"""
        # 这里可以集成更复杂的视频分析功能
        # 目前返回基于时间的简单分析
        
        if current_time < 60:
            context = "比赛开始阶段，运动员正在热身和试探"
        elif current_time < 180:
            context = "比赛进行中，双方展开激烈对抗"
        elif current_time < 300:
            context = "比赛进入关键阶段，比分胶着"
        else:
            context = "比赛接近尾声，运动员全力以赴"
        
        return f"根据视频内容分析，当前处于{context}。建议关注运动员的技术运用和战术变化。"
    
    def get_fencing_tips(self) -> List[str]:
        """获取击剑技巧提示"""
        tips = [
            "保持正确的实战姿势，重心要稳",
            "进攻时要把握时机，不要盲目出击",
            "防守要主动，为反击创造机会",
            "注意距离控制，保持合适的攻击距离",
            "运用假动作迷惑对手，寻找破绽",
            "保持冷静，在压力下发挥最佳水平"
        ]
        return random.sample(tips, 3)
    
    def get_competition_analysis(self, context: str) -> str:
        """获取比赛分析"""
        if "进攻" in context:
            return "这个进攻动作展现了运动员的技术水平，时机把握得很好，假动作运用也很巧妙。"
        elif "防守" in context:
            return "防守很到位，不仅化解了对手进攻，还为反击创造了机会。"
        elif "战术" in context:
            return "战术运用很灵活，能够根据对手特点调整策略，体现了高水平的比赛智慧。"
        else:
            return "这场比赛展现了击剑运动的魅力，运动员的技术、战术和心理素质都达到了很高水平。"
    
    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history
    
    def clear_conversation_history(self):
        """清除对话历史"""
        self.conversation_history = []
    
    def export_knowledge(self) -> Dict:
        """导出知识库"""
        return {
            "knowledge_base": self.knowledge_base,
            "fencing_terms": self.fencing_terms,
            "competition_contexts": self.competition_contexts,
            "export_time": datetime.now().isoformat()
        }
    
    def _get_deepseek_response(self, user_message: str, video_context: str = "") -> Optional[str]:
        """使用DeepSeek API获取回复"""
        if not self.config.DEEPSEEK_API_KEY:
            print("[DeepSeek] API密钥未配置")
            return None
        
        print(f"[DeepSeek] 开始调用API，API密钥长度: {len(self.config.DEEPSEEK_API_KEY)}")
        
        try:
            # 构建系统提示词
            system_prompt = self.config.FENCING_SYSTEM_PROMPT
            if video_context:
                system_prompt += f"\n\n当前上下文：{video_context}"
            
            # 构建消息历史（最近5轮对话）
            messages = [{"role": "system", "content": system_prompt}]
            
            # 添加对话历史
            recent_history = self.conversation_history[-10:]  # 最近10条消息
            for item in recent_history:
                if "user" in item:
                    messages.append({"role": "user", "content": item["user"]})
                elif "ai" in item:
                    messages.append({"role": "assistant", "content": item["ai"]})
            
            # 添加当前用户消息
            messages.append({"role": "user", "content": user_message})
            
            # 调用DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.DEEPSEEK_API_KEY}"
            }
            
            payload = {
                "model": self.config.DEEPSEEK_MODEL,
                "messages": messages,
                "max_tokens": self.config.DEEPSEEK_MAX_TOKENS,
                "temperature": self.config.DEEPSEEK_TEMPERATURE,
                "stream": False
            }
            
            print(f"[DeepSeek] 发送请求到: {self.config.DEEPSEEK_BASE_URL}/chat/completions")
            print(f"[DeepSeek] 模型: {self.config.DEEPSEEK_MODEL}, 消息数: {len(messages)}")
            
            response = requests.post(
                f"{self.config.DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30  # 增加超时时间到30秒，给DeepSeek更多时间响应
            )
            
            print(f"[DeepSeek] 收到响应，状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"].strip()
                    if content:
                        return content
            else:
                # API调用失败，记录错误但不抛出异常（让回退机制处理）
                print(f"DeepSeek API调用失败: {response.status_code} - {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print("[DeepSeek] API请求超时（30秒），使用本地知识库")
            return None
        except requests.exceptions.RequestException as e:
            print(f"[DeepSeek] API请求异常: {e}")
            return None
        except Exception as e:
            print(f"[DeepSeek] API调用异常: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        return None
    
    def test_deepseek_connection(self) -> bool:
        """测试DeepSeek连接"""
        if not self.config.DEEPSEEK_API_KEY:
            return False
        
        try:
            test_message = "你好"
            response = self._get_deepseek_response(test_message)
            return response is not None and len(response) > 0
        except Exception as e:
            print(f"DeepSeek连接测试失败: {e}")
            return False
    
    def switch_to_deepseek(self):
        """切换到DeepSeek模式"""
        if self.config.DEEPSEEK_API_KEY:
            self.use_deepseek = True
            return True
        return False
    
    def switch_to_local_ai(self):
        """切换到本地AI模式"""
        self.use_deepseek = False
        return True
    
    def get_ai_status(self) -> Dict:
        """获取AI系统状态"""
        return {
            "deepseek_available": bool(self.config.DEEPSEEK_API_KEY),
            "use_deepseek": self.use_deepseek,
            "fallback_enabled": self.fallback_to_local,
            "conversation_count": len(self.conversation_history),
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    def get_advanced_analysis(self, question: str, video_context: str = "") -> str:
        """获取高级分析"""
        # 优先使用DeepSeek（如果可用）
        if self.use_deepseek:
            try:
                response = self._get_deepseek_response(question, video_context)
                if response:
                    return response
            except Exception:
                pass
        
        # 使用本地知识库进行深度分析
        # 结合多个知识库类别生成更全面的回答
        analysis_parts = []
        
        # 根据问题关键词搜索相关知识点
        question_lower = question.lower()
        if "教练" in question_lower:
            analysis_parts.append(self.knowledge_base.get("训练", {}).get("教练作用", ""))
            analysis_parts.append(self.knowledge_base.get("角色", {}).get("教练", ""))
        
        if "训练" in question_lower:
            analysis_parts.append(self.knowledge_base.get("训练", {}).get("训练方法", ""))
        
        if analysis_parts:
            return "\n\n".join([part for part in analysis_parts if part])
        
        # 如果找不到相关内容，使用一般回复
        return self._generate_general_response(question, video_context)
