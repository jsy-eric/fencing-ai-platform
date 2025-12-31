import json
import random
import time
from datetime import datetime
from typing import Dict, List, Optional
from .fencing_ai import FencingAI

class DanmakuSystem:
    def __init__(self):
        self.danmaku_history = []
        self.active_danmaku = []
        self.max_danmaku = 100
        self.fencing_ai = FencingAI()
        self.danmaku_templates = self._load_danmaku_templates()
        self.context_patterns = self._load_context_patterns()
        
    def _load_danmaku_templates(self) -> Dict[str, List[str]]:
        """加载弹幕模板"""
        return {
            "进攻": [
                "进攻很犀利！",
                "这个直刺很准",
                "转移刺时机很好",
                "速度真快！",
                "时机把握得很好",
                "假动作很巧妙",
                "复合进攻很精彩",
                "这个进攻很有创意"
            ],
            "防守": [
                "防守很稳健",
                "格挡很及时",
                "闪避很灵活",
                "反应很快",
                "防守很到位",
                "这个防守很漂亮",
                "反击时机很好",
                "防守反击很精彩"
            ],
            "战术": [
                "战术运用得当",
                "节奏控制很好",
                "变化很丰富",
                "策略很清晰",
                "配合很默契",
                "心理战很成功",
                "这个战术很聪明",
                "临场应变很好"
            ],
            "技术": [
                "技术很纯熟",
                "动作很标准",
                "基本功很扎实",
                "技术很全面",
                "发挥很稳定",
                "这个动作很漂亮",
                "技术运用很灵活",
                "基本功很扎实"
            ],
            "精彩": [
                "太精彩了！",
                "神操作！",
                "完美！",
                "太棒了！",
                "精彩绝伦！",
                "这个动作太帅了！",
                "绝了！",
                "太厉害了！"
            ],
            "鼓励": [
                "继续加油",
                "稳住",
                "调整一下",
                "不要着急",
                "保持冷静",
                "相信自己",
                "还有机会",
                "坚持住"
            ]
        }
    
    def _load_context_patterns(self) -> Dict[str, List[str]]:
        """加载上下文模式"""
        return {
            "比赛开始": ["热身", "试探", "开始", "准备"],
            "比赛进行": ["进行", "对抗", "激烈", "胶着"],
            "关键时刻": ["关键", "重要", "决定", "最后"],
            "比分领先": ["领先", "优势", "控制", "主导"],
            "比分落后": ["落后", "追赶", "反击", "绝地"],
            "技术展示": ["技术", "动作", "技巧", "展示"]
        }
    
    def add_user_danmaku(self, message: str, user_id: str, type: str = "user") -> str:
        """添加用户弹幕"""
        danmaku_id = f"user_{int(time.time() * 1000)}"
        
        danmaku = {
            "id": danmaku_id,
            "text": message,
            "type": type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "category": self._categorize_danmaku(message)
        }
        
        self.danmaku_history.append(danmaku)
        
        # 限制历史记录数量
        if len(self.danmaku_history) > self.max_danmaku:
            self.danmaku_history.pop(0)
        
        return danmaku_id
    
    def generate_contextual_danmaku(self, video_frame_analysis: Dict, current_time: int = 0) -> str:
        """基于视频帧分析生成弹幕"""
        # 如果传入的是字符串（旧接口兼容），使用原来的方法
        if isinstance(video_frame_analysis, str):
            return self.generate_contextual_danmaku_legacy(video_frame_analysis, current_time)
        
        # 分析画面中的动作、运动员、场景
        action = video_frame_analysis.get("action", {})
        scene = video_frame_analysis.get("scene", {})
        
        # 根据动作生成弹幕
        if action and action.get("action"):
            action_name = action.get("action", "")
            analysis = action.get("analysis", "")
            
            # 生成技术分析弹幕
            if "转移刺" in action_name:
                return f"精彩的{action_name}！{analysis}"
            elif "格挡" in action_name:
                return f"防守到位！{analysis}"
            elif "复合进攻" in action_name:
                return f"复合进攻很巧妙！{analysis}"
            else:
                return f"{action_name}时机把握很好！"
        
        # 根据场景生成弹幕
        if scene:
            weapon = scene.get("weapon", "")
            stage = scene.get("stage", "")
            if weapon and weapon != "未知":
                return f"这是{weapon}比赛，当前处于{stage}阶段"
        
        return self._generate_general_danmaku(current_time)
    
    def generate_contextual_danmaku_legacy(self, video_context: str, current_time: int = 0) -> str:
        """生成基于视频上下文的弹幕（旧接口）"""
    
    def generate_ai_danmaku(self, video_context: str = "", user_message: str = "") -> str:
        """生成AI弹幕"""
        # 分析上下文
        context_category = self._analyze_context(video_context, user_message)
        
        # 根据上下文选择弹幕类型
        if context_category == "比赛开始":
            danmaku_type = random.choice(["技术", "鼓励"])
        elif context_category == "比赛进行":
            danmaku_type = random.choice(["进攻", "防守", "战术", "技术"])
        elif context_category == "关键时刻":
            danmaku_type = random.choice(["精彩", "战术", "技术"])
        elif context_category == "比分领先":
            danmaku_type = random.choice(["技术", "战术", "精彩"])
        elif context_category == "比分落后":
            danmaku_type = random.choice(["鼓励", "战术", "技术"])
        else:
            danmaku_type = random.choice(["进攻", "防守", "战术", "技术"])
        
        # 从模板中选择弹幕
        templates = self.danmaku_templates.get(danmaku_type, self.danmaku_templates["技术"])
        danmaku_text = random.choice(templates)
        
        # 创建AI弹幕
        ai_danmaku = {
            "id": f"ai_{int(time.time() * 1000)}",
            "text": danmaku_text,
            "type": "ai",
            "user_id": "ai_system",
            "timestamp": datetime.now().isoformat(),
            "category": danmaku_type,
            "context": video_context
        }
        
        self.danmaku_history.append(ai_danmaku)
        
        return danmaku_text
    
    def generate_contextual_danmaku(self, video_context: str, current_time: int = 0) -> str:
        """生成基于视频上下文的弹幕"""
        # 根据时间分析比赛阶段
        if current_time < 60:
            stage = "比赛开始"
        elif current_time < 180:
            stage = "比赛进行"
        elif current_time < 300:
            stage = "关键时刻"
        else:
            stage = "比赛结束"
        
        # 根据阶段和上下文生成弹幕
        if "进攻" in video_context:
            return self._generate_offensive_danmaku(stage)
        elif "防守" in video_context:
            return self._generate_defensive_danmaku(stage)
        elif "战术" in video_context:
            return self._generate_tactical_danmaku(stage)
        else:
            return self._generate_general_danmaku(stage)
    
    def _generate_offensive_danmaku(self, stage: str) -> str:
        """生成进攻相关弹幕"""
        if stage == "比赛开始":
            templates = ["开始试探", "寻找机会", "热身进攻"]
        elif stage == "比赛进行":
            templates = ["进攻很犀利", "时机把握很好", "假动作很巧妙"]
        elif stage == "关键时刻":
            templates = ["关键进攻", "绝佳时机", "决定性一击"]
        else:
            templates = ["最后进攻", "全力以赴", "绝地反击"]
        
        return random.choice(templates)
    
    def _generate_defensive_danmaku(self, stage: str) -> str:
        """生成防守相关弹幕"""
        if stage == "比赛开始":
            templates = ["稳健防守", "保持距离", "观察对手"]
        elif stage == "比赛进行":
            templates = ["防守很到位", "反应很快", "格挡很及时"]
        elif stage == "关键时刻":
            templates = ["关键防守", "稳住阵脚", "化解危机"]
        else:
            templates = ["最后防守", "坚持到底", "守住优势"]
        
        return random.choice(templates)
    
    def _generate_tactical_danmaku(self, stage: str) -> str:
        """生成战术相关弹幕"""
        if stage == "比赛开始":
            templates = ["战术试探", "了解对手", "制定策略"]
        elif stage == "比赛进行":
            templates = ["战术运用", "灵活调整", "随机应变"]
        elif stage == "关键时刻":
            templates = ["关键战术", "临场决策", "智慧选择"]
        else:
            templates = ["最终战术", "完美收官", "策略成功"]
        
        return random.choice(templates)
    
    def _generate_general_danmaku(self, stage: str) -> str:
        """生成一般性弹幕"""
        if stage == "比赛开始":
            templates = ["比赛开始", "精彩即将开始", "拭目以待"]
        elif stage == "比赛进行":
            templates = ["比赛很激烈", "双方都很强", "精彩继续"]
        elif stage == "关键时刻":
            templates = ["关键时刻", "决定胜负", "紧张时刻"]
        else:
            templates = ["比赛结束", "精彩比赛", "感谢观看"]
        
        return random.choice(templates)
    
    def _analyze_context(self, video_context: str, user_message: str) -> str:
        """分析上下文"""
        context_lower = (video_context + " " + user_message).lower()
        
        for category, patterns in self.context_patterns.items():
            if any(pattern in context_lower for pattern in patterns):
                return category
        
        return "比赛进行"
    
    def _categorize_danmaku(self, message: str) -> str:
        """分类弹幕"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["进攻", "攻击", "刺击", "出击"]):
            return "进攻"
        elif any(word in message_lower for word in ["防守", "格挡", "闪避", "后退"]):
            return "防守"
        elif any(word in message_lower for word in ["战术", "策略", "节奏", "变化"]):
            return "战术"
        elif any(word in message_lower for word in ["技术", "动作", "技巧", "基本功"]):
            return "技术"
        elif any(word in message_lower for word in ["精彩", "漂亮", "厉害", "棒"]):
            return "精彩"
        else:
            return "一般"
    
    def get_recent_danmaku(self, limit: int = 50) -> List[Dict]:
        """获取最近的弹幕"""
        return self.danmaku_history[-limit:] if self.danmaku_history else []
    
    def get_danmaku_by_category(self, category: str, limit: int = 20) -> List[Dict]:
        """根据类别获取弹幕"""
        filtered_danmaku = [d for d in self.danmaku_history if d.get("category") == category]
        return filtered_danmaku[-limit:] if filtered_danmaku else []
    
    def get_danmaku_by_type(self, danmaku_type: str, limit: int = 20) -> List[Dict]:
        """根据类型获取弹幕"""
        filtered_danmaku = [d for d in self.danmaku_history if d.get("type") == danmaku_type]
        return filtered_danmaku[-limit:] if filtered_danmaku else []
    
    def get_danmaku_stats(self) -> Dict:
        """获取弹幕统计信息"""
        total = len(self.danmaku_history)
        user_count = len([d for d in self.danmaku_history if d.get("type") == "user"])
        ai_count = len([d for d in self.danmaku_history if d.get("type") == "ai"])
        
        category_stats = {}
        for danmaku in self.danmaku_history:
            category = danmaku.get("category", "未知")
            category_stats[category] = category_stats.get(category, 0) + 1
        
        return {
            "total": total,
            "user": user_count,
            "ai": ai_count,
            "categories": category_stats,
            "last_updated": datetime.now().isoformat()
        }
    
    def search_danmaku(self, keyword: str, limit: int = 20) -> List[Dict]:
        """搜索弹幕"""
        keyword_lower = keyword.lower()
        results = []
        
        for danmaku in self.danmaku_history:
            if keyword_lower in danmaku.get("text", "").lower():
                results.append(danmaku)
                if len(results) >= limit:
                    break
        
        return results
    
    def clear_danmaku_history(self):
        """清除弹幕历史"""
        self.danmaku_history = []
    
    def export_danmaku_data(self) -> Dict:
        """导出弹幕数据"""
        return {
            "danmaku_history": self.danmaku_history,
            "stats": self.get_danmaku_stats(),
            "templates": self.danmaku_templates,
            "export_time": datetime.now().isoformat()
        }
    
    def import_danmaku_data(self, data: Dict):
        """导入弹幕数据"""
        if "danmaku_history" in data:
            self.danmaku_history = data["danmaku_history"]
        if "templates" in data:
            self.danmaku_templates.update(data["templates"])
    
    def get_trending_topics(self, hours: int = 24) -> List[str]:
        """获取热门话题"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        recent_danmaku = [
            d for d in self.danmaku_history 
            if datetime.fromisoformat(d["timestamp"]).timestamp() > cutoff_time
        ]
        
        # 统计关键词频率
        keyword_count = {}
        for danmaku in recent_danmaku:
            text = danmaku.get("text", "")
            words = text.split()
            for word in words:
                if len(word) > 1:  # 过滤单字符
                    keyword_count[word] = keyword_count.get(word, 0) + 1
        
        # 返回前10个热门关键词
        sorted_keywords = sorted(keyword_count.items(), key=lambda x: x[1], reverse=True)
        return [keyword for keyword, count in sorted_keywords[:10]]
    
    def generate_personalized_danmaku(self, user_preferences: Dict) -> str:
        """生成个性化弹幕"""
        # 根据用户偏好生成弹幕
        preferred_categories = user_preferences.get("categories", ["技术", "战术"])
        preferred_style = user_preferences.get("style", "专业")
        
        # 选择类别
        category = random.choice(preferred_categories)
        templates = self.danmaku_templates.get(category, self.danmaku_templates["技术"])
        
        # 根据风格调整
        if preferred_style == "专业":
            # 保持专业术语
            pass
        elif preferred_style == "轻松":
            # 添加表情符号或轻松语气
            templates = [t + " 😊" for t in templates]
        elif preferred_style == "激情":
            # 添加感叹号
            templates = [t + "！" for t in templates]
        
        return random.choice(templates)
