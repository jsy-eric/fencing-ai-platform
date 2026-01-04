#!/bin/bash

# Google Cloud Run 部署脚本
# 使用方法: ./deploy-cloud-run.sh

set -e

# 配置变量（请修改为您的项目ID）
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
SERVICE_NAME="fencing-ai-platform"
REGION="${REGION:-us-central1}"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "⚔️  击剑AI智能体平台 - Google Cloud Run 部署"
echo "================================================"
echo "项目ID: ${PROJECT_ID}"
echo "服务名称: ${SERVICE_NAME}"
echo "区域: ${REGION}"
echo "================================================"

# 检查gcloud是否安装
if ! command -v gcloud &> /dev/null; then
    echo "❌ 错误: 未找到 gcloud 命令"
    echo "请安装 Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# 检查是否登录
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "⚠️  未检测到活动账户，正在登录..."
    gcloud auth login
fi

# 设置项目
echo "📋 设置项目..."
gcloud config set project ${PROJECT_ID}

# 启用必要的API
echo "🔧 启用必要的API..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 构建Docker镜像
echo "📦 构建Docker镜像..."
gcloud builds submit --tag ${IMAGE_NAME} --timeout=20m

# 部署到Cloud Run
echo "🚀 部署到Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars="FLASK_ENV=production,PORT=8080" \
  --port 8080

# 获取服务URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region ${REGION} \
  --format 'value(status.url)')

echo ""
echo "✅ 部署完成！"
echo "================================================"
echo "🌐 服务URL: ${SERVICE_URL}"
echo "================================================"
echo ""
echo "📝 后续操作:"
echo "1. 设置环境变量（如API密钥）:"
echo "   gcloud run services update ${SERVICE_NAME} \\"
echo "     --region ${REGION} \\"
echo "     --set-env-vars=\"DEEPSEEK_API_KEY=your-key\""
echo ""
echo "2. 查看日志:"
echo "   gcloud run services logs read ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "3. 更新应用:"
echo "   重新运行此脚本即可"
echo ""

