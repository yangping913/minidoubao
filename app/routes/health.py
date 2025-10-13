from flask import Blueprint, jsonify, current_app
from datetime import datetime
from app.config import Config

# 创建蓝图
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "deepseek_configured": bool(Config.DEEPSEEK_API_KEY),
        "conversation_count": len(current_app.context_manager.conversation_history)
    })