"""
学习路径跟踪系统 - 个性化学习推荐
"""
from typing import Dict, List, Optional
from datetime import datetime
import json

class LearningPathTracker:
    """学习路径跟踪器"""
    
    def __init__(self):
        self.learning_paths = {
            "初级": [
                {"id": "path_001", "title": "击剑基础", "topics": ["规则", "基本动作", "装备"]},
                {"id": "path_002", "title": "基本技术", "topics": ["直刺", "格挡", "步法"]},
            ],
            "中级": [
                {"id": "path_003", "title": "进阶技术", "topics": ["转移刺", "复合进攻", "战术"]},
                {"id": "path_004", "title": "比赛策略", "topics": ["距离控制", "时机把握", "心理"]},
            ],
            "高级": [
                {"id": "path_005", "title": "高级战术", "topics": ["假动作", "节奏变化", "心理战"]},
            ]
        }
        self.user_progress = {}  # 存储用户学习进度
    
    def get_user_level(self, user_id: str) -> str:
        """获取用户水平"""
        progress = self.user_progress.get(user_id, {})
        completed_paths = progress.get("completed_paths", [])
        
        if len(completed_paths) >= 3:
            return "高级"
        elif len(completed_paths) >= 1:
            return "中级"
        else:
            return "初级"
    
    def get_next_knowledge(self, user_profile: Dict) -> Dict:
        """获取下一个推荐知识点"""
        user_level = user_profile.get("level", "初级")
        user_id = user_profile.get("user_id", "default")
        
        # 获取当前学习路径
        current_paths = self.learning_paths.get(user_level, [])
        progress = self.user_progress.get(user_id, {
            "current_path": None,
            "completed_topics": [],
            "completed_paths": []
        })
        
        # 如果用户没有当前路径，推荐第一个
        if not progress["current_path"] and current_paths:
            progress["current_path"] = current_paths[0]["id"]
            self.user_progress[user_id] = progress
        
        # 获取当前路径的未完成主题
        current_path_id = progress["current_path"]
        if current_path_id:
            for path in current_paths:
                if path["id"] == current_path_id:
                    for topic in path["topics"]:
                        if topic not in progress["completed_topics"]:
                            return {
                                "path_id": current_path_id,
                                "path_title": path["title"],
                                "next_topic": topic,
                                "recommendation": f"建议学习：{topic}，这是{path['title']}的重要组成部分。"
                            }
        
        # 如果当前路径已完成，推荐下一个路径
        if current_path_id:
            current_index = next((i for i, p in enumerate(current_paths) if p["id"] == current_path_id), -1)
            if current_index >= 0 and current_index < len(current_paths) - 1:
                next_path = current_paths[current_index + 1]
                return {
                    "path_id": next_path["id"],
                    "path_title": next_path["title"],
                    "next_topic": next_path["topics"][0] if next_path["topics"] else None,
                    "recommendation": f"恭喜完成当前路径！建议开始学习：{next_path['title']}"
                }
        
        return {
            "recommendation": "您已经完成了当前水平的所有学习路径，建议观看更多比赛视频来提升实战理解。"
        }
    
    def update_progress(self, user_id: str, topic: str, path_id: Optional[str] = None):
        """更新学习进度"""
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {
                "current_path": path_id,
                "completed_topics": [],
                "completed_paths": []
            }
        
        progress = self.user_progress[user_id]
        if topic not in progress["completed_topics"]:
            progress["completed_topics"].append(topic)
        
        # 检查是否完成当前路径
        if path_id:
            progress["current_path"] = path_id
            user_level = self.get_user_level(user_id)
            current_paths = self.learning_paths.get(user_level, [])
            
            for path in current_paths:
                if path["id"] == path_id:
                    if all(topic in progress["completed_topics"] for topic in path["topics"]):
                        if path_id not in progress["completed_paths"]:
                            progress["completed_paths"].append(path_id)

