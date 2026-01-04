// 知识卡片系统
class KnowledgeCardSystem {
    constructor() {
        this.cards = [];
        this.activeCards = new Map(); // time -> card
        this.cardContainer = this.createCardContainer();
    }

    createCardContainer() {
        let container = document.getElementById('knowledge-cards-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'knowledge-cards-container';
            container.className = 'knowledge-cards-container';
            document.body.appendChild(container);
        }
        return container;
    }

    showCardAtTime(time, knowledge) {
        // 如果该时间点已有卡片，不重复显示
        if (this.activeCards.has(time)) {
            return;
        }

        const card = this.createCard(knowledge, time);
        this.cardContainer.appendChild(card);
        this.activeCards.set(time, card);

        // 3秒后自动隐藏
        setTimeout(() => {
            this.hideCard(time);
        }, 5000);
    }

    createCard(knowledge, time) {
        const card = document.createElement('div');
        card.className = 'knowledge-card';
        card.dataset.time = time;

        const header = document.createElement('div');
        header.className = 'knowledge-card-header';
        header.innerHTML = `
            <span class="card-type">${knowledge.type || '知识'}</span>
            <button class="card-close" onclick="knowledgeCardSystem.hideCard(${time})">&times;</button>
        `;

        const body = document.createElement('div');
        body.className = 'knowledge-card-body';
        body.innerHTML = `
            <h4>${knowledge.title || '击剑知识'}</h4>
            <p>${knowledge.content || ''}</p>
            ${knowledge.tips ? `<ul class="card-tips">${knowledge.tips.map(tip => `<li>${tip}</li>`).join('')}</ul>` : ''}
        `;

        const footer = document.createElement('div');
        footer.className = 'knowledge-card-footer';
        const saveText = window.i18n ? window.i18n.t('knowledge.save', '收藏') : '收藏';
        const shareText = window.i18n ? window.i18n.t('knowledge.share', '分享') : '分享';
        footer.innerHTML = `
            <button class="btn-card-action" onclick="knowledgeCardSystem.saveCard(${time})">
                <i class="fas fa-bookmark"></i> ${saveText}
            </button>
            <button class="btn-card-action" onclick="knowledgeCardSystem.shareCard(${time})">
                <i class="fas fa-share"></i> ${shareText}
            </button>
        `;

        card.appendChild(header);
        card.appendChild(body);
        card.appendChild(footer);

        // 添加动画
        card.classList.add('fade-in');

        return card;
    }

    hideCard(time) {
        const card = this.activeCards.get(time);
        if (card) {
            card.classList.add('fade-out');
            setTimeout(() => {
                if (card.parentNode) {
                    card.parentNode.removeChild(card);
                }
                this.activeCards.delete(time);
            }, 300);
        }
    }

    saveCard(time) {
        const card = this.activeCards.get(time);
        if (card) {
            const knowledge = {
                title: card.querySelector('h4').textContent,
                content: card.querySelector('p').textContent,
                time: time,
                savedAt: new Date().toISOString()
            };
            
            // 保存到本地存储
            let savedCards = JSON.parse(localStorage.getItem('saved_knowledge_cards') || '[]');
            savedCards.push(knowledge);
            localStorage.setItem('saved_knowledge_cards', JSON.stringify(savedCards));
            
            // 显示提示（使用i18n）
            const savedMsg = window.i18n ? window.i18n.t('knowledge.saved', '知识卡片已收藏') : '知识卡片已收藏';
            this.showNotification(savedMsg, 'success');
        }
    }

    shareCard(time) {
        const card = this.activeCards.get(time);
        if (card) {
            const title = card.querySelector('h4').textContent;
            const content = card.querySelector('p').textContent;
            
            if (navigator.share) {
                navigator.share({
                    title: title,
                    text: content
                });
            } else {
                // 复制到剪贴板
                navigator.clipboard.writeText(`${title}\n\n${content}`);
                const copiedMsg = window.i18n ? window.i18n.t('knowledge.copied', '内容已复制到剪贴板') : '内容已复制到剪贴板';
                this.showNotification(copiedMsg, 'success');
            }
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
}

// 初始化
window.knowledgeCardSystem = new KnowledgeCardSystem();

