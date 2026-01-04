"""
姿态检测模块 - 使用MediaPipe进行实时姿态检测
"""
from typing import Dict, List, Optional, Tuple
import base64

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV not available. Using fallback pose detection.")

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("MediaPipe not available. Using fallback pose detection.")

class PoseDetector:
    """姿态检测器 - 使用MediaPipe"""
    
    def __init__(self):
        self.mediapipe_available = MEDIAPIPE_AVAILABLE and CV2_AVAILABLE
        if self.mediapipe_available:
            self.mp_pose = mp.solutions.pose
            self.pose = self.mp_pose.Pose(
                static_image_mode=False,
                model_complexity=1,
                enable_segmentation=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
            self.mp_drawing = mp.solutions.drawing_utils
        else:
            self.pose = None
            print("Using fallback pose detection (simulated)")
    
    def detect_pose(self, image_data: bytes) -> Dict:
        """检测人体姿态
        
        Args:
            image_data: 图像数据（bytes或base64字符串）
        
        Returns:
            姿态检测结果字典
        """
        if self.mediapipe_available and self.pose:
            return self._detect_with_mediapipe(image_data)
        else:
            return self._detect_fallback(image_data)
    
    def _detect_with_mediapipe(self, image_data: bytes) -> Dict:
        """使用MediaPipe检测姿态"""
        try:
            import cv2
            import numpy as np
            
            # 解码图像
            if isinstance(image_data, str):
                # base64字符串
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(image_data)
            else:
                image_bytes = image_data
            
            # 转换为numpy数组
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                return self._detect_fallback(image_data)
            
            # 转换BGR到RGB
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # 检测姿态
            results = self.pose.process(image_rgb)
            
            if results.pose_landmarks:
                return self._parse_mediapipe_results(results, image.shape)
            else:
                return self._detect_fallback(image_data)
                
        except Exception as e:
            print(f"MediaPipe detection error: {e}")
            return self._detect_fallback(image_data)
    
    def _parse_mediapipe_results(self, results, image_shape: Tuple) -> Dict:
        """解析MediaPipe结果"""
        landmarks = results.pose_landmarks.landmark
        h, w = image_shape[:2]
        
        # 提取关键点
        keypoints = {}
        keypoint_names = [
            'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
            'right_eye_inner', 'right_eye', 'right_eye_outer',
            'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
            'left_index', 'right_index', 'left_thumb', 'right_thumb',
            'left_hip', 'right_hip', 'left_knee', 'right_knee',
            'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
            'left_foot_index', 'right_foot_index'
        ]
        
        for i, landmark in enumerate(landmarks):
            if i < len(keypoint_names):
                keypoints[keypoint_names[i]] = {
                    'x': landmark.x * w,
                    'y': landmark.y * h,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                }
        
        # 计算关键特征
        features = self._extract_features(keypoints)
        
        return {
            'keypoints': keypoints,
            'features': features,
            'confidence': self._calculate_confidence(keypoints),
            'detection_method': 'mediapipe'
        }
    
    def _extract_features(self, keypoints: Dict) -> Dict:
        """提取动作特征"""
        features = {}
        
        # 计算手臂角度
        if 'left_shoulder' in keypoints and 'left_elbow' in keypoints and 'left_wrist' in keypoints:
            features['left_arm_angle'] = self._calculate_angle(
                keypoints['left_shoulder'],
                keypoints['left_elbow'],
                keypoints['left_wrist']
            )
        
        if 'right_shoulder' in keypoints and 'right_elbow' in keypoints and 'right_wrist' in keypoints:
            features['right_arm_angle'] = self._calculate_angle(
                keypoints['right_shoulder'],
                keypoints['right_elbow'],
                keypoints['right_wrist']
            )
        
        # 计算身体角度
        if 'left_shoulder' in keypoints and 'right_shoulder' in keypoints:
            features['shoulder_angle'] = self._calculate_shoulder_angle(
                keypoints['left_shoulder'],
                keypoints['right_shoulder']
            )
        
        # 计算手臂伸展度
        if 'left_shoulder' in keypoints and 'left_wrist' in keypoints:
            features['left_arm_extension'] = self._calculate_distance(
                keypoints['left_shoulder'],
                keypoints['left_wrist']
            )
        
        if 'right_shoulder' in keypoints and 'right_wrist' in keypoints:
            features['right_arm_extension'] = self._calculate_distance(
                keypoints['right_shoulder'],
                keypoints['right_wrist']
            )
        
        # 计算身体重心
        if 'left_hip' in keypoints and 'right_hip' in keypoints:
            features['body_center'] = {
                'x': (keypoints['left_hip']['x'] + keypoints['right_hip']['x']) / 2,
                'y': (keypoints['left_hip']['y'] + keypoints['right_hip']['y']) / 2
            }
        
        return features
    
    def _calculate_angle(self, p1: Dict, p2: Dict, p3: Dict) -> float:
        """计算三点之间的角度"""
        import math
        
        # 向量1: p2 -> p1
        v1 = (p1['x'] - p2['x'], p1['y'] - p2['y'])
        # 向量2: p2 -> p3
        v2 = (p3['x'] - p2['x'], p3['y'] - p2['y'])
        
        # 计算角度
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        mag1 = math.sqrt(v1[0]**2 + v1[1]**2)
        mag2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if mag1 == 0 or mag2 == 0:
            return 0
        
        cos_angle = dot_product / (mag1 * mag2)
        cos_angle = max(-1, min(1, cos_angle))  # 限制范围
        
        angle = math.degrees(math.acos(cos_angle))
        return angle
    
    def _calculate_shoulder_angle(self, left_shoulder: Dict, right_shoulder: Dict) -> float:
        """计算肩膀角度（身体倾斜度）"""
        import math
        dx = right_shoulder['x'] - left_shoulder['x']
        dy = right_shoulder['y'] - left_shoulder['y']
        angle = math.degrees(math.atan2(dy, dx))
        return angle
    
    def _calculate_distance(self, p1: Dict, p2: Dict) -> float:
        """计算两点之间的距离"""
        import math
        dx = p2['x'] - p1['x']
        dy = p2['y'] - p1['y']
        return math.sqrt(dx**2 + dy**2)
    
    def _calculate_confidence(self, keypoints: Dict) -> float:
        """计算检测置信度"""
        if not keypoints:
            return 0.0
        
        # 基于关键点的可见性计算置信度
        visibilities = [kp.get('visibility', 0) for kp in keypoints.values()]
        if visibilities:
            return sum(visibilities) / len(visibilities)
        return 0.5
    
    def _detect_fallback(self, image_data: bytes) -> Dict:
        """降级检测（模拟）"""
        return {
            'keypoints': {
                'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0, 'visibility': 0.8},
                'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0, 'visibility': 0.8},
                'left_elbow': {'x': 0.35, 'y': 0.4, 'z': 0, 'visibility': 0.75},
                'right_elbow': {'x': 0.65, 'y': 0.4, 'z': 0, 'visibility': 0.75},
                'left_wrist': {'x': 0.3, 'y': 0.5, 'z': 0, 'visibility': 0.7},
                'right_wrist': {'x': 0.7, 'y': 0.5, 'z': 0, 'visibility': 0.7},
            },
            'features': {
                'left_arm_extension': 0.3,
                'right_arm_extension': 0.3,
                'shoulder_angle': 0
            },
            'confidence': 0.75,
            'detection_method': 'fallback'
        }

