#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
击剑AI智能体平台启动脚本
"""

import os
import sys
from app import app

def main():
    """主函数"""
    print("⚔️ 击剑AI智能体平台启动中...")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 错误: 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)
    
    # 检查依赖
    try:
        import flask
        import requests
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 依赖缺失: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 设置环境变量
    os.environ.setdefault('FLASK_ENV', 'development')
    os.environ.setdefault('FLASK_DEBUG', 'True')
    
    print("🚀 启动Flask应用...")
    print("📱 访问地址: http://localhost:8888")
    print("🛑 按 Ctrl+C 停止应用")
    print("=" * 50)
    
    try:
        # 启动应用
        app.run(
            host='0.0.0.0',
            port=8888,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n🛑 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

