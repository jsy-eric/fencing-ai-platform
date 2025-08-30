// 击剑AI智能体平台 - 主JavaScript文件
class FencingAIPlatform {
    constructor() {
        this.currentVideo = null;
        this.isAutoGenerating = false;
        this.autoGenerateInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadFiedata();
        this.setupWebSocket();
    }

    bindEvents() {
        // 导航链接点击事件
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleNavigation(e.target.getAttribute('href'));
            });
        });

        // 弹幕设置事件
        document.getElementById('show-danmaku').addEventListener('change', (e) => {
            this.toggleDanmaku(e.target.checked);
        });

        document.getElementById('danmaku-speed').addEventListener('change', (e) => {
            this.setDanmakuSpeed(e.target.value);
        });

        // 自动生成弹幕事件
        document.getElementById('auto-generate').addEventListener('click', () => {
            this.toggleAutoGenerate();
        });

        // 刷新FIE数据
        document.getElementById('refresh-fie').addEventListener('click', () => {
            this.loadFiedata();
        });
    }

    handleNavigation(href) {
        // 移除所有活动状态
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });

        // 添加活动状态到当前点击的链接
        event.target.classList.add('active');

        // 处理导航逻辑
        switch (href) {
            case '#home':
                this.showHome();
                break;
            case '#about':
                this.showAbout();
                break;
            case '#contact':
                this.showContact();
                break;
        }
    }

    showHome() {
        // 显示主页内容
        console.log('显示主页');
    }

    showAbout() {
        // 显示关于页面
        console.log('显示关于页面');
    }

    showContact() {
        // 显示联系页面
        console.log('显示联系页面');
    }

    async loadFiedata() {
        try {
            const fieDataElement = document.getElementById('fie-data');
            fieDataElement.innerHTML = '<div class="spinner"></div>';

            const response = await fetch('/api/fie_data');
            const data = await response.json();

            if (data.success) {
                this.displayFiedata(data.results);
            } else {
                fieDataElement.innerHTML = '<div class="error">加载失败</div>';
            }
        } catch (error) {
            console.error('加载FIE数据失败:', error);
            document.getElementById('fie-data').innerHTML = '<div class="error">网络错误</div>';
        }
    }

    displayFiedata(results) {
        const fieDataElement = document.getElementById('fie-data');
        
        if (!results || results.length === 0) {
            fieDataElement.innerHTML = '<div class="no-data">暂无数据</div>';
            return;
        }

        let html = '<div class="fie-results">';
        results.forEach(result => {
            html += `
                <div class="fie-result">
                    <div class="result-header">
                        <span class="tournament">${result.tournament || '未知比赛'}</span>
                        <span class="date">${result.date || '未知日期'}</span>
                    </div>
                    <div class="result-content">
                        <div class="winner">🏆 ${result.winner || '未知'}</div>
                        <div class="runner-up">🥈 ${result.runner_up || '未知'}</div>
                        <div class="third">🥉 ${result.third || '未知'}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        fieDataElement.innerHTML = html;
    }

    toggleDanmaku(show) {
        const danmakuDisplay = document.getElementById('danmaku-display');
        if (show) {
            danmakuDisplay.style.display = 'block';
        } else {
            danmakuDisplay.style.display = 'none';
        }
    }

    setDanmakuSpeed(speed) {
        // 设置弹幕速度
        const duration = 12 - speed; // 速度越快，持续时间越短
        document.documentElement.style.setProperty('--danmaku-duration', `${duration}s`);
    }

    toggleAutoGenerate() {
        const button = document.getElementById('auto-generate');
        
        if (this.isAutoGenerating) {
            this.stopAutoGenerate();
            button.innerHTML = '<i class="fas fa-sync"></i> 自动生成';
            button.classList.remove('btn-danger');
            button.classList.add('btn-info');
        } else {
            this.startAutoGenerate();
            button.innerHTML = '<i class="fas fa-stop"></i> 停止生成';
            button.classList.remove('btn-info');
            button.classList.add('btn-danger');
        }
    }

    startAutoGenerate() {
        this.isAutoGenerating = true;
        this.autoGenerateInterval = setInterval(() => {
            this.generateRandomDanmaku();
        }, 3000); // 每3秒生成一条弹幕
    }

    stopAutoGenerate() {
        this.isAutoGenerating = false;
        if (this.autoGenerateInterval) {
            clearInterval(this.autoGenerateInterval);
            this.autoGenerateInterval = null;
        }
    }

    async generateRandomDanmaku() {
        try {
            const contexts = ['进攻', '防守', '战术', '技术', '精彩'];
            const randomContext = contexts[Math.floor(Math.random() * contexts.length)];
            
            const response = await fetch('/api/generate_danmaku', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_context: randomContext,
                    user_message: ''
                })
            });

            const data = await response.json();
            if (data.success) {
                // 触发弹幕显示
                window.danmakuSystem.addDanmaku(data.danmaku);
            }
        } catch (error) {
            console.error('生成AI弹幕失败:', error);
        }
    }

    setupWebSocket() {
        // 设置WebSocket连接（如果需要实时通信）
        // 这里可以用于实时弹幕推送等功能
        console.log('WebSocket连接已设置');
    }

    // 工具方法
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// 全局错误处理
window.addEventListener('error', (event) => {
    console.error('全局错误:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('未处理的Promise拒绝:', event.reason);
});

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    window.fencingAIPlatform = new FencingAIPlatform();
    console.log('击剑AI智能体平台已初始化');
});

// 导出到全局作用域
window.FencingAIPlatform = FencingAIPlatform;
