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

        // 初始化帧捕获
        if (window.frameCapture && window.youtubeSystem && window.youtubeSystem.player) {
            window.frameCapture.init(window.youtubeSystem.player);
            // 开始捕获帧（每5-10秒）
            window.frameCapture.startCapturing(this.analysisInterval);
        }

        // 开始定期分析
        this.monitoringInterval = setInterval(() => {
            this.analyzeCurrentFrame();
        }, this.analysisInterval * 1000);
        
        console.log(`[VideoMonitor] 开始监控视频，每${this.analysisInterval}秒分析一次`);
    }

    stopMonitoring() {
        if (this.monitoringInterval) {
            clearInterval(this.monitoringInterval);
            this.monitoringInterval = null;
        }
        
        // 停止帧捕获
        if (window.frameCapture) {
            window.frameCapture.stopCapturing();
        }
        
        console.log('[VideoMonitor] 停止监控视频');
    }

    async analyzeCurrentFrame() {
        if (!this.currentVideo) return;

        const currentTime = this.getCurrentVideoTime();
        if (currentTime === null) return;

        // 避免重复分析同一时间点
        const timeKey = Math.floor(currentTime / this.analysisInterval) * this.analysisInterval;
        if (this.frameAnalysisCache.has(timeKey)) {
            // 即使已缓存，也显示结果
            const cached = this.frameAnalysisCache.get(timeKey);
            this.processAnalysis(cached, currentTime);
            return;
        }

        try {
            // 尝试捕获当前帧
            let frameImage = null;
            if (window.frameCapture) {
                const frameData = await window.frameCapture.captureFrame();
                if (frameData && frameData.imageData) {
                    frameImage = frameData.imageData;
                }
            }

            // 分析当前帧
            const requestBody = {
                frame_data: {
                    timestamp: currentTime,
                    video_url: this.currentVideo.url,
                    video_id: this.currentVideo.id
                },
                current_time: currentTime
            };

            // 如果有图像数据，添加到请求中
            if (frameImage) {
                requestBody.frame_image = frameImage;
            }

            const response = await fetch('/api/analyze_frame', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            if (data.success) {
                const analysis = data.analysis;
                this.frameAnalysisCache.set(timeKey, analysis);
                
                // 处理分析结果
                this.processAnalysis(analysis, currentTime);
                
                // 显示动作识别结果
                if (data.action_detected) {
                    this.displayActionRecognition(data);
                }
            }
        } catch (error) {
            console.error('分析视频帧失败:', error);
        }
    }

    displayActionRecognition(data) {
        // 在界面上显示动作识别结果和技术解说
        const actionPanel = document.getElementById('action-analysis-panel');
        if (!actionPanel) return;

        const action = data.analysis?.action || {};
        const actionName = action.action || data.action_detected || '未知动作';
        const confidence = (action.confidence || data.confidence || 0) * 100;
        const technique = action.technique || '';
        const keyPoints = action.key_points || [];
        const analysis = action.analysis || '';
        const category = action.category || '';
        
        // 获取技术解说
        const commentary = data.commentary || data.detailed_commentary?.main_commentary || '';
        const detailedCommentary = data.detailed_commentary || {};
        const technicalAnalysis = detailedCommentary.technical_analysis || analysis;

        // 创建动作识别显示（包含技术解说）
        const actionHtml = `
            <div class="action-recognition-result">
                <div class="action-header">
                    <h4 class="action-name">${actionName}</h4>
                    <span class="action-category badge-${category.toLowerCase().replace(/\s/g, '-')}">${category}</span>
                    <span class="action-confidence">置信度: ${confidence.toFixed(0)}%</span>
                </div>
                ${commentary ? `
                    <div class="action-commentary">
                        <div class="commentary-icon">🎙️</div>
                        <p class="commentary-text">${commentary}</p>
                    </div>
                ` : ''}
                <div class="action-technique">
                    <p>${technique}</p>
                </div>
                ${technicalAnalysis ? `<div class="action-analysis"><p>${technicalAnalysis}</p></div>` : ''}
                ${keyPoints.length > 0 ? `
                    <div class="action-key-points">
                        <strong>技术要点：</strong>
                        <ul>
                            ${keyPoints.map(point => `<li>${point}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                <div class="action-timestamp">
                    <small>识别时间: ${this.formatTime(data.timestamp || 0)}</small>
                </div>
            </div>
        `;

        // 添加淡入动画
        actionPanel.innerHTML = actionHtml;
        actionPanel.classList.add('action-updated');
        setTimeout(() => {
            actionPanel.classList.remove('action-updated');
        }, 1000);
        
        // 如果有解说，可以同时显示在弹幕区域
        if (commentary && window.danmakuSystem) {
            window.danmakuSystem.addDanmaku({
                id: Date.now(),
                text: `💬 ${commentary}`,
                type: 'commentary',
                timestamp: new Date().toISOString()
            });
        }
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${minutes}:${secs < 10 ? '0' : ''}${secs}`;
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
        // 在侧边栏显示动作分析（使用i18n）
        const actionPanel = document.getElementById('action-analysis-panel');
        if (actionPanel) {
            const actionLabel = window.i18n ? window.i18n.t('action_analysis.action', '动作识别') : '动作识别';
            const confidenceLabel = window.i18n ? window.i18n.t('action_analysis.confidence', '置信度') : '置信度';
            const tipsLabel = window.i18n ? window.i18n.t('action_analysis.tips', '技术要点：') : '技术要点：';
            
            actionPanel.innerHTML = `
                <div class="action-analysis">
                    <h4>${actionLabel}</h4>
                    <div class="action-name">${action.action}</div>
                    <div class="action-confidence">${confidenceLabel}: ${(action.confidence * 100).toFixed(0)}%</div>
                    <p class="action-technique">${action.technique}</p>
                    <div class="action-tips">
                        <strong>${tipsLabel}</strong>
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
            const recTitle = window.i18n ? window.i18n.t('recommendations.title', '推荐学习') : '推荐学习';
            recPanel.innerHTML = `
                <h4>${recTitle}</h4>
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

