from flask import Flask, render_template, request, jsonify, session
import requests
import json
import os
from datetime import datetime
import re
from utils.fencing_ai import FencingAI
from utils.danmaku_system import DanmakuSystem
from utils.fie_data import FIEDataCollector
from utils.youtube_parser import YouTubeParser
from utils.video_analyzer import VideoAnalyzer
from utils.knowledge_recommender import KnowledgeRecommender
from utils.learning_path import LearningPathTracker
from utils.multimodal_analyzer import MultimodalAnalyzer
from utils.action_recognizer import FencingActionRecognizer
from utils.cv_analyzer import CVAnalyzer
from utils.pose_detector import PoseDetector
from utils.action_commentator import ActionCommentator
from utils.i18n import i18n
from config import Config
import base64

app = Flask(__name__)
config = Config()
app.secret_key = config.SECRET_KEY

# 初始化各个系统
fencing_ai = FencingAI()
danmaku_system = DanmakuSystem()
fie_collector = FIEDataCollector()
youtube_parser = YouTubeParser()
video_analyzer = VideoAnalyzer()
knowledge_recommender = KnowledgeRecommender()
learning_path_tracker = LearningPathTracker()
multimodal_analyzer = MultimodalAnalyzer()
action_recognizer = FencingActionRecognizer()
cv_analyzer = CVAnalyzer()
pose_detector = PoseDetector()
action_commentator = ActionCommentator()

@app.route('/')
def index():
    """主页面"""
    # 从session或请求参数获取语言设置
    lang = request.args.get('lang') or session.get('language', 'zh_CN')
    i18n.set_language(lang)
    session['language'] = lang
    return render_template('index.html', current_lang=lang)

