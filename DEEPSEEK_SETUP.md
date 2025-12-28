# DeepSeek API 设置指南

## 🚀 获取DeepSeek API密钥

### 1. 注册DeepSeek账户
1. 访问 [DeepSeek官网](https://www.deepseek.com/)
2. 点击"注册"创建账户
3. 完成邮箱验证

### 2. 获取API密钥
1. 登录后进入 [API管理页面](https://platform.deepseek.com/)
2. 点击"创建API密钥"
3. 复制生成的API密钥（格式：`sk-xxxxxxxxxxxxxxxx`）

### 3. 配置环境变量
1. 复制 `env_example.txt` 为 `.env`
2. 编辑 `.env` 文件，填入你的API密钥：

```bash
# DeepSeek配置
DEEPSEEK_API_KEY=sk-your-actual-api-key-here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_MAX_TOKENS=1000
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_BASE_URL=https://api.deepseek.com

# AI系统配置
USE_DEEPSEEK=True
FALLBACK_TO_LOCAL=True
```

## 💰 DeepSeek定价优势

- **更便宜**: DeepSeek的价格通常比OpenAI便宜很多
- **中文支持**: 对中文理解更好
- **高性能**: 提供高质量的对话体验
- **稳定**: 服务稳定可靠

## 🔧 测试配置

配置完成后，重启服务器并测试：

```bash
# 重启服务器
python3 app.py

# 测试DeepSeek连接
curl -X POST http://localhost:8080/api/test_deepseek
```

## 📊 API状态检查

访问以下端点检查AI系统状态：

```bash
curl http://localhost:8080/api/ai_status
```

应该看到：
```json
{
  "status": {
    "deepseek_available": true,
    "use_deepseek": true,
    "fallback_enabled": true,
    "conversation_count": 0,
    "last_activity": null
  },
  "success": true
}
```

## 🎯 使用建议

1. **首次使用**: 建议先测试连接，确保API密钥正确
2. **备用系统**: 启用 `FALLBACK_TO_LOCAL=True` 确保服务稳定
3. **监控使用**: 定期检查API使用量和余额
4. **优化设置**: 根据需求调整 `MAX_TOKENS` 和 `TEMPERATURE`

## ❓ 常见问题

### Q: API密钥无效怎么办？
A: 检查密钥格式是否正确，确保没有多余的空格或字符

### Q: 连接超时怎么办？
A: 检查网络连接，或尝试增加超时时间

### Q: 如何切换回本地AI？
A: 设置 `USE_DEEPSEEK=False` 或使用切换API

## 🎉 完成！

配置完成后，你的击剑AI平台将使用DeepSeek提供更智能的对话体验！

