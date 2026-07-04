"""
本地视频处理模块 - 帧提取 + AI 多模态分析 + 持久化

流程：
1. ffmpeg 抽帧（每 N 秒一帧，缩放到 480p 省 token）
2. 把帧 base64 编码批量送入 LLM（带多模态能力的部分 provider）
3. 让 LLM 返回结构化 JSON：关键时刻、动作识别、文字/字幕
4. 落地到 data/analysis/{video_id}.json
5. 通过内存 job_store 暴露进度供前端轮询
"""
import os
import io
import re
import json
import time
import base64
import hashlib
import logging
import subprocess
import threading
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)

# 文件大小限制（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024
ALLOWED_EXT = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}

# 落地目录
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "uploads")
FRAME_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "frames")
ANALYSIS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "analysis")

for d in (UPLOAD_DIR, FRAME_DIR, ANALYSIS_DIR):
    os.makedirs(d, exist_ok=True)


class JobStore:
    """轻量级内存任务状态（重启即丢失，符合"本地"语义）"""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, video_id: str) -> str:
        job_id = uuid.uuid4().hex[:16]
        with self._lock:
            self._jobs[job_id] = {
                "job_id": job_id,
                "video_id": video_id,
                "status": "pending",  # pending / running / done / error
                "progress": 0,
                "step": "等待开始",
                "result": None,
                "error": None,
                "created_at": time.time(),
            }
        return job_id

    def update(self, job_id: str, **kwargs) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.update(kwargs)

    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            job = self._jobs.get(job_id)
            return dict(job) if job else None

    def cleanup(self, max_age: int = 3600) -> None:
        """清理 1 小时前的旧任务"""
        cutoff = time.time() - max_age
        with self._lock:
            for jid in list(self._jobs.keys()):
                if self._jobs[jid].get("created_at", 0) < cutoff:
                    del self._jobs[jid]


job_store = JobStore()


