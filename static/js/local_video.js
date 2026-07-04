/**
 * Local Video System - 本地视频上传 + AI 多模态分析 + 时间轴渲染 + 上下文注入
 *
 * 流程：
 * 1. 用户点击"本地视频"按钮 → 弹出文件选择器
 * 2. 选择文件后校验大小/格式 → POST /api/upload_video
 * 3. 进度模态框显示：上传 → 抽帧 → AI 分析
 * 4. 轮询 /api/analyze_status/<job_id> 获取进度
 * 5. 完成后：
 *    - 用 <video> 替换 #video-player 内的内容，src 指向 /api/local_video/<video_id>
 *    - 渲染 #analysis-panel（summary + 关键时刻 + 动作）
 *    - 注入聊天上下文（视频摘要会作为 system context 传给 AI）
 * 6. 关键时刻点击 → 跳转视频到该时间
 */
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const ALLOWED_EXT = ['mp4', 'mov', 'webm', 'avi', 'mkv', 'm4v'];

class LocalVideoSystem {
    constructor() {
        this.videoId = null;
        this.analysis = null;
        this.videoEl = null;       // 当前 <video> 元素
        this.polling = null;        // 进度轮询定时器
        this.uploadedFilename = '';
        this._contextKey = null;    // 注入聊天时使用的唯一 key
    }

    init() {
        const btn = document.getElementById('local-video-btn');
        const input = document.getElementById('local-video-input');
        const cancelBtn = document.getElementById('upload-cancel');
        if (btn) btn.addEventListener('click', () => input?.click());
        if (input) input.addEventListener('change', (e) => this._onFileChosen(e));
        if (cancelBtn) cancelBtn.addEventListener('click', () => this.hideProgress());
    }

    // ----------------------------------------------------------
    _onFileChosen(e) {
        const file = e.target.files?.[0];
        // 重置 input 以便同一文件可重选
        e.target.value = '';
        if (!file) return;

        const ext = (file.name.split('.').pop() || '').toLowerCase();
        if (!ALLOWED_EXT.includes(ext)) {
            alert(`不支持的格式 .${ext}，请使用 ${ALLOWED_EXT.join('/')}`);
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            alert(`文件过大（${(file.size/1024/1024).toFixed(1)}MB），最大支持 100MB`);
            return;
        }
        this._uploadAndAnalyze(file);
    }

    async _uploadAndAnalyze(file) {
        this.uploadedFilename = file.name;
        this.showProgress(0, '上传中...', file.name);

        const weaponSel = document.getElementById('weapon-select');
        const weapon = weaponSel?.value || 'auto';

        const fd = new FormData();
        fd.append('video', file);
        if (weapon && weapon !== 'auto') fd.append('weapon', weapon);

        try {
            // 用 XHR 拿上传进度
            const data = await this._xhrUpload('/api/upload_video', fd, (pct) => {
                this.showProgress(Math.min(40, pct * 0.4), '上传中...', file.name);
            });

            if (!data.success) {
                this.showProgress(0, `失败：${data.error || '未知错误'}`, file.name);
                return;
            }

            this.videoId = data.video_id;
            this.uploadedFilename = data.filename;

            if (data.cached && data.analysis) {
                // 已分析过，直接渲染
                this.analysis = data.analysis;
                this.showProgress(100, '已使用缓存分析', file.name);
                setTimeout(() => {
                    this.hideProgress();
                    this._renderLocalPlayer();
                    this._renderAnalysisPanel();
                    this._injectChatContext();
                }, 600);
                return;
            }

            // 启动轮询
            this.showProgress(45, '排队分析中...', file.name);
            this._pollJob(data.job_id);
        } catch (e) {
            this.showProgress(0, `上传失败：${e.message}`, file.name);
        }
    }

