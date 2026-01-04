// 国际化支持 - 前端i18n模块
class I18n {
    constructor() {
        // 从window.I18N_CONFIG或localStorage获取语言设置
        const configLang = window.I18N_CONFIG ? window.I18N_CONFIG.currentLanguage : null;
        this.currentLanguage = configLang || localStorage.getItem('language') || 'zh_CN';
        this.translations = {};
        this.init();
    }

    async init() {
        await this.loadTranslations();
        // 延迟应用翻译，确保DOM已加载
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                this.applyTranslations();
                this.setupLanguageSwitcher();
            });
        } else {
            this.applyTranslations();
            this.setupLanguageSwitcher();
        }
    }

    async loadTranslations() {
        try {
            const response = await fetch(`/api/translations?lang=${this.currentLanguage}`);
            const data = await response.json();
            if (data.success) {
                this.translations = data.translations;
            }
        } catch (error) {
            console.error('Failed to load translations:', error);
            // 使用默认翻译
            this.translations = this.getDefaultTranslations();
        }
    }

    getDefaultTranslations() {
        // 默认翻译（如果API加载失败时使用）
        const defaults = {
            zh_CN: {
                app: { title: "击剑AI智能体平台" },
                video: { title: "YouTube视频播放", placeholder: "请输入YouTube视频链接...", load_button: "加载视频" },
                chat: { title: "AI击剑专家", placeholder: "输入您的问题..." },
                danmaku: { title: "弹幕控制", placeholder: "输入弹幕内容...", send: "发送" }
            },
            en_US: {
                app: { title: "Fencing AI Platform" },
                video: { title: "YouTube Video Player", placeholder: "Enter YouTube video link...", load_button: "Load Video" },
                chat: { title: "AI Fencing Expert", placeholder: "Enter your question..." },
                danmaku: { title: "Danmaku Control", placeholder: "Enter danmaku content...", send: "Send" }
            }
        };
        return defaults[this.currentLanguage] || {};
    }

    t(key, defaultValue = '') {
        const keys = key.split('.');
        let value = this.translations;
        
        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = value[k];
            } else {
                return defaultValue || key;
            }
        }
        
        return typeof value === 'string' ? value : (defaultValue || key);
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('language', lang);
        this.loadTranslations().then(() => {
            this.applyTranslations();
            this.updateLanguageSwitcher();
        });
    }

    applyTranslations() {
        // 更新所有带有 data-i18n 属性的元素
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            if (translation) {
                element.textContent = translation;
            }
        });

        // 更新所有带有 data-i18n-placeholder 属性的元素
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            const translation = this.t(key);
            if (translation) {
                element.placeholder = translation;
            }
        });

        // 更新标题
        const titleElement = document.querySelector('title');
        if (titleElement) {
            titleElement.textContent = this.t('app.title', '击剑AI智能体平台');
        }

        // 更新HTML lang属性
        document.documentElement.lang = this.currentLanguage === 'zh_CN' ? 'zh-CN' : 'en-US';
    }

    setupLanguageSwitcher() {
        const langSwitch = document.getElementById('lang-switch');
        if (langSwitch) {
            langSwitch.addEventListener('click', () => {
                const newLang = this.currentLanguage === 'zh_CN' ? 'en_US' : 'zh_CN';
                this.setLanguage(newLang);
                
                // 通知后端更新语言
                fetch('/api/set_language', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ language: newLang })
                });
            });
        }
        this.updateLanguageSwitcher();
    }

    updateLanguageSwitcher() {
        const langCode = document.getElementById('lang-code');
        if (langCode) {
            langCode.textContent = this.currentLanguage === 'zh_CN' ? '中文' : 'English';
        }
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// 全局i18n实例
window.i18n = new I18n();

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // i18n已经在构造函数中初始化
    console.log('i18n initialized, current language:', window.i18n.getCurrentLanguage());
});

