// AI聊天系统
class ChatSystem {
    constructor() {
        this.chatContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-chat');
        this.messageHistory = [];
        this.isTyping = false;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadChatHistory();
    }

    bindEvents() {
        // 发送消息事件
        this.sendButton.addEventListener('click', () => {
            this.sendMessage();
        });

        // 输入框回车事件
        this.chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // 输入框输入事件（用于实时验证）
        this.chatInput.addEventListener('input', () => {
            this.validateInput();
        });
    }

    validateInput() {
        const message = this.chatInput.value.trim();
        const isValid = message.length > 0 && message.length <= 500;
        
        this.sendButton.disabled = !isValid;
        
        if (message.length > 500) {
            this.showInputWarning('消息不能超过500个字符');
        } else {
            this.hideInputWarning();
        }
    }

    showInputWarning(message) {
        let warning = document.getElementById('input-warning');
        if (!warning) {
            warning = document.createElement('div');
            warning.id = 'input-warning';
            warning.className = 'input-warning';
            this.chatInput.parentNode.appendChild(warning);
        }
        warning.textContent = message;
        warning.style.display = 'block';
    }

    hideInputWarning() {
        const warning = document.getElementById('input-warning');
        if (warning) {
            warning.style.display = 'none';
        }
    }

    async sendMessage() {
        const message = this.chatInput.value.trim();
        
        if (!message || this.isTyping) {
            return;
        }

        // 添加用户消息到聊天界面
        this.addMessage(message, 'user');
        
        // 清空输入框
        this.chatInput.value = '';
        this.validateInput();

        // 显示AI正在输入状态
        this.showTypingIndicator();

        try {
            // 获取当前视频上下文
            const videoContext = this.getVideoContext();
            
            // 发送消息到AI
            const response = await this.sendMessageToAI(message, videoContext);
            
            // 隐藏输入状态
            this.hideTypingIndicator();
            
            // 添加AI回复
            if (response && response.trim().length > 0) {
                this.addMessage(response, 'ai');
            } else {
                console.warn('收到空响应');
                this.addMessage('抱歉，我收到了空响应，请稍后再试。', 'ai');
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            this.hideTypingIndicator();
            const errorMessage = error.message || '未知错误';
            this.addMessage(`抱歉，我遇到了一些问题：${errorMessage}。请稍后再试。`, 'ai');
        }
    }

    async sendMessageToAI(message, videoContext) {
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    video_context: videoContext
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP错误: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();
            if (data.success) {
                if (data.response && data.response.trim().length > 0) {
                    return data.response;
                } else {
                    throw new Error('AI返回了空响应');
                }
            } else {
                throw new Error(data.error || '未知错误');
            }
        } catch (error) {
            console.error('发送消息到AI失败:', error);
            throw error;
        }
    }

    getVideoContext() {
        // 获取当前视频的上下文信息
        const videoPlayer = document.getElementById('video-player');
        const iframe = videoPlayer.querySelector('iframe');
        
        if (iframe) {
            // 如果有YouTube iframe，尝试获取当前播放信息
            try {
                // 这里可以集成YouTube Player API获取更多信息
                // 返回不带"正在观看"前缀的文本，由后端处理
                return '击剑比赛视频';
            } catch (e) {
                return '击剑比赛视频';
            }
        }
        
        // 如果没有视频，返回空字符串，让后端使用默认回复
        return '';
    }

    addMessage(content, type) {
        const message = {
            id: Date.now(),
            content: content,
            type: type,
            timestamp: new Date().toISOString()
        };

        // 添加到历史记录
        this.messageHistory.push(message);
        
        // 限制历史记录数量
        if (this.messageHistory.length > 100) {
            this.messageHistory.shift();
        }

        // 显示消息
        this.displayMessage(message);
        
        // 滚动到底部
        this.scrollToBottom();
        
        // 保存到本地存储
        this.saveChatHistory();
    }

    displayMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.type}-message`;
        messageElement.dataset.id = message.id;

        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        
        if (message.type === 'ai') {
            avatar.innerHTML = '<i class="fas fa-robot"></i>';
        } else {
            avatar.innerHTML = '<i class="fas fa-user"></i>';
        }

        const content = document.createElement('div');
        content.className = 'message-content';
        
        // 处理消息内容，支持换行和链接
        const formattedContent = this.formatMessageContent(message.content);
        content.innerHTML = formattedContent;

        messageElement.appendChild(avatar);
        messageElement.appendChild(content);

        // 添加时间戳
        const timestamp = document.createElement('div');
        timestamp.className = 'message-timestamp';
        timestamp.textContent = this.formatTimestamp(message.timestamp);
        messageElement.appendChild(timestamp);

        // 添加到聊天容器
        this.chatContainer.appendChild(messageElement);
        
        // 添加淡入动画
        messageElement.classList.add('fade-in');
    }

    formatMessageContent(content) {
        // 处理换行符
        content = content.replace(/\n/g, '<br>');
        
        // 处理链接
        content = content.replace(
            /(https?:\/\/[^\s]+)/g,
            '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
        );
        
        // 处理击剑相关术语高亮
        const fencingTerms = [
            '花剑', '重剑', '佩剑', '进攻', '防守', '格挡', '闪避',
            '直刺', '转移刺', '击打刺', '复合进攻', '战术', '策略'
        ];
        
        fencingTerms.forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            content = content.replace(regex, '<span class="fencing-term">$1</span>');
        });
        
        return content;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;
        
        if (diff < 60000) { // 1分钟内
            return '刚刚';
        } else if (diff < 3600000) { // 1小时内
            return `${Math.floor(diff / 60000)}分钟前`;
        } else if (diff < 86400000) { // 1天内
            return `${Math.floor(diff / 3600000)}小时前`;
        } else {
            return date.toLocaleDateString();
        }
    }

    showTypingIndicator() {
        this.isTyping = true;
        
        const typingElement = document.createElement('div');
        typingElement.className = 'message ai-message typing-indicator';
        typingElement.id = 'typing-indicator';
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = '<i class="fas fa-robot"></i>';
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        
        typingElement.appendChild(avatar);
        typingElement.appendChild(content);
        
        this.chatContainer.appendChild(typingElement);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingIndicator = document.getElementById('typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    scrollToBottom() {
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    loadChatHistory() {
        try {
            const saved = localStorage.getItem('fencing_chat_history');
            if (saved) {
                this.messageHistory = JSON.parse(saved);
                // 显示最近的消息
                this.messageHistory.slice(-10).forEach(message => {
                    this.displayMessage(message);
                });
            }
        } catch (error) {
            console.error('加载聊天历史失败:', error);
        }
    }

    saveChatHistory() {
        try {
            localStorage.setItem('fencing_chat_history', JSON.stringify(this.messageHistory));
        } catch (error) {
            console.error('保存聊天历史失败:', error);
        }
    }

    clearChatHistory() {
        this.messageHistory = [];
        this.chatContainer.innerHTML = '';
        localStorage.removeItem('fencing_chat_history');
        
        // 添加欢迎消息（使用i18n）
        const welcomeMsg = window.i18n ? window.i18n.t('chat.welcome_message', '您好！我是击剑AI专家，可以为您解答击剑相关问题，分析比赛内容，并生成相关弹幕。请问有什么可以帮助您的吗？') : '聊天历史已清除。您好！我是击剑AI专家，可以为您解答击剑相关问题，分析比赛内容，并生成相关弹幕。请问有什么可以帮助您的吗？';
        this.addMessage(welcomeMsg, 'ai');
    }

    // 快速回复功能
    addQuickReply(text) {
        this.chatInput.value = text;
        this.validateInput();
        this.chatInput.focus();
    }

    // 获取聊天统计信息
    getChatStats() {
        const userMessages = this.messageHistory.filter(m => m.type === 'user').length;
        const aiMessages = this.messageHistory.filter(m => m.type === 'ai').length;
        
        return {
            total: this.messageHistory.length,
            user: userMessages,
            ai: aiMessages,
            ratio: userMessages > 0 ? (aiMessages / userMessages).toFixed(2) : 0
        };
    }

    // 导出聊天记录
    exportChatHistory() {
        const data = {
            exportDate: new Date().toISOString(),
            stats: this.getChatStats(),
            messages: this.messageHistory
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        
        const a = document.createElement('a');
        a.href = url;
        a.download = `fencing_chat_history_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        
        URL.revokeObjectURL(url);
    }
}

// 页面加载完成后初始化聊天系统
document.addEventListener('DOMContentLoaded', () => {
    window.chatSystem = new ChatSystem();
    console.log('聊天系统已初始化');
});

// 导出到全局作用域
window.ChatSystem = ChatSystem;
