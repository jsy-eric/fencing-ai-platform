"""
视频分析模块 - 实现视频帧分析、动作识别、场景理解等功能
"""
import requests
import json
from typing import Dict, List, Optional
from datetime import datetime
from config import Config

class VideoAnalyzer:
    """视频分析器"""
    
    def __init__(self):
        self.config = Config()
        self.use_deepseek = self.config.USE_DEEPSEEK and bool(self.config.DEEPSEEK_API_KEY)
        
    def detect_key_moments(self, video_url: str, video_duration: int = 0) -> List[Dict]:
        """检测视频关键时刻"""
        moments = []
        
        # 基于视频时长和击剑比赛特点，预测关键时刻
        if video_duration > 0:
            # 击剑比赛通常的关键时刻
            key_times = [
                {"time": 0, "type": "开始", "description": "比赛开始"},
                {"time": video_duration // 4, "type": "阶段", "description": "比赛进行中"},
                {"time": video_duration // 2, "type": "关键", "description": "关键阶段"},
                {"time": video_duration * 3 // 4, "type": "关键", "description": "关键时刻"},
            ]
            
            for moment in key_times:
                if moment["time"] < video_duration:
                    moments.append({
                        "time": moment["time"],
                        "type": moment["type"],
                        "description": moment["description"],
                        "knowledge": self._get_knowledge_for_moment(moment["type"])
                    })
        
        return moments
    
    def _get_knowledge_for_moment(self, moment_type: str) -> Dict:
        """获取关键时刻的相关知识"""
        knowledge_map = {
            "开始": {
                "title": "比赛开始阶段",
                "content": "比赛开始时，运动员通常会进行试探，观察对手的技术特点和战术倾向。",
                "tips": ["注意观察对手的站位", "保持警惕，准备应对突然进攻"]
            },
            "阶段": {
                "title": "比赛进行中",
                "content": "比赛进行中，双方会展开激烈的对抗，运用各种技术和战术。",
                "tips": ["注意距离控制", "观察对手的节奏变化"]
            },
            "关键": {
                "title": "关键时刻",
                "content": "关键时刻需要运动员保持冷静，运用最擅长的技术，把握得分机会。",
                "tips": ["保持心理稳定", "相信自己的技术", "把握时机"]
            }
        }
        return knowledge_map.get(moment_type, {
            "title": "击剑知识",
            "content": "这是一个精彩的击剑比赛时刻。",
            "tips": []
        })
    
    def analyze_video_scene(self, video_url: str, current_time: int, frame_data: Optional[Dict] = None) -> Dict:
        """分析视频场景"""
        scene_info = {
            "competition_type": self._detect_competition_type(video_url),
            "weapon": self._detect_weapon_type(video_url, frame_data),
            "stage": self._detect_stage(current_time),
            "related_knowledge": []
        }
        
        # 根据场景生成相关知识
        scene_info["related_knowledge"] = self._generate_related_knowledge(scene_info)
        
        return scene_info
    
    def _detect_competition_type(self, video_url: str) -> str:
        """检测比赛类型"""
        # 基于URL或视频标题分析
        url_lower = video_url.lower()
        if "olympic" in url_lower or "奥运会" in url_lower:
            return "奥运会"
        elif "world" in url_lower or "世锦赛" in url_lower:
            return "世锦赛"
        elif "training" in url_lower or "训练" in url_lower:
            return "训练"
        else:
            return "比赛"
    
    def _detect_weapon_type(self, video_url: str, frame_data: Optional[Dict]) -> str:
        """检测剑种"""
        url_lower = video_url.lower()
        if "foil" in url_lower or "花剑" in url_lower:
            return "花剑"
        elif "epee" in url_lower or "重剑" in url_lower:
            return "重剑"
        elif "sabre" in url_lower or "佩剑" in url_lower:
            return "佩剑"
        else:
            return "未知"
    
    def _detect_stage(self, current_time: int) -> str:
        """检测比赛阶段"""
        if current_time < 60:
            return "开局"
        elif current_time < 180:
            return "中段"
        elif current_time < 300:
            return "关键分"
        else:
            return "结束"
    
    def _generate_related_knowledge(self, scene_info: Dict) -> List[Dict]:
        """生成相关知识"""
        knowledge = []
        
        # 根据剑种推荐知识
        weapon = scene_info.get("weapon", "未知")
        if weapon != "未知":
            knowledge.append({
                "type": "剑种介绍",
                "title": f"{weapon}的特点",
                "content": self._get_weapon_knowledge(weapon)
            })
        
        # 根据比赛类型推荐知识
        comp_type = scene_info.get("competition_type", "比赛")
        knowledge.append({
            "type": "比赛知识",
            "title": f"{comp_type}规则",
            "content": f"这是{comp_type}级别的击剑比赛，具有很高的竞技水平。"
        })
        
        return knowledge
    
    def _get_weapon_knowledge(self, weapon: str) -> str:
        """获取剑种知识"""
        knowledge_map = {
            "花剑": "花剑有效部位是躯干，使用剑尖刺击。花剑比赛强调技术和战术，被称为'击剑中的芭蕾'。",
            "重剑": "重剑全身都是有效部位，使用剑尖刺击。重剑比赛节奏相对较慢，更注重战术思考。",
            "佩剑": "佩剑有效部位是上半身，使用剑尖刺击和剑刃劈砍。佩剑比赛节奏最快，最具观赏性。"
        }
        return knowledge_map.get(weapon, "击剑是一项优雅而激烈的运动。")
    
    def recognize_action(self, video_frame_data: Optional[Dict], current_time: int) -> Dict:
        """识别击剑动作"""
        # 这里可以集成实际的计算机视觉模型
        # 目前使用基于时间和上下文的推断
        
        action_types = ["直刺", "转移刺", "击打刺", "格挡", "闪避", "复合进攻"]
        
        # 模拟动作识别（实际应该使用CV模型）
        detected_action = {
            "action": "转移刺",
            "confidence": 0.75,
            "technique": "这是一个经典的转移刺动作，运动员利用假动作迷惑对手，然后快速转移攻击方向。",
            "analysis": "动作时机把握很好，假动作运用巧妙，成功突破了对手的防守。",
            "tips": ["注意观察对手的防守习惯", "假动作要逼真", "转移要快速果断"]
        }
        
        return detected_action
    
    def analyze_frame(self, frame_data: Dict, current_time: int) -> Dict:
        """分析视频帧"""
        analysis = {
            "timestamp": current_time,
            "scene": self.analyze_video_scene("", current_time, frame_data),
            "action": self.recognize_action(frame_data, current_time),
            "knowledge_points": []
        }
        
        # 生成知识点
        analysis["knowledge_points"] = self._extract_knowledge_points(analysis)
        
        return analysis
    
    def _extract_knowledge_points(self, analysis: Dict) -> List[Dict]:
        """提取知识点"""
        points = []
        
        # 从动作分析中提取知识点
        action = analysis.get("action", {})
        if action:
            points.append({
                "type": "技术",
                "title": action.get("action", "技术动作"),
                "content": action.get("technique", ""),
                "time": analysis.get("timestamp", 0)
            })
        
        # 从场景分析中提取知识点
        scene = analysis.get("scene", {})
        if scene.get("weapon") != "未知":
            points.append({
                "type": "规则",
                "title": f"{scene.get('weapon')}规则",
                "content": self._get_weapon_knowledge(scene.get("weapon")),
                "time": analysis.get("timestamp", 0)
            })
        
        return points

