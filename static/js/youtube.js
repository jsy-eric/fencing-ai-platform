// YouTube 视频集成系统
class YouTubeSystem {
    constructor() {
        this.currentVideo = null;
        this.player = null;
        this.apiReadyPromise = null;
        this.videoContainer = document.getElementById('video-player');
        this.urlInput = document.getElementById('youtube-url');
        this.weaponSelect = document.getElementById('weapon-select');
        this.loadButton = document.getElementById('load-video');
        this.init();
    }

    init() {
        this.bindEvents();
        this.ensureYouTubeAPIReady();
    }

    bindEvents() {
        this.loadButton?.addEventListener('click', () => this.loadVideo());
        this.urlInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.loadVideo();
        });
        this.urlInput?.addEventListener('input', () => this.validateYouTubeUrl());
    }

    ensureYouTubeAPIReady() {
        if (this.apiReadyPromise) return this.apiReadyPromise;
        if (window.YT && window.YT.Player) {
            this.apiReadyPromise = Promise.resolve();
            return this.apiReadyPromise;
        }
        this.apiReadyPromise = new Promise((resolve) => {
            if (!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')) {
                const tag = document.createElement('script');
                tag.src = 'https://www.youtube.com/iframe_api';
                document.head.appendChild(tag);
            }
            const previous = window.onYouTubeIframeAPIReady;
            window.onYouTubeIframeAPIReady = () => {
                try { if (typeof previous === 'function') previous(); } finally { resolve(); }
            };
        });
        return this.apiReadyPromise;
    }

    isValidYouTubeUrl(url) {
        if (!url) return false;
        return /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/.test(url);
    }

    validateYouTubeUrl() {
        const url = (this.urlInput?.value || '').trim();
        if (this.loadButton) this.loadButton.disabled = !this.isValidYouTubeUrl(url);
    }

    async loadVideo() {
        const url = (this.urlInput?.value || '').trim();
        if (!this.isValidYouTubeUrl(url)) return;

        this.showLoadingState();
        try {
            const videoInfo = await this.parseYouTubeUrl(url);
            if (!videoInfo) throw new Error('无法解析视频');

            const weapon = this.weaponSelect?.value || 'auto';
            videoInfo.weapon = weapon;
            this.currentVideo = videoInfo;

            await this.ensureYouTubeAPIReady();
            await this.createVideoPlayer(videoInfo);
            this.hideLoadingState();
        } catch (e) {
            console.error('加载视频失败:', e);
            this.showError(e.message);
            this.hideLoadingState();
        }
    }

    async parseYouTubeUrl(url) {
        try {
            const r = await fetch('/api/parse_youtube', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_url: url })
            });
            const data = await r.json();
            if (data.success) return data.video_info;
        } catch (e) {
            // ignore
        }
        return this.parseYouTubeUrlLocally(url);
    }

    parseYouTubeUrlLocally(url) {
        let id = null;
        if (url.includes('youtube.com/watch')) {
            id = new URLSearchParams(url.split('?')[1]).get('v');
        } else if (url.includes('youtu.be/')) {
            id = url.split('youtu.be/')[1].split('?')[0];
        }
        if (!id) return null;
        return {
            id,
            url,
            embed_url: `https://www.youtube.com/embed/${id}?rel=0&modestbranding=1`,
            title: 'YouTube 视频',
            thumbnail: `https://img.youtube.com/vi/${id}/maxresdefault.jpg`
        };
    }

    createVideoPlayer(videoInfo) {
        return new Promise((resolve) => {
            this.videoContainer.innerHTML = '';
            const mount = document.createElement('div');
            mount.id = 'yt-player';
            this.videoContainer.appendChild(mount);

            try {
                if (this.player && typeof this.player.destroy === 'function') {
                    this.player.destroy();
                }
            } catch (e) { /* ignore */ }

            this.player = new window.YT.Player('yt-player', {
                videoId: videoInfo.id,
                height: '100%',
                width: '100%',
                playerVars: { rel: 0, modestbranding: 1, controls: 1, fs: 1, playsinline: 1 },
                events: {
                    onReady: () => {
                        try {
                            const d = this.player.getDuration?.();
                            if (typeof d === 'number' && d > 0) this.currentVideo.duration = d;
                        } catch (e) { /* ignore */ }
                        // 通知弹幕系统视频已加载
                        if (window.danmakuSystem) {
                            window.danmakuSystem.clearAllDanmaku();
                        }
                        resolve();
                    },
                    onError: () => { resolve(); }
                }
            });
        });
    }

    showLoadingState() {
        if (this.loadButton) {
            this.loadButton.disabled = true;
            this.loadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中...';
        }
        if (this.videoContainer) {
            this.videoContainer.innerHTML = '<div class="player__placeholder"><i class="fas fa-spinner fa-spin"></i><p>正在加载视频...</p></div>';
        }
    }

    hideLoadingState() {
        if (this.loadButton) {
            this.loadButton.disabled = false;
            this.loadButton.innerHTML = '<i class="fas fa-play"></i> 加载视频';
        }
    }

    showError(msg) {
        if (this.videoContainer) {
            this.videoContainer.innerHTML = `<div class="player__placeholder"><i class="fas fa-triangle-exclamation"></i><p>${msg}</p></div>`;
        }
    }

    getCurrentVideoInfo() { return this.currentVideo; }
    getCurrentTime() { try { return this.player?.getCurrentTime?.() || 0; } catch (e) { return 0; } }
}

document.addEventListener('DOMContentLoaded', () => {
    window.youtubeSystem = new YouTubeSystem();
});

window.YouTubeSystem = YouTubeSystem;
