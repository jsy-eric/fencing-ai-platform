// 视频监控系统 - 实时分析视频并推送知识
class VideoMonitor {
    constructor() {
        this.monitoringInterval = null;
        this.lastAnalysisTime = 0;
        this.analysisInterval = 5; // 每5秒分析一次
        this.currentVideo = null;
        this.frameAnalysisCache = new Map();
    }

    startMonitoring(videoInfo) {
        this.currentVideo = videoInfo;
        this.lastAnalysisTime = 0;
        
        // 加载关键时刻
        if (window.timelineAnnotator) {
            const duration = videoInfo.duration || 300; // 默认5分钟
            window.timelineAnnotator.loadKeyMoments(videoInfo.url, duration);
        }

        // 开始定期分析
        this.monitoringInterval = setInterval(() => {
            this.analyzeCurrentFrame();
        }, this.analysisInterval * 1000);
    }

    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
    }

    async analyzeCurrentFrame() {
        if (!this.currentVideo) return;

        const currentTime = this.getCurrentVideoTime();
        if (currentTime === null) return;

        // 避免重复分析同一时间点
        const timeKey = Math.floor(currentTime / this.analysisInterval) * this.analysisInterval;
        if (this.frameAnalysisCache.has(timeKey)) {
            return;
        }

        try {
            // 分析当前帧
            const response = await fetch('/api/analyze_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    frame_data: {
                        timestamp: currentTime,
                        video_url: this.currentVideo.url
                    },
                    current_time: currentTime
                })
            });

            const data = await response.json();
            if (data.success) {
                const analysis = data.analysis;
                this.frameAnalysisCache.set(timeKey, analysis);
                
                // 处理分析结果
                this.processAnalysis(analysis, currentTime);
            }
        } catch (error) {
            console.error('分析视频帧失败:', error);
        }
    }

    processAnalysis(analysis, currentTime) {
        // 1. 显示知识卡片
        const knowledgePoints = analysis.knowledge_points || [];
        knowledgePoints.forEach(point => {
            if (window.knowledgeCardSystem) {
                window.knowledgeCardSystem.showCardAtTime(currentTime, {
                    type: point.type,
                    title: point.title,
                    content: point.content,
                    tips: []
                });
            }
        });

        // 2. 生成智能弹幕
        if (window.danmakuSystem) {
            const danmaku = window.danmakuSystem.generate_contextual_danmaku(analysis, currentTime);
            if (danmaku) {
                window.danmakuSystem.addDanmaku({
                    id: Date.now(),
                    text: danmaku,
                    type: 'ai',
                    timestamp: new Date().toISOString()
                });
            }
        }

        // 3. 显示动作识别结果
        const action = analysis.action;
        if (action && action.action) {
            this.showActionAnalysis(action, currentTime);
        }

        // 4. 推荐相关知识
        this.recommendKnowledge(analysis.scene, currentTime);

        // 5. 生成互动问题（每30秒一次）
        if (currentTime % 30 === 0) {
            if (window.interactiveQA) {
                const context = `${analysis.scene.weapon} - ${analysis.scene.stage}`;
                window.interactiveQA.generateQuestionAtTime(currentTime, context);
            }
        }
    }

    showActionAnalysis(action, currentTime) {
        // 在侧边栏显示动作分析
        const actionPanel = document.getElementById('action-analysis-panel');
        if (actionPanel) {
            actionPanel.innerHTML = `
                <div class="action-analysis">
                    <h4>动作识别</h4>
                    <div class="action-name">${action.action}</div>
                    <div class="action-confidence">置信度: ${(action.confidence * 100).toFixed(0)}%</div>
                    <p class="action-technique">${action.technique}</p>
                    <div class="action-tips">
                        <strong>技术要点：</strong>
                        <ul>
                            ${action.key_points.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        }
    }

    async recommendKnowledge(scene, currentTime) {
        try {
            const response = await fetch('/api/recommend_knowledge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_context: scene,
                    user_id: 'default'
                })
            });

            const data = await response.json();
            if (data.success && data.recommendations.length > 0) {
                this.showRecommendations(data.recommendations);
            }
        } catch (error) {
            console.error('获取知识推荐失败:', error);
        }
    }

    showRecommendations(recommendations) {
        const recPanel = document.getElementById('knowledge-recommendations');
        if (recPanel) {
            recPanel.innerHTML = `
                <h4>推荐学习</h4>
                <ul class="recommendation-list">
                    ${recommendations.slice(0, 3).map(rec => `
                        <li class="recommendation-item" onclick="videoMonitor.showRecommendationDetail('${rec.id}')">
                            <strong>${rec.title}</strong>
                            <p>${rec.content.substring(0, 50)}...</p>
                        </li>
                    `).join('')}
                </ul>
            `;
        }
    }

    showRecommendationDetail(recommendationId) {
        // 显示推荐详情
        console.log('显示推荐详情:', recommendationId);
    }

    getCurrentVideoTime() {
        // 尝试从YouTube Player获取当前时间
        if (window.youtubeSystem && window.youtubeSystem.player) {
            // 如果使用YouTube Player API
            if (window.youtubeSystem.player.getCurrentTime) {
                return window.youtubeSystem.player.getCurrentTime();
            }
        }
        
        // 从URL参数获取（如果iframe支持）
        const iframe = document.querySelector('#video-player iframe');
        if (iframe && iframe.src) {
            const match = iframe.src.match(/[?&]start=(\d+)/);
            if (match) {
                return parseInt(match[1]);
            }
        }
        
        return null;
    }
}

// 初始化
window.videoMonitor = new VideoMonitor();

// 当视频加载时自动开始监控
document.addEventListener('DOMContentLoaded', () => {
    // 监听视频加载事件
    if (window.youtubeSystem) {
        const originalOnVideoLoaded = window.youtubeSystem.onVideoLoaded;
        window.youtubeSystem.onVideoLoaded = function(videoInfo) {
            if (originalOnVideoLoaded) {
                originalOnVideoLoaded.call(this, videoInfo);
            }
            // 开始监控
            if (window.videoMonitor) {
                window.videoMonitor.startMonitoring(videoInfo);
            }
        };
    }
});

