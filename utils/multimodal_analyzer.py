"""
多模态内容分析 - 结合视频、音频、字幕进行分析
"""
from typing import Dict, List, Optional
import re

class MultimodalAnalyzer:
    """多模态分析器"""
    
    def __init__(self):
        self.fencing_keywords = {
            "技术": ["直刺", "转移刺", "格挡", "闪避", "进攻", "防守", "复合进攻"],
            "规则": ["得分", "有效部位", "优先权", "犯规", "裁判"],
            "战术": ["距离控制", "时机", "节奏", "假动作", "心理"],
            "剑种": ["花剑", "重剑", "佩剑"]
        }
    
    def analyze(self, video_url: str, video_data: Optional[Dict] = None, 
                audio_transcript: Optional[str] = None, 
                subtitles: Optional[List[Dict]] = None) -> Dict:
        """多模态分析"""
        analysis = {
            "video_analysis": {},
            "audio_keywords": [],
            "subtitle_keywords": [],
            "combined_insights": []
        }
        
        # 分析视频
        if video_data:
            analysis["video_analysis"] = self._analyze_video_data(video_data)
        
        # 分析音频/字幕
        if audio_transcript:
            analysis["audio_keywords"] = self._extract_keywords(audio_transcript)
        
        if subtitles:
            analysis["subtitle_keywords"] = self._extract_keywords_from_subtitles(subtitles)
        
        # 综合分析
        analysis["combined_insights"] = self._combine_insights(analysis)
        
        return analysis
    
    def _analyze_video_data(self, video_data: Dict) -> Dict:
        """分析视频数据"""
        return {
            "detected_actions": video_data.get("actions", []),
            "scene_type": video_data.get("scene", "比赛"),
            "weapon_type": video_data.get("weapon", "未知")
        }
    
    def _extract_keywords(self, text: str) -> List[Dict]:
        """提取关键词"""
        keywords = []
        text_lower = text.lower()
        
        for category, words in self.fencing_keywords.items():
            for word in words:
                if word in text_lower:
                    keywords.append({
                        "category": category,
                        "keyword": word,
                        "context": self._extract_context(text, word)
                    })
        
        return keywords
    
    def _extract_keywords_from_subtitles(self, subtitles: List[Dict]) -> List[Dict]:
        """从字幕中提取关键词"""
        all_text = " ".join([sub.get("text", "") for sub in subtitles])
        return self._extract_keywords(all_text)
    
    def _extract_context(self, text: str, keyword: str) -> str:
        """提取关键词上下文"""
        # 在关键词前后各取20个字符
        index = text.lower().find(keyword.lower())
        if index >= 0:
            start = max(0, index - 20)
            end = min(len(text), index + len(keyword) + 20)
            return text[start:end].strip()
        return ""
    
    def _combine_insights(self, analysis: Dict) -> List[Dict]:
        """综合多模态分析结果"""
        insights = []
        
        # 合并所有关键词
        all_keywords = []
        all_keywords.extend(analysis.get("audio_keywords", []))
        all_keywords.extend(analysis.get("subtitle_keywords", []))
        
        # 按类别分组
        category_groups = {}
        for kw in all_keywords:
            category = kw.get("category", "其他")
            if category not in category_groups:
                category_groups[category] = []
            category_groups[category].append(kw)
        
        # 生成洞察
        for category, keywords in category_groups.items():
            if keywords:
                insights.append({
                    "type": category,
                    "keywords": [kw["keyword"] for kw in keywords],
                    "summary": f"视频中多次提到{category}相关内容，包括：{', '.join([kw['keyword'] for kw in keywords[:3]])}",
                    "recommendation": self._get_recommendation(category, keywords)
                })
        
        return insights
    
    def _get_recommendation(self, category: str, keywords: List[Dict]) -> str:
        """获取推荐"""
        recommendations = {
            "技术": "建议深入学习这些技术动作的要领和训练方法。",
            "规则": "建议了解相关规则的详细说明和判罚标准。",
            "战术": "建议学习这些战术的运用时机和变化。",
            "剑种": "建议了解这个剑种的特点和比赛规则。"
        }
        return recommendations.get(category, "建议进一步了解相关内容。")
    
    def extract_subtitles(self, video_id: str) -> List[Dict]:
        """提取视频字幕（需要YouTube API或第三方服务）"""
        # 这里应该调用YouTube API或使用字幕提取服务
        # 目前返回空列表，实际实现需要API密钥
        return []

