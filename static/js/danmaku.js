// 弹幕系统
class DanmakuSystem {
    constructor() {
        this.danmakuContainer = document.getElementById('danmaku-display');
        this.activeDanmaku = [];
        this.danmakuQueue = [];
        this.maxDanmaku = 50;
        this.danmakuSpeed = 5;
        this.isEnabled = true;
        this.init();
    }

    init() {
        this.bindEvents();
        this.startRenderLoop();
    }

    bindEvents() {
        // 发送弹幕事件
        document.getElementById('send-danmaku').addEventListener('click', () => {
            this.sendUserDanmaku();
        });

        // 弹幕输入框回车事件
        document.getElementById('danmaku-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendUserDanmaku();
            }
        });

        // AI生成弹幕事件
        document.getElementById('generate-ai-danmaku').addEventListener('click', () => {
            this.generateAIDanmaku();
        });
    }

    sendUserDanmaku() {
        const input = document.getElementById('danmaku-input');
        const message = input.value.trim();
        
        if (!message) {
            this.showNotification('请输入弹幕内容', 'warning');
            return;
        }

        if (message.length > 50) {
            this.showNotification('弹幕内容不能超过50个字符', 'warning');
            return;
        }

        // 发送弹幕到服务器
        this.sendDanmakuToServer(message, 'user');
        
        // 清空输入框
        input.value = '';
    }

    async sendDanmakuToServer(message, type = 'user') {
        try {
            const response = await fetch('/api/send_danmaku', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    user_id: this.getUserId(),
                    type: type
                })
            });

            const data = await response.json();
            if (data.success) {
                // 添加到弹幕队列
                this.addDanmaku({
                    id: data.danmaku_id,
                    text: message,
                    type: type,
                    timestamp: new Date().toISOString()
                });
            } else {
                this.showNotification('发送弹幕失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('发送弹幕失败:', error);
            this.showNotification('网络错误，发送失败', 'error');
        }
    }

    async generateAIDanmaku() {
        try {
            const response = await fetch('/api/generate_danmaku', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    video_context: '击剑比赛',
                    user_message: ''
                })
            });

            const data = await response.json();
            if (data.success) {
                this.addDanmaku({
                    id: Date.now(),
                    text: data.danmaku,
                    type: 'ai',
                    timestamp: new Date().toISOString()
                });
            } else {
                this.showNotification('生成AI弹幕失败: ' + data.error, 'error');
            }
        } catch (error) {
            console.error('生成AI弹幕失败:', error);
            this.showNotification('网络错误，生成失败', 'error');
        }
    }

    addDanmaku(danmaku) {
        // 添加到队列
        this.danmakuQueue.push(danmaku);
        
        // 如果队列过长，移除旧的弹幕
        if (this.danmakuQueue.length > this.maxDanmaku) {
            this.danmakuQueue.shift();
        }

        // 如果弹幕系统已启用，立即显示
        if (this.isEnabled) {
            this.displayDanmaku(danmaku);
        }
    }

    displayDanmaku(danmaku) {
        if (!this.isEnabled) return;

        // 创建弹幕元素
        const danmakuElement = this.createDanmakuElement(danmaku);
        
        // 添加到容器
        this.danmakuContainer.appendChild(danmakuElement);
        
        // 添加到活动弹幕列表
        this.activeDanmaku.push({
            element: danmakuElement,
            startTime: Date.now()
        });

        // 设置动画结束后的清理
        setTimeout(() => {
            this.removeDanmaku(danmakuElement);
        }, 8000); // 8秒后自动移除
    }

    createDanmakuElement(danmaku) {
        const element = document.createElement('div');
        element.className = 'danmaku';
        element.textContent = danmaku.text;
        element.dataset.id = danmaku.id;
        element.dataset.type = danmaku.type;

        // 设置弹幕样式
        this.setDanmakuStyle(element, danmaku);

        // 设置随机位置
        const top = Math.random() * (this.danmakuContainer.clientHeight - 30);
        element.style.top = `${top}px`;

        return element;
    }

    setDanmakuStyle(element, danmaku) {
        // 根据弹幕类型设置不同样式
        switch (danmaku.type) {
            case 'ai':
                element.style.color = '#FFD700'; // 金色
                element.style.fontSize = '18px';
                element.style.fontWeight = 'bold';
                break;
            case 'user':
                element.style.color = '#FFFFFF'; // 白色
                element.style.fontSize = '16px';
                break;
            default:
                element.style.color = '#FFFFFF';
                element.style.fontSize = '16px';
        }

        // 设置动画持续时间
        const duration = 12 - this.danmakuSpeed;
        element.style.animationDuration = `${duration}s`;
    }

    removeDanmaku(element) {
        // 从DOM中移除
        if (element.parentNode) {
            element.parentNode.removeChild(element);
        }

        // 从活动弹幕列表中移除
        this.activeDanmaku = this.activeDanmaku.filter(d => d.element !== element);
    }

    startRenderLoop() {
        // 渲染循环，用于更新弹幕位置和状态
        setInterval(() => {
            this.updateDanmaku();
        }, 100); // 每100ms更新一次
    }

    updateDanmaku() {
        // 更新弹幕状态
        this.activeDanmaku.forEach(danmaku => {
            const elapsed = Date.now() - danmaku.startTime;
            const progress = elapsed / 8000; // 8秒总时长

            // 根据进度调整透明度
            if (progress > 0.8) {
                danmaku.element.style.opacity = 1 - (progress - 0.8) * 5;
            }
        });
    }

    clearAllDanmaku() {
        // 清除所有弹幕
        this.activeDanmaku.forEach(danmaku => {
            this.removeDanmaku(danmaku.element);
        });
        this.activeDanmaku = [];
        this.danmakuQueue = [];
    }

    toggleDanmaku(show) {
        this.isEnabled = show;
        if (show) {
            this.danmakuContainer.style.display = 'block';
            // 显示队列中的弹幕
            this.danmakuQueue.forEach(danmaku => {
                this.displayDanmaku(danmaku);
            });
        } else {
            this.danmakuContainer.style.display = 'none';
            this.clearAllDanmaku();
        }
    }

    setSpeed(speed) {
        this.danmakuSpeed = speed;
        // 更新现有弹幕的速度
        this.activeDanmaku.forEach(danmaku => {
            const duration = 12 - speed;
            danmaku.element.style.animationDuration = `${duration}s`;
        });
    }

    getUserId() {
        // 获取用户ID，这里可以集成用户系统
        return 'user_' + Math.random().toString(36).substr(2, 9);
    }

    showNotification(message, type = 'info') {
        // 显示通知
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        // 添加到页面
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    // 批量添加弹幕（用于初始化或批量导入）
    addBatchDanmaku(danmakuList) {
        danmakuList.forEach(danmaku => {
            this.addDanmaku(danmaku);
        });
    }

    // 获取弹幕统计信息
    getStats() {
        return {
            active: this.activeDanmaku.length,
            queued: this.danmakuQueue.length,
            total: this.activeDanmaku.length + this.danmakuQueue.length
        };
    }

    // 导出弹幕数据
    exportDanmaku() {
        return {
            active: this.activeDanmaku.map(d => ({
                id: d.element.dataset.id,
                text: d.element.textContent,
                type: d.element.dataset.type,
                timestamp: d.startTime
            })),
            queue: this.danmakuQueue
        };
    }
}

// 页面加载完成后初始化弹幕系统
document.addEventListener('DOMContentLoaded', () => {
    window.danmakuSystem = new DanmakuSystem();
    console.log('弹幕系统已初始化');
});

// 导出到全局作用域
window.DanmakuSystem = DanmakuSystem;