@app.route('/api/parse_youtube', methods=['POST'])
def parse_youtube():
    """解析YouTube链接"""
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        
        if not video_url:
            return jsonify({'error': '请提供YouTube链接'}), 400
        
        # 解析YouTube链接
        video_info = youtube_parser.parse_url(video_url)
        
        if not video_info:
            return jsonify({'error': '无法解析YouTube链接'}), 400
        
        # 存储到session
        session['current_video'] = video_info
        
        return jsonify({
            'success': True,
            'video_info': video_info
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI聊天接口"""
    try:
        data = request.get_json()
        user_message = data.get('message')
        video_context = data.get('video_context', '')
        
        if not user_message:
            return jsonify({'error': '请提供消息内容'}), 400
        
        # 获取AI回复
        ai_response = fencing_ai.get_response(
            user_message, 
            video_context=video_context
        )
        
        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_danmaku', methods=['POST'])
def generate_danmaku():
    """生成弹幕"""
    try:
        data = request.get_json()
        video_context = data.get('video_context', '')
        user_message = data.get('user_message', '')
        
        # 生成AI弹幕
        danmaku = danmaku_system.generate_ai_danmaku(
            video_context=video_context,
            user_message=user_message
        )
        
        return jsonify({
            'success': True,
            'danmaku': danmaku,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send_danmaku', methods=['POST'])
def send_danmaku():
    """发送用户弹幕"""
    try:
        data = request.get_json()
        message = message = data.get('message')
        user_id = data.get('user_id', 'anonymous')
        
        if not message:
            return jsonify({'error': '请提供弹幕内容'}), 400
        
        # 添加弹幕到系统
        danmaku_id = danmaku_system.add_user_danmaku(
            message=message,
            user_id=user_id
        )
        
        return jsonify({
            'success': True,
            'danmaku_id': danmaku_id,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_danmaku', methods=['GET'])
def get_danmaku():
    """获取弹幕列表"""
    try:
        # 获取最近的弹幕
        recent_danmaku = danmaku_system.get_recent_danmaku(limit=50)
        
        return jsonify({
            'success': True,
            'danmaku': recent_danmaku
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fie_data', methods=['GET'])
def get_fie_data():
    """获取FIE数据"""
    try:
        # 获取最近的比赛结果
        recent_results = fie_collector.get_recent_results()
        
        return jsonify({
            'success': True,
            'results': recent_results
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video_analysis', methods=['POST'])
def analyze_video():
    """分析视频内容"""
    try:
        data = request.get_json()
        video_url = data.get('video_url')
        current_time = data.get('current_time', 0)
        
        # 分析视频内容（这里可以集成更复杂的视频分析）
        analysis = fencing_ai.analyze_video_context(
            video_url=video_url,
            current_time=current_time
        )
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai_status', methods=['GET'])
def get_ai_status():
    """获取AI系统状态"""
    try:
        status = fencing_ai.get_ai_status()
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/test_deepseek', methods=['POST'])
def test_deepseek():
    """测试DeepSeek连接"""
    try:
        is_available = fencing_ai.test_deepseek_connection()
        return jsonify({
            'success': True,
            'deepseek_available': is_available
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/switch_ai', methods=['POST'])
def switch_ai():
    """切换AI系统"""
    try:
        data = request.get_json()
        ai_type = data.get('ai_type', 'auto')
        
        if ai_type == 'deepseek':
            fencing_ai.switch_to_deepseek()
        elif ai_type == 'local':
            fencing_ai.switch_to_local_ai()
        
        status = fencing_ai.get_ai_status()
        return jsonify({
            'success': True,
            'message': f'已切换到{ai_type} AI系统',
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/advanced_analysis', methods=['POST'])
def advanced_analysis():
    """高级分析功能"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        video_context = data.get('video_context', '')
        
        if not question:
            return jsonify({'error': '请提供问题内容'}), 400
        
        analysis = fencing_ai.get_advanced_analysis(question, video_context)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ========== 新增API端点 ==========

@app.route('/api/detect_key_moments', methods=['POST'])
def detect_key_moments():
    """检测视频关键时刻"""
    try:
        data = request.get_json()
        video_url = data.get('video_url', '')
        video_duration = data.get('duration', 0)
        
        moments = video_analyzer.detect_key_moments(video_url, video_duration)
        
        return jsonify({
            'success': True,
            'moments': moments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze_video_scene', methods=['POST'])
def analyze_video_scene():
    """分析视频场景"""
    try:
        data = request.get_json()
        video_url = data.get('video_url', '')
        current_time = data.get('current_time', 0)
        frame_data = data.get('frame_data')
        
        scene_info = video_analyzer.analyze_video_scene(video_url, current_time, frame_data)
        
        return jsonify({
            'success': True,
            'scene': scene_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recognize_action', methods=['POST'])
def recognize_action():
    """识别击剑动作"""
    try:
        data = request.get_json()
        frame_data = data.get('frame_data')
        current_time = data.get('current_time', 0)
        context = data.get('context')
        
        action_info = action_recognizer.recognize_action(frame_data, current_time, context)
        
        return jsonify({
            'success': True,
            'action': action_info
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recommend_knowledge', methods=['POST'])
def recommend_knowledge():
    """推荐相关知识"""
    try:
        data = request.get_json()
        video_context = data.get('video_context', {})
        user_id = data.get('user_id', 'default')
        
        recommendations = knowledge_recommender.recommend(video_context, user_id)
        
        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_learning_path', methods=['POST'])
def get_learning_path():
    """获取学习路径推荐"""
    try:
        data = request.get_json()
        user_profile = data.get('user_profile', {'level': '初级', 'user_id': 'default'})
        
        next_knowledge = learning_path_tracker.get_next_knowledge(user_profile)
        
        return jsonify({
            'success': True,
            'recommendation': next_knowledge
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update_learning_progress', methods=['POST'])
def update_learning_progress():
    """更新学习进度"""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default')
        topic = data.get('topic', '')
        path_id = data.get('path_id')
        
        learning_path_tracker.update_progress(user_id, topic, path_id)
        
        return jsonify({
            'success': True,
            'message': '学习进度已更新'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/multimodal_analyze', methods=['POST'])
def multimodal_analyze():
    """多模态分析"""
    try:
        data = request.get_json()
        video_url = data.get('video_url', '')
        video_data = data.get('video_data')
        audio_transcript = data.get('audio_transcript')
        subtitles = data.get('subtitles')
        
        analysis = multimodal_analyzer.analyze(video_url, video_data, audio_transcript, subtitles)
        
        return jsonify({
            'success': True,
            'analysis': analysis
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_contextual_danmaku', methods=['POST'])
def generate_contextual_danmaku():
    """生成基于视频分析的弹幕"""
    try:
        data = request.get_json()
        frame_analysis = data.get('frame_analysis', {})
        current_time = data.get('current_time', 0)
        
        danmaku = danmaku_system.generate_contextual_danmaku(frame_analysis, current_time)
        
        return jsonify({
            'success': True,
            'danmaku': danmaku
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze_frame', methods=['POST'])
def analyze_frame():
    """分析视频帧（支持图像数据）"""
    try:
        data = request.get_json()
        frame_data = data.get('frame_data', {})
        current_time = data.get('current_time', 0)
        frame_image_base64 = data.get('frame_image', None)  # base64编码的图像
        
        # 如果有图像数据，进行CV分析
        frame_image_bytes = None
        if frame_image_base64:
            try:
                # 移除data:image前缀（如果有）
                if ',' in frame_image_base64:
                    frame_image_base64 = frame_image_base64.split(',')[1]
                frame_image_bytes = base64.b64decode(frame_image_base64)
            except Exception as e:
                print(f"Failed to decode frame image: {e}")
        
        # 使用CV分析器分析图像
        cv_analysis = None
        if frame_image_bytes:
            cv_analysis = cv_analyzer.analyze_frame(frame_image_bytes, current_time)
        
        # 使用姿态检测器检测姿态
        pose_result = None
        if frame_image_bytes:
            try:
                pose_result = pose_detector.detect_pose(frame_image_bytes)
            except Exception as e:
                print(f"Pose detection error: {e}")
        
        # 使用动作识别器识别动作
        action_result = action_recognizer.recognize_action(
            frame_data, 
            current_time, 
            context=cv_analysis,
            frame_image=frame_image_bytes
        )
        
        # 生成技术解说
        pose_features = pose_result.get('features', {}) if pose_result else None
        commentary = action_commentator.generate_detailed_commentary(
            action_result,
            pose_features=pose_features,
            context=cv_analysis
        )
        
        # 综合分析结果
        analysis = video_analyzer.analyze_frame(frame_data, current_time)
        analysis['action'] = action_result
        analysis['cv_analysis'] = cv_analysis
        analysis['pose_detection'] = pose_result
        analysis['commentary'] = commentary
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'action_detected': action_result.get('action'),
            'confidence': action_result.get('confidence', 0),
            'commentary': commentary.get('main_commentary', ''),
            'detailed_commentary': commentary,
            'timestamp': current_time
        })
    except Exception as e:
        import traceback
        print(f"Frame analysis error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/translations', methods=['GET'])
def get_translations():
    """获取翻译文本"""
    try:
        lang = request.args.get('lang', 'zh_CN')
        i18n.set_language(lang)
        translations = i18n.get_all_translations()
        
        return jsonify({
            'success': True,
            'translations': translations,
            'language': lang
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/set_language', methods=['POST'])
def set_language():
    """设置语言"""
    try:
        data = request.get_json()
        lang = data.get('language', 'zh_CN')
        
        if lang in ['zh_CN', 'en_US']:
            i18n.set_language(lang)
            session['language'] = lang
            
            return jsonify({
                'success': True,
                'language': lang,
                'message': 'Language updated successfully'
            })
        else:
            return jsonify({'error': 'Invalid language code'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 支持Cloud Run和App Engine的PORT环境变量
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV', 'development') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)
