// AI 聊天系统
class ChatSystem {
    constructor() {
        this.chatContainer = document.getElementById('chat-messages');
        this.chatInput = document.getElementById('chat-input');
        this.sendButton = document.getElementById('send-chat');
        this.isTyping = false;
        this.bindEvents();
    }

    bindEvents() {
        this.sendButton?.addEventListener('click', () => this.sendMessage());
        this.chatInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    async sendMessage() {
        const message = (this.chatInput?.value || '').trim();
        if (!message || this.isTyping) return;

        this.addMessage(message, 'user');
        this.chatInput.value = '';
        this.showTyping();

        try {
            const videoContext = this.getVideoContext();
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message, video_context: videoContext })
            });
            const data = await response.json();
            this.hideTyping();
            if (data.success && data.response) {
                this.addMessage(data.response, 'ai');
            } else {
                this.addMessage('抱歉，未能获取到回复。', 'ai');
            }
        } catch (e) {
            this.hideTyping();
            this.addMessage('网络错误：' + e.message, 'ai');
        }
    }

    getVideoContext() {
        const video = window.youtubeSystem?.getCurrentVideoInfo?.();
        if (video && video.title) {
            return '正在观看：' + video.title;
        }
        return '击剑比赛';
    }

    addMessage(content, type) {
        const msg = document.createElement('div');
        msg.className = 'msg ' + (type === 'user' ? 'msg--user' : 'msg--ai');

        if (type === 'user') {
            msg.innerHTML = `
                <div class="msg__body msg__body--user">
                    <p>${escapeHtml(content)}</p>
                </div>
                <div class="msg__avatar msg__avatar--user">U</div>
            `;
        } else {
            msg.innerHTML = `
                <div class="msg__avatar msg__avatar--ai"><i class="fas fa-microchip"></i></div>
                <div class="msg__body">
                    <div class="msg__author">FencingAI <span class="msg__time">${this.formatTime(new Date())}</span></div>
                    <p>${escapeHtml(content)}</p>
                </div>
            `;
        }
        this.chatContainer?.appendChild(msg);
        this.scrollToBottom();
    }

    showTyping() {
        this.isTyping = true;
        const typing = document.createElement('div');
        typing.id = 'typing-indicator';
        typing.className = 'msg msg--ai msg--typing';
        typing.innerHTML = `
            <div class="msg__avatar msg__avatar--ai"><i class="fas fa-microchip"></i></div>
            <div class="msg__body">
                <div class="msg__author">FencingAI <span class="msg__time">正在输入...</span></div>
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
        `;
        this.chatContainer?.appendChild(typing);
        this.scrollToBottom();
    }

    hideTyping() {
        this.isTyping = false;
        const t = document.getElementById('typing-indicator');
        if (t) t.remove();
    }

    scrollToBottom() {
        if (this.chatContainer) {
            this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
        }
    }

    formatTime(date) {
        const h = date.getHours().toString().padStart(2, '0');
        const m = date.getMinutes().toString().padStart(2, '0');
        return `${h}:${m}`;
    }

    clearChatHistory() {
        if (!this.chatContainer) return;
        this.chatContainer.innerHTML = '';
        this.addMessage('对话已清空。您好！我是击剑AI专家，可以为您解答击剑相关问题。请问有什么可以帮助您的吗？', 'ai');
    }
}

function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;')
        .replace(/\n/g, '<br>');
}

document.addEventListener('DOMContentLoaded', () => {
    window.chatSystem = new ChatSystem();
});

window.ChatSystem = ChatSystem;
