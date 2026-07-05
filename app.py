from flask import Flask, render_template, request, jsonify, session, send_from_directory, Response
import os
from datetime import datetime
from utils.fencing_ai import FencingAI
from utils.danmaku_system import DanmakuSystem
from utils.fie_data import FIEDataCollector
from utils.youtube_parser import YouTubeParser
from utils.video_analyzer import VideoAnalyzer
from utils.knowledge_recommender import KnowledgeRecommender
from utils.local_video_processor import LocalVideoProcessor, job_store
from config import Config

app = Flask(__name__)
config = Config()
app.secret_key = config.SECRET_KEY
# 100MB 上传限制
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

# 开发模式禁用静态资源缓存，方便 i18n 改动即时生效
@app.after_request
def no_cache_for_dev(response):
    if app.debug:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response

# 初始化各个系统
fencing_ai = FencingAI()
danmaku_system = DanmakuSystem()
fie_collector = FIEDataCollector()
youtube_parser = YouTubeParser()
video_analyzer = VideoAnalyzer()
knowledge_recommender = KnowledgeRecommender()
local_video_processor = LocalVideoProcessor()


# ============================================================
# 页面路由
# ============================================================
@app.route('/')
def index():
    return render_template('index.html')


# ============================================================
# YouTube 视频
# ============================================================
@app.route('/api/parse_youtube', methods=['POST'])
def parse_youtube():
    """解析 YouTube 链接，返回 embed URL 与缩略图"""
    try:
        data = request.get_json() or {}
        video_url = (data.get('video_url') or '').strip()
        if not video_url:
            return jsonify({'error': '请提供YouTube链接'}), 400

        video_info = youtube_parser.parse_url(video_url)
        if not video_info:
            return jsonify({'error': '无法解析YouTube链接'}), 400

        session['current_video'] = video_info
        return jsonify({'success': True, 'video_info': video_info})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# AI 聊天
