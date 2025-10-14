from flask import Blueprint, jsonify, current_app
from datetime import datetime

# 创建蓝图
health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    app = current_app
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "deepseek_configured": bool(app.config.get('DEEPSEEK_API_KEY')),
        "conversation_count": len(app.context_manager.conversation_history)
    })