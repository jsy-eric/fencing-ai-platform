// YouTube视频集成系统
class YouTubeSystem {
    constructor() {
        this.currentVideo = null;
        this.player = null;
        this.videoContainer = document.getElementById('video-player');
        this.urlInput = document.getElementById('youtube-url');
        this.loadButton = document.getElementById('load-video');
        this.init();
    }

    init() {
        this.bindEvents();
        // 移除YouTube API加载，使用简单的iframe嵌入
    }

    bindEvents() {
        // 加载视频按钮事件
        this.loadButton.addEventListener('click', () => {
            this.loadVideo();
        });

        // 输入框回车事件
        this.urlInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.loadVideo();
            }
        });

        // 输入框输入事件
        this.urlInput.addEventListener('input', () => {
            this.validateYouTubeUrl();
        });
    }

    // 移除YouTube API加载方法，使用简单的iframe嵌入

    validateYouTubeUrl() {
        const url = this.urlInput.value.trim();
        const isValid = this.isValidYouTubeUrl(url);
        
        this.loadButton.disabled = !isValid;
        
        if (url && !isValid) {
            this.showUrlError('请输入有效的YouTube链接');
        } else {
            this.hideUrlError();
        }
    }

    isValidYouTubeUrl(url) {
        if (!url) return false;
        
        const patterns = [
            /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/,
            /^(https?:\/\/)?(www\.)?youtube\.com\/watch\?v=[\w-]+/,
            /^(https?:\/\/)?(www\.)?youtu\.be\/[\w-]+/
        ];
        
        return patterns.some(pattern => pattern.test(url));
    }

    showUrlError(message) {
        let errorElement = document.getElementById('url-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.id = 'url-error';
            errorElement.className = 'url-error';
            this.urlInput.parentNode.appendChild(errorElement);
        }
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }

    hideUrlError() {
        const errorElement = document.getElementById('url-error');
        if (errorElement) {
            errorElement.style.display = 'none';
        }
    }

    async loadVideo() {
        const url = this.urlInput.value.trim();
        
        if (!this.isValidYouTubeUrl(url)) {
            this.showUrlError('请输入有效的YouTube链接');
            return;
        }

        try {
            // 显示加载状态
            this.showLoadingState();
            
            // 解析YouTube链接
            const videoInfo = await this.parseYouTubeUrl(url);
            
            if (videoInfo) {
                // 创建视频播放器
                this.createVideoPlayer(videoInfo);
                
                // 更新当前视频信息
                this.currentVideo = videoInfo;
                
                // 通知其他系统视频已加载
                this.onVideoLoaded(videoInfo);
                
                // 初始化帧捕获
                if (window.frameCapture) {
                    window.frameCapture.init(this.player);
                }
                
                // 隐藏加载状态
                this.hideLoadingState();
            } else {
                throw new Error('无法解析视频信息');
            }
        } catch (error) {
            console.error('加载视频失败:', error);
            this.showUrlError('加载视频失败: ' + error.message);
            this.hideLoadingState();
        }
    }

    async parseYouTubeUrl(url) {
        try {
            const response = await fetch('/api/parse_youtube', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ video_url: url })
            });

            const data = await response.json();
            if (data.success) {
                return data.video_info;
            } else {
                throw new Error(data.error || '解析失败');
            }
        } catch (error) {
            // 如果API调用失败，尝试本地解析
            return this.parseYouTubeUrlLocally(url);
        }
    }

    parseYouTubeUrlLocally(url) {
        // 本地解析YouTube链接
        let videoId = null;
        
        if (url.includes('youtube.com/watch')) {
            const urlParams = new URLSearchParams(url.split('?')[1]);
            videoId = urlParams.get('v');
        } else if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split('?')[0];
        }
        
        if (videoId) {
            // 使用最简化的嵌入URL参数，避免任何可能导致问题的参数
            const embedParams = [
                'rel=0',
                'modestbranding=1',
                'controls=1',
                'fs=1',
                'playsinline=1'
            ].join('&');
            
            return {
                id: videoId,
                url: url,
                embed_url: `https://www.youtube.com/embed/${videoId}?${embedParams}`,
                title: 'YouTube视频',
                thumbnail: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
            };
        }
        
        return null;
    }

    createVideoPlayer(videoInfo) {
        // 清空视频容器
        this.videoContainer.innerHTML = '';
        
        // 调试信息
        console.log('创建视频播放器:', videoInfo);
        console.log('嵌入URL:', videoInfo.embed_url);
        
        // 创建YouTube iframe
        const iframe = document.createElement('iframe');
        iframe.src = videoInfo.embed_url;
        iframe.width = '100%';
        iframe.height = '400';
        iframe.frameBorder = '0';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        iframe.title = videoInfo.title || 'YouTube视频';
        
        // 添加加载错误处理
        iframe.onload = () => {
            console.log('YouTube iframe 加载完成');
        };
        
        iframe.onerror = () => {
            console.error('YouTube iframe 加载失败');
            this.showEmbedError(videoInfo);
        };
        
        // 添加到容器
        this.videoContainer.appendChild(iframe);
        
        // 存储iframe引用
        this.player = iframe;
        
        // 添加视频信息显示
        this.addVideoInfo(videoInfo);
        
        // 移除自动检查，让YouTube自然加载
        // 只有在用户明确遇到问题时才显示错误页面
    }

    addVideoInfo(videoInfo) {
        const infoContainer = document.createElement('div');
        infoContainer.className = 'video-info';
        infoContainer.innerHTML = `
            <div class="video-title">${videoInfo.title || 'YouTube视频'}</div>
            <div class="video-controls">
                <button class="btn btn-sm btn-outline" onclick="youtubeSystem.analyzeCurrentVideo()">
                    <i class="fas fa-brain"></i> AI分析
                </button>
                <button class="btn btn-sm btn-outline" onclick="youtubeSystem.generateContextDanmaku()">
                    <i class="fas fa-comments"></i> 生成弹幕
                </button>
            </div>
        `;
        
        this.videoContainer.appendChild(infoContainer);
    }

    showLoadingState() {
        this.loadButton.disabled = true;
        this.loadButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 加载中...';
        
        // 显示加载占位符
        this.videoContainer.innerHTML = `
            <div class="video-loading">
                <div class="spinner"></div>
                <p>正在加载视频...</p>
            </div>
        `;
    }

    hideLoadingState() {
        this.loadButton.disabled = false;
        this.loadButton.innerHTML = '<i class="fas fa-play"></i> 加载视频';
    }

    onVideoLoaded(videoInfo) {
        // 通知弹幕系统（如果存在onVideoLoaded方法）
        if (window.danmakuSystem && typeof window.danmakuSystem.onVideoLoaded === 'function') {
            window.danmakuSystem.onVideoLoaded(videoInfo);
        }
        
        // 通知聊天系统
        if (window.chatSystem) {
            // 可以在这里添加视频相关的欢迎消息
        }
        
        // 记录视频加载事件
        console.log('视频已加载:', videoInfo);
    }

    async analyzeCurrentVideo() {
        if (!this.currentVideo) {
            this.showNotification('请先加载视频', 'warning');
            return;
        }

        try {
            const response = await fetch('/api/video_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: this.currentVideo.url,
                    current_time: 0
                })
            });

            const data = await response.json();
            if (data.success) {
                // 显示分析结果
                this.showAnalysisResult(data.analysis);
            } else {
                throw new Error(data.error || '分析失败');
            }
        } catch (error) {
            console.error('视频分析失败:', error);
            this.showNotification('视频分析失败: ' + error.message, 'error');
        }
    }

    showAnalysisResult(analysis) {
        // 创建分析结果弹窗
        const modal = document.createElement('div');
        modal.className = 'analysis-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>AI视频分析结果</h3>
                    <button class="close-btn" onclick="this.parentElement.parentElement.parentElement.remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="analysis-content">${analysis}</div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // 3秒后自动关闭
        setTimeout(() => {
            if (modal.parentNode) {
                modal.remove();
            }
        }, 10000);
    }

    async generateContextDanmaku() {
        if (!this.currentVideo) {
            this.showNotification('请先加载视频', 'warning');
            return;
        }

        try {
            // 生成基于当前视频上下文的弹幕
            const response = await fetch('/api/generate_danmaku', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_context: `正在观看: ${this.currentVideo.title}`,
                    user_message: '基于当前视频内容生成弹幕'
                })
            });

            const data = await response.json();
            if (data.success) {
                // 添加到弹幕系统
                if (window.danmakuSystem) {
                    window.danmakuSystem.addDanmaku({
                        id: Date.now(),
                        text: data.danmaku,
                        type: 'ai',
                        timestamp: new Date().toISOString()
                    });
                }
                
                this.showNotification('AI弹幕已生成', 'success');
            } else {
                throw new Error(data.error || '生成失败');
            }
        } catch (error) {
            console.error('生成上下文弹幕失败:', error);
            this.showNotification('生成弹幕失败: ' + error.message, 'error');
        }
    }

    getCurrentVideoInfo() {
        return this.currentVideo;
    }

    isVideoLoaded() {
        return this.currentVideo !== null && this.player !== null;
    }

    checkEmbedStatus(videoInfo) {
        // 简化的检查逻辑，只在明确失败时显示错误
        const iframe = this.player;
        
        if (!iframe || !iframe.src) {
            console.warn('iframe不存在或没有src');
            return;
        }
        
        // 检查iframe的尺寸，如果为0可能表示加载失败
        if (iframe.offsetWidth === 0 || iframe.offsetHeight === 0) {
            console.warn('iframe尺寸为0，可能嵌入失败');
            this.showEmbedError(videoInfo);
            return;
        }
        
        // 如果iframe存在且有正常尺寸，认为加载成功
        console.log('YouTube iframe 加载正常');
    }

    showEmbedError(videoInfo) {
        // 显示嵌入错误和备用方案
        const errorContainer = document.createElement('div');
        errorContainer.className = 'embed-error-container';
        errorContainer.innerHTML = `
            <div class="embed-error">
                <div class="error-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="error-content">
                    <h3>视频无法在此页面播放</h3>
                    <p>该视频的拥有者已禁止在其他网站上播放此视频。</p>
                    <div class="error-actions">
                        <a href="${videoInfo.url || `https://www.youtube.com/watch?v=${videoInfo.id}`}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt"></i> 在YouTube上观看
                        </a>
                        <button onclick="youtubeSystem.tryAlternativeEmbed('${videoInfo.id}')" class="btn btn-secondary">
                            <i class="fas fa-redo"></i> 尝试其他方式
                        </button>
                    </div>
                    <div class="video-preview">
                        <img src="${videoInfo.thumbnail || `https://img.youtube.com/vi/${videoInfo.id}/maxresdefault.jpg`}" alt="视频缩略图" class="video-thumbnail">
                        <div class="video-details">
                            <h4>${videoInfo.title || 'YouTube视频'}</h4>
                            <p>视频ID: ${videoInfo.id}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // 替换当前视频容器内容
        this.videoContainer.innerHTML = '';
        this.videoContainer.appendChild(errorContainer);
    }

    tryAlternativeEmbed(videoId) {
        // 尝试使用最简化的嵌入参数
        const alternativeParams = [
            'rel=0',
            'modestbranding=1',
            'controls=1',
            'fs=1',
            'playsinline=1'
        ].join('&');
        
        const alternativeUrl = `https://www.youtube.com/embed/${videoId}?${alternativeParams}`;
        
        const iframe = document.createElement('iframe');
        iframe.src = alternativeUrl;
        iframe.width = '100%';
        iframe.height = '400';
        iframe.frameBorder = '0';
        iframe.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
        iframe.allowFullscreen = true;
        iframe.title = 'YouTube视频';
        
        // 清空容器并添加新的iframe
        this.videoContainer.innerHTML = '';
        this.videoContainer.appendChild(iframe);
        this.player = iframe;
        
        this.showNotification('正在尝试简化嵌入方式...', 'info');
        
        // 再次检查状态
        setTimeout(() => {
            this.checkEmbedStatus({id: videoId, url: `https://www.youtube.com/watch?v=${videoId}`});
        }, 3000);
    }

    showNotification(message, type = 'info') {
        // 显示通知
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // 获取视频播放状态（如果集成了YouTube Player API）
    getPlayerState() {
        if (this.player && this.player.getPlayerState) {
            return this.player.getPlayerState();
        }
        return null;
    }

    // 获取当前播放时间
    getCurrentTime() {
        if (this.player && this.player.getCurrentTime) {
            return this.player.getCurrentTime();
        }
        return 0;
    }

    // 跳转到指定时间
    seekTo(seconds) {
        if (this.player && this.player.seekTo) {
            this.player.seekTo(seconds);
        }
    }

    // 播放/暂停
    playPause() {
        if (this.player && this.player.playVideo) {
            const state = this.getPlayerState();
            if (state === 1) { // 正在播放
                this.player.pauseVideo();
            } else {
                this.player.playVideo();
            }
        }
    }
}

// 页面加载完成后初始化YouTube系统
document.addEventListener('DOMContentLoaded', () => {
    window.youtubeSystem = new YouTubeSystem();
    console.log('YouTube系统已初始化');
});

// 导出到全局作用域
window.YouTubeSystem = YouTubeSystem;
