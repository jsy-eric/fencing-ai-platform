// 互动式知识问答系统
class InteractiveQA {
    constructor() {
        this.questions = [];
        this.currentQuestion = null;
        this.qaContainer = null;
    }

    init(containerId = 'interactive-qa-container') {
        this.qaContainer = document.getElementById(containerId);
        if (!this.qaContainer) {
            this.qaContainer = document.createElement('div');
            this.qaContainer.id = containerId;
            this.qaContainer.className = 'interactive-qa-container';
            const videoContainer = document.getElementById('video-player');
            if (videoContainer && videoContainer.parentNode) {
                videoContainer.parentNode.appendChild(this.qaContainer);
            }
        }
    }

    generateQuestionAtTime(time, context) {
        const questions = this.getQuestionsForContext(context);
        if (questions.length > 0) {
            const question = questions[Math.floor(Math.random() * questions.length)];
            this.showQuestion(question, time);
        }
    }

    getQuestionsForContext(context) {
        const contextLower = context.toLowerCase();
        const questions = [];

        if (contextLower.includes('进攻') || contextLower.includes('直刺')) {
            questions.push({
                text: "你知道直刺技术的关键要点吗？",
                options: [
                    "保持身体平衡，手臂伸直",
                    "快速出击，剑尖对准目标",
                    "以上都是"
                ],
                correct: 2,
                explanation: "直刺需要保持身体平衡、手臂伸直、快速出击，并且剑尖要对准目标。"
            });
        }

        if (contextLower.includes('防守') || contextLower.includes('格挡')) {
            questions.push({
                text: "格挡防守的关键是什么？",
                options: [
                    "及时反应",
                    "准备反击",
                    "以上都是"
                ],
                correct: 2,
                explanation: "格挡防守需要及时反应，同时要为反击做好准备。"
            });
        }

        if (contextLower.includes('战术') || contextLower.includes('策略')) {
            questions.push({
                text: "击剑战术的核心是什么？",
                options: [
                    "距离控制",
                    "时机把握",
                    "以上都是"
                ],
                correct: 2,
                explanation: "击剑战术的核心包括距离控制、时机把握、节奏变化等多个方面。"
            });
        }

        // 默认问题
        if (questions.length === 0) {
            questions.push({
                text: "你想了解更多关于这个动作的技术要点吗？",
                options: ["是的", "稍后再说"],
                correct: 0,
                explanation: "点击'是的'可以查看详细的技术分析。"
            });
        }

        return questions;
    }

    showQuestion(question, time) {
        if (!this.qaContainer) {
            this.init();
        }

        // 移除旧问题
        if (this.currentQuestion) {
            this.currentQuestion.remove();
        }

        const qaCard = document.createElement('div');
        qaCard.className = 'qa-card';
        qaCard.dataset.time = time;

        qaCard.innerHTML = `
            <div class="qa-header">
                <h4>💡 知识问答</h4>
                <button class="qa-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
            </div>
            <div class="qa-body">
                <p class="qa-question">${question.text}</p>
                <div class="qa-options">
                    ${question.options.map((option, index) => `
                        <button class="qa-option" onclick="interactiveQA.selectAnswer(${index}, ${question.correct}, '${question.explanation.replace(/'/g, "\\'")}')">
                            ${option}
                        </button>
                    `).join('')}
                </div>
            </div>
        `;

        this.qaContainer.appendChild(qaCard);
        this.currentQuestion = qaCard;
    }

    selectAnswer(selectedIndex, correctIndex, explanation) {
        const qaCard = this.currentQuestion;
        if (!qaCard) return;

        const options = qaCard.querySelectorAll('.qa-option');
        options.forEach((option, index) => {
            if (index === correctIndex) {
                option.classList.add('correct');
            } else if (index === selectedIndex && index !== correctIndex) {
                option.classList.add('wrong');
            }
            option.disabled = true;
        });

        // 显示解释
        const explanationDiv = document.createElement('div');
        explanationDiv.className = 'qa-explanation';
        explanationDiv.innerHTML = `
            <p><strong>${selectedIndex === correctIndex ? '✓ 回答正确！' : '✗ 回答错误'}</strong></p>
            <p>${explanation}</p>
        `;
        qaCard.querySelector('.qa-body').appendChild(explanationDiv);

        // 3秒后自动关闭
        setTimeout(() => {
            if (qaCard.parentNode) {
                qaCard.classList.add('fade-out');
                setTimeout(() => {
                    if (qaCard.parentNode) {
                        qaCard.parentNode.removeChild(qaCard);
                    }
                }, 300);
            }
        }, 3000);
    }
}

// 初始化
window.interactiveQA = new InteractiveQA();

