import json
import random
import requests
from datetime import datetime
from typing import Dict, List, Optional

class FencingAI:
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.conversation_history = []
        self.fencing_terms = self._load_fencing_terms()
        self.competition_contexts = self._load_competition_contexts()
        
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
        
        # 根据意图生成回复
        if intent == "规则询问":
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
        
        if any(word in message_lower for word in ["规则", "得分", "场地", "装备", "裁判"]):
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
    
    def _generate_general_response(self, question: str, video_context: str) -> str:
        """生成一般性回复"""
        if video_context:
            return f"我正在观看{video_context}。作为击剑AI专家，我可以为您解答击剑相关问题，包括规则、技术、历史等方面。请问您想了解什么？"
        else:
            return "您好！我是击剑AI专家，可以为您解答击剑相关问题，包括规则、技术、历史、比赛分析等。请问有什么可以帮助您的吗？"
    
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
