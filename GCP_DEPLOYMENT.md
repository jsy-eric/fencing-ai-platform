# Google Cloud Platform 部署指南

本指南将帮助您在Google Cloud Platform上部署和运行击剑AI智能体平台。

## 部署方式选择

### 方式1: Google Cloud Run（推荐）
- ✅ 最简单，无需管理服务器
- ✅ 自动扩缩容
- ✅ 按使用量付费
- ✅ 支持HTTPS

### 方式2: Google App Engine
- ✅ 完全托管
- ✅ 自动扩缩容
- ✅ 内置监控

### 方式3: Google Compute Engine
- ✅ 完全控制
- ✅ 适合长期运行
- ✅ 需要手动管理

---

## 方式1: Google Cloud Run 部署（推荐）

### 前置要求

1. **Google Cloud账户**
   - 访问 https://cloud.google.com/
   - 创建新项目或选择现有项目
   - 启用计费（有免费额度）

2. **安装Google Cloud SDK**
   ```bash
   # macOS
   brew install google-cloud-sdk

   # 或下载安装包
   # https://cloud.google.com/sdk/docs/install
   ```

3. **登录和初始化**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

### 部署步骤

#### 步骤1: 创建Dockerfile

已创建 `Dockerfile`（见下文）

#### 步骤2: 构建和推送Docker镜像

```bash
# 设置项目ID
export PROJECT_ID=your-project-id

# 构建镜像
gcloud builds submit --tag gcr.io/$PROJECT_ID/fencing-ai-platform

# 或使用Docker直接构建
docker build -t gcr.io/$PROJECT_ID/fencing-ai-platform .
docker push gcr.io/$PROJECT_ID/fencing-ai-platform
```

#### 步骤3: 部署到Cloud Run

```bash
# 部署服务
gcloud run deploy fencing-ai-platform \
  --image gcr.io/$PROJECT_ID/fencing-ai-platform \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --set-env-vars="FLASK_ENV=production"
```

#### 步骤4: 访问应用

部署完成后，Cloud Run会提供一个HTTPS URL，例如：
```
https://fencing-ai-platform-xxxxx-uc.a.run.app
```

### 配置环境变量

在Cloud Run控制台或使用命令行设置环境变量：

```bash
gcloud run services update fencing-ai-platform \
  --set-env-vars="DEEPSEEK_API_KEY=your-key,FLASK_ENV=production"
```

---

## 方式2: Google App Engine 部署

### 步骤1: 创建app.yaml

已创建 `app.yaml`（见下文）

### 步骤2: 部署应用

```bash
# 初始化App Engine（首次部署）
gcloud app create --region=us-central

# 部署应用
gcloud app deploy

# 查看应用
gcloud app browse
```

### 步骤3: 配置环境变量

在 `app.yaml` 中设置环境变量，或使用Secret Manager。

---

## 方式3: Google Compute Engine 部署

### 步骤1: 创建VM实例

```bash
# 创建实例
gcloud compute instances create fencing-ai-vm \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud \
  --machine-type=e2-medium \
  --boot-disk-size=20GB \
  --tags=http-server,https-server

# 允许HTTP流量
gcloud compute firewall-rules create allow-http \
  --allow tcp:8080 \
  --source-ranges 0.0.0.0/0 \
  --target-tags http-server
```

### 步骤2: SSH连接到实例

```bash
gcloud compute ssh fencing-ai-vm
```

### 步骤3: 在VM上安装和运行

```bash
# 更新系统
sudo apt-get update
sudo apt-get install -y python3 python3-pip git

# 克隆项目（或上传文件）
git clone YOUR_REPO_URL
cd fencing_ai_platform

# 安装依赖
pip3 install -r requirements.txt

# 运行应用
python3 app.py
```

### 步骤4: 使用systemd保持运行

创建服务文件 `/etc/systemd/system/fencing-ai.service`:

