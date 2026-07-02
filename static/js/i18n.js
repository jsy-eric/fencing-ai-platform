// 简易 i18n：中英文切换（UI 文案）
(() => {
    const STORAGE_KEY = 'ui_lang';

    const DICT = {
        zh: {
            'nav.home': '首页',
            'nav.about': '关于',
            'nav.contact': '联系',

            'video.title': 'YouTube视频播放',
            'video.url.placeholder': '请输入YouTube视频链接...',
            'video.weapon.auto': '剑种：自动',
            'video.weapon.foil': '花剑',
            'video.weapon.epee': '重剑',
            'video.weapon.sabre': '佩剑',
            'video.load': '加载视频',

            'chat.title': 'AI击剑专家',
            'chat.welcome': '您好！我是击剑AI专家，可以为您解答击剑相关问题，分析比赛内容，并生成相关弹幕。请问有什么可以帮助您的吗？',
            'chat.input.placeholder': '输入您的问题...',

            'danmaku.title': '弹幕控制',
            'danmaku.input.placeholder': '输入弹幕内容...',
            'danmaku.send': '发送',
            'danmaku.ai': 'AI生成弹幕',
            'danmaku.auto': '自动生成',
            'danmaku.show': '显示弹幕',
            'danmaku.speed': '弹幕速度',

            'action.title': '动作分析',
            'action.placeholder': '视频播放时将显示动作分析',

            'rec.title': '推荐学习',
            'rec.autoPush': '自动推送',
            'rec.placeholder': '正在分析视频内容...',

            'fie.title': 'FIE比赛数据',
            'fie.loading': '加载中...',
            'fie.refresh': '刷新数据',

            'footer': '© 2024 击剑AI智能体平台. 基于AI技术提供专业击剑知识和弹幕服务.'
        },
        en: {
            'nav.home': 'Home',
            'nav.about': 'About',
            'nav.contact': 'Contact',

            'video.title': 'YouTube Player',
            'video.url.placeholder': 'Paste a YouTube URL...',
            'video.weapon.auto': 'Weapon: Auto',
            'video.weapon.foil': 'Foil',
            'video.weapon.epee': 'Epee',
            'video.weapon.sabre': 'Sabre',
            'video.load': 'Load',

            'chat.title': 'AI Fencing Coach',
            'chat.welcome': "Hi! I'm an AI fencing coach. Ask me about rules, techniques, and what’s happening in the match. How can I help?",
            'chat.input.placeholder': 'Type your question...',

            'danmaku.title': 'Danmaku Controls',
            'danmaku.input.placeholder': 'Type a comment...',
            'danmaku.send': 'Send',
            'danmaku.ai': 'AI Danmaku',
            'danmaku.auto': 'Auto',
            'danmaku.show': 'Show Danmaku',
            'danmaku.speed': 'Speed',

            'action.title': 'Action Analysis',
            'action.placeholder': 'Action analysis will appear during playback',

            'rec.title': 'Recommendations',
            'rec.autoPush': 'Auto push',
            'rec.placeholder': 'Analyzing video...',

            'fie.title': 'FIE Data',
            'fie.loading': 'Loading...',
            'fie.refresh': 'Refresh',

            'footer': '© 2024 Fencing AI Platform. Professional fencing knowledge & danmaku powered by AI.'
        }
    };

    function getLang() {
        const saved = localStorage.getItem(STORAGE_KEY);
        return saved === 'en' ? 'en' : 'zh';
    }

    function setLang(lang) {
        localStorage.setItem(STORAGE_KEY, lang);
    }

    function t(lang, key) {
        return (DICT[lang] && DICT[lang][key]) || (DICT.zh && DICT.zh[key]) || '';
    }

    function applyLang(lang) {
        document.documentElement.lang = lang === 'en' ? 'en' : 'zh-CN';

        // text nodes
        document.querySelectorAll('[data-i18n]').forEach((el) => {
            const key = el.getAttribute('data-i18n');
            const val = t(lang, key);
            if (val) el.textContent = val;
        });

        // placeholders
        document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
            const key = el.getAttribute('data-i18n-placeholder');
            const val = t(lang, key);
            if (val) el.setAttribute('placeholder', val);
        });

        // option texts
        document.querySelectorAll('option[data-i18n]').forEach((el) => {
            const key = el.getAttribute('data-i18n');
            const val = t(lang, key);
            if (val) el.textContent = val;
        });

        // update language button states
        document.querySelectorAll('.lang-btn').forEach((btn) => {
            btn.classList.toggle('active', btn.dataset.lang === lang);
        });
    }

    function bindLangToggle() {
        document.querySelectorAll('.lang-btn').forEach((btn) => {
            btn.addEventListener('click', () => {
                const lang = btn.dataset.lang === 'en' ? 'en' : 'zh';
                setLang(lang);
                applyLang(lang);
            });
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        bindLangToggle();
        applyLang(getLang());
    });

    window.uiI18n = { applyLang, getLang };
})();

