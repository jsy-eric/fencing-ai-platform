"""
知识推荐系统 - 根据视频内容推荐相关知识
"""
from typing import Dict, List, Optional
from datetime import datetime
import random

class KnowledgeRecommender:
    """知识推荐器"""
    
    def __init__(self):
        self.knowledge_base = self._load_knowledge_base()
        self.user_profiles = {}  # 存储用户学习档案
    
    def _load_knowledge_base(self) -> Dict:
        """加载知识库"""
        return {
            "技术": [
                {"id": "tech_001", "title": "直刺技术", "content": "直刺是击剑最基本的进攻技术...", "level": "初级"},
                {"id": "tech_002", "title": "转移刺技术", "content": "转移刺是通过改变攻击方向来突破防守...", "level": "中级"},
                {"id": "tech_003", "title": "复合进攻", "content": "复合进攻是结合多个动作的进攻方式...", "level": "高级"},
            ],
            "规则": [
                {"id": "rule_001", "title": "得分规则", "content": "击中有效部位得1分...", "level": "初级"},
                {"id": "rule_002", "title": "优先权规则", "content": "在花剑和佩剑中，优先权很重要...", "level": "中级"},
            ],
            "历史": [
                {"id": "hist_001", "title": "击剑历史", "content": "击剑起源于欧洲...", "level": "初级"},
            ],
            "训练": [
                {"id": "train_001", "title": "基础训练", "content": "基础训练包括...", "level": "初级"},
            ]
        }
    
    def recommend(self, current_video_context: Dict, user_id: str = "default") -> List[Dict]:
        """推荐相关知识"""
        recommendations = []
        
        # 获取用户档案
        user_profile = self.user_profiles.get(user_id, {
            "level": "初级",
            "interests": [],
            "viewed_topics": []
        })
        
        # 根据视频上下文推荐
        weapon = current_video_context.get("weapon", "")
        stage = current_video_context.get("stage", "")
        action = current_video_context.get("action", {})
        
        # 推荐技术知识
        if weapon and weapon != "未知":
            tech_knowledge = self._get_weapon_tech_knowledge(weapon, user_profile["level"])
            recommendations.extend(tech_knowledge)
        
        # 推荐动作相关知识
        if action and action.get("action"):
            action_knowledge = self._get_action_knowledge(action.get("action"), user_profile["level"])
            recommendations.extend(action_knowledge)
        
        # 推荐阶段相关知识
        if stage:
            stage_knowledge = self._get_stage_knowledge(stage, user_profile["level"])
            recommendations.extend(stage_knowledge)
        
        # 去重并限制数量
        unique_recommendations = self._deduplicate(recommendations, user_profile["viewed_topics"])
        return unique_recommendations[:5]  # 返回最多5个推荐
    
    def _get_weapon_tech_knowledge(self, weapon: str, level: str) -> List[Dict]:
        """获取剑种技术知识"""
        knowledge = []
        tech_base = self.knowledge_base.get("技术", [])
        
        for item in tech_base:
            if item["level"] == level or (level == "初级" and item["level"] in ["初级", "中级"]):
                knowledge.append({
                    "type": "技术",
                    "category": weapon,
                    **item
                })
        
        return knowledge[:2]  # 返回最多2个
    
    def _get_action_knowledge(self, action: str, level: str) -> List[Dict]:
        """获取动作相关知识"""
        knowledge = []
        tech_base = self.knowledge_base.get("技术", [])
        
        # 根据动作类型匹配知识
        for item in tech_base:
            if action in item["title"] or item["title"] in action:
                if item["level"] == level or (level == "初级" and item["level"] in ["初级", "中级"]):
                    knowledge.append({
                        "type": "技术",
                        "category": "动作",
                        **item
                    })
        
        return knowledge[:1]
    
    def _get_stage_knowledge(self, stage: str, level: str) -> List[Dict]:
        """获取阶段相关知识"""
        knowledge = []
        
        stage_map = {
            "开局": {"title": "比赛开局策略", "content": "比赛开局时，运动员需要..."},
            "中段": {"title": "比赛中期战术", "content": "比赛中期，双方已经..."},
            "关键分": {"title": "关键分处理", "content": "关键分时，运动员需要..."},
        }
        
        if stage in stage_map:
            knowledge.append({
                "type": "战术",
                "category": stage,
                "id": f"stage_{stage}",
                **stage_map[stage],
                "level": level
            })
        
        return knowledge
    
    def _deduplicate(self, recommendations: List[Dict], viewed_topics: List[str]) -> List[Dict]:
        """去重推荐"""
        unique = []
        seen_ids = set(viewed_topics)
        
        for rec in recommendations:
            if rec.get("id") not in seen_ids:
                unique.append(rec)
                seen_ids.add(rec.get("id"))
        
        return unique
    
    def update_user_profile(self, user_id: str, viewed_topic_id: str, interest: Optional[str] = None):
        """更新用户档案"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {
                "level": "初级",
                "interests": [],
                "viewed_topics": []
            }
        
        profile = self.user_profiles[user_id]
        if viewed_topic_id not in profile["viewed_topics"]:
            profile["viewed_topics"].append(viewed_topic_id)
        
        if interest and interest not in profile["interests"]:
            profile["interests"].append(interest)