    _xhrUpload(url, formData, onProgress) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', url);
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    onProgress((e.loaded / e.total) * 100);
                }
            });
            xhr.onload = () => {
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (xhr.status >= 200 && xhr.status < 300) resolve(data);
                    else reject(new Error(data.error || `HTTP ${xhr.status}`));
                } catch (e) {
                    reject(new Error('解析响应失败'));
                }
            };
            xhr.onerror = () => reject(new Error('网络错误'));
            xhr.send(formData);
        });
    }

    _pollJob(jobId) {
        if (this.polling) clearInterval(this.polling);
        this.polling = setInterval(async () => {
            try {
                const r = await fetch(`/api/analyze_status/${jobId}`);
                const data = await r.json();
                if (!data.success) {
                    this.showProgress(0, `任务异常：${data.error || '未知'}`, this.uploadedFilename);
                    clearInterval(this.polling);
                    this.polling = null;
                    return;
                }
                // 把"分析"阶段映射到 45-100%
                const pct = 45 + (data.progress || 0) * 0.55;
                this.showProgress(pct, data.step || '处理中...', this.uploadedFilename);

                if (data.status === 'done') {
                    clearInterval(this.polling);
                    this.polling = null;
                    this.analysis = data.result;
                    setTimeout(() => {
                        this.hideProgress();
                        this._renderLocalPlayer();
                        this._renderAnalysisPanel();
                        this._injectChatContext();
                    }, 400);
                } else if (data.status === 'error') {
                    clearInterval(this.polling);
                    this.polling = null;
                    this.showProgress(0, `分析失败：${data.error || ''}`, this.uploadedFilename);
                }
            } catch (e) {
                // 网络抖动继续轮询
            }
        }, 1500);
    }

    // ----------------------------------------------------------
    // 进度模态
    // ----------------------------------------------------------
    showProgress(pct, step, file) {
        const wrap = document.getElementById('upload-progress');
        if (wrap) wrap.hidden = false;
        const fill = document.getElementById('upload-fill');
        if (fill) fill.style.width = `${Math.max(0, Math.min(100, pct))}%`;
        const stepEl = document.getElementById('upload-step');
        if (stepEl) stepEl.textContent = step;
        const fileEl = document.getElementById('upload-file');
        if (fileEl) fileEl.textContent = file || '';
    }
    hideProgress() {
        const wrap = document.getElementById('upload-progress');
        if (wrap) wrap.hidden = true;
    }

    // ----------------------------------------------------------
    // 渲染本地播放器（替换 YouTube 区域）
    // ----------------------------------------------------------
    _renderLocalPlayer() {
        const container = document.getElementById('video-player');
        if (!container || !this.videoId) return;

        container.innerHTML = '';
        const v = document.createElement('video');
        v.id = 'local-video-element';
        v.className = 'player__video';
        v.controls = true;
        v.preload = 'metadata';
        v.playsInline = true;
        v.src = `/api/local_video/${this.videoId}`;
        v.style.width = '100%';
        v.style.height = '100%';
        v.style.objectFit = 'contain';
        v.style.background = '#000';
        container.appendChild(v);
        this.videoEl = v;
    }

    // ----------------------------------------------------------
    // 渲染分析面板
    // ----------------------------------------------------------
    _renderAnalysisPanel() {
        if (!this.analysis) return;
        const a = this.analysis;
        const panel = document.getElementById('analysis-panel');
        if (panel) panel.hidden = false;

        const fname = document.getElementById('analysis-filename');
        if (fname) fname.textContent = this.uploadedFilename || a.video_id;

        const meta = document.getElementById('analysis-meta-info');
        if (meta) {
            const dur = Math.round(a.duration || 0);
            const wg = a.weapon_guess || '未知';
            const res = a.resolution || '?';
            const n = a.frame_count || 0;
            meta.textContent = `· ${wg} · ${dur}s · ${res} · ${n} 帧`;
        }

        const sum = document.getElementById('analysis-summary');
        if (sum) sum.textContent = a.summary || '';

        // 标签区
        const tags = document.getElementById('analysis-tags');
        if (tags) {
            tags.innerHTML = '';
            const items = [];
            if (a.weapon_guess) items.push(`剑种：${a.weapon_guess}`);
            const txt = a.text_in_video || [];
            if (txt.length) items.push(`字幕：${txt.slice(0, 3).join(' / ')}`);
            for (const t of items) {
                const el = document.createElement('span');
                el.className = 'analysis-tag';
                el.textContent = t;
                tags.appendChild(el);
            }
        }

        // 关键时刻
        const wrap = document.getElementById('analysis-moments');
        if (wrap) {
            wrap.innerHTML = '';
            const moments = a.key_moments || [];
            if (!moments.length) {
                wrap.innerHTML = '<p class="muted">未识别到关键时刻</p>';
            } else {
                for (const m of moments) {
                    const card = document.createElement('div');
                    card.className = 'analysis-moment';
                    card.innerHTML = `
                        <div class="analysis-moment__time">${this._fmtTime(m.time)}</div>
                        <div class="analysis-moment__body">
                            <div class="analysis-moment__title">
                                <span class="analysis-moment__type analysis-moment__type--${this._typeClass(m.type)}">${m.type || '节点'}</span>
                                ${m.title || ''}
                            </div>
                            <p class="analysis-moment__desc">${m.description || ''}</p>
                            ${m.tactic ? `<p class="analysis-moment__tactic"><i class="fas fa-lightbulb"></i> ${m.tactic}</p>` : ''}
                        </div>
                        <button class="analysis-moment__btn" data-time="${m.time}">
                            <i class="fas fa-play"></i> 跳转
                        </button>
                    `;
                    card.querySelector('[data-time]').addEventListener('click', (e) => {
                        e.stopPropagation();
                        this._seekTo(parseFloat(e.currentTarget.getAttribute('data-time')));
                    });
                    card.addEventListener('click', () => this._seekTo(parseFloat(m.time)));
                    wrap.appendChild(card);
                }
            }
        }
    }

    _typeClass(t) {
        if (!t) return 'default';
        if (/进攻|攻/.test(t)) return 'attack';
        if (/防/.test(t)) return 'defense';
        if (/得分|赢|胜/.test(t)) return 'score';
        if (/失误|失/.test(t)) return 'miss';
        if (/精彩|亮/.test(t)) return 'highlight';
        return 'default';
    }

    _fmtTime(sec) {
        sec = Math.max(0, parseInt(sec || 0));
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return `${m}:${String(s).padStart(2, '0')}`;
    }

    _seekTo(sec) {
        if (!this.videoEl) return;
        try {
            this.videoEl.currentTime = sec;
            this.videoEl.play().catch(() => {});
        } catch (e) { /* ignore */ }
    }

    // ----------------------------------------------------------
    // 把分析结果注入到聊天上下文
    // 通过自定义事件让 chat.js 捕获
    // ----------------------------------------------------------
    _injectChatContext() {
        if (!this.analysis) return;
        const summary = this.analysis.summary || '';
        const moments = (this.analysis.key_moments || []).slice(0, 5).map(m =>
            `${Math.round(m.time||0)}s[${m.type||''}] ${m.title||''}: ${m.description||''}`
        ).join('\n');
        const actions = (this.analysis.actions || []).slice(0, 5).map(a =>
            `${Math.round(a.time||0)}s ${a.action||''} (${Math.round((a.confidence||0)*100)}%): ${a.note||''}`
        ).join('\n');
        const ctx = `[本地视频分析]\n${summary}\n关键时刻:\n${moments}\n动作:\n${actions}`.trim();
        window.__localVideoContext = ctx;
        window.__localVideoFilename = this.uploadedFilename;
        // 触发一个事件让 chat.js 知道有上下文可用
        window.dispatchEvent(new CustomEvent('localVideoContextUpdated', {
            detail: { videoId: this.videoId, context: ctx, filename: this.uploadedFilename }
        }));
    }

    // 给 chat.js 调用：拉取当前上下文
    getContext() {
        return window.__localVideoContext || '';
    }
    getFilename() {
        return window.__localVideoFilename || '';
    }
    hasAnalysis() {
        return !!this.analysis;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.localVideoSystem = new LocalVideoSystem();
    window.localVideoSystem.init();
});
window.LocalVideoSystem = LocalVideoSystem;
