// 弹幕系统
class DanmakuSystem {
    constructor() {
        this.danmakuContainer = document.getElementById('danmaku-display');
        this.activeDanmaku = [];
        this.danmakuQueue = [];
        this.maxDanmaku = 50;
        this.danmakuSpeed = 5;
        this.isEnabled = true;
        this.isAutoGenerating = false;
        this.autoGenerateInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('send-danmaku')?.addEventListener('click', () => this.sendUserDanmaku());
        document.getElementById('danmaku-input')?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendUserDanmaku();
        });
        document.getElementById('generate-ai-danmaku')?.addEventListener('click', () => this.generateAIDanmaku());
        document.getElementById('auto-generate')?.addEventListener('click', () => this.toggleAutoGenerate());
        document.getElementById('show-danmaku')?.addEventListener('change', (e) => this.toggleDanmaku(e.target.checked));
        document.getElementById('danmaku-speed')?.addEventListener('input', (e) => this.setSpeed(parseInt(e.target.value, 10)));
    }

    sendUserDanmaku() {
        const input = document.getElementById('danmaku-input');
        const message = (input?.value || '').trim();
        if (!message) return;
        if (message.length > 50) {
            message = message.slice(0, 50);
        }
        this.sendDanmakuToServer(message, 'user');
        if (input) input.value = '';
    }

    async sendDanmakuToServer(message, type = 'user') {
        try {
            const response = await fetch('/api/send_danmaku', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, user_id: this.getUserId(), type })
            });
            const data = await response.json();
            if (data.success) {
                this.addDanmaku({ id: data.danmaku_id, text: message, type });
            }
        } catch (e) {
            console.error('发送弹幕失败:', e);
        }
    }

    async generateAIDanmaku() {
        try {
            const response = await fetch('/api/generate_danmaku', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_context: '击剑比赛', user_message: '' })
            });
            const data = await response.json();
            if (data.success) {
                this.addDanmaku({ id: Date.now(), text: data.danmaku, type: 'ai' });
            }
        } catch (e) {
            console.error('生成AI弹幕失败:', e);
        }
    }

    toggleAutoGenerate() {
        const btn = document.getElementById('auto-generate');
        if (this.isAutoGenerating) {
            this.isAutoGenerating = false;
            if (this.autoGenerateInterval) {
                clearInterval(this.autoGenerateInterval);
                this.autoGenerateInterval = null;
            }
            if (btn) btn.innerHTML = '<i class="fas fa-arrows-rotate"></i> 自动生成';
        } else {
            this.isAutoGenerating = true;
            this.generateAIDanmaku();
            this.autoGenerateInterval = setInterval(() => this.generateAIDanmaku(), 5000);
            if (btn) btn.innerHTML = '<i class="fas fa-stop"></i> 停止生成';
        }
    }

    addDanmaku(danmaku) {
        this.danmakuQueue.push(danmaku);
        if (this.danmakuQueue.length > this.maxDanmaku) this.danmakuQueue.shift();
        if (this.isEnabled) this.displayDanmaku(danmaku);
    }

    displayDanmaku(danmaku) {
        if (!this.isEnabled || !this.danmakuContainer) return;
        const el = document.createElement('div');
        el.className = 'danmaku' + (danmaku.type === 'ai' ? ' danmaku--ai' : '');
        el.textContent = danmaku.text;
        const containerH = this.danmakuContainer.clientHeight || 400;
        el.style.top = (Math.random() * (containerH - 30)) + 'px';
        el.style.animationDuration = (12 - this.danmakuSpeed) + 's';
        this.danmakuContainer.appendChild(el);
        this.activeDanmaku.push({ element: el, startTime: Date.now() });
        setTimeout(() => this.removeDanmaku(el), 8000);
    }

    removeDanmaku(el) {
        if (el.parentNode) el.parentNode.removeChild(el);
        this.activeDanmaku = this.activeDanmaku.filter(d => d.element !== el);
    }

    toggleDanmaku(show) {
        this.isEnabled = show;
        if (!this.danmakuContainer) return;
        this.danmakuContainer.style.display = show ? 'block' : 'none';
        if (!show) this.clearAllDanmaku();
    }

    setSpeed(speed) {
        this.danmakuSpeed = speed;
        this.activeDanmaku.forEach(d => {
            d.element.style.animationDuration = (12 - speed) + 's';
        });
    }

    clearAllDanmaku() {
        this.activeDanmaku.forEach(d => this.removeDanmaku(d.element));
        this.activeDanmaku = [];
        this.danmakuQueue = [];
    }

    getUserId() {
        let uid = localStorage.getItem('fencing_uid');
        if (!uid) {
            uid = 'user_' + Math.random().toString(36).slice(2, 11);
            localStorage.setItem('fencing_uid', uid);
        }
        return uid;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.danmakuSystem = new DanmakuSystem();
});

window.DanmakuSystem = DanmakuSystem;