```ini
[Unit]
Description=Fencing AI Platform
After=network.target

[Service]
Type=simple
User=YOUR_USER
WorkingDirectory=/path/to/fencing_ai_platform
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl enable fencing-ai
sudo systemctl start fencing-ai
```

---

## 必需文件

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=8080

# 启动应用
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

### app.yaml (App Engine)

```yaml
runtime: python39

env_variables:
  FLASK_ENV: production
  PORT: 8080

automatic_scaling:
  min_instances: 1
  max_instances: 10

resources:
  cpu: 2
  memory_gb: 2
  disk_size_gb: 10

handlers:
- url: /.*
  script: auto
```

### .gcloudignore

```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
env/
.venv
.git/
.gitignore
*.md
.env
*.log
```

---

## 配置环境变量

### 使用Secret Manager（推荐）

```bash
# 创建密钥
echo -n "your-deepseek-api-key" | gcloud secrets create deepseek-api-key --data-file=-

# 在Cloud Run中引用
gcloud run services update fencing-ai-platform \
  --update-secrets=DEEPSEEK_API_KEY=deepseek-api-key:latest
```

### 在app.yaml中设置（App Engine）

```yaml
env_variables:
  DEEPSEEK_API_KEY: 'your-key-here'
  FLASK_ENV: production
```

---

## 使用Gunicorn（生产环境）

### 安装Gunicorn

```bash
pip install gunicorn
```

### 更新requirements.txt

添加：
```
gunicorn==21.2.0
```

### 运行命令

```bash
gunicorn --bind 0.0.0.0:8080 --workers 4 --threads 2 app:app
```

---

## 快速部署脚本

### deploy-cloud-run.sh

```bash
#!/bin/bash

PROJECT_ID="your-project-id"
SERVICE_NAME="fencing-ai-platform"
REGION="us-central1"

echo "🚀 开始部署到Google Cloud Run..."

# 构建镜像
echo "📦 构建Docker镜像..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME

# 部署服务
echo "🚀 部署服务..."
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10

echo "✅ 部署完成！"
echo "访问URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'
```

使用：
```bash
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

---

## 常见问题

### Q: 如何查看日志？

```bash
# Cloud Run
gcloud run services logs read fencing-ai-platform --region us-central1

# App Engine
gcloud app logs tail -s default

# Compute Engine
journalctl -u fencing-ai -f
```

### Q: 如何更新应用？

```bash
# Cloud Run
gcloud run deploy fencing-ai-platform --image gcr.io/$PROJECT_ID/fencing-ai-platform

# App Engine
gcloud app deploy

# Compute Engine
git pull && sudo systemctl restart fencing-ai
```

### Q: 如何设置自定义域名？

1. 在Cloud Run控制台添加自定义域名
2. 验证域名所有权
3. 配置DNS记录

### Q: MediaPipe在Cloud Run上能运行吗？

可以，但需要注意：
- 使用较大的内存配置（至少2Gi）
- 可能需要更长的启动时间
- 考虑使用GPU实例（Cloud Run暂不支持，可用Compute Engine）

---

## 成本估算

### Cloud Run
- 免费额度：每月200万请求，360,000 GB-秒
- 超出后：约$0.40/百万请求，$0.0000025/GB-秒

### App Engine
- 免费额度：每天28小时实例时间
- 超出后：约$0.05/小时（F1实例）

### Compute Engine
- e2-medium: 约$30/月
- 包含750小时免费额度（f1-micro）

---

## 安全建议

1. **使用Secret Manager存储API密钥**
2. **启用HTTPS（Cloud Run自动提供）**
3. **设置访问控制（IAM）**
4. **定期更新依赖**
5. **启用日志监控**

---

## 下一步

1. **设置CI/CD**: 使用Cloud Build自动部署
2. **监控**: 设置Cloud Monitoring告警
3. **备份**: 配置定期备份
4. **扩展**: 根据流量调整资源配置

---

**🎉 部署完成后，您的应用将在Google Cloud上运行！**

