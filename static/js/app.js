// SportsAI-Fencing - 主控脚本
// 串联：tabs、剑种同步、侧边栏导航、快速提问、AI 状态/切换、深度分析、关键时刻、动态推荐
(() => {
    'use strict';

    // ====== Tabs (with lazy load) ======
    const state = {
        fieLoaded: false,
        insightLoaded: false,
        knowledgeLoaded: false,
        recsLoaded: false,
        momentsLoaded: false,
        currentWeapon: ''
    };

    function switchTab(target) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('tab--active'));
        const tab = document.querySelector('.tab[data-tab="' + target + '"]');
        if (tab) tab.classList.add('tab--active');

        document.querySelectorAll('.panel').forEach(p => p.hidden = true);
        const panel = document.getElementById('panel-' + target);
        if (panel) panel.hidden = false;

        if (target === 'fie' && !state.fieLoaded)        loadFieData();
        if (target === 'action' && !state.insightLoaded) loadVideoInsight();
        if (target === 'knowledge' && !state.knowledgeLoaded) loadKnowledge();
    }

    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });

    // ====== Sidebar toggle (持久化收缩状态) ======
    const sidebar = document.getElementById('sidebar');
    const main = document.getElementById('main');

    // 页面初始化时从 localStorage 恢复状态
    if (localStorage.getItem('fencing_ai_sidebar_mini') === '1') {
        sidebar?.classList.add('sidebar--mini');
        main?.classList.add('main--full');
    }

    document.getElementById('menu-toggle')?.addEventListener('click', () => {
        const isMini = sidebar?.classList.toggle('sidebar--mini');
        main?.classList.toggle('main--full', isMini);
        // 持久化到 localStorage
        localStorage.setItem('fencing_ai_sidebar_mini', isMini ? '1' : '0');
    });

    // ====== Sidebar navigation ======
    document.querySelectorAll('.sidebar__item[data-target]').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const target = item.dataset.target;
            document.querySelectorAll('.sidebar__item').forEach(i => i.classList.remove('sidebar__item--active'));
            item.classList.add('sidebar__item--active');
            if (target === 'home') {
                switchTab('ai-assistant');
            } else {
                switchTab(target);
            }
        });
    });

    // ====== Weapon select (视频下拉) ======
    document.getElementById('weapon-select')?.addEventListener('change', (e) => {
        state.currentWeapon = e.target.value;
        state.recsLoaded = false;
        state.knowledgeLoaded = false;
        if (!document.getElementById('panel-knowledge').hidden) loadKnowledge();
        loadRecommendations();
    });

    // ====== Quick help buttons（使用事件委托支持动态加载）======
    const quickHelpList = document.getElementById('quick-help-list');
    if (quickHelpList) {
        quickHelpList.addEventListener('click', (e) => {
            const btn = e.target.closest('.quick-help__btn');
            if (!btn) return;
            const q = btn.dataset.q;
            switchTab('ai-assistant');
            setTimeout(() => {
                const input = document.getElementById('chat-input');
                if (input) {
                    input.value = q;
                    document.getElementById('send-chat')?.click();
                }
            }, 50);
        });
    }

    // ====== Quick help 刷新按钮 ======
    const refreshBtn = document.getElementById('refresh-quick-help');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', async () => {
            // 转圈动画
            refreshBtn.classList.add('refreshing');
            refreshBtn.disabled = true;
            try {
                // 获取当前剑种和视频上下文
                const weapon = document.getElementById('weapon-select')?.value || 'auto';
                const videoInfo = window.youtubeSystem?.getCurrentVideoInfo?.();
                const videoContext = videoInfo?.title || '';
                const r = await fetch('/api/quick_questions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ weapon, video_context: videoContext })
                });
                const data = await r.json();
                if (data.questions && Array.isArray(data.questions)) {
                    renderQuickQuestions(data.questions);
                }
            } catch (e) {
                console.error('刷新快速提问失败:', e);
            } finally {
                refreshBtn.classList.remove('refreshing');
                refreshBtn.disabled = false;
            }
        });
    }

    function renderQuickQuestions(questions) {
        if (!quickHelpList) return;
        quickHelpList.innerHTML = '';
        questions.forEach(q => {
            const btn = document.createElement('button');
            btn.className = 'quick-help__btn';
            btn.dataset.q = q;
            btn.textContent = q;
            quickHelpList.appendChild(btn);
        });
    }

    // ====== Clear chat / Advanced analysis ======
    document.getElementById('clear-chat')?.addEventListener('click', () => {
        if (window.chatSystem?.clearChatHistory) {
            window.chatSystem.clearChatHistory();
        }
    });

    document.getElementById('advanced-analysis')?.addEventListener('click', async () => {
        const lastUserMsg = getLastUserMessage();
        if (!lastUserMsg) {
            alert('请先向 AI 提问，然后我才能对问题进行深度分析。');
            return;
        }
        await runAdvancedAnalysis(lastUserMsg);
    });

    function getLastUserMessage() {
        const msgs = document.querySelectorAll('#chat-messages .msg--user');
        for (let i = msgs.length - 1; i >= 0; i--) {
            const p = msgs[i].querySelector('.msg__body p');
            if (p && p.textContent.trim()) return p.textContent.trim();
        }
        return null;
    }

    async function runAdvancedAnalysis(question) {
        const video = window.youtubeSystem?.getCurrentVideoInfo?.();
        const videoContext = video?.title ? '正在观看：' + video.title : '击剑比赛';
        if (window.chatSystem?.addMessage) {
            window.chatSystem.addMessage('正在深度分析...', 'ai');
        }
        try {
            const r = await fetch('/api/advanced_analysis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ question, video_context: videoContext })
            });
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '分析失败');
            window.chatSystem?.addMessage(data.analysis, 'ai');
        } catch (e) {
            window.chatSystem?.addMessage('深度分析失败：' + e.message, 'ai');
        }
    }

    // ====== FIE Data ======
    async function loadFieData() {
        const el = document.getElementById('fie-data');
        if (!el) return;
        el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-spinner fa-spin"></i><p data-i18n="loading.text">加载中...</p></div>';
        // 应用当前语言
        const tEls = el.querySelectorAll('[data-i18n]');
        if (window.applyI18n) tEls.forEach(e => e.textContent = window.t ? window.t(e.dataset.i18n) : e.textContent);
        try {
            const lang = state.currentLang || 'zh';
            const r = await fetch(`/api/fie_data?lang=${lang}`);
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '加载失败');
            state.fieLoaded = true;
            el.classList.remove('panel__placeholder');
            el.innerHTML = (data.results || []).map(res => {
                const isTeam = /Team|队|代表/.test(res.category);
                const winnerSuffix = isTeam ? '' : (res.winner_country ? ' (' + escapeHtml(res.winner_country) + ')' : '');
                const runnerSuffix = isTeam ? '' : (res.runner_up_country ? ' (' + escapeHtml(res.runner_up_country) + ')' : '');
                const thirdSuffix = isTeam ? '' : (res.third_country ? ' (' + escapeHtml(res.third_country) + ')' : '');
                return '<article class="fie-card">' +
                    '<div class="fie-card__head">' +
                        '<span class="fie-card__tournament">' + escapeHtml(res.tournament) + '</span>' +
                        '<span class="fie-card__date">' + escapeHtml(res.date || '') + '</span>' +
                    '</div>' +
                    '<div class="fie-card__meta">' +
                        '<span><i class="fas fa-map-marker-alt"></i> ' + escapeHtml(res.location || '') + '</span>' +
                        '<span class="fie-card__weapon">' + escapeHtml(res.weapon || '') + '</span>' +
                        '<span class="fie-card__cat">' + escapeHtml(res.category || '') + '</span>' +
                    '</div>' +
                    '<div class="fie-card__score">' + escapeHtml(res.score || '') + '</div>' +
                    '<div class="fie-card__podium">' +
                        '<div class="podium-row podium-row--gold">' +
                            '<span class="podium-rank">🥇</span>' +
                            '<span>' + escapeHtml(res.winner || '-') + winnerSuffix + '</span>' +
                        '</div>' +
                        '<div class="podium-row podium-row--silver">' +
                            '<span class="podium-rank">🥈</span>' +
                            '<span>' + escapeHtml(res.runner_up || '-') + runnerSuffix + '</span>' +
                        '</div>' +
                        '<div class="podium-row podium-row--bronze">' +
                            '<span class="podium-rank">🥉</span>' +
                            '<span>' + escapeHtml(res.third || '-') + thirdSuffix + '</span>' +
                        '</div>' +
                    '</div>' +
                '</article>';
            }).join('') || '<div class="panel__placeholder"><i class="fas fa-trophy"></i><p>暂无数据</p></div>';
        } catch (e) {
            el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-triangle-exclamation"></i><p>加载失败: ' + escapeHtml(e.message) + '</p></div>';
        }
    }
    document.getElementById('refresh-fie')?.addEventListener('click', () => { state.fieLoaded = false; loadFieData(); });

    // ====== Action Insight ======
    async function loadVideoInsight() {
        const el = document.getElementById('action-analysis-panel');
        if (!el) return;
        el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-spinner fa-spin"></i><p>分析中...</p></div>';
        try {
            const video = window.youtubeSystem?.getCurrentVideoInfo?.();
            const weapon = document.getElementById('weapon-select')?.value;
            const r = await fetch('/api/video_insight', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    video_url: video?.url || '',
                    current_time: window.youtubeSystem?.getCurrentTime?.() || 0,
                    weapon: weapon === 'auto' ? '' : (weapon || '')
                })
            });
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '分析失败');
            state.insightLoaded = true;
            renderInsight(el, data);
        } catch (e) {
            el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-triangle-exclamation"></i><p>分析失败: ' + escapeHtml(e.message) + '</p></div>';
        }
    }

    function renderInsight(el, data) {
        const a = data.action || {};
        const s = data.scene || {};
        el.classList.remove('panel__placeholder');
        el.innerHTML = `
            <div class="insight-block">
                <div class="insight-block__head">
                    <span class="insight-tag">${escapeHtml(t('动作'))}</span>
                    <span class="insight-title">${escapeHtml(t(a.action || '未识别'))}</span>
                    <span class="insight-confidence">${escapeHtml(t('置信度'))} ${Math.round((a.confidence || 0) * 100)}%</span>
                </div>
                <p class="insight-text">${escapeHtml(t(a.analysis || ''))}</p>
                <p class="insight-text insight-text--dim">${escapeHtml(t(a.technique || ''))}</p>
                ${(a.tips && a.tips.length) ? `
                <div class="insight-tips">
                    <div class="insight-tips__label">${escapeHtml(t('要点'))}</div>
                    <ul>${a.tips.map(tip => '<li>' + escapeHtml(t(tip)) + '</li>').join('')}</ul>
                </div>` : ''}
            </div>
            <div class="insight-block">
                <div class="insight-block__head">
                    <span class="insight-tag insight-tag--blue">${escapeHtml(t('场景'))}</span>
                    <span class="insight-title">${escapeHtml(t(s.weapon || '未知'))} · ${escapeHtml(t(s.competition_type || '比赛'))} · ${escapeHtml(t(s.stage || '-'))}</span>
                </div>
                ${(s.related_knowledge && s.related_knowledge.length) ? `
                <div class="insight-list">
                    ${s.related_knowledge.map(k => `
                        <div class="insight-list__item">
                            <strong>${escapeHtml(t(k.title))}</strong>
                            <span>${escapeHtml(t(k.content))}</span>
                        </div>
                    `).join('')}
                </div>` : ''}
            </div>
        `;
    }
    document.getElementById('refresh-insight')?.addEventListener('click', () => { state.insightLoaded = false; loadVideoInsight(); });

    // ====== Knowledge Recommend ======
    async function loadKnowledge() {
        const el = document.getElementById('knowledge-recommendations');
        if (!el) return;
        el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-spinner fa-spin"></i><p>推荐中...</p></div>';
        try {
            const weapon = document.getElementById('weapon-select')?.value;
            const r = await fetch('/api/knowledge_recommend', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    weapon: weapon === 'auto' ? '' : (weapon || ''),
                    stage: '中段'
                })
            });
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '推荐失败');
            state.knowledgeLoaded = true;
            el.classList.remove('panel__placeholder');
            const recs = data.recommendations || [];
            if (!recs.length) {
                el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-lightbulb"></i><p>暂无推荐</p></div>';
                return;
            }
            el.innerHTML = recs.map(k => `
                <article class="kb-card">
                    <div class="kb-card__head">
                        <span class="kb-card__type">${escapeHtml(t(k.type || '知识'))}</span>
                        <span class="kb-card__level">${escapeHtml(t(k.level || ''))}</span>
                    </div>
                    <h4 class="kb-card__title">${escapeHtml(t(k.title))}</h4>
                    <p class="kb-card__content">${escapeHtml(t(k.content))}</p>
                </article>
            `).join('');
        } catch (e) {
            el.innerHTML = '<div class="panel__placeholder"><i class="fas fa-triangle-exclamation"></i><p>推荐失败: ' + escapeHtml(e.message) + '</p></div>';
        }
    }
    document.getElementById('refresh-knowledge')?.addEventListener('click', () => { state.knowledgeLoaded = false; loadKnowledge(); });

    // ====== 右侧动态推荐 ======
    async function loadRecommendations() {
        const el = document.getElementById('rec-list');
        const sub = document.getElementById('rec-sub');
        if (!el) return;
        el.innerHTML = '<div class="rec rec--placeholder"><i class="fas fa-spinner fa-spin"></i><p>推荐中...</p></div>';
        try {
            const weapon = document.getElementById('weapon-select')?.value;
            const r = await fetch('/api/knowledge_recommend', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    weapon: weapon === 'auto' ? '' : (weapon || ''),
                    stage: '中段'
                })
            });
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '推荐失败');
            state.recsLoaded = true;
            const recs = data.recommendations || [];
            if (sub) {
                const w = (weapon && weapon !== 'auto') ? weapon : '综合';
                sub.textContent = recs.length ? `${w} · ${recs.length} 条` : `${w} · 暂无`;
            }
            if (!recs.length) {
                el.innerHTML = '<div class="rec rec--placeholder"><i class="fas fa-lightbulb"></i><p>暂无推荐</p></div>';
                return;
            }
            const colors = {'花剑': '#3ea6ff', '重剑': '#ff5e5e', '佩剑': '#ffbb00'};
            const icons = { '技术': 'fa-bolt', '规则': 'fa-shield-halved', '战术': 'fa-chess', '历史': 'fa-landmark', '训练': 'fa-dumbbell' };
            el.innerHTML = recs.map(k => {
                const cat = k.category || k.type || '知识';
                const color = colors[cat] || '#aaaaaa';
                const icon = icons[k.type] || 'fa-lightbulb';
                return `
                    <article class="rec" data-title="${escapeHtml(k.title)}">
                        <div class="rec__thumb" style="--c:${color}">
                            <i class="fas ${icon} rec__icon"></i>
                            <span class="rec__cat">${escapeHtml(t(k.type || cat))}</span>
                        </div>
                        <div class="rec__info">
                            <h4 class="rec__title">${escapeHtml(t(k.title))}</h4>
                            <p class="rec__ch">${escapeHtml(t(k.content || ''))}</p>
                        </div>
                    </article>
                `;
            }).join('');
            el.querySelectorAll('.rec').forEach(card => {
                card.addEventListener('click', () => {
                    const t = card.dataset.title;
                    if (!t) return;
                    switchTab('knowledge');
                });
            });
        } catch (e) {
            el.innerHTML = '<div class="rec rec--placeholder"><i class="fas fa-triangle-exclamation"></i><p>推荐失败</p></div>';
        }
    }

    // ====== 关键时刻时间轴 ======
    async function loadKeyMoments() {
        const wrap = document.getElementById('moments');
        const list = document.getElementById('moments-list');
        const video = window.youtubeSystem?.getCurrentVideoInfo?.();
        if (!wrap || !list) return;
        if (!video || !video.url) {
            wrap.hidden = true;
            return;
        }
        list.innerHTML = '<div class="moments__placeholder"><i class="fas fa-spinner fa-spin"></i> 检测中...</div>';
        wrap.hidden = false;
        try {
            const r = await fetch('/api/key_moments', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    video_url: video.url,
                    duration: video.duration || 0
                })
            });
            const data = await r.json();
            if (!data.success) throw new Error(data.error || '检测失败');
            state.momentsLoaded = true;
            const moments = data.moments || [];
            if (!moments.length) {
                list.innerHTML = '<div class="moments__placeholder">未检测到关键时刻</div>';
                return;
            }
            list.innerHTML = moments.map(m => `
                <button class="moment" data-time="${m.time}">
                    <span class="moment__time">${formatTime(m.time)}</span>
                    <span class="moment__type moment__type--${escapeHtml(m.type || '阶段')}">${escapeHtml(m.type || '阶段')}</span>
                    <span class="moment__desc">${escapeHtml(m.description || '')}</span>
                </button>
            `).join('');
            list.querySelectorAll('.moment').forEach(btn => {
                btn.addEventListener('click', () => {
                    const t = parseFloat(btn.dataset.time || '0');
                    if (window.youtubeSystem?.player?.seekTo) {
                        try { window.youtubeSystem.player.seekTo(t, true); } catch (e) { /* ignore */ }
                    }
                });
            });
        } catch (e) {
            list.innerHTML = '<div class="moments__placeholder">检测失败：' + escapeHtml(e.message) + '</div>';
        }
    }

    function formatTime(s) {
        s = Math.max(0, Math.floor(s || 0));
        const m = Math.floor(s / 60);
        const ss = (s % 60).toString().padStart(2, '0');
        return `${m}:${ss}`;
    }

    // 在视频加载完成后拉关键时刻
    const _origCreate = window.YouTubeSystem;
    if (_origCreate) {
        const _orig = _origCreate.prototype.createVideoPlayer;
        _origCreate.prototype.createVideoPlayer = function (...args) {
            const p = _orig.apply(this, args);
            p && p.then?.(() => {
                state.momentsLoaded = false;
                loadKeyMoments();
            });
            return p;
        };
    }

    // ====== AI Status pill + AI Switch ======
    async function loadAIStatus() {
        const pill = document.getElementById('ai-status-pill');
        const text = document.getElementById('ai-status-text');
        if (!pill || !text) return;
        try {
            const r = await fetch('/api/ai_status');
            const data = await r.json();
            if (!data.success || !data.status) throw new Error('获取失败');
            const s = data.status;
            updateAIStatusPill(s);
            updateAISwitch(s);
        } catch (e) {
            text.textContent = '离线';
            pill.className = 'top-bar__status top-bar__status--err';
        }
    }

    function updateAIStatusPill(s) {
        const text = document.getElementById('ai-status-text');
        const pill = document.getElementById('ai-status-pill');
        const active = s.current_provider;
        if (s.deepseek_available) {
            text.textContent = 'DeepSeek V3';
            pill.className = 'top-bar__status top-bar__status--ok';
        } else if (s.minimax_available) {
            text.textContent = 'MiniMax';
            pill.className = 'top-bar__status top-bar__status--ok';
        } else {
            text.textContent = '本地知识库';
            pill.className = 'top-bar__status top-bar__status--local';
        }
    }

    function updateAISwitch(s) {
        document.querySelectorAll('#ai-switch .ai-switch__btn').forEach(btn => {
            const ai = btn.dataset.ai;
            btn.classList.toggle('ai-switch__btn--active', ai === s.current_provider);
            btn.disabled = (ai === 'deepseek' && !s.deepseek_available) ||
                           (ai === 'minimax' && !s.minimax_available);
        });
    }

    document.querySelectorAll('#ai-switch .ai-switch__btn').forEach(btn => {
        btn.addEventListener('click', async () => {
            const ai = btn.dataset.ai;
            btn.disabled = true;
            try {
                const r = await fetch('/api/switch_ai', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ ai_type: ai })
                });
                const data = await r.json();
                if (data.status) {
                    updateAIStatusPill(data.status);
                    updateAISwitch(data.status);
                }
            } catch (e) {
                console.error('AI 切换失败', e);
            } finally {
                btn.disabled = false;
            }
        });
    });

    // ====== Mode Switcher (弹幕+对话 / 仅对话) ======
    const modeState = {
        current: localStorage.getItem('fencing_ai_mode') || 'hybrid',  // hybrid | chat
        currentVideoId: null,
        userDanmaku: JSON.parse(localStorage.getItem('fencing_ai_user_danmaku') || '{}')  // { videoId: [{time, text, type}] }
    };

    function setupModeSwitcher() {
        document.querySelectorAll('.mode-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const mode = btn.dataset.mode;
                if (modeState.current === mode) return;
                modeState.current = mode;
                localStorage.setItem('fencing_ai_mode', mode);
                document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === mode));
                // 切换模式时清空当前视频的弹幕显示
                const layer = document.querySelector('.danmaku-layer, #danmaku-layer');
                if (layer) layer.innerHTML = '';
                // 重新加载弹幕
                if (modeState.currentVideoId) loadUserDanmaku(modeState.currentVideoId);
                // 更新聊天输入框 placeholder（区分两种模式）
                updateChatPlaceholder();
            });
        });
        // 初始化 active 状态
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.toggle('active', b.dataset.mode === modeState.current));
        // 初始化 placeholder
        updateChatPlaceholder();
    }

    function updateChatPlaceholder() {
        const chatInput = document.getElementById('chat-input');
        if (!chatInput) return;
        try {
            const lang = (typeof state !== 'undefined' && state.currentLang) || 'zh';
            // 防御：i18n 字典可能尚未初始化（hoist 顺序问题）
            const dict = (typeof i18n !== 'undefined' && i18n[lang]) || (typeof i18n !== 'undefined' && i18n.zh) || null;
            if (!dict) return;
            const key = modeState.current === 'hybrid' ? 'chatDanmaku' : 'chat';
            chatInput.placeholder = (dict.placeholder && dict.placeholder[key]) || '';
        } catch (e) {
            // 静默失败，不影响其他功能
        }
    }

    // 监听语言变化，实时更新 placeholder
    window.addEventListener('languageChanged', () => updateChatPlaceholder());

    // ====== Toolbar Switch Sync (显示弹幕开关视觉反馈) ======
    function setupToolbarSwitch() {
        const sw = document.getElementById('show-danmaku');
        const lbl = sw?.closest('.toolbar-btn');
        if (!sw || !lbl) return;

        const sync = () => {
            lbl.classList.toggle('active', sw.checked);
        };
        sw.addEventListener('change', sync);
        sync();
    }

    // ====== Per-video Danmaku Storage ======
    function getVideoId() {
        const info = window.youtubeSystem?.getCurrentVideoInfo?.();
        return info?.id || info?.videoId || null;
    }

    function saveUserDanmaku(videoId, danmaku) {
        if (!videoId) return;
        modeState.userDanmaku[videoId] = danmaku;
        try {
            localStorage.setItem('fencing_ai_user_danmaku', JSON.stringify(modeState.userDanmaku));
        } catch (e) {
            console.warn('保存弹幕失败', e);
        }
    }

    function getUserDanmaku(videoId) {
        if (!videoId) return [];
        return modeState.userDanmaku[videoId] || [];
    }

    function loadUserDanmaku(videoId) {
        if (modeState.current !== 'hybrid') return;
        const layer = document.querySelector('.danmaku-layer, #danmaku-layer');
        if (!layer) return;
        layer.innerHTML = '';
        const danmakuList = getUserDanmaku(videoId);
        danmakuList.forEach((d, idx) => {
            setTimeout(() => addDanmakuToLayer(d.text, d.type), idx * 300);
        });
    }

    function addDanmakuToLayer(text, type = 'user') {
        const layer = document.querySelector('.danmaku-layer, #danmaku-layer');
        if (!layer) return;
        if (document.getElementById('show-danmaku') && !document.getElementById('show-danmaku').checked) return;
        const speed = document.getElementById('danmaku-speed')?.value || 5;
        const duration = (11 - speed) * 1.5;  // 速度越快 duration 越短
        const track = layer.children.length % 6;  // 6条轨道
        const danmaku = document.createElement('div');
        danmaku.className = 'danmaku danmaku--' + type;  // danmaku--user / danmaku--ai
        danmaku.textContent = text;
        danmaku.style.top = (track * 32 + 10) + 'px';
        danmaku.style.animationDuration = duration + 's';
        layer.appendChild(danmaku);
        setTimeout(() => danmaku.remove(), duration * 1000);
    }

    // ====== 弹幕模式下截断长文本（按汉字数量，不算标点） ======
    function truncateForDanmaku(text, maxChineseChars = 50) {
        if (!text) return '';
        text = String(text).replace(/\s+/g, ' ').trim();
        // 计算汉字数量（不包括标点、空格、数字、英文字母）
        const chineseChars = text.match(/[\u4e00-\u9fff]/g) || [];
        if (chineseChars.length <= maxChineseChars) return text;
        // 截取包含 maxChineseChars 个汉字的部分
        let truncated = '';
        let count = 0;
        for (const ch of text) {
            truncated += ch;
            if (/[\u4e00-\u9fff]/.test(ch)) {
                count++;
            }
            if (count >= maxChineseChars) break;
        }
        return truncated + '...';
    }

    // ====== Chat send with mode-aware danmaku ======
    function setupChatSend() {
        const sendBtn = document.getElementById('send-chat');
        const input = document.getElementById('chat-input');
        if (!sendBtn || !input) return;

        const handleSend = async () => {
            const text = input.value.trim();
            if (!text) return;
            const videoId = getVideoId();
            const now = Date.now();
            const isHybrid = modeState.current === 'hybrid';

            // 1. 添加到聊天记录（始终为完整内容）
            if (window.chatSystem?.addMessage) {
                window.chatSystem.addMessage(text, 'user');
            }

            // 2. 添加为用户弹幕（如果 hybrid 模式）
            if (isHybrid) {
                // 用户弹幕超过 50 个汉字也截断
                const userDanmakuText = truncateForDanmaku(text, 50);
                addDanmakuToLayer(userDanmakuText, 'user');
                // 保存到视频弹幕库
                if (videoId) {
                    const list = getUserDanmaku(videoId);
                    list.push({ time: now, text: userDanmakuText, original: text, type: 'user' });
                    saveUserDanmaku(videoId, list);
                }
            }

            // 3. 发送给 AI
            input.value = '';
            try {
                const r = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        video_id: videoId,
                        mode: isHybrid ? 'danmaku' : 'chat'
                    })
                });
                const data = await r.json();
                const fullReply = data.reply || data.response || data.message || '抱歉，AI 服务暂时不可用。';

                // 4. 聊天区域始终显示完整回复
                if (window.chatSystem?.addMessage) {
                    window.chatSystem.addMessage(fullReply, 'ai');
                }

                // 5. 弹幕模式下，作为弹幕显示（后端已限制30字以内）
                if (isHybrid) {
                    addDanmakuToLayer(fullReply, 'ai');
                }
            } catch (e) {
                if (window.chatSystem?.addMessage) {
                    window.chatSystem.addMessage('请求失败：' + e.message, 'ai');
                }
            }
        };

        sendBtn.addEventListener('click', handleSend);
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleSend();
        });
    }

    // ====== AI 生成弹幕 / 自动生成 ======
    function setupDanmakuToolbar() {
        const aiBtn = document.getElementById('generate-ai-danmaku');
        const autoBtn = document.getElementById('auto-generate');
        let autoTimer = null;

        // AI 生成弹幕
        aiBtn?.addEventListener('click', async () => {
            aiBtn.classList.add('active');
            try {
                const info = window.youtubeSystem?.getCurrentVideoInfo?.();
                const videoContext = info?.title ? `正在观看：${info.title}` : '击剑比赛';
                const r = await fetch('/api/generate_danmaku', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ video_context: videoContext })
                });
                const data = await r.json();
                if (data.success && data.danmaku) {
                    if (modeState.current === 'hybrid') {
                        addDanmakuToLayer(data.danmaku, 'ai');
                    } else {
                        // 聊天模式下添加到聊天记录
                        if (window.chatSystem?.addMessage) {
                            window.chatSystem.addMessage(data.danmaku, 'ai');
                        }
                    }
                } else {
                    alert('生成弹幕失败：' + (data.error || '未知错误'));
                }
            } catch (e) {
                alert('生成弹幕失败：' + e.message);
            } finally {
                setTimeout(() => aiBtn.classList.remove('active'), 400);
            }
        });

        // 自动生成弹幕（每 8 秒生成一条）
        autoBtn?.addEventListener('click', () => {
            if (autoTimer) {
                clearInterval(autoTimer);
                autoTimer = null;
                autoBtn.classList.remove('active');
            } else {
                autoBtn.classList.add('active');
                // 立即生成一条
                aiBtn?.click();
                autoTimer = setInterval(() => {
                    aiBtn?.click();
                }, 8000);
            }
        });
    }

    // ====== 监听视频变化，加载该视频的弹幕 ======
    function setupVideoChangeListener() {
        // 定时检查视频变化
        let lastVideoId = null;
        setInterval(() => {
            const currentId = getVideoId();
            if (currentId && currentId !== lastVideoId) {
                lastVideoId = currentId;
                modeState.currentVideoId = currentId;
                if (modeState.current === 'hybrid') {
                    loadUserDanmaku(currentId);
                }
            }
        }, 1000);
    }

    // ====== Init mode switcher & chat send ======
    setupModeSwitcher();
    setupToolbarSwitch();
    setupChatSend();
    setupDanmakuToolbar();
    setupVideoChangeListener();

    // ====== Helpers ======
    function escapeHtml(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // ====== Init ======
    document.addEventListener('DOMContentLoaded', () => {
        loadAIStatus();
        loadRecommendations();
        setupLanguageSwitcher();

        // 监听语言变化，重新加载动态内容
        window.addEventListener('languageChanged', () => {
            state.fieLoaded = false;
            state.insightLoaded = false;
            state.knowledgeLoaded = false;
            state.recsLoaded = false;
            state.momentsLoaded = false;
            // 根据当前可见的 panel 重新加载
            const knowledgePanel = document.getElementById('panel-knowledge');
            const actionPanel = document.getElementById('panel-action');
            const fiePanel = document.getElementById('panel-fie');
            if (knowledgePanel && !knowledgePanel.hidden) loadKnowledge();
            if (actionPanel && !actionPanel.hidden) loadVideoInsight();
            if (fiePanel && !fiePanel.hidden) loadFieData();
            // 侧边栏推荐总是重新加载
            loadRecommendations();
        });
    });

    // ====== Language Switcher (i18n) ======
    const i18n = {
        zh: {
            currentLabel: '中文',
            nav: { home: '首页', fie: 'FIE 数据', chat: 'AI 助手' },
            hero: { title: '粘贴视频链接开始', sub: '支持比赛回放、训练视频、技术教学等内容' },
            tabs: { aiAssistant: 'AI 助手', danmaku: '弹幕', chat: 'AI 助手', action: '动作分析', knowledge: '知识推荐', fie: 'FIE 数据', fencingKnowledge: '击剑知识' },
            mode: { hybrid: '弹幕+对话', chat: '仅对话' },
            weapon: { auto: '智能识别', foil: '花剑 · FOIL', epee: '重剑 · ÉPÉE', sabre: '佩剑 · SABRE' },
            btn: { load: '加载视频', send: '发送', aiDanmaku: 'AI 生成弹幕', autoGen: '自动生成', local: '本地视频', localTitle: '选择本地视频' },
            settings: { showDanmaku: '显示弹幕', speed: '弹幕速度' },
            chat: { title: 'SportsAI-Fencing 助手', advanced: '深度分析', clear: '清空对话', now: '现在',
                    welcome: '您好！我是击剑AI专家，可以为您解答击剑相关问题。请问有什么可以帮助您的吗？' },
            action: { title: '动作分析', refresh: '重新分析', hint: '点击刷新按钮即可进行动作分析' },
            analysis: { title: '本地视频分析' },
            knowledge: { title: '推荐学习', refresh: '重新推荐', hint: '点击刷新按钮获取相关知识推荐' },
            fie: { title: '实时 FIE 数据' },
            side: { knowledge: '击剑知识', recommend: '根据剑种推荐', quickHelp: '快速提问' },
            quick: { foil: '花剑的有效部位', epee: '重剑 vs 花剑', sabre: '佩剑规则', scoring: '计分规则', refresh: '刷新问题' },
            common: { loading: '加载中...' },
            ai: { localShort: '本地', local: '本地知识库', deepseek: 'DeepSeek V3', minimax: 'MiniMax' },
            moments: { title: '关键时刻', hint: '点击节点跳转' },
            dynamic: {
                '技术': '技术', '战术': '战术',
                '动作': '动作',
                '比赛开局策略': '比赛开局策略',
                '比赛中期战术': '比赛中期战术',
                '关键分处理': '关键分处理',
                '击剑基础姿势与步伐': '击剑基础姿势与步伐',
                '花剑基本攻击动作': '花剑基本攻击动作',
                '直刺技巧详解': '直刺技巧详解',
                '转移刺技巧': '转移刺技巧',
                '弓步刺动作要领': '弓步刺动作要领',
                '防守与反击策略': '防守与反击策略',
                '时机把握的重要性': '时机把握的重要性',
                '判罚与裁判规则': '判罚与裁判规则',
                '比赛节奏控制': '比赛节奏控制',
                '体能分配技巧': '体能分配技巧',
                '心理素质训练': '心理素质训练',
                '比赛开局时，运动员需要观察对手的站位、习惯动作和反应速度': '比赛开局时，运动员需要观察对手的站位、习惯动作和反应速度',
                '比赛中期，双方已经': '比赛中期，双方已经',
                '关键分时，运动员需要': '关键分时，运动员需要'
            },
            placeholder: { url: 'https://www.youtube.com/watch?v=...', danmaku: '发送弹幕...', chat: '向 AI 提问...', chatDanmaku: '弹幕并向 AI 提问...' }
        },
        en: {
            currentLabel: 'English',
            nav: { home: 'Home', fie: 'FIE Data', chat: 'AI Assistant' },
            hero: { title: 'Paste a YouTube link to start analysis', sub: 'Supports match replays, training videos, technique tutorials, and more' },
            tabs: { aiAssistant: 'AI Assistant', danmaku: 'Danmaku', chat: 'AI Assistant', action: 'Action Analysis', knowledge: 'Knowledge', fie: 'FIE Data', fencingKnowledge: 'Fencing Knowledge' },
            mode: { hybrid: 'Danmaku + Chat', chat: 'Chat Only' },
            weapon: { auto: 'Auto Detect', foil: 'Foil · FOIL', epee: 'Épée · ÉPÉE', sabre: 'Sabre · SABRE' },
            btn: { load: 'Load Video', send: 'Send', aiDanmaku: 'AI Generate Danmaku', autoGen: 'Auto Generate' },
            settings: { showDanmaku: 'Show Danmaku', speed: 'Danmaku Speed' },
            chat: { title: 'SportsAI-Fencing Assistant', advanced: 'Advanced Analysis', clear: 'Clear Chat', now: 'Now',
                    welcome: 'Hello! I am the Fencing AI expert. Feel free to ask me any questions about fencing. How can I help you?' },
            action: { title: 'Action Analysis', refresh: 'Re-analyze', hint: 'Click the refresh button to start action analysis' },
            knowledge: { title: 'Recommended Learning', refresh: 'Refresh', hint: 'Click refresh to get relevant knowledge recommendations' },
            fie: { title: 'Real-time FIE Data' },
            side: { knowledge: 'Fencing Knowledge', recommend: 'Based on weapon', quickHelp: 'Quick Questions' },
            quick: { foil: 'Foil target area', epee: 'Épée vs Foil', sabre: 'Sabre rules', scoring: 'Scoring rules', refresh: 'Refresh questions' },
            common: { loading: 'Loading...' },
            ai: { localShort: 'Local', local: 'Local Knowledge', deepseek: 'DeepSeek V3', minimax: 'MiniMax' },
            moments: { title: 'Key Moments', hint: 'Click node to jump' },
            dynamic: {
                '技术': 'Technique', '战术': 'Tactics',
                '动作': 'Action',
                '比赛开局策略': 'Match Opening Strategy',
                '比赛中期战术': 'Mid-Match Tactics',
                '关键分处理': 'Key Point Handling',
                '击剑基础姿势与步伐': 'Fencing Basic Stance and Footwork',
                '花剑基本攻击动作': 'Foil Basic Attack Moves',
                '直刺技巧详解': 'Direct Thrust Techniques',
                '转移刺技巧': 'Disengage Thrust Techniques',
                '弓步刺动作要领': 'Lunge Thrust Essentials',
                '防守与反击策略': 'Defense and Counter-Attack Strategy',
                '时机把握的重要性': 'Importance of Timing',
                '判罚与裁判规则': 'Penalties and Referee Rules',
                '比赛节奏控制': 'Match Rhythm Control',
                '体能分配技巧': 'Energy Distribution Tips',
                '心理素质训练': 'Mental Training',
                '比赛开局时，运动员需要观察对手的站位、习惯动作和反应速度': 'At the start of the match, athletes need to observe opponent\'s stance, habits, and reaction speed',
                '比赛中期，双方已经': 'In the middle of the match, both sides have',
                '关键分时，运动员需要': 'At key points, athletes need to'
            },
            placeholder: { url: 'https://www.youtube.com/watch?v=...', danmaku: 'Send a danmaku...', chat: 'Ask the AI...', chatDanmaku: 'Danmaku & Ask the AI...' }
        },
        ja: {
            currentLabel: '日本語',
            nav: { home: 'ホーム', fie: 'FIE データ', chat: 'AI アシスタント' },
            hero: { title: 'YouTube リンクを貼り付けて分析を開始', sub: '試合の録画、トレーニング動画、テクニック解説などに対応' },
            tabs: { aiAssistant: 'AI アシスタント', danmaku: '弾幕', chat: 'AI アシスタント', action: '動作分析', knowledge: 'ナレッジ', fie: 'FIE データ', fencingKnowledge: 'フェンシング知識' },
            mode: { hybrid: '弾幕+チャット', chat: 'チャットのみ' },
            weapon: { auto: '自動識別', foil: 'フォイル · FOIL', epee: 'エペ · ÉPÉE', sabre: 'サーブル · SABRE' },
            btn: { load: '動画を読み込む', send: '送信', aiDanmaku: 'AI 弾幕生成', autoGen: '自動生成', local: 'ローカル動画', localTitle: 'ローカル動画を選択' },
            settings: { showDanmaku: '弾幕を表示', speed: '弾幕速度' },
            chat: { title: 'SportsAI-Fencing アシスタント', advanced: '詳細分析', clear: 'クリア', now: '今',
                    welcome: 'こんにちは！フェンシングAI expert です。フェンシングに関するご質問にお答えします。' },
            action: { title: '動作分析', refresh: '再分析', hint: '更新ボタンをクリックして動作分析を開始' },
            analysis: { title: 'ローカル動画分析' },
            knowledge: { title: '推奨学習', refresh: '更新', hint: '更新ボタンをクリックして関連知識を推薦' },
            fie: { title: 'リアルタイム FIE データ' },
            side: { knowledge: 'フェンシング知識', recommend: '武器に基づく推薦', quickHelp: 'クイック質問' },
            quick: { foil: 'フォイル有効部位', epee: 'エペ vs フォイル', sabre: 'サーブル規則', scoring: '採点規則', refresh: '質問を更新' },
            common: { loading: '読み込み中...' },
            ai: { localShort: 'ローカル', local: 'ローカル知識ベース', deepseek: 'DeepSeek V3', minimax: 'MiniMax' },
            moments: { title: 'キーモーメント', hint: 'ノードをクリックしてジャンプ' },
            dynamic: {
                '技术': 'テクニック', '战术': '戦術',
                '动作': '動作',
                '比赛开局策略': '試合開始戦略',
                '比赛中期战术': '試合中盤戦術',
                '关键分处理': 'キーポイント処理',
                '击剑基础姿势与步伐': 'フェンシング基本姿勢と足さばき',
                '花剑基本攻击动作': 'フォイル基本攻撃動作',
                '直刺技巧详解': '突き技详解',
                '转移刺技巧': '切り返し突き技',
                '弓步刺动作要领': 'ランジュ突き要諦',
                '防守与反击策略': '防御と反撃戦略',
                '时机把握的重要性': 'タイミング把握の重要性',
                '判罚与裁判规则': '判定と審判規則',
                '比赛节奏控制': '試合リズムコントロール',
                '体能分配技巧': '体力配分テクニック',
                '心理素质训练': 'メンタルトレーニング',
                '比赛开局时，运动员需要观察对手的站位、习惯动作和反应速度': '試合開始時、選手は相手の立ち位置、習慣動作、反応速度を観察する必要があります',
                '比赛中期，双方已经': '試合中盤、両者はすでに',
                '关键分时，运动员需要': 'キーポイント時、選手は'
            },
            placeholder: { url: 'https://www.youtube.com/watch?v=...', danmaku: '弾幕を送信...', chat: 'AI に質問...', chatDanmaku: '弾幕＋AI に質問...' }
        }
    };

    function setupLanguageSwitcher() {
        const btn = document.getElementById('langBtn');
        const dropdown = document.getElementById('langDropdown');
        if (!btn || !dropdown) return;

        // Restore saved language
        const saved = localStorage.getItem('fencing_ai_lang') || 'zh';
        applyLanguage(saved);

        // Toggle dropdown
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            dropdown.classList.toggle('show');
        });

        // Click outside to close
        document.addEventListener('click', () => {
            dropdown.classList.remove('show');
        });

        // Language option click
        dropdown.querySelectorAll('.lang-option').forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                const lang = opt.dataset.lang;
                applyLanguage(lang);
                localStorage.setItem('fencing_ai_lang', lang);
                dropdown.classList.remove('show');
                // 触发自定义事件，通知其他模块重新加载
                window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
            });
        });
    }

    function getNested(obj, path) {
        return path.split('.').reduce((o, k) => (o == null ? o : o[k]), obj);
    }

    // 翻译动态内容（来自后端API的中文文本）
    function getCurrentLang() {
        return localStorage.getItem('fencing_ai_lang') || 'zh';
    }

    function t(text) {
        if (!text) return text;
        const lang = getCurrentLang();
        if (lang === 'zh') return text;
        const dict = i18n[lang];
        if (!dict || !dict.dynamic) return text;
        // 完整匹配
        if (dict.dynamic[text]) return dict.dynamic[text];
        // 尝试逐段替换
        let result = text;
        for (const [zh, translated] of Object.entries(dict.dynamic)) {
            if (result.includes(zh)) {
                result = result.split(zh).join(translated);
            }
        }
        return result;
    }

    function applyLanguage(lang) {
        const dict = i18n[lang];
        if (!dict) return;

        // Update active option
        document.querySelectorAll('.lang-option').forEach(opt => {
            opt.classList.toggle('active', opt.dataset.lang === lang);
        });

        // Update current label
        const current = document.getElementById('langCurrent');
        if (current) current.textContent = dict.currentLabel;

        // Translate all data-i18n elements
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = getNested(dict, key);
            if (text) el.textContent = text;
        });

        // Translate all data-i18n-placeholder elements
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            const text = getNested(dict, key);
            if (text) el.setAttribute('placeholder', text);
        });

        // Translate all data-i18n-title elements
        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            const text = getNested(dict, key);
            if (text) el.setAttribute('title', text);
        });

        // 聊天输入框 placeholder 翻译（区分模式）
        const chatInput = document.getElementById('chat-input');
        if (chatInput) {
            // 从 localStorage 读取当前模式，hybrid/chat 区分
            const mode = localStorage.getItem('fencing_ai_mode') || 'hybrid';
            const phKey = mode === 'hybrid' ? 'chatDanmaku' : 'chat';
            const phText = getNested(dict, `placeholder.${phKey}`);
            if (phText) chatInput.placeholder = phText;
        }
    }
})();