# ============================================================
@app.route('/api/chat', methods=['POST'])
def chat():
    """AI 聊天接口（支持 DeepSeek / MiniMax / 本地知识库）"""
    try:
        data = request.get_json() or {}
        user_message = (data.get('message') or '').strip()
        video_context = data.get('video_context', '')
        mode = data.get('mode', 'chat')  # 'chat' 或 'danmaku'
        if not user_message:
            return jsonify({'error': '请提供消息内容'}), 400

        # 弹幕模式下让 AI 限制回复在 50 个汉字以内
        ai_response = fencing_ai.get_response(
            user_message,
            video_context=video_context,
            short_response=(mode == 'danmaku')
        )

        # 弹幕模式下，截断为 50 个汉字（不算标点和空格）
        if mode == 'danmaku':
            # 计算中文字符数（不包括标点）
            import re
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', ai_response)
            if len(chinese_chars) > 50:
                # 如果中文字数超过 50，截取包含 50 个汉字的部分
                truncated = ''
                count = 0
                for ch in ai_response:
                    truncated += ch
                    if re.match(r'[\u4e00-\u9fff]', ch):
                        count += 1
                    if count >= 50:
                        break
                ai_response = truncated.rstrip() + '...'
            elif len(ai_response) > 100:
                # 总字符数超过 100 也截断
                ai_response = ai_response[:80].rstrip() + '...'

        return jsonify({
            'success': True,
            'response': ai_response,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/advanced_analysis', methods=['POST'])
def advanced_analysis():
    """高级分析（结合多知识库类别）"""
    try:
        data = request.get_json() or {}
        question = (data.get('question') or '').strip()
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


# ============================================================
# AI 状态 / 切换
# ============================================================
@app.route('/api/ai_status', methods=['GET'])
def get_ai_status():
    try:
        status = fencing_ai.get_ai_status()
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/switch_ai', methods=['POST'])
def switch_ai():
    """切换 AI 提供商"""
    try:
        data = request.get_json() or {}
        ai_type = data.get('ai_type', 'auto')

        success = False
        if ai_type == 'deepseek':
            success = fencing_ai.switch_to_deepseek()
        elif ai_type == 'minimax':
            success = fencing_ai.switch_to_minimax()
        elif ai_type == 'local':
            success = fencing_ai.switch_to_local_ai()

        status = fencing_ai.get_ai_status()
        msg = f'已切换到{ai_type} AI系统' if success else f'无法切换到{ai_type}，请检查API密钥配置'
        return jsonify({
            'success': success,
            'message': msg,
            'status': status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 弹幕
# ============================================================
@app.route('/api/send_danmaku', methods=['POST'])
def send_danmaku():
    """发送用户弹幕"""
    try:
        data = request.get_json() or {}
        message = (data.get('message') or '').strip()
        user_id = data.get('user_id', 'anonymous')
        if not message:
            return jsonify({'error': '请提供弹幕内容'}), 400

        danmaku_id = danmaku_system.add_user_danmaku(message=message, user_id=user_id)
        return jsonify({
            'success': True,
            'danmaku_id': danmaku_id,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/get_danmaku', methods=['GET'])
def get_danmaku():
    """获取最近弹幕"""
    try:
        recent = danmaku_system.get_recent_danmaku(limit=50)
        return jsonify({'success': True, 'danmaku': recent})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate_danmaku', methods=['POST'])
def generate_danmaku():
    """生成 AI 弹幕"""
    try:
        data = request.get_json() or {}
        video_context = data.get('video_context', '')
        user_message = data.get('user_message', '')

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


@app.route('/api/quick_questions', methods=['POST'])
def quick_questions():
    """生成快速提问问题（AI 根据剑种/视频上下文生成4个相关问题）"""
    try:
        data = request.get_json() or {}
        weapon = data.get('weapon', 'auto')
        video_context = data.get('video_context', '')

        # 剑种中文名映射
        weapon_names = {
            '花剑': '花剑（FOIL）',
            '重剑': '重剑（ÉPÉE）',
            '佩剑': '佩剑（SABRE）',
            'auto': '击剑'
        }
        weapon_label = weapon_names.get(weapon, weapon)

        # 根据剑种和问题类型，构造 prompt 让 AI 生成 4 个不同问题
        # 限制每个问题 12 字以内（按钮显示需要简短）
        question_types = [
            '基础规则',
            '技术动作',
            '战术策略',
            '常见错误'
        ]
        prompt = f"""请针对{weapon_label}运动，生成 4 个常见的新手问题。
要求：
1. 每个问题不超过 12 个汉字
2. 涵盖：{ '、'.join(question_types) }
3. 适合击剑新手提问
4. 直接返回 4 行问题，每行一个问题，不要编号，不要其他说明

参考视频上下文：{video_context if video_context else '击剑比赛'}"""

        questions_text = fencing_ai.get_response(
            user_message=prompt,
            video_context=video_context,
            short_response=True  # 限制返回短文本
        )

        # 解析 4 个问题
        questions = []
        for line in questions_text.split('\n'):
            line = line.strip()
            # 去除可能的编号（"1." "1、" "①" 等）
            import re
            line = re.sub(r'^[0-9①②③④⑤⑥⑦⑧⑨⑩]+[\.、\s]\s*', '', line)
            # 去除 - * 等符号
            line = re.sub(r'^[-*•\.\s]+', '', line)
            if line and len(line) > 2:
                questions.append(line)
            if len(questions) >= 4:
                break

        # 如果不足 4 个，用剑种默认问题补全
        defaults = {
            '花剑': ['花剑的有效部位？', '花剑如何判分？', '花剑进攻动作？', '花剑的防守？'],
            '重剑': ['重剑的有效部位？', '重剑 vs 花剑？', '重剑双中怎么办？', '重剑战术特点？'],
            '佩剑': ['佩剑的得分区？', '佩剑可以劈砍吗？', '佩剑的进攻？', '佩剑的防守？'],
            'auto': ['击剑的种类？', '击剑的得分规则？', '击剑的装备？', '击剑的基本动作？']
        }
        default_list = defaults.get(weapon, defaults['auto'])
        i = 0
        while len(questions) < 4 and i < len(default_list):
            if default_list[i] not in questions:
                questions.append(default_list[i])
            i += 1

        return jsonify({
            'success': True,
            'questions': questions[:4],
            'weapon': weapon
        })
    except Exception as e:
        # 出错时返回默认问题
        return jsonify({
            'success': False,
            'error': str(e),
            'questions': ['击剑的种类？', '击剑的得分规则？', '击剑的装备？', '击剑的基本动作？']
        })


# ============================================================
# FIE 数据
# ============================================================
@app.route('/api/fie_data', methods=['GET'])
def get_fie_data():
    """获取 FIE 比赛数据"""
    try:
        lang = request.args.get('lang', 'zh')
        results = fie_collector.get_recent_results(lang=lang)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 视频分析（合并：场景/动作/关键时刻/知识点）
# ============================================================
@app.route('/api/video_insight', methods=['POST'])
def video_insight():
    """
    统一视频洞察接口：返回当前帧的场景、动作识别、相关知识。
    请求体：{ video_url, current_time, weapon? }
    """
    try:
        data = request.get_json() or {}
        video_url = data.get('video_url', '')
        current_time = int(data.get('current_time') or 0)
        weapon = data.get('weapon')  # 前端显式选择的剑种

        # 构造 frame_data，供 analyzer 使用
        frame_data = {'video_url': video_url}
        if weapon:
            frame_data['weapon'] = weapon

        # 场景 + 动作 + 知识
        scene = video_analyzer.analyze_video_scene(video_url, current_time, frame_data)
        action = video_analyzer.recognize_action(frame_data, current_time)
        knowledge_points = video_analyzer.analyze_frame(frame_data, current_time).get('knowledge_points', [])

        return jsonify({
            'success': True,
            'scene': scene,
            'action': action,
            'knowledge_points': knowledge_points,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/key_moments', methods=['POST'])
def key_moments():
    """
    检测视频关键时刻及其关联知识。
    请求体：{ video_url, duration }
    """
    try:
        data = request.get_json() or {}
        video_url = data.get('video_url', '')
        duration = int(data.get('duration') or 0)

        moments = video_analyzer.detect_key_moments(video_url, duration)
        return jsonify({'success': True, 'moments': moments})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# 本地视频上传 + AI 多模态分析
# ============================================================
@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """接收本地视频文件，启动异步分析任务"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': '未找到视频文件'}), 400
        f = request.files['video']
        if not f or not f.filename:
            return jsonify({'error': '文件无效'}), 400
        content = f.read()
        if not content:
            return jsonify({'error': '文件内容为空'}), 400
        try:
            saved = local_video_processor.save_upload(f.filename, content)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        video_id = saved['video_id']

        # 已有分析结果？直接返回，避免重复分析
        existing = local_video_processor.load_analysis(video_id)
        if existing:
            session['current_local_video'] = {
                'video_id': video_id,
                'filename': f.filename,
                'size': saved['size'],
                'analyzed': True,
            }
            return jsonify({
                'success': True,
                'video_id': video_id,
                'filename': f.filename,
                'size': saved['size'],
                'cached': True,
                'analysis': existing,
            })

        # 否则启动异步分析
        weapon_hint = (request.form.get('weapon') or '').strip()
        lang = (request.form.get('lang') or 'zh').strip().lower()
        if lang not in ('zh', 'en', 'ja'):
            lang = 'zh'
        job_id = local_video_processor.analyze_async(video_id, saved['path'], weapon_hint, lang)
        session['current_local_video'] = {
            'video_id': video_id,
            'filename': f.filename,
            'size': saved['size'],
            'job_id': job_id,
            'analyzed': False,
        }
        return jsonify({
            'success': True,
            'video_id': video_id,
            'filename': f.filename,
            'size': saved['size'],
            'job_id': job_id,
            'cached': False,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze_status/<job_id>', methods=['GET'])
def analyze_status(job_id: str):
    """轮询分析任务状态"""
    job = job_store.get(job_id)
    if not job:
        return jsonify({'error': '任务不存在或已过期'}), 404
    return jsonify({
        'success': True,
        'status': job.get('status'),
        'progress': job.get('progress', 0),
        'step': job.get('step', ''),
        'error': job.get('error'),
        'result': job.get('result') if job.get('status') == 'done' else None,
    })


@app.route('/api/local_video/<video_id>')
def serve_local_video(video_id: str):
    """流式返回本地视频文件（支持 Range 协议）"""
    from utils.local_video_processor import UPLOAD_DIR
    # 找到对应文件
    for ext in ('.mp4', '.mov', '.webm', '.avi', '.mkv', '.m4v'):
        candidate = os.path.join(UPLOAD_DIR, f"{video_id}{ext}")
        if os.path.exists(candidate):
            return send_from_directory(
                UPLOAD_DIR,
                f"{video_id}{ext}",
                conditional=True,  # 支持 Range
            )
    return jsonify({'error': '视频不存在'}), 404


@app.route('/api/analysis/<video_id>', methods=['GET'])
def get_analysis(video_id: str):
    """获取已完成分析的结果（用于页面刷新后恢复）"""
    data = local_video_processor.load_analysis(video_id)
    if not data:
        return jsonify({'error': '未找到分析结果'}), 404
    return jsonify({'success': True, 'analysis': data})


# ============================================================
# 错误处理
# ============================================================
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': '文件超过 100MB 限制'}), 413


@app.route('/api/knowledge_recommend', methods=['POST'])
def knowledge_recommend():
    """
    基于视频上下文推荐相关知识。
    请求体：{ weapon, action?, stage? }
    """
    try:
        data = request.get_json() or {}
        ctx = {
            'weapon': data.get('weapon', ''),
            'stage': data.get('stage', ''),
            'action': data.get('action', {}) or {},
        }
        recs = knowledge_recommender.recommend(ctx, user_id=data.get('user_id', 'default'))
        return jsonify({'success': True, 'recommendations': recs})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8888)
