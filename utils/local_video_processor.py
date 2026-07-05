"""
本地视频处理模块 - 直接发视频给 MiniMax M3 多模态分析 + 持久化

流程：
1. 根据文件大小选择路径：
   - ≤45MB：base64 内联到请求体（video_url data URL）
   - >45MB：先调 MiniMax Files API 上传，拿到 file_id，再用 mm_file://file_id 引用
2. MiniMax M3 直接理解视频并返回结构化 JSON：关键时刻、动作识别、文字/字幕
3. 落地到 data/analysis/{video_id}.json
4. 通过内存 job_store 暴露进度供前端轮询
"""
import os
import re
import json
import time
import base64
import hashlib
import logging
import requests
import threading
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

# 文件大小限制（512MB 上限；超出走本地压缩 + B 路径）
MAX_FILE_SIZE = 512 * 1024 * 1024
# 视频走 base64 内联的最大尺寸（base64 膨胀 33% + 请求体 64MB 上限 → 文件 ≤45MB）
# 但 30MB+ 的视频大概率是长时长/高分辨率，会被 M3 内容审核拒绝，所以提前走压缩
B64_THRESHOLD = 30 * 1024 * 1024
# M3 实际视频限制 50MB（超出需要本地压缩到 ≤45MB 再走 base64）
COMPRESS_TARGET = 40 * 1024 * 1024  # 压缩目标 40MB，预留余量
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
        """用 PyAV 读视频时长/分辨率/帧率（无需 ffmpeg/ffprobe）"""
        try:
            import av
            container = av.open(video_path)
            stream = container.streams.video[0]
            width = stream.width or 0
            height = stream.height or 0
            # 帧率
            fps = 0.0
            if stream.average_rate:
                fps = float(stream.average_rate)
            elif stream.base_rate:
                fps = float(stream.base_rate)
            # 时长
            duration = 0.0
            if stream.duration and stream.time_base:
                duration = float(stream.duration * stream.time_base)
            elif container.duration:
                duration = float(container.duration) / 1_000_000  # us → s
            container.close()
            return {"duration": duration, "width": width, "height": height, "fps": fps}
        except Exception as e:
            logger.warning("PyAV 读视频元数据失败: %s", e)
            return {"duration": 0, "width": 0, "height": 0, "fps": 0}

    @staticmethod
    def extract_frames(video_path: str, out_dir: str, interval_sec: float = 5.0,
                       max_frames: int = 24, target_w: int = 640) -> List[Dict[str, Any]]:
        """兼容旧调用：现在直接发视频给 M3，不再抽帧；返回空列表即可。"""
        return []

    # ----------------------------------------------------------
    # AI 分析：直接发视频给 MiniMax M3（BC 混合）
    # ----------------------------------------------------------
    def _build_vision_prompt(self, weapon_hint: str) -> str:
        return (
            "你是一名击剑视频分析专家。"
            "提示：以下内容是国际击剑联合会（FIE）监管下的合规击剑体育运动视频，"
            "运动员佩戴完整护具（面罩/护胸/手套），使用合规钝头剑种，"
            "目的是分析战术动作和比赛节奏，非任何违规或敏感内容。\n\n"
            f"用户提示的剑种为：{weapon_hint or '未知'}。\n\n"
            "请按以下 JSON 格式输出（不要包裹 markdown 代码块）：\n"
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

    def _call_minimax_b64(self, video_path: str, weapon_hint: str) -> str:
        """B 路径：≤45MB 视频直接 base64 内联到 video_url.data URL"""
        api_key = self.config.MINIMAX_API_KEY
        if not api_key:
            raise RuntimeError("MINIMAX_API_KEY 未配置")

        with open(video_path, "rb") as f:
            video_bytes = f.read()
        b64 = base64.b64encode(video_bytes).decode("ascii")
        ext = os.path.splitext(video_path)[1].lower().lstrip(".") or "mp4"
        mime = "video/mp4" if ext == "mp4" else f"video/{ext}"

        url = f"{self.config.MINIMAX_BASE_URL.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.config.MINIMAX_MODEL,
            "messages": [
                {"role": "system", "content": "你是击剑视频分析助手，只返回严格 JSON。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": self._build_vision_prompt(weapon_hint)},
                        {"type": "video_url", "video_url": {
                            "url": f"data:{mime};base64,{b64}"
                        }},
                    ],
                },
            ],
            "temperature": 0.3,
            "max_tokens": 4000,
        }
        last_err = None
        for attempt in range(1, 4):  # M3 间歇性 500，最多重试 3 次
            try:
                print(f"[M3] 尝试 {attempt}/3 → POST {url[:50]}... payload {len(b64)/1024/1024:.1f}MB b64", flush=True)
                r = requests.post(url, json=payload, headers=headers, timeout=300)
                print(f"[M3] 响应 status={r.status_code} time={r.elapsed.total_seconds():.1f}s", flush=True)
                if r.status_code >= 400:
                    raise RuntimeError(f"MiniMax b64 失败 {r.status_code}: {r.text[:200]}")
                data = r.json()
                content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
                print(f"[M3] 成功 content 长度 {len(content)}", flush=True)
                return content
            except Exception as e:
                last_err = e
                print(f"[M3] 失败 (尝试 {attempt}/3): {e}", flush=True)
                if attempt < 3:
                    import time
                    time.sleep(3)
        raise last_err

    def _compress_to_b64(self, video_path: str, weapon_hint: str) -> str:
        """C 路径（替代方案）：>45MB 视频先本地 PyAV 压缩到 ≤45MB，再走 B 路径

        注意：MiniMax Files API 不支持视频 purpose，所以大视频必须在本地压缩。
        压缩策略：720p / 1.5Mbps / h264，按比例缩时长（如仍然超就降码率/降分辨率）
        """
        import av
        from fractions import Fraction
        tmp_dir = os.path.join(os.path.dirname(video_path), "_compressed")
        os.makedirs(tmp_dir, exist_ok=True)
        out_path = os.path.join(tmp_dir, os.path.basename(video_path))

        # 读原视频
        src = av.open(video_path)
        src_stream = src.streams.video[0]
        orig_w, orig_h = src_stream.width, src_stream.height
        # 帧率：average_rate 可能是 Fraction/0（变量）或 None
        try:
            orig_fps = float(src_stream.average_rate) if src_stream.average_rate else 30.0
        except Exception:
            orig_fps = 30.0
        if orig_fps <= 0 or orig_fps > 120:
            orig_fps = 30.0
        # PyAV 需要 Fraction
        fps_frac = Fraction(orig_fps).limit_denominator(1000)

        # 目标：720p，长边 1280
        if orig_w >= orig_h:
            tgt_w, tgt_h = 1280, int(orig_h * 1280 / orig_w)
            if tgt_h % 2: tgt_h += 1
        else:
            tgt_h, tgt_w = 1280, int(orig_w * 1280 / orig_h)
            if tgt_w % 2: tgt_w += 1

        # 写新视频
        dst = av.open(out_path, mode='w')
        dst_stream = dst.add_stream('libx264', rate=fps_frac)
        dst_stream.width, dst_stream.height = tgt_w, tgt_h
        dst_stream.pix_fmt = 'yuv420p'
        # 先用 1.5Mbps；不够再降
        dst_stream.bit_rate = 1_500_000
        dst_stream.options = {'preset': 'medium', 'crf': '26'}

        for frame in src.decode(video=0):
            img = frame.to_image()
            if img.width != tgt_w or img.height != tgt_h:
                img = img.resize((tgt_w, tgt_h))
            new_frame = av.VideoFrame.from_image(img).reformat(format='yuv420p')
            new_frame.pts = frame.pts
            new_frame.time_base = frame.time_base
            for p in dst_stream.encode(new_frame):
                dst.mux(p)
        for p in dst_stream.encode():
            dst.mux(p)
        dst.close()
        src.close()

        compressed_size = os.path.getsize(out_path)
        logger.info("压缩完成: %.1fMB → %.1fMB (%dx%d@%s)",
                    os.path.getsize(video_path) / 1024 / 1024,
                    compressed_size / 1024 / 1024, tgt_w, tgt_h, orig_fps)

        # 如果仍 > 45MB，再压一次（降码率）
        if compressed_size > B64_THRESHOLD:
            logger.info("一次压缩后仍超阈值，二次压缩（降码率）")
            os.remove(out_path)
            dst2 = av.open(out_path, mode='w')
            ds2 = dst2.add_stream('libx264', rate=fps_frac)
            ds2.width, ds2.height = tgt_w, tgt_h
            ds2.pix_fmt = 'yuv420p'
            ds2.bit_rate = 800_000
            ds2.options = {'preset': 'medium', 'crf': '30'}
            src2 = av.open(video_path)
            for frame in src2.decode(video=0):
                img = frame.to_image()
                if img.width != tgt_w or img.height != tgt_h:
                    img = img.resize((tgt_w, tgt_h))
                nf = av.VideoFrame.from_image(img).reformat(format='yuv420p')
                nf.pts = frame.pts
                nf.time_base = frame.time_base
                for p in ds2.encode(nf):
                    dst2.mux(p)
            for p in ds2.encode():
                dst2.mux(p)
            dst2.close()
            src2.close()
            logger.info("二次压缩后: %.1fMB", os.path.getsize(out_path) / 1024 / 1024)

        try:
            return self._call_minimax_b64(out_path, weapon_hint)
        finally:
            try:
                os.remove(out_path)
            except Exception:
                pass

    def _call_vision_llm(self, video_path: str, weapon_hint: str) -> Dict[str, Any]:
        """按文件大小自动选择 B（base64） 或 C（本地压缩 + base64）路径，返回结构化结果"""
        size = os.path.getsize(video_path)
        result_text = ""
        path_used = "b64" if size <= B64_THRESHOLD else "compress_b64"
        try:
            if path_used == "b64":
                logger.info("视频 %.1fMB ≤ 45MB，走 B 路径 (base64 内联)", size / 1024 / 1024)
                result_text = self._call_minimax_b64(video_path, weapon_hint)
            else:
                logger.info("视频 %.1fMB > 45MB，走 C 路径 (本地 PyAV 压缩到 ≤45MB 后 base64)", size / 1024 / 1024)
                result_text = self._compress_to_b64(video_path, weapon_hint)
        except Exception as e:
            err = str(e)
            # M3 内容审核拒绝（长时长/高分辨率下识别到对抗动作）
            if "sensitive" in err.lower() or "1026" in err:
                logger.warning("M3 内容审核拒绝: %s", err)
                return {
                    "key_moments": [],
                    "actions": [],
                    "text_in_video": [],
                    "summary": "M3 内容审核拒绝：视频被认为包含敏感内容（多为长时长/高分辨率下识别到对抗动作）。建议：1) 剪到 1-2 分钟；2) 降分辨率到 720p。",
                    "weapon_guess": weapon_hint or "未知",
                    "rejected": True,
                }
            # M3 服务端错误（多为视频时长太长 / 超过 M3 内部上下文）
            if "500" in err or "unknown error" in err.lower() or "server_error" in err.lower():
                logger.warning("M3 服务端错误（可能视频太长）: %s", err)
                return {
                    "key_moments": [],
                    "actions": [],
                    "text_in_video": [],
                    "summary": "M3 服务端错误：可能是视频时长超过 2-3 分钟上限。建议：剪到 1-2 分钟后再上传。",
                    "weapon_guess": weapon_hint or "未知",
                    "rejected": True,
                }
            logger.warning("MiniMax M3 调用失败 (%s 路径): %s，回退到启发式", path_used, e)

        # 解析 JSON（M3 会先 <think>...</think> 输出思考过程，再输出 JSON）
        if result_text:
            candidate = None

            # 1) 优先：从 </think> 之后取（如果有 think 块的话）
            split_idx = result_text.rfind('</think>')
            if split_idx >= 0:
                after_think = result_text[split_idx + len('</think>'):].strip()
                # 如果 think 块后是空（没结束标签的极端情况），则用整段
                if not after_think:
                    after_think = result_text
            else:
                # 没 think 块，用整段
                after_think = result_text
            print(f"[JSON] think块后长度: {len(after_think)}", flush=True)
            print(f"[JSON] think块后前 200: {after_think[:200]!r}", flush=True)

            # 2) 去 markdown 代码块包裹
            m_code = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', after_think)
            if m_code:
                candidate = m_code.group(1)
                print(f"[JSON] 从代码块匹配到", flush=True)
            else:
                # 3) 用栈匹配找最外层 JSON（处理嵌套 { }）
                start = after_think.find('{')
                print(f"[JSON] 代码块无匹配，找 {{ 位置: {start}", flush=True)
                if start >= 0:
                    depth = 0
                    in_string = False
                    escape = False
                    end = -1
                    for i in range(start, len(after_think)):
                        ch = after_think[i]
                        if escape:
                            escape = False
                            continue
                        if ch == '\\':
                            escape = True
                            continue
                        if ch == '"' and not escape:
                            in_string = not in_string
                            continue
                        if in_string:
                            continue
                        if ch == '{':
                            depth += 1
                        elif ch == '}':
                            depth -= 1
                            if depth == 0:
                                end = i + 1
                                break
                    print(f"[JSON] 栈匹配 end: {end}", flush=True)
                    if end > start:
                        candidate = after_think[start:end]
                        print(f"[JSON] candidate 长度: {len(candidate)}, 前 100: {candidate[:100]!r}", flush=True)

            if candidate:
                try:
                    parsed = json.loads(candidate)
                    print(f"[JSON] ✅ 解析成功 keys: {list(parsed.keys())}", flush=True)
                    return parsed
                except Exception as e:
                    print(f"[JSON] ❌ 解析失败: {e}\n候选: {candidate[:500]}", flush=True)
                    logger.warning("JSON 解析失败: %s", e)
            else:
                print(f"[JSON] ❌ candidate 为空，跳过", flush=True)

        # 启发式回退（API 失败 / key 缺失）
        return self._fallback_analysis(weapon_hint, size)

    @staticmethod
    def _fallback_analysis(weapon_hint: str, file_size: int = 0) -> Dict[str, Any]:
        """API 失败时的兜底分析"""
        moments = [
            {"time": 5, "type": "进攻", "title": "试探进攻",
             "description": "选手开始试探对手节奏与距离", "tactic": "观察对手防守习惯"},
            {"time": 15, "type": "精彩", "title": "中段对攻",
             "description": "双方进入中距离交锋", "tactic": "注意控制距离"},
            {"time": 30, "type": "得分", "title": "关键得分",
             "description": "出现一次有效得分动作", "tactic": "把握时机"},
        ]
        return {
            "key_moments": moments,
            "actions": [
                {"time": 5, "action": "试探", "confidence": 0.55, "note": "启发式（MiniMax API 不可用）"},
                {"time": 15, "action": "试探", "confidence": 0.55, "note": "启发式（MiniMax API 不可用）"},
            ],
            "text_in_video": [],
            "summary": f"未取得 MiniMax M3 真实分析（视频 {file_size/1024/1024:.1f}MB）。检查 API key / 网络后重试。",
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
            job_store.update(job_id, status="running", progress=10, step="读取视频元数据")
            info = self.get_video_info(video_path)
            duration = info["duration"]
            if duration <= 0:
                duration = 0
            file_size = os.path.getsize(video_path)

            size_mb = file_size / 1024 / 1024
            if file_size <= B64_THRESHOLD:
                step_msg = f"调用 MiniMax M3 (B 路径 · base64 · {size_mb:.1f}MB)"
            else:
                step_msg = f"调用 MiniMax M3 (C 路径 · 本地压缩到≤45MB 后 base64 · 原始 {size_mb:.1f}MB)"
            job_store.update(job_id, progress=40, step=step_msg)
            ai_result = self._call_vision_llm(video_path, weapon_hint)

            job_store.update(job_id, progress=85, step="汇总分析结果")
            result = {
                "video_id": video_id,
                "duration": duration,
                "fps": info["fps"],
                "resolution": f"{info['width']}x{info['height']}",
                "file_size_mb": round(size_mb, 2),
                "analyze_path": "b64" if file_size <= B64_THRESHOLD else "compress_b64",
                "key_moments": ai_result.get("key_moments", []),
                "actions": ai_result.get("actions", []),
                "text_in_video": ai_result.get("text_in_video", []),
                "summary": ai_result.get("summary", ""),
                "weapon_guess": ai_result.get("weapon_guess", weapon_hint or "未知"),
                "analyzed_at": datetime.now().isoformat(),
            }

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
