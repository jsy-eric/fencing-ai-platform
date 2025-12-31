// 时间轴标注系统
class TimelineAnnotator {
    constructor() {
        this.moments = [];
        this.timelineContainer = null;
        this.currentVideo = null;
    }

    init(containerId = 'video-timeline') {
        this.timelineContainer = document.getElementById(containerId);
        if (!this.timelineContainer) {
            this.timelineContainer = document.createElement('div');
            this.timelineContainer.id = containerId;
            this.timelineContainer.className = 'video-timeline';
            const videoContainer = document.getElementById('video-player');
            if (videoContainer && videoContainer.parentNode) {
                videoContainer.parentNode.insertBefore(this.timelineContainer, videoContainer.nextSibling);
            }
        }
    }

    async loadKeyMoments(videoUrl, duration) {
        try {
            const response = await fetch('/api/detect_key_moments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_url: videoUrl,
                    duration: duration
                })
            });

            const data = await response.json();
            if (data.success) {
                this.moments = data.moments;
                this.renderTimeline();
            }
        } catch (error) {
            console.error('加载关键时刻失败:', error);
        }
    }

    renderTimeline() {
        if (!this.timelineContainer) {
            this.init();
        }

        this.timelineContainer.innerHTML = '<div class="timeline-header">关键时刻</div>';
        const timelineBar = document.createElement('div');
        timelineBar.className = 'timeline-bar';

        this.moments.forEach(moment => {
            const marker = this.createMarker(moment);
            timelineBar.appendChild(marker);
        });

        this.timelineContainer.appendChild(timelineBar);
    }

    createMarker(moment) {
        const marker = document.createElement('div');
        marker.className = `timeline-marker marker-${moment.type}`;
        marker.dataset.time = moment.time;
        marker.title = `${moment.description} - ${this.formatTime(moment.time)}`;

        const dot = document.createElement('div');
        dot.className = 'marker-dot';
        marker.appendChild(dot);

        const label = document.createElement('div');
        label.className = 'marker-label';
        label.textContent = this.formatTime(moment.time);
        marker.appendChild(label);

        // 点击跳转
        marker.addEventListener('click', () => {
            this.seekToTime(moment.time);
            this.showKnowledgeCard(moment);
        });

        return marker;
    }

    seekToTime(time) {
        if (window.youtubeSystem && window.youtubeSystem.player) {
            // 如果使用YouTube Player API
            if (window.youtubeSystem.player.seekTo) {
                window.youtubeSystem.player.seekTo(time, true);
            } else {
                // 使用URL参数跳转
                const iframe = window.youtubeSystem.player;
                if (iframe && iframe.src) {
                    const newUrl = iframe.src.split('&start=')[0] + `&start=${time}`;
                    iframe.src = newUrl;
                }
            }
        }
    }

    showKnowledgeCard(moment) {
        if (moment.knowledge && window.knowledgeCardSystem) {
            window.knowledgeCardSystem.showCardAtTime(moment.time, {
                type: moment.type,
                title: moment.knowledge.title,
                content: moment.knowledge.content,
                tips: moment.knowledge.tips || []
            });
        }
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }

    addMoment(moment) {
        this.moments.push(moment);
        this.moments.sort((a, b) => a.time - b.time);
        this.renderTimeline();
    }
}

// 初始化
window.timelineAnnotator = new TimelineAnnotator();