class LocalVideoProcessor:
    """本地视频处理器"""

    def __init__(self) -> None:
        self.config = Config()

    # ----------------------------------------------------------
    # 工具
    # ----------------------------------------------------------
    @staticmethod
    def compute_video_id(filename: str, content: bytes) -> str:
        """根据文件名+内容前 1MB 算一个稳定 id（同名不同内容也能区分）"""
        h = hashlib.sha1()
        h.update(filename.encode("utf-8"))
        h.update(content[: 1024 * 1024])
        return h.hexdigest()[:16]

    @staticmethod
    def get_video_info(video_path: str) -> Dict[str, Any]:
        """用 ffprobe 取时长和帧率"""
        try:
            out = subprocess.check_output(
                [
                    "ffprobe", "-v", "error",
                    "-select_streams", "v:0",
                    "-show_entries", "stream=width,height,r_frame_rate,duration:format=duration",
                    "-of", "json",
                    video_path,
                ],
                stderr=subprocess.STDOUT,
                timeout=15,
            )
            data = json.loads(out.decode("utf-8", errors="ignore"))
            stream = (data.get("streams") or [{}])[0]
            fmt = data.get("format") or {}
            duration = float(fmt.get("duration") or stream.get("duration") or 0)
            width = int(stream.get("width") or 0)
            height = int(stream.get("height") or 0)
            fps_str = stream.get("r_frame_rate") or "0/1"
            try:
                num, den = fps_str.split("/")
                fps = float(num) / float(den) if float(den) else 0
            except Exception:
                fps = 0
            return {
                "duration": duration,
                "width": width,
                "height": height,
                "fps": fps,
            }
        except Exception as e:
            logger.warning("ffprobe 失败: %s", e)
            return {"duration": 0, "width": 0, "height": 0, "fps": 0}

    @staticmethod
    def extract_frames(video_path: str, out_dir: str, interval_sec: float = 5.0,
                       max_frames: int = 24, target_w: int = 640) -> List[Dict[str, Any]]:
        """每 interval_sec 秒抽一帧，最多 max_frames 帧

        优先用 PyAV（libav 解码，不依赖 ffmpeg muxer），失败时再尝试 ffmpeg 命令。
        用 PIL 缩放并转 jpeg + base64。
        """
        os.makedirs(out_dir, exist_ok=True)
        info = LocalVideoProcessor.get_video_info(video_path)
        duration = info["duration"]
        if duration <= 0:
            duration = 300

        # 抽帧时刻
        times = []
        t = 1.0
        while t < duration and len(times) < max_frames:
            times.append(round(t, 2))
            t += interval_sec

        results: List[Dict[str, Any]] = []
        # 优先用 PyAV
        try:
            import av
            container = av.open(video_path)
            stream = container.streams.video[0]
            # 设置 pts-based seek
            stream.codec_context.thread_type = "AUTO"
            # 用 seek + decode 方式取帧
            # 简化：顺序解码，记录每帧 pts，找到最接近 target 的帧
            for ts in times:
                # seek 到目标位置（前后都留点余量）
                tb = float(stream.time_base) if stream.time_base else 1/30
                target_pts = int(ts / tb)
                # 用 frame.index 和平均帧率估计
                container.seek(target_pts, backward=True, any_frame=False)
                # 解码到目标帧附近
                best_frame = None
                best_diff = float('inf')
                for frame in container.decode(video=0):
                    if frame.pts is None:
                        continue
                    diff = abs(frame.pts - target_pts)
                    if diff < best_diff:
                        best_diff = diff
                        best_frame = frame
                    if frame.pts and frame.pts >= target_pts:
                        break
                if best_frame is None:
                    continue
                img = best_frame.to_image()  # PIL.Image
                if img.width > target_w:
                    nh = int(img.height * target_w / img.width)
                    img = img.resize((target_w, nh), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=70)
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                jpg_path = os.path.join(out_dir, f"frame_{int(ts*1000):08d}.jpg")
                results.append({
                    "time": ts,
                    "path": jpg_path,
                    "b64": b64,
                })
            container.close()
            if results:
                return results
        except Exception as e:
            logger.warning("PyAV 抽帧失败 fallback 到 ffmpeg: %s", e)

        # Fallback: ffmpeg 抽帧
        for idx, ts in enumerate(times):
            try:
                proc = subprocess.run(
                    [
                        "ffmpeg", "-y", "-loglevel", "error",
                        "-ss", f"{ts}",
                        "-i", video_path,
                        "-frames:v", "1",
                        "-an", "-sn",
                        "-c:v", "mjpeg",   # 尝试 mjpeg
                        "-f", "mp4",
                        "-",
                    ],
                    capture_output=True,
                    timeout=20,
                )
                if proc.returncode != 0 or not proc.stdout:
                    # 再尝试 bmp (image2 family) - 但通常也不支持
                    proc = subprocess.run(
                        [
                            "ffmpeg", "-y", "-loglevel", "error",
                            "-ss", f"{ts}",
                            "-i", video_path,
                            "-frames:v", "1",
                            "-an", "-sn",
                            "-f", "mp4",
                            "-c:v", "libx264",
                            "-",
                        ],
                        capture_output=True,
                        timeout=20,
                    )
                    if proc.returncode != 0 or not proc.stdout:
                        logger.warning("ffmpeg fallback 也失败 t=%.2f", ts)
                        continue

                # 写入临时 mp4，再用 PyAV 解码（PyAV 已经初始化过，缓存）
                tmp_mp4 = os.path.join(out_dir, f"_tmp_{idx:03d}.mp4")
                with open(tmp_mp4, "wb") as f:
                    f.write(proc.stdout)
                try:
                    import av
                    c2 = av.open(tmp_mp4)
                    for fr in c2.decode(video=0):
                        img = fr.to_image()
                        if img.width > target_w:
                            nh = int(img.height * target_w / img.width)
                            img = img.resize((target_w, nh), Image.LANCZOS)
                        buf = io.BytesIO()
                        img.save(buf, format="JPEG", quality=70)
                        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                        jpg_path = os.path.join(out_dir, f"frame_{int(ts*1000):08d}.jpg")
                        results.append({
                            "time": ts,
                            "path": jpg_path,
                            "b64": b64,
                        })
                        break
                    c2.close()
                finally:
                    try:
                        os.remove(tmp_mp4)
                    except Exception:
                        pass
            except Exception as e:
                logger.warning("ffmpeg 抽帧异常 t=%.2f: %s", ts, e)
                continue

        return results

    # ----------------------------------------------------------
    # AI 分析
    # ----------------------------------------------------------
    def _call_vision_llm(self, frames_b64: List[str], weapon_hint: str) -> Dict[str, Any]:
        """调用 LLM 多模态分析帧序列，返回结构化结果"""
        from utils.fencing_ai import FencingAI
        ai = FencingAI()
        provider = ai.current_provider if hasattr(ai, "current_provider") else self.config.LLM_PROVIDER

        # 组装多模态消息
        content: List[Dict[str, Any]] = [{
            "type": "text",
            "text": (
                "你是一名击剑视频分析专家。下面是一段击剑视频中按时间顺序抽出的关键帧（每张约 5 秒间隔）。"
                f"用户提示的剑种为：{weapon_hint or '未知'}。\n\n"
                "请逐帧分析并按以下 JSON 格式输出（不要包裹 markdown 代码块）：\n"
                "{\n"
                '  "key_moments": [{"time": 秒数, "type": "进攻/防守/得分/失误/精彩", '
                '"title": "短标题", "description": "该时刻在做什么", "tactic": "战术解读"}],\n'
                '  "actions": [{"time": 秒数, "action": "直刺/劈/格挡/...", "confidence": 0-1, "note": "备注"}],\n'
                '  "text_in_video": ["视频中出现的文字/字幕/比分/姓名等"],\n'
                '  "summary": "对整段视频 100 字以内的整体描述",\n'
                '  "weapon_guess": "花剑/重剑/佩剑/未知"\n'
                "}\n"
                "只输出 JSON，不要其他说明。"
            )
        }]
        for f in frames_b64:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{f}"},
            })

        messages = [
            {"role": "system", "content": "你是击剑视频分析助手，只返回严格 JSON。"},
            {"role": "user", "content": content},
        ]

        result_text = ""
        try:
            # DeepSeek/MiniMax/OpenAI 兼容接口
            base_url = self.config.DEEPSEEK_BASE_URL
            api_key = self.config.DEEPSEEK_API_KEY
            if provider == "minimax":
                base_url = self.config.MINIMAX_BASE_URL
                api_key = self.config.MINIMAX_API_KEY
            elif provider == "local":
                base_url = "http://localhost:11434/v1"
                api_key = "ollama"

            # DeepSeek 当前没有视觉；切换到 OpenAI 兼容的多模态服务（如 siliconflow/qwen-vl）
            # 这里走 siliconflow 作为多模态 fallback
            try:
                result_text = self._call_siliconflow_vision(messages, frames_b64, weapon_hint)
            except Exception as e:
                logger.warning("多模态 API 失败：%s，使用启发式回退", e)
                result_text = ""
        except Exception as e:
            logger.warning("多模态调用异常: %s", e)

        # 解析 JSON
        if result_text:
            m = re.search(r"\{[\s\S]*\}", result_text)
            if m:
                try:
                    return json.loads(m.group(0))
                except Exception as e:
                    logger.warning("JSON 解析失败: %s\n原始: %s", e, result_text[:300])

        # 启发式回退：基于采样时间均匀给出关键时刻
        return self._fallback_analysis(frames_b64, weapon_hint)

    def _call_siliconflow_vision(self, messages, frames_b64, weapon_hint) -> str:
        """调用 siliconflow Qwen2-VL 进行多模态分析（用户需配置 SILICONFLOW_API_KEY）"""
        api_key = os.getenv("SILICONFLOW_API_KEY", "")
        if not api_key:
            raise RuntimeError("SILICONFLOW_API_KEY 未配置")

        url = "https://api.siliconflow.cn/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": os.getenv("SILICONFLOW_VL_MODEL", "Qwen/Qwen2-VL-72B-Instruct"),
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1500,
        }
        import requests
        r = requests.post(url, json=payload, headers=headers, timeout=120)
        r.raise_for_status()
        data = r.json()
        return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")

    @staticmethod
    def _fallback_analysis(frames_b64: List[str], weapon_hint: str) -> Dict[str, Any]:
        """无 API key / API 失败时的启发式分析"""
        n = len(frames_b64)
        interval = 5
        moments = []
        actions = [
            {"time": interval * (i + 1), "action": "试探", "confidence": 0.55, "note": "启发式推断（未配置多模态 API）"}
            for i in range(min(4, n))
        ]
        if n >= 2:
            moments = [
                {"time": interval, "type": "进攻", "title": "试探进攻",
                 "description": "选手开始试探对手节奏与距离", "tactic": "观察对手防守习惯"},
                {"time": interval * max(1, n // 2), "type": "精彩", "title": "中段对攻",
                 "description": "双方进入中距离交锋", "tactic": "注意控制距离"},
                {"time": interval * max(2, n - 1), "type": "得分", "title": "关键得分",
                 "description": "出现一次有效得分动作", "tactic": "把握时机"},
            ]
        return {
            "key_moments": moments,
            "actions": actions,
            "text_in_video": [],
            "summary": f"已采样 {n} 帧，未配置多模态 API 时仅能给出启发式标记。配置 SILICONFLOW_API_KEY 后可获得更精确识别。",
            "weapon_guess": weapon_hint or "未知",
        }

    # ----------------------------------------------------------
    # 公开入口
    # ----------------------------------------------------------
    def analyze_async(self, video_id: str, video_path: str, weapon_hint: str) -> str:
        """异步分析：返回 job_id，后台线程跑完后写入 job_store"""
        job_id = job_store.create(video_id)
        thread = threading.Thread(
            target=self._analyze_worker,
            args=(job_id, video_id, video_path, weapon_hint),
            daemon=True,
        )
        thread.start()
        return job_id

    def _analyze_worker(self, job_id: str, video_id: str, video_path: str, weapon_hint: str) -> None:
        try:
            job_store.update(job_id, status="running", progress=5, step="读取视频元数据")
            info = self.get_video_info(video_path)
            duration = info["duration"]
            if duration <= 0:
                duration = 300
            # 根据视频时长动态决定抽帧数：5s 一帧，封顶 30
            interval = 5.0
            max_frames = min(30, max(8, int(duration / interval) + 1))

            job_store.update(job_id, progress=15, step=f"抽帧中（间隔 {interval}s，最多 {max_frames} 帧）")
            frames = self.extract_frames(
                video_path,
                out_dir=os.path.join(FRAME_DIR, video_id),
                interval_sec=interval,
                max_frames=max_frames,
            )
            if not frames:
                raise RuntimeError("未能抽到任何帧，请检查视频文件")

            job_store.update(job_id, progress=55, step=f"AI 多模态分析（{len(frames)} 帧）")
            # 只把 b64 送给 LLM，不写盘以省空间
            frames_b64 = [f["b64"] for f in frames]
            ai_result = self._call_vision_llm(frames_b64, weapon_hint)

            job_store.update(job_id, progress=85, step="汇总时间轴")
            # 整理最终结果
            result = {
                "video_id": video_id,
                "duration": duration,
                "fps": info["fps"],
                "resolution": f"{info['width']}x{info['height']}",
                "frame_count": len(frames),
                "key_moments": ai_result.get("key_moments", []),
                "actions": ai_result.get("actions", []),
                "text_in_video": ai_result.get("text_in_video", []),
                "summary": ai_result.get("summary", ""),
                "weapon_guess": ai_result.get("weapon_guess", weapon_hint or "未知"),
                "analyzed_at": datetime.now().isoformat(),
            }

            # 持久化
            self._save_analysis(video_id, result)
            job_store.update(
                job_id,
                status="done",
                progress=100,
                step="完成",
                result=result,
            )
        except Exception as e:
            logger.exception("analyze worker 失败")
            job_store.update(job_id, status="error", error=str(e), step="失败")

    @staticmethod
    def _save_analysis(video_id: str, result: Dict[str, Any]) -> None:
        path = os.path.join(ANALYSIS_DIR, f"{video_id}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_analysis(video_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(ANALYSIS_DIR, f"{video_id}.json")
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    @staticmethod
    def save_upload(filename: str, content: bytes) -> Dict[str, Any]:
        """保存上传文件，返回 video_id 与文件路径"""
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXT:
            raise ValueError(f"不支持的视频格式: {ext}")
        if len(content) > MAX_FILE_SIZE:
            raise ValueError(f"文件过大，超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制")
        video_id = LocalVideoProcessor.compute_video_id(filename, content)
        path = os.path.join(UPLOAD_DIR, f"{video_id}{ext}")
        with open(path, "wb") as f:
            f.write(content)
        return {
            "video_id": video_id,
            "path": path,
            "size": len(content),
            "ext": ext,
        }

    @staticmethod
    def build_chat_context(analysis: Dict[str, Any]) -> str:
        """把分析结果转成 AI 提问时的上下文文本"""
        if not analysis:
            return ""
        parts = []
        dur = analysis.get("duration", 0)
        parts.append(f"用户上传了本地视频（{analysis.get('resolution','?')}，约 {int(dur)}s）。")
        wg = analysis.get("weapon_guess")
        if wg and wg != "未知":
            parts.append(f"系统推测剑种：{wg}。")
        if analysis.get("summary"):
            parts.append(f"整体概述：{analysis['summary']}")
        km = analysis.get("key_moments") or []
        if km:
            km_lines = [f"- {int(m.get('time',0))}s [{m.get('type','')}] {m.get('title','')}: {m.get('description','')}"
                        for m in km[:8]]
            parts.append("关键时刻：\n" + "\n".join(km_lines))
        acts = analysis.get("actions") or []
        if acts:
            act_lines = [f"- {int(a.get('time',0))}s {a.get('action','')} ({a.get('confidence',0):.0%}): {a.get('note','')}"
                         for a in acts[:8]]
            parts.append("识别动作：\n" + "\n".join(act_lines))
        txt = analysis.get("text_in_video") or []
        if txt:
            parts.append("视频中出现的文字/字幕：\n" + "\n".join(f"- {t}" for t in txt[:8]))
        return "\n\n".join(parts)


# 简单 Pillow 缺失保护
try:
    from PIL import Image  # noqa: F401
except ImportError:
    logger.error("缺少依赖 Pillow，请 pip install Pillow")
    raise
