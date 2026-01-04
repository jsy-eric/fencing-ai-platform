# 🚀 Google Cloud 快速部署指南

## 最简单的方法：使用部署脚本

### 1. 安装Google Cloud SDK

```bash
# macOS
brew install google-cloud-sdk

# 或访问
# https://cloud.google.com/sdk/docs/install
```

### 2. 登录和设置项目

```bash
# 登录
gcloud auth login

# 设置项目ID（替换为您的项目ID）
export GOOGLE_CLOUD_PROJECT=your-project-id
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

### 3. 运行部署脚本

```bash
# 修改脚本中的PROJECT_ID，然后运行
chmod +x deploy-cloud-run.sh
./deploy-cloud-run.sh
```

### 4. 访问应用

脚本会输出服务URL，例如：
```
https://fencing-ai-platform-xxxxx-uc.a.run.app
```

---

## 手动部署步骤

### 步骤1: 构建镜像

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/fencing-ai-platform
```

### 步骤2: 部署服务

```bash
gcloud run deploy fencing-ai-platform \
  --image gcr.io/YOUR_PROJECT_ID/fencing-ai-platform \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 步骤3: 设置环境变量

```bash
gcloud run services update fencing-ai-platform \
  --set-env-vars="DEEPSEEK_API_KEY=your-key"
```

---

## 常见问题

**Q: 如何获取项目ID？**
A: 访问 https://console.cloud.google.com/ 创建或选择项目

**Q: 部署需要多长时间？**
A: 首次部署约5-10分钟，后续更新约2-3分钟

**Q: 如何查看日志？**
A: `gcloud run services logs read fencing-ai-platform --region us-central1`

**Q: 如何更新应用？**
A: 重新运行部署脚本或 `gcloud run deploy` 命令

---

**详细文档请查看 `GCP_DEPLOYMENT.md`**

