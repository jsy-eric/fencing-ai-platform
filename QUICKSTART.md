# 🚀 快速启动指南

## 📋 系统要求

- Python 3.8 或更高版本
- pip 包管理器
- 现代浏览器（Chrome, Firefox, Safari, Edge）

## ⚡ 快速启动

### 1. 安装Python依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动应用

```bash
# 方法1: 使用启动脚本
python3 run.py

# 方法2: 直接启动Flask
python3 app.py

# 方法3: 使用Flask命令
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

### 3. 访问应用

打开浏览器访问: `http://localhost:5000`

## 🔧 常见问题

### Q: 提示"command not found: python"
**A:** 使用 `python3` 命令，或者创建 `python` 别名

### Q: 依赖安装失败
**A:** 确保pip是最新版本：
```bash
pip install --upgrade pip
```

### Q: 端口被占用
**A:** 修改 `app.py` 中的端口号，或关闭占用端口的程序

### Q: 模块导入错误
**A:** 确保在项目根目录下运行，且虚拟环境已激活

## 📱 功能测试

### 1. 测试YouTube视频播放
- 输入YouTube链接（如：https://www.youtube.com/watch?v=dQw4w9WgXcQ）
- 点击"加载视频"按钮
- 验证视频是否正常播放

### 2. 测试AI聊天
- 在聊天框输入击剑相关问题
- 验证AI是否正常回复
- 测试快速问题按钮

### 3. 测试弹幕系统
- 发送用户弹幕
- 使用AI生成弹幕功能
- 测试弹幕显示效果

### 4. 测试FIE数据
- 查看比赛结果数据
- 点击刷新按钮
- 验证数据更新

## 🎯 下一步

1. **自定义配置**: 修改 `config.py` 中的设置
2. **扩展功能**: 添加新的AI功能或弹幕类型
3. **部署上线**: 配置生产环境部署
4. **集成真实API**: 替换模拟数据为真实FIE API

## 📞 获取帮助

- 查看 `README.md` 获取详细文档
- 检查控制台错误信息
- 确保所有依赖正确安装

---

**⚔️ 开始您的击剑AI智能体之旅！**

