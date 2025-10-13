from flask import Blueprint, jsonify
from datetime import datetime
from app import create_app
from app.config import Config

# 创建蓝图
health_bp = Blueprint('health', __name__)

# 获取应用实例以访问全局对象
app = create_app()

@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "deepseek_configured": bool(Config.DEEPSEEK_API_KEY),
        "conversation_count": len(app.context_manager.conversation_history)
    })