"""
计算机视觉分析模块 - 用于视频帧分析和动作识别
支持Google Vision API和本地模型
"""
import base64
import requests
import json
from typing import Dict, Optional, List
from config import Config

class CVAnalyzer:
    """计算机视觉分析器"""
    
    def __init__(self):
        self.config = Config()
        self.google_vision_api_key = getattr(self.config, 'GOOGLE_VISION_API_KEY', None)
        self.use_google_vision = bool(self.google_vision_api_key)
    
    def analyze_frame(self, frame_image: bytes, current_time: int = 0) -> Dict:
        """分析视频帧
        
        Args:
            frame_image: 视频帧图像数据（bytes或base64字符串）
            current_time: 当前播放时间
        
        Returns:
            分析结果字典
        """
        if self.use_google_vision and self.google_vision_api_key:
            return self._analyze_with_google_vision(frame_image, current_time)
        else:
            return self._analyze_with_local_model(frame_image, current_time)
    
    def _analyze_with_google_vision(self, frame_image: bytes, current_time: int) -> Dict:
        """使用Google Vision API分析"""
        try:
            # 确保是base64编码
            if isinstance(frame_image, bytes):
                image_base64 = base64.b64encode(frame_image).decode('utf-8')
            else:
                image_base64 = frame_image
            
            # 调用Google Vision API
            url = f"https://vision.googleapis.com/v1/images:annotate?key={self.google_vision_api_key}"
            
            payload = {
                "requests": [{
                    "image": {
                        "content": image_base64
                    },
                    "features": [
                        {
                            "type": "OBJECT_LOCALIZATION",
                            "maxResults": 10
                        },
                        {
                            "type": "LABEL_DETECTION",
                            "maxResults": 10
                        }
                    ]
                }]
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                return self._parse_google_vision_result(result, current_time)
            else:
                print(f"Google Vision API error: {response.status_code}")
                return self._analyze_with_local_model(frame_image, current_time)
                
        except Exception as e:
            print(f"Google Vision API failed: {e}")
            return self._analyze_with_local_model(frame_image, current_time)
    
    def _parse_google_vision_result(self, result: Dict, current_time: int) -> Dict:
        """解析Google Vision API结果"""
        # 提取检测到的对象和标签
        detected_objects = []
        labels = []
        
        if 'responses' in result and len(result['responses']) > 0:
            response = result['responses'][0]
            
            # 提取对象
            if 'localizedObjectAnnotations' in response:
                for obj in response['localizedObjectAnnotations']:
                    detected_objects.append({
                        "name": obj.get('name', ''),
                        "score": obj.get('score', 0),
                        "bounding_poly": obj.get('boundingPoly', {})
                    })
            
            # 提取标签
            if 'labelAnnotations' in response:
                for label in response['labelAnnotations']:
                    labels.append({
                        "description": label.get('description', ''),
                        "score": label.get('score', 0)
                    })
        
        # 分析是否为击剑相关
        fencing_keywords = ['person', 'sport', 'fencing', 'sword', 'athlete', 'competition']
        is_fencing = any(
            any(keyword in str(obj.get('name', '')).lower() or 
                keyword in str(label.get('description', '')).lower() 
                for keyword in fencing_keywords)
            for obj in detected_objects + labels
        )
        
        return {
            "timestamp": current_time,
            "detected_objects": detected_objects,
            "labels": labels,
            "is_fencing_scene": is_fencing,
            "confidence": 0.8 if is_fencing else 0.3,
            "analysis_method": "google_vision"
        }
    
    def _analyze_with_local_model(self, frame_image: bytes, current_time: int) -> Dict:
        """使用本地模型分析（模拟）"""
        # 这里可以集成本地CV模型，如OpenPose、MediaPipe等
        # 目前返回模拟结果
        
        return {
            "timestamp": current_time,
            "detected_objects": [
                {"name": "person", "score": 0.85},
                {"name": "sport_equipment", "score": 0.7}
            ],
            "labels": [
                {"description": "sport", "score": 0.8},
                {"description": "athlete", "score": 0.75}
            ],
            "is_fencing_scene": True,
            "confidence": 0.75,
            "analysis_method": "local_model"
        }
    
    def detect_pose(self, frame_image: bytes) -> Dict:
        """检测人体姿态（用于动作识别）"""
        # 这里可以集成OpenPose、MediaPipe等姿态检测模型
        # 返回关键点位置
        
        # 模拟姿态检测结果
        return {
            "keypoints": {
                "nose": {"x": 0.5, "y": 0.2, "confidence": 0.9},
                "left_shoulder": {"x": 0.4, "y": 0.3, "confidence": 0.85},
                "right_shoulder": {"x": 0.6, "y": 0.3, "confidence": 0.85},
                "left_elbow": {"x": 0.35, "y": 0.4, "confidence": 0.8},
                "right_elbow": {"x": 0.65, "y": 0.4, "confidence": 0.8},
                "left_wrist": {"x": 0.3, "y": 0.5, "confidence": 0.75},
                "right_wrist": {"x": 0.7, "y": 0.5, "confidence": 0.75}
            },
            "confidence": 0.8
        }
    
    def extract_action_features(self, frame_image: bytes, pose: Optional[Dict] = None) -> Dict:
        """提取动作特征"""
        if pose is None:
            pose = self.detect_pose(frame_image)
        
        # 基于姿态关键点提取特征
        features = {
            "arm_extension": self._calculate_arm_extension(pose),
            "body_angle": self._calculate_body_angle(pose),
            "sword_position": self._estimate_sword_position(pose),
            "movement_direction": "forward"  # 需要多帧分析
        }
        
        return features
    
    def _calculate_arm_extension(self, pose: Dict) -> float:
        """计算手臂伸展度"""
        # 基于关键点计算
        return 0.7  # 模拟值
    
    def _calculate_body_angle(self, pose: Dict) -> float:
        """计算身体角度"""
        return 15.0  # 模拟值（度）
    
    def _estimate_sword_position(self, pose: Dict) -> Dict:
        """估计剑的位置"""
        return {
            "x": 0.7,
            "y": 0.5,
            "angle": 45.0
        }

