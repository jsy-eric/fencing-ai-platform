"""
动作解说生成器 - 基于动作识别结果生成技术解说
"""
from typing import Dict, List, Optional
import random

class ActionCommentator:
    """动作解说生成器"""
    
    def __init__(self):
        self.commentary_templates = {
            "直刺": [
                "这是一个经典的直刺动作，运动员动作直接、快速，剑尖准确对准目标。",
                "看这个直刺！运动员保持了良好的身体平衡，手臂完全伸展，时机把握精准。",
                "精彩的直刺！动作干净利落，展现了扎实的基本功。",
                "这个直刺动作非常标准，身体重心稳定，出剑速度快，展现了专业的技术水平。"
            ],
            "转移刺": [
                "这是一个经典的转移刺，运动员利用假动作迷惑对手，然后快速转移攻击方向。",
                "看这个转移刺！假动作非常逼真，成功骗过了对手的防守，转移快速果断。",
                "精彩的转移刺！运动员观察敏锐，抓住了对手防守的空当，转移时机完美。",
                "这个转移刺运用巧妙，假动作和真动作的衔接非常流畅，展现了高超的技术。"
            ],
            "格挡": [
                "这是一个及时的格挡，运动员反应迅速，成功化解了对手的进攻。",
                "看这个格挡！剑身位置准确，不仅挡住了攻击，还为反击创造了机会。",
                "精彩的格挡！运动员判断准确，格挡后立即准备反击，展现了良好的防守意识。",
                "这个格挡非常到位，不仅化解了危险，还保持了有利的防守位置。"
            ],
            "闪避": [
                "这是一个灵活的闪避动作，运动员身体移动快速，成功避开了对手的攻击。",
                "看这个闪避！判断准确，移动迅速，保持了良好的身体平衡。",
                "精彩的闪避！运动员柔韧性很好，闪避后立即寻找反攻机会。",
                "这个闪避动作展现了运动员的身体控制能力，成功避开了攻击并保持了有利位置。"
            ],
            "复合进攻": [
                "这是一个复合进攻，运动员结合了多个动作，节奏变化成功迷惑了对手。",
                "看这个复合进攻！动作连贯流畅，假动作逼真，真动作果断，展现了高超的技术。",
                "精彩的复合进攻！运动员观察敏锐，动作组合巧妙，成功突破了对手的防守。",
                "这个复合进攻运用得当，动作之间的衔接非常自然，展现了专业的技术水平。"
            ],
            "抢攻": [
                "这是一个抢攻！运动员判断准确，在对手准备进攻时抢先发起攻击。",
                "看这个抢攻！时机把握完美，快速启动，成功抢占了先机。",
                "精彩的抢攻！运动员观察敏锐，判断对手意图准确，动作果断迅速。",
                "这个抢攻展现了运动员的战术意识，成功在对手进攻前发起攻击。"
            ],
            "进攻": [
                "这是一个主动进攻，运动员把握时机，动作果断，展现了积极的进攻意识。",
                "看这个进攻！运动员保持了良好的距离控制，动作直接有效。",
                "精彩的进攻！运动员观察敏锐，抓住了进攻机会，动作执行到位。",
                "这个进攻展现了运动员的技术水平，时机把握准确，动作果断有力。"
            ],
            "反攻": [
                "这是一个反攻！运动员在对手进攻时及时反应，进行了有效的反击。",
                "看这个反攻！判断准确，反应迅速，反击时机把握完美。",
                "精彩的反攻！运动员在防守的同时寻找反击机会，展现了良好的战术意识。",
                "这个反攻展现了运动员的应变能力，成功化解了对手的进攻并进行了反击。"
            ],
            "击打刺": [
                "这是一个击打刺，运动员通过击打对手的剑来创造进攻机会。",
                "看这个击打刺！击打准确，快速跟进，成功创造了进攻空间。",
                "精彩的击打刺！运动员技术娴熟，击打和跟进动作连贯流畅。",
                "这个击打刺运用巧妙，成功破坏了对手的防守，为进攻创造了机会。"
            ]
        }
        
        self.technical_phrases = [
            "展现了扎实的基本功",
            "时机把握精准",
            "动作干净利落",
            "技术运用娴熟",
            "战术意识良好",
            "身体控制能力强",
            "观察敏锐",
            "反应迅速",
            "动作连贯流畅",
            "展现了专业的技术水平"
        ]
    
    def generate_commentary(self, action_result: Dict, pose_features: Optional[Dict] = None) -> str:
        """生成动作解说
        
        Args:
            action_result: 动作识别结果
            pose_features: 姿态特征（可选）
        
        Returns:
            解说文本
        """
        action_name = action_result.get('action', '未知动作')
        confidence = action_result.get('confidence', 0)
        technique = action_result.get('technique', '')
        
        # 获取基础解说模板
        templates = self.commentary_templates.get(action_name, [
            f"这是一个{action_name}动作，展现了运动员的技术水平。"
        ])
        
        # 随机选择一个模板
        base_commentary = random.choice(templates)
        
        # 根据置信度调整解说
        if confidence > 0.8:
            base_commentary = "非常清晰的" + base_commentary
        elif confidence < 0.6:
            base_commentary = "疑似" + base_commentary
        
        # 根据姿态特征增强解说
        if pose_features:
            enhanced_commentary = self._enhance_with_pose_features(
                base_commentary, 
                pose_features, 
                action_name
            )
            return enhanced_commentary
        
        return base_commentary
    
    def _enhance_with_pose_features(self, base_commentary: str, 
                                   pose_features: Dict, 
                                   action_name: str) -> str:
        """根据姿态特征增强解说"""
        enhancements = []
        
        # 检查手臂伸展度
        left_extension = pose_features.get('left_arm_extension', 0)
        right_extension = pose_features.get('right_arm_extension', 0)
        
        if action_name in ['直刺', '转移刺', '进攻']:
            if left_extension > 0.4 or right_extension > 0.4:
                enhancements.append("手臂完全伸展")
            elif left_extension < 0.2 or right_extension < 0.2:
                enhancements.append("手臂未完全伸展")
        
        # 检查身体角度
        shoulder_angle = pose_features.get('shoulder_angle', 0)
        if abs(shoulder_angle) > 15:
            if shoulder_angle > 0:
                enhancements.append("身体略微右倾")
            else:
                enhancements.append("身体略微左倾")
        
        # 检查手臂角度
        left_arm_angle = pose_features.get('left_arm_angle', 0)
        right_arm_angle = pose_features.get('right_arm_angle', 0)
        
        if action_name in ['格挡']:
            if left_arm_angle > 90 or right_arm_angle > 90:
                enhancements.append("格挡角度正确")
        
        # 组合增强信息
        if enhancements:
            enhancement_text = "，" + "，".join(enhancements)
            return base_commentary + enhancement_text
        
        return base_commentary
    
    def generate_detailed_commentary(self, action_result: Dict, 
                                    pose_features: Optional[Dict] = None,
                                    context: Optional[Dict] = None) -> Dict:
        """生成详细解说（包含技术要点）"""
        commentary = self.generate_commentary(action_result, pose_features)
        
        action_name = action_result.get('action', '未知动作')
        key_points = action_result.get('key_points', [])
        analysis = action_result.get('analysis', '')
        
        # 构建详细解说
        detailed = {
            'main_commentary': commentary,
            'technical_analysis': analysis,
            'key_points': key_points,
            'action_name': action_name,
            'confidence': action_result.get('confidence', 0)
        }
        
        # 添加上下文信息
        if context:
            if context.get('is_fencing_scene'):
                detailed['scene_context'] = "这是一个击剑比赛场景"
            if context.get('competition_type'):
                detailed['competition_type'] = context['competition_type']
        
        return detailed

