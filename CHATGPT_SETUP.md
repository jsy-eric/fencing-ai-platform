# 🤖 ChatGPT集成设置指南

## 📋 概述

你的击剑AI平台现在支持ChatGPT集成！这意味着AI回复将更加智能、自然和个性化。

## 🔧 设置步骤

### 1. 获取OpenAI API密钥

1. 访问 [OpenAI官网](https://platform.openai.com/)
2. 注册或登录账户
3. 进入 [API Keys页面](https://platform.openai.com/api-keys)
4. 点击 "Create new secret key"
5. 复制生成的API密钥（格式类似：`sk-...`）

### 2. 配置环境变量

创建 `.env` 文件（在项目根目录）：

```bash
# 复制示例文件
cp env_example.txt .env
```

编辑 `.env` 文件，填入你的API密钥：

```env
# Flask配置
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True

# OpenAI配置
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.7

# AI系统配置
USE_CHATGPT=True
FALLBACK_TO_LOCAL=True
```

### 3. 重启服务器

```bash
# 停止当前服务器（Ctrl+C）
# 然后重新启动
python3 app.py
```

## 🎯 功能特性

### 智能回复
- **情感识别**：根据用户情感调整回复风格
- **上下文感知**：理解视频内容和对话历史
- **个性化**：根据用户偏好定制回复

### 双重保障
- **优先使用ChatGPT**：提供最智能的回复
- **本地AI备用**：ChatGPT不可用时自动切换
- **无缝切换**：用户无感知的故障转移

### 专业领域
- **击剑专业知识**：专门针对击剑运动优化
- **技术分析**：提供专业的技术和战术分析
- **历史知识**：丰富的击剑历史和趣闻

## 🔍 测试功能

### 1. 检查AI状态
访问：`http://localhost:8080/api/ai_status`

### 2. 测试ChatGPT连接
```bash
curl -X POST http://localhost:8080/api/test_chatgpt
```

### 3. 切换AI系统
```bash
# 切换到ChatGPT
curl -X POST http://localhost:8080/api/switch_ai \
  -H "Content-Type: application/json" \
  -d '{"ai_type": "chatgpt"}'

# 切换到本地AI
curl -X POST http://localhost:8080/api/switch_ai \
  -H "Content-Type: application/json" \
  -d '{"ai_type": "local"}'
```

## 💡 使用建议

### 1. 问题类型
- **规则询问**：ChatGPT提供详细、准确的规则解释
- **技术分析**：结合视频内容进行专业分析
- **历史知识**：分享有趣的击剑历史和故事
- **个人建议**：根据用户水平提供个性化建议

### 2. 最佳实践
- 描述具体问题，获得更准确的回复
- 结合视频内容提问，获得更相关的分析
- 保持对话连贯性，AI会记住之前的交流

## ⚠️ 注意事项

### 1. API费用
- ChatGPT API按使用量计费
- 建议设置使用限制
- 可以随时切换回本地AI

### 2. 网络要求
- 需要稳定的网络连接
- 首次调用可能需要几秒钟
- 网络问题时自动切换到本地AI

### 3. 隐私保护
- API密钥请妥善保管
- 不要将密钥提交到代码仓库
- 定期更换API密钥

## 🛠️ 故障排除

### 问题1：ChatGPT不可用
**解决方案**：
1. 检查API密钥是否正确
2. 确认网络连接正常
3. 检查OpenAI账户余额
4. 查看服务器日志

### 问题2：回复质量不佳
**解决方案**：
1. 调整 `OPENAI_TEMPERATURE` 参数
2. 增加 `OPENAI_MAX_TOKENS` 限制
3. 尝试不同的模型（gpt-4）

### 问题3：响应速度慢
**解决方案**：
1. 减少 `OPENAI_MAX_TOKENS`
2. 使用 `gpt-3.5-turbo` 模型
3. 启用本地AI备用

## 📊 监控和优化

### 1. 查看使用统计
```bash
curl http://localhost:8080/api/ai_status
```

### 2. 性能优化
- 调整模型参数
- 优化提示词
- 监控API使用量

## 🎉 享受智能击剑AI！

现在你的击剑AI平台具备了最先进的人工智能能力，可以为用户提供专业、智能、个性化的击剑知识服务！

---

**需要帮助？** 查看项目README或提交Issue。

