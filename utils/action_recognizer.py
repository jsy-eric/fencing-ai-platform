"""
动作识别模块 - 识别击剑技术动作
"""
from typing import Dict, List, Optional
import random

class FencingActionRecognizer:
    """击剑动作识别器"""
    
    def __init__(self):
        self.action_templates = {
            "直刺": {
                "description": "直刺是击剑最基本的进攻技术，要求动作直接、快速、准确。",
                "key_points": ["保持身体平衡", "手臂伸直", "剑尖对准目标", "快速出击"],
                "common_mistakes": ["身体前倾过度", "动作不够直接", "时机把握不准"],
                "category": "进攻"
            },
            "转移刺": {
                "description": "转移刺是通过改变攻击方向来突破对手防守的技术。",
                "key_points": ["假动作要逼真", "转移要快速", "保持身体稳定", "观察对手反应"],
                "common_mistakes": ["假动作不够逼真", "转移速度慢", "失去平衡"],
                "category": "进攻"
            },
            "格挡": {
                "description": "格挡是防守技术，用于化解对手的进攻。",
                "key_points": ["及时反应", "剑身位置正确", "为反击做准备", "保持距离"],
                "common_mistakes": ["反应太慢", "格挡位置不对", "没有准备反击"],
                "category": "防守"
            },
            "闪避": {
                "description": "闪避是通过身体移动来避开对手攻击的技术。",
                "key_points": ["判断准确", "移动快速", "保持平衡", "准备反击"],
                "common_mistakes": ["判断失误", "移动太慢", "失去平衡"],
                "category": "防守"
            },
            "复合进攻": {
                "description": "复合进攻是结合多个动作的进攻方式，更具迷惑性。",
                "key_points": ["动作连贯", "节奏变化", "观察对手", "把握时机"],
                "common_mistakes": ["动作不连贯", "节奏单一", "时机把握不准"],
                "category": "进攻"
            },
            "抢攻": {
                "description": "抢攻是在对手准备进攻时，抢先发起攻击的技术。",
                "key_points": ["判断对手意图", "快速启动", "抢占先机", "动作果断"],
                "common_mistakes": ["判断失误", "启动太慢", "动作犹豫"],
                "category": "进攻"
            },
            "进攻": {
                "description": "进攻是主动发起攻击的技术，包括各种进攻方式。",
                "key_points": ["把握时机", "动作果断", "保持距离", "观察对手"],
                "common_mistakes": ["时机不当", "动作犹豫", "距离控制不当"],
                "category": "进攻"
            },
            "反攻": {
                "description": "反攻是在对手进攻时，进行反击的技术。",
                "key_points": ["及时反应", "准确判断", "快速反击", "把握时机"],
                "common_mistakes": ["反应太慢", "判断失误", "反击时机不当"],
                "category": "防守反击"
            },
            "击打刺": {
                "description": "击打刺是通过击打对手的剑来创造进攻机会的技术。",
                "key_points": ["击打准确", "快速跟进", "保持平衡", "观察对手反应"],
                "common_mistakes": ["击打不准确", "跟进太慢", "失去平衡"],
                "category": "进攻"
            }
        }
    
    def recognize_action(self, video_frame_data: Optional[Dict], current_time: int, 
                        context: Optional[Dict] = None, frame_image: Optional[bytes] = None) -> Dict:
        """识别击剑动作
        
        Args:
            video_frame_data: 视频帧数据（元数据）
            current_time: 当前播放时间
            context: 上下文信息
            frame_image: 视频帧图像数据（base64或bytes）
        """
        # 如果有图像数据，使用计算机视觉API分析
        if frame_image:
            return self._recognize_with_cv(frame_image, current_time, context)
        
        # 否则使用基于时间和上下文的推断
        return self._recognize_with_context(current_time, context)
    
    def _recognize_with_cv(self, frame_image: bytes, current_time: int, 
                          context: Optional[Dict] = None) -> Dict:
        """使用计算机视觉识别动作"""
        try:
            # 尝试使用姿态检测识别动作
            from utils.pose_detector import PoseDetector
            pose_detector = PoseDetector()
            pose_result = pose_detector.detect_pose(frame_image)
            
            # 基于姿态特征识别动作
            if pose_result and pose_result.get('keypoints'):
                return self._recognize_from_pose(pose_result, current_time, context)
            else:
                # 降级到模拟识别
                return self._simulate_cv_recognition(frame_image, current_time, context)
        except Exception as e:
            print(f"CV recognition failed: {e}")
            # 降级到基于上下文的识别
            return self._recognize_with_context(current_time, context)
    
    def _recognize_from_pose(self, pose_result: Dict, current_time: int,
                            context: Optional[Dict] = None) -> Dict:
        """基于姿态数据识别动作"""
        features = pose_result.get('features', {})
        keypoints = pose_result.get('keypoints', {})
        
        # 基于姿态特征判断动作类型
        action_probabilities = self._estimate_action_from_pose(features, keypoints)
        
        # 选择最可能的动作
        detected_action = max(action_probabilities.items(), key=lambda x: x[1])
        action_name = detected_action[0]
        confidence = detected_action[1]
        
        # 构建结果
        result = self._build_action_result(action_name, confidence, current_time, context)
        result['pose_features'] = features
        result['pose_keypoints'] = keypoints
        
        return result
    
    def _estimate_action_from_pose(self, features: Dict, keypoints: Dict) -> Dict:
        """基于姿态特征估计动作概率"""
        probabilities = {
            "直刺": 0.2,
            "转移刺": 0.15,
            "格挡": 0.15,
            "闪避": 0.1,
            "复合进攻": 0.1,
            "抢攻": 0.1,
            "进攻": 0.1,
            "反攻": 0.08,
            "击打刺": 0.02
        }
        
        # 根据手臂伸展度判断
        left_extension = features.get('left_arm_extension', 0)
        right_extension = features.get('right_arm_extension', 0)
        max_extension = max(left_extension, right_extension)
        
        if max_extension > 0.4:
            # 手臂伸展，可能是进攻动作
            probabilities["直刺"] += 0.2
            probabilities["转移刺"] += 0.15
            probabilities["进攻"] += 0.1
        elif max_extension < 0.2:
            # 手臂未伸展，可能是防守动作
            probabilities["格挡"] += 0.2
            probabilities["闪避"] += 0.15
        
        # 根据手臂角度判断
        left_arm_angle = features.get('left_arm_angle', 0)
        right_arm_angle = features.get('right_arm_angle', 0)
        
        if left_arm_angle > 120 or right_arm_angle > 120:
            # 手臂角度大，可能是格挡
            probabilities["格挡"] += 0.15
        elif left_arm_angle < 90 and right_arm_angle < 90:
            # 手臂角度小，可能是进攻
            probabilities["直刺"] += 0.15
        
        # 根据身体角度判断
        shoulder_angle = abs(features.get('shoulder_angle', 0))
        if shoulder_angle > 15:
            # 身体倾斜，可能是闪避或转移
            probabilities["闪避"] += 0.1
            probabilities["转移刺"] += 0.1
        
        # 归一化概率
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {k: v / total for k, v in probabilities.items()}
        
        return probabilities
    
    def _simulate_cv_recognition(self, frame_image: bytes, current_time: int,
                                 context: Optional[Dict] = None) -> Dict:
        """模拟CV识别（实际应该调用真实API）"""
        # 基于图像特征和时间上下文进行识别
        # 实际实现应该：
        # 1. 调用Google Vision API或本地模型
        # 2. 分析人体姿态
        # 3. 识别剑的位置和动作
        # 4. 判断动作类型
        
        action_probabilities = self._estimate_action_probabilities(current_time, context)
        
        # 根据图像特征调整概率（模拟）
        # 实际应该分析图像中的关键点、姿态等
        if frame_image:
            # 模拟：根据图像大小、时间等调整
            import random
            # 随机调整概率，模拟CV分析结果
            for action in action_probabilities:
                action_probabilities[action] += random.uniform(-0.1, 0.1)
                action_probabilities[action] = max(0, min(1, action_probabilities[action]))
        
        # 选择最可能的动作
        detected_action = max(action_probabilities.items(), key=lambda x: x[1])
        
        action_name = detected_action[0]
        confidence = detected_action[1]
        
        return self._build_action_result(action_name, confidence, current_time, context)
    
    def _recognize_with_context(self, current_time: int, context: Optional[Dict] = None) -> Dict:
        """基于上下文识别动作"""
        action_probabilities = self._estimate_action_probabilities(current_time, context)
        detected_action = max(action_probabilities.items(), key=lambda x: x[1])
        
        action_name = detected_action[0]
        confidence = detected_action[1]
        
        return self._build_action_result(action_name, confidence, current_time, context)
    
    def _build_action_result(self, action_name: str, confidence: float, 
                            current_time: int, context: Optional[Dict] = None) -> Dict:
        """构建动作识别结果"""
        action_info = self.action_templates.get(action_name, {
            "description": "识别到击剑动作",
            "key_points": [],
            "common_mistakes": [],
            "category": "未知"
        })
        
        return {
            "action": action_name,
            "confidence": round(confidence, 2),
            "timestamp": current_time,
            "technique": action_info["description"],
            "key_points": action_info["key_points"],
            "analysis": self._generate_analysis(action_name, context),
            "tips": self._generate_tips(action_name),
            "common_mistakes": action_info["common_mistakes"],
            "category": action_info.get("category", "未知")
        }
    
    def _estimate_action_probabilities(self, current_time: int, context: Optional[Dict]) -> Dict:
        """估计动作概率（模拟）"""
        # 基于时间和上下文估计
        probabilities = {
            "直刺": 0.2,
            "转移刺": 0.15,
            "格挡": 0.15,
            "闪避": 0.1,
            "复合进攻": 0.1,
            "抢攻": 0.1,
            "进攻": 0.1,
            "反攻": 0.08,
            "击打刺": 0.02
        }
        
        # 根据时间调整概率
        if current_time < 60:
            probabilities["直刺"] = 0.4  # 开局多试探
        elif current_time > 180:
            probabilities["转移刺"] = 0.35  # 后期多变化
        
        # 根据上下文调整
        if context:
            if "进攻" in str(context):
                probabilities["直刺"] += 0.2
                probabilities["转移刺"] += 0.15
            elif "防守" in str(context):
                probabilities["格挡"] += 0.2
                probabilities["闪避"] += 0.15
        
        return probabilities
    
    def _generate_analysis(self, action: str, context: Optional[Dict]) -> str:
        """生成动作分析"""
        analyses = {
            "直刺": "这是一个经典的直刺动作，时机把握很好，动作直接有效。",
            "转移刺": "转移刺运用巧妙，假动作成功迷惑了对手，转移快速果断。",
            "格挡": "格挡及时到位，不仅化解了对手进攻，还为反击创造了机会。",
            "闪避": "闪避动作灵活，成功避开了对手的攻击，保持了有利位置。",
            "复合进攻": "复合进攻运用得当，动作连贯，节奏变化成功迷惑了对手。"
        }
        return analyses.get(action, "这是一个技术动作，展现了运动员的技术水平。")
    
    def _generate_tips(self, action: str) -> List[str]:
        """生成技巧提示"""
        tips_map = {
            "直刺": ["注意时机把握", "保持动作直接", "剑尖要对准目标"],
            "转移刺": ["假动作要逼真", "转移要快速", "观察对手反应"],
            "格挡": ["及时反应", "准备反击", "保持距离"],
            "闪避": ["判断要准确", "移动要快速", "保持平衡"],
            "复合进攻": ["动作要连贯", "节奏要变化", "把握时机"]
        }
        return tips_map.get(action, ["注意技术细节", "保持专注"])

