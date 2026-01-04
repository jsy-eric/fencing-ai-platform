// 视频帧捕获模块 - 从YouTube视频中捕获帧
class FrameCapture {
    constructor() {
        this.captureInterval = null;
        this.captureIntervalSeconds = 5; // 每5秒捕获一次
        this.player = null;
        this.canvas = null;
        this.ctx = null;
        this.isCapturing = false;
    }

    init(player) {
        this.player = player;
        this.setupCanvas();
    }

    setupCanvas() {
        // 创建隐藏的canvas用于截图
        this.canvas = document.createElement('canvas');
        this.canvas.width = 640;
        this.canvas.height = 360;
        this.canvas.style.display = 'none';
        document.body.appendChild(this.canvas);
        this.ctx = this.canvas.getContext('2d');
    }

    startCapturing(intervalSeconds = 5) {
        if (this.isCapturing) {
            this.stopCapturing();
        }

        this.captureIntervalSeconds = intervalSeconds;
        this.isCapturing = true;

        // 立即捕获一次
        this.captureFrame();

        // 设置定期捕获
        this.captureInterval = setInterval(() => {
            this.captureFrame();
        }, this.captureIntervalSeconds * 1000);
    }

    stopCapturing() {
        if (this.captureInterval) {
            clearInterval(this.captureInterval);
            this.captureInterval = null;
        }
        this.isCapturing = false;
    }

    async captureFrame() {
        if (!this.player || !this.canvas) {
            console.warn('Player or canvas not initialized');
            return null;
        }

        try {
            // 获取视频iframe
            const iframe = this.player.querySelector('iframe');
            if (!iframe) {
                console.warn('No iframe found');
                return null;
            }

            // 由于跨域限制，无法直接从iframe截图
            // 使用替代方案：通过YouTube Player API获取当前帧信息
            const frameData = await this.captureFrameFromPlayer();
            return frameData;
        } catch (error) {
            console.error('Frame capture error:', error);
            return null;
        }
    }

    async captureFrameFromPlayer() {
        // 由于YouTube iframe的跨域限制，我们使用以下方案：
        // 1. 获取当前播放时间
        // 2. 使用YouTube Thumbnail API获取该时间点的缩略图
        // 3. 或者使用YouTube Player API的状态信息
        
        if (!window.youtubeSystem || !window.youtubeSystem.currentVideo) {
            return null;
        }

        const videoId = window.youtubeSystem.currentVideo.id;
        const currentTime = window.youtubeSystem.getCurrentTime();

        if (!videoId || currentTime === null) {
            return null;
        }

        try {
            // 方案1: 使用YouTube Thumbnail API（需要视频ID和时间）
            // 注意：YouTube Thumbnail API只能获取预设的缩略图，不能获取任意时间点
            
            // 方案2: 使用canvas绘制当前可见的视频帧（如果可能）
            // 由于跨域限制，这通常不可行
            
            // 方案3: 发送当前时间到后端，后端可以尝试获取帧
            // 或者使用YouTube Data API
            
            // 当前实现：返回元数据，后端可以基于此进行分析
            return {
                videoId: videoId,
                timestamp: currentTime,
                videoUrl: window.youtubeSystem.currentVideo.url,
                // 注意：由于跨域限制，无法直接获取图像数据
                // 实际应用中可能需要：
                // 1. 使用服务器端代理获取帧
                // 2. 使用YouTube Data API
                // 3. 使用浏览器扩展绕过跨域限制
            };
        } catch (error) {
            console.error('Frame capture from player error:', error);
            return null;
        }
    }

    // 尝试从可见的视频元素截图（如果同源）
    captureFromVideoElement(videoElement) {
        if (!videoElement || !this.canvas) {
            return null;
        }

        try {
            // 设置canvas尺寸
            this.canvas.width = videoElement.videoWidth || 640;
            this.canvas.height = videoElement.videoHeight || 360;

            // 绘制视频帧到canvas
            this.ctx.drawImage(videoElement, 0, 0, this.canvas.width, this.canvas.height);

            // 转换为base64
            const imageData = this.canvas.toDataURL('image/jpeg', 0.8);
            return imageData;
        } catch (error) {
            console.error('Capture from video element error:', error);
            return null;
        }
    }

    // 使用YouTube Player API获取视频信息
    async getVideoFrameInfo() {
        if (!this.player) {
            return null;
        }

        try {
            // 获取当前播放状态
            const currentTime = window.youtubeSystem?.getCurrentTime();
            const videoId = window.youtubeSystem?.currentVideo?.id;

            if (currentTime === null || !videoId) {
                return null;
            }

            return {
                videoId: videoId,
                timestamp: currentTime,
                // 可以尝试获取YouTube的缩略图
                thumbnailUrl: `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`
            };
        } catch (error) {
            console.error('Get video frame info error:', error);
            return null;
        }
    }
}

// 全局实例
window.frameCapture = new FrameCapture();

