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

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 初始化各个系统
fencing_ai = FencingAI()
danmaku_system = DanmakuSystem()
fie_collector = FIEDataCollector()
youtube_parser = YouTubeParser()

@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')

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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
