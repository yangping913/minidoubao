from flask import Blueprint, jsonify, current_app
from datetime import datetime
import logging
from app.config import Config

# 创建蓝图
health_bp = Blueprint('health', __name__)
logger = logging.getLogger(__name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    try:
        # 检查基础服务状态
        deepseek_configured = bool(Config.DEEPSEEK_API_KEY)

        # 检查管理器是否可用
        model_manager_ready = hasattr(current_app, 'model_manager') and current_app.model_manager is not None
        context_manager_ready = hasattr(current_app, 'context_manager') and current_app.context_manager is not None

        conversation_count = 0
        if context_manager_ready:
            try:
                conversation_count = len(current_app.context_manager.conversation_history)
            except Exception:
                conversation_count = -1  # 表示无法获取

        status = "healthy" if (deepseek_configured and model_manager_ready and context_manager_ready) else "degraded"

        return jsonify({
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "services": {
                "deepseek_configured": deepseek_configured,
                "model_manager_ready": model_manager_ready,
                "context_manager_ready": context_manager_ready
            },
            "conversation_count": conversation_count,
            "environment": "production" if not Config.DEBUG else "development"
        })

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 500


@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """就绪检查端点"""
    try:
        # 检查所有必要的服务是否就绪
        checks = {
            "model_manager": hasattr(current_app, 'model_manager') and current_app.model_manager is not None,
            "context_manager": hasattr(current_app, 'context_manager') and current_app.context_manager is not None,
            "deepseek_api": bool(Config.DEEPSEEK_API_KEY)
        }

        all_ready = all(checks.values())

        response = {
            "status": "ready" if all_ready else "not_ready",
            "timestamp": datetime.now().isoformat(),
            "checks": checks
        }

        return jsonify(response), 200 if all_ready else 503

    except Exception as e:
        logger.error(f"就绪检查失败: {str(e)}")
        return jsonify({
            "status": "not_ready",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }), 503